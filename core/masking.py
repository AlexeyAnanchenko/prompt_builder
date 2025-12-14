import re
import json
from collections import defaultdict
from typing import Dict, Any, List, Optional, Set

class ContextMasker:
    def __init__(self):
        # forward: {(category, real_value): mask_id}
        self.map_forward: Dict[tuple, str] = {}
        # reverse: {mask_id: real_value}
        self.map_reverse: Dict[str, str] = {}
        # счетчики
        self.counters: Dict[str, int] = defaultdict(int)
        # Сюда мы загрузим ID всех параметров перед генерацией
        self.known_parameters: Set[str] = set()

        # Сюда входят имена агрегатных функций ClickHouse и другие ключевые слова
        self.reserved_literals = {
            # ClickHouse Aggregates (часто используются в arrayReduce)
            'groupUniqArray', 'uniq', 'uniqExact', 'groupArray', 
            'sum', 'min', 'max', 'avg', 'count', 'any', 'anyLast', 'argMin', 'argMax',
            'topK', 'quantiles', 'quantilesExact', 'median',
            # Типы данных (иногда бывают в строках)
            'String', 'Int64', 'UInt64', 'Float64', 'Date', 'DateTime'
            # Специальные значения (уже были в логике, но добавим явно)
            'none', 'null', 'true', 'false', '', '%d.%m', 'MONTH', 'DAY', 'YEAR',
            # Форматирование
            'JSON', 'CSV', 'TSV'
        }
        
        # --- Регулярки ---
        
        # 1. dictGet с TUPLE
        self.re_dict_tuple = re.compile(r"dictGet\s*\(\s*'([^']+)'\s*,\s*tuple\s*\((.*?)\)", re.DOTALL)
        # 2. dictGet одиночный
        self.re_dict_single = re.compile(r"dictGet\s*\(\s*'([^']+)'\s*,\s*'([^']+)'", re.DOTALL)
        # 3. tupleElement (tuple, 'columnName')
        self.re_tuple_element = re.compile(r"(?i)tupleElement\s*\(\s*([a-zA-Z0-9_\.]+)\s*,\s*'((?:''|[^'])*)'\s*\)", re.DOTALL)
        # 4. Параметры в фигурных скобках {param}
        self.re_param_braces = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')
        # 5. Свойства через точку: Entity.Property
        self.re_dot_prop = re.compile(r"\b([a-zA-Z][a-zA-Z0-9_]*)\.([a-zA-Z0-9_]+)\b")
        # 6. Литералы в кавычках 'value' (с учетом экранирования '')
        self.re_literal = re.compile(r"'((?:''|[^'])*)'")
        # 7. Отдельные слова (для Java-style условий: structRoots != null)
        self.re_word = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b")

    def clear(self) -> None:
        self.map_forward.clear()
        self.map_reverse.clear()
        self.counters.clear()
        self.known_parameters.clear()

    def set_known_parameters(self, params: Set[str]) -> None:
        """Загружает список известных ID параметров, чтобы детектировать их в Java-условиях."""
        self.known_parameters = params

    def _is_generated_mask(self, val: str) -> bool:
        """
        Проверяет, является ли строка уже сгенерированной маской.
        Ловит форматы: ENT_1, PARAM_2, DB.DICT_1, DB.TBL_5 и т.д.
        """
        if not val:
            return False
            
        # Паттерн покрывает:
        # 1. Простые маски: ENT_1, P_2, TBL_3
        # 2. Составные маски БД: DB.DICT_1, DB.TBL_2
        # ^ - начало строки, $ - конец, \d+ - цифры
        return bool(re.match(r'^(DB\.[A-Z]+|[A-Z]+)_\d+$', val))

    def register(self, value: Any, category: str) -> str:
        if value is None: return "null"
        val_str = str(value)
        if not val_str: return val_str

        # --- ИСПРАВЛЕНИЕ: Защита от двойного маскирования ---
        # Если значение уже похоже на нашу маску (например, DB.DICT_1),
        # мы возвращаем его как есть, не регистрируя новую маску.
        if self._is_generated_mask(val_str):
            return val_str
            
        key = (category, val_str)
        if key in self.map_forward:
            return self.map_forward[key]
        
        self.counters[category] += 1
        mask = f"{category}_{self.counters[category]}"
        self.map_forward[key] = mask
        self.map_reverse[mask] = val_str
        return mask

    def mask_text(self, text: str) -> str:
        """Для обычного текста (не SQL кода)."""
        if not text: return ""
        # Сортируем от длинных к коротким
        sorted_items = sorted(self.map_forward.items(), key=lambda x: len(x[0][1]), reverse=True)
        masked_text = text
        for (cat, val), mask in sorted_items:
            # Не заменяем системные слова типа null, true (если они вдруг попали в словарь)
            if val.lower() in ['null', 'true', 'false']: continue
            pattern = r'\b' + re.escape(val) + r'\b'
            masked_text = re.sub(pattern, mask, masked_text)
        return masked_text

    def unmask_text(self, text: str) -> str:
        """
        НОВЫЙ МЕТОД: Расшифровывает замаскированный текст обратно в оригинальный.
        Использует map_reverse для замены масок на реальные значения.
        """
        if not text:
            return ""
        
        if not self.map_reverse:
            return text
        
        # Сортируем маски от длинных к коротким (чтобы избежать частичных замен)
        # Например, DB.DICT_10 должна быть обработана раньше, чем P_1
        sorted_masks = sorted(self.map_reverse.items(), key=lambda x: len(x[0]), reverse=True)
        
        unmasked_text = text
        for mask, original_value in sorted_masks:
            # Используем границы слов для точной замены
            pattern = r'\b' + re.escape(mask) + r'\b'
            unmasked_text = re.sub(pattern, original_value, unmasked_text)
        
        return unmasked_text

    def mask_json(self, data: Any) -> Any:
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                category = self._infer_json_category(k)
                if k in ['valueExpr', 'condition', 'expression'] and isinstance(v, str):
                     new_dict[k] = self.mask_formula(v)
                elif category and isinstance(v, str):
                    new_dict[k] = self.register(v, category)
                elif isinstance(v, (dict, list)):
                    new_dict[k] = self.mask_json(v)
                else:
                    new_dict[k] = v
            return new_dict
        elif isinstance(data, list):
            return [self.mask_json(item) for item in data]
        return data

    def _infer_json_category(self, key: str) -> Optional[str]:
        # Словарь маппинга ключей JSON на категории масок
        mapping = {
            'entity': 'ENT', 'entity_type': 'ENT',
            'property': 'P', 'property_id': 'P', 
            'parameter': 'PARAM',
            'dataset': 'DS',
            'ordering': 'ORD', 'limitation': 'LIM', 'aggregation': 'AGG',
            'table': 'TBL', 'physical_name': 'DB.TBL',
        }
        return mapping.get(key)
    
    def _is_meaningful_string(self, s: str) -> bool:
        """Фильтр, чтобы не маскировать знаки препинания и короткий мусор."""
        if len(s) < 2: return False
        # Если состоит только из символов пунктуации - пропускаем
        if re.match(r'^[.,;(){}\[\]\s\-_=]+$', s): return False
        # Если это похоже на кусок SQL (например, contains comma and space)
        # но это спорно, оставим пока проверку на пунктуацию
        return True

    def mask_formula(self, text: str) -> str:
        if not text: return text
        
        # 1. dictGet с TUPLE
        def replace_tuple_dict(match):
            d_name = match.group(1)
            tuple_content = match.group(2)
            mask_d = self.register(d_name, 'DB.DICT')
            
            # Внутри кортежа заменяем литералы на COL
            def replace_col_item(m):
                col_val = m.group(1)
                if col_val:
                    return f"'{self.register(col_val, 'COL')}'"
                return "''"
            
            masked_content = self.re_literal.sub(replace_col_item, tuple_content)
            return f"dictGet('{mask_d}', tuple({masked_content})"
        
        text = self.re_dict_tuple.sub(replace_tuple_dict, text)

        # 2. dictGet одиночный
        def replace_single_dict(match):
            d_name = match.group(1)
            c_name = match.group(2)
            mask_d = self.register(d_name, 'DB.DICT')
            mask_c = self.register(c_name, 'COL')
            return f"dictGet('{mask_d}', '{mask_c}'"
        text = self.re_dict_single.sub(replace_single_dict, text)

        # 3. tupleElement (tuple, 'columnName')
        def replace_tuple_elem(match):
            prefix = match.group(1)
            col_name = match.group(2)
            mask_c = self.register(col_name, 'COL')
            return f"tupleElement({prefix}, '{mask_c}')"

        text = self.re_tuple_element.sub(replace_tuple_elem, text)
        
        # 4. Параметры в фигурных скобках {param}
        def replace_param_braces(match):
            p_val = match.group(1)
            return f"{{{self.register(p_val, 'PARAM')}}}"
        text = self.re_param_braces.sub(replace_param_braces, text)

        # 5. Entity.Property
        def replace_prop(match):
            left = match.group(1)
            right = match.group(2)
            
            is_entity = (('ENT', left) in self.map_forward) or (('TBL', left) in self.map_forward) or left.startswith('ENT_') or left.startswith('TBL_')
            
            if is_entity:
                cat = 'ENT' if ('ENT', left) in self.map_forward or left.startswith('ENT_') else 'TBL'
                mask_l = self.register(left, cat)
                mask_r = self.register(right, 'P')
                return f"{mask_l}.{mask_r}"
            
            return match.group(0)
        text = self.re_dot_prop.sub(replace_prop, text)
        
        # 6. Java-style параметры
        def replace_java_var(match):
            word = match.group(1)
            if word in self.known_parameters:
                return self.register(word, 'PARAM')
            return word
        
        text = self.re_word.sub(replace_java_var, text)

        # 7. Литералы 'string' -> БОЛЬШЕ НЕ OBJ (ИЗМЕНЕНО)
        def replace_lit(match):
            val = match.group(1)
            
            # Если это зарезервированное слово или артефакт синтаксиса - возвращаем как есть
            if val in self.reserved_literals:
                return f"'{val}'"

            if ')' in val or '(' in val or (',' in val and ' ' not in val):
                 return f"'{val}'"

            # Оставляем маскировку словарей (DB.DICT), если это похоже на схему (schema.name)
            # Если хотите убрать и это - закомментируйте следующие две строки
            if '.' in val and '_' in val and ' ' not in val:
                 return f"'{self.register(val, 'DB.DICT')}'"

            # Если значение УЖЕ есть в словаре (например, имя сущности попало в кавычки) - используем маску
            # Это полезно для целостности (чтобы 'person' стало 'ENT_1', если person уже ENT_1)
            if val in self.map_forward: # Проверка по ключу требует кортежа, тут упрощенно ищем value
                 # Но у нас ключи (cat, val). Сложно найти быстро без категории.
                 # Поэтому проверим обратный маппинг на случай повторного прохода (не нужно)
                 pass

            # Ищем, не зарегистрировано ли это слово уже под какой-то категорией
            # Это опционально, но полезно.
            for (cat, real_val), mask in self.map_forward.items():
                if real_val == val:
                    return f"'{mask}'"

            return f"'{val}'"

        text = self.re_literal.sub(replace_lit, text)
        
        return text