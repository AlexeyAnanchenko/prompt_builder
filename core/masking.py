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
            'String', 'Int64', 'UInt64', 'Float64', 'Date', 'DateTime',
            # Специальные значения (уже были в логике, но добавим явно)
            'none', 'null', 'true', 'false', '', 
            # Форматирование
            'JSON', 'CSV', 'TSV'
        }
        
        # --- Регулярки ---
        
        # 1. dictGet с TUPLE
        self.re_dict_tuple = re.compile(r"dictGet\s*\(\s*'([^']+)'\s*,\s*tuple\s*\((.*?)\)", re.DOTALL)
        # 2. dictGet одиночный
        self.re_dict_single = re.compile(r"dictGet\s*\(\s*'([^']+)'\s*,\s*'([^']+)'", re.DOTALL)
        # 3. Параметры в фигурных скобках {param}
        self.re_param_braces = re.compile(r'\{([a-zA-Z0-9_]+)\}')
        # 4. Свойства через точку: Entity.Property
        self.re_dot_prop = re.compile(r"\b([a-zA-Z][a-zA-Z0-9_]*)\.([a-zA-Z0-9_]+)\b")
        # 5. Литералы в кавычках 'value' (с учетом экранирования '')
        # Группа 1 захватывает содержимое.
        self.re_literal = re.compile(r"'((?:''|[^'])*)'")
        # 6. Отдельные слова (для Java-style условий: structRoots != null)
        self.re_word = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b")

    def clear(self):
        self.map_forward.clear()
        self.map_reverse.clear()
        self.counters.clear()
        self.known_parameters.clear()

    def set_known_parameters(self, params: Set[str]):
        """Загружает список известных ID параметров, чтобы детектировать их в Java-условиях."""
        self.known_parameters = params

    def register(self, value: Any, category: str) -> str:
        if value is None: return "null"
        val_str = str(value)
        if not val_str: return val_str
            
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
        mapping = {
            'entity': 'ENT', 'entity_type': 'ENT',
            'property': 'P', 'property_id': 'P', 
            'parameter': 'PARAM',
            'dataset': 'DS',
            'ordering': 'ORD', 'limitation': 'LIM', 'aggregation': 'AGG',
            'table': 'TBL', 'physical_name': 'DB.TBL'
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
                # Если это не пустая строка
                if col_val:
                    return f"'{self.register(col_val, 'COL')}'"
                return "''"
            
            # Применяем замену только к строкам внутри tuple(...)
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
        
        # 3. Параметры в фигурных скобках {param}
        def replace_param_braces(match):
            p_val = match.group(1)
            return f"{{{self.register(p_val, 'PARAM')}}}"
        text = self.re_param_braces.sub(replace_param_braces, text)
        
        # 4. Java-style параметры (слова без кавычек, совпадающие с known_parameters)
        # Делаем это ДО обработки свойств через точку, чтобы structRoots != null сработало
        def replace_java_var(match):
            word = match.group(1)
            if word in self.known_parameters:
                return self.register(word, 'PARAM')
            # Также ловим обращения к словарям без dictGet, если они похожи на schema.table
            if '.' in word and not word.startswith('ENT_') and not word.startswith('TBL_'):
                 # Простая эвристика: если есть точка и это не замаскированная сущность
                 # Можно попробовать замаскировать как DB.DICT или DB.TBL?
                 # Но это опасно для методов Java (var.equals).
                 # Оставим пока только параметры.
                 pass
            return word
        
        text = self.re_word.sub(replace_java_var, text)

        # 5. Entity.Property
        def replace_prop(match):
            left = match.group(1)
            right = match.group(2)
            
            # Если левая часть - известная сущность (или уже маска ENT/TBL)
            is_entity = (('ENT', left) in self.map_forward) or (('TBL', left) in self.map_forward) or left.startswith('ENT_') or left.startswith('TBL_')
            
            if is_entity:
                cat = 'ENT' if ('ENT', left) in self.map_forward or left.startswith('ENT_') else 'TBL'
                mask_l = self.register(left, cat)
                mask_r = self.register(right, 'P')
                return f"{mask_l}.{mask_r}"
            
            # Попытка поймать словари вне dictGet: organization.dict
            if not is_entity and left not in ['date_diff', 'equals', 'dictGet', 'tuple', 'arrayMap', 'toString']:
                 # Если левая часть похожа на схему БД (не содержит больших букв CamelCase, обычно snake_case)?
                 # Сложно. Давайте доверимся пользователю: если он хочет маскировать DB.DICT, пусть это будет через явные списки или dictGet.
                 # Но в пункте 3 вы просили organization.unit_hierarhy_dict -> OBJ_5 (или DB.DICT).
                 # Давайте проверим, не является ли это 'schema.table' в литерале (см. пункт 6).
                 pass

            return match.group(0)
        text = self.re_dot_prop.sub(replace_prop, text)

        # 6. Литералы 'string' -> OBJ (С ИСПРАВЛЕНИЕМ)
        def replace_lit(match):
            val = match.group(1)
            
            # А. Проверка на зарезервированные слова (функции ClickHouse и т.д.)
            if val in self.reserved_literals:
                return f"'{val}'"

            # Б. Артефакты кода
            if ')' in val or '(' in val or (',' in val and ' ' not in val):
                 return f"'{val}'"

            # В. Попытка определить DB.DICT по синтаксису "schema.name"
            if '.' in val and '_' in val and ' ' not in val:
                 return f"'{self.register(val, 'DB.DICT')}'"

            # Г. Фильтр мусора
            if not self._is_meaningful_string(val):
                return f"'{val}'"
                
            if val in self.map_reverse: return f"'{val}'"
            
            mask = self.register(val, 'OBJ')
            return f"'{mask}'"

        text = self.re_literal.sub(replace_lit, text)
        
        return text