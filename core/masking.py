import re
import json
from collections import defaultdict
from typing import Dict, Any, List, Optional, Union

class ContextMasker:
    def __init__(self):
        # forward: {(category, real_value): mask_id}
        self.map_forward: Dict[tuple, str] = {}
        # reverse: {mask_id: real_value}
        self.map_reverse: Dict[str, str] = {}
        # счетчики для каждой категории (ENT -> 1, P -> 1...)
        self.counters: Dict[str, int] = defaultdict(int)
        
        # --- Регулярки для формул ---
        
        # 1. dictGet с кортежем: dictGet('dict', tuple('c1', 'c2'), ...)
        # Группа 1: имя словаря, Группа 2: содержимое кортежа
        self.re_dict_tuple = re.compile(r"dictGet\s*\(\s*'([^']+)'\s*,\s*tuple\s*\((.*?)\)", re.DOTALL)
        
        # 2. dictGet одиночный: dictGet('dict', 'col', ...)
        self.re_dict_single = re.compile(r"dictGet\s*\(\s*'([^']+)'\s*,\s*'([^']+)'", re.DOTALL)
        
        # 3. Параметры: {paramName}
        self.re_param = re.compile(r'\{([a-zA-Z0-9_]+)\}')
        
        # 4. Свойства через точку: Entity.Property
        # Ищем слова, разделенные точкой, где левая часть не начинается с цифры
        self.re_dot_prop = re.compile(r"\b([a-zA-Z][a-zA-Z0-9_]*)\.([a-zA-Z0-9_]+)\b")
        
        # 5. Литералы в кавычках: 'value'
        self.re_literal = re.compile(r"'([^']+)'")

    def clear(self):
        self.map_forward.clear()
        self.map_reverse.clear()
        self.counters.clear()

    def register(self, value: Any, category: str) -> str:
        """
        Регистрирует значение в реестре и возвращает маску.
        Если значение уже есть для этой категории, возвращает существующую маску.
        """
        if value is None:
            return "null"
        
        val_str = str(value)
        if not val_str:
            return val_str
            
        key = (category, val_str)
        
        if key in self.map_forward:
            return self.map_forward[key]
        
        # Создаем новую маску
        self.counters[category] += 1
        # Формат: PREFIX_N (например ENT_1, P_5)
        mask = f"{category}_{self.counters[category]}"
        
        self.map_forward[key] = mask
        self.map_reverse[mask] = val_str
        
        return mask

    def mask_text(self, text: str) -> str:
        """Для маскирования обычного текста (системный промпт, запрос пользователя)."""
        if not text: return ""
        # Простой проход по всем известным значениям (от длинных к коротким)
        # Это упрощенный вариант, для SQL используется mask_formula
        sorted_items = sorted(self.map_forward.items(), key=lambda x: len(x[0][1]), reverse=True)
        masked_text = text
        for (cat, val), mask in sorted_items:
            # Заменяем только полные слова, чтобы 'id' не заменил часть 'android'
            pattern = r'\b' + re.escape(val) + r'\b'
            masked_text = re.sub(pattern, mask, masked_text)
        return masked_text

    def mask_json(self, data: Any) -> Any:
        """Рекурсивно маскирует значения в JSON, основываясь на ключах."""
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
        """Определяет категорию маски по ключу JSON."""
        mapping = {
            'entity': 'ENT', 'entity_type': 'ENT',
            'property': 'P', 'property_id': 'P', 'operator': None, # операторы не маскируем
            'parameter': 'PARAM',
            'dataset': 'DS',
            'ordering': 'ORD',
            'limitation': 'LIM',
            'aggregation': 'AGG',
            'table': 'TBL'
        }
        return mapping.get(key)

    def mask_formula(self, text: str) -> str:
        """
        Умное маскирование SQL/ClickHouse выражений.
        Порядок важен! Сначала специфичные функции, потом общие литералы.
        """
        if not text: return text
        
        # 1. dictGet с TUPLE: dictGet('dict', tuple('c1', 'c2')...)
        def replace_tuple_dict(match):
            d_name = match.group(1)
            tuple_content = match.group(2)
            
            mask_d = self.register(d_name, 'DB.DICT')
            
            # Внутри кортежа заменяем все литералы '...' на COL
            def replace_col_item(m):
                col_val = m.group(1)
                # Если пустая строка, оставляем как есть
                if not col_val: return "''"
                return f"'{self.register(col_val, 'COL')}'"
            
            masked_content = self.re_literal.sub(replace_col_item, tuple_content)
            return f"dictGet('{mask_d}', tuple({masked_content})"

        text = self.re_dict_tuple.sub(replace_tuple_dict, text)

        # 2. dictGet одиночный: dictGet('dict', 'col')
        def replace_single_dict(match):
            d_name = match.group(1)
            c_name = match.group(2)
            mask_d = self.register(d_name, 'DB.DICT')
            mask_c = self.register(c_name, 'COL')
            return f"dictGet('{mask_d}', '{mask_c}'"
            
        text = self.re_dict_single.sub(replace_single_dict, text)
        
        # 3. Параметры {param}
        def replace_param(match):
            p_val = match.group(1)
            return f"{{{self.register(p_val, 'PARAM')}}}"
        
        text = self.re_param.sub(replace_param, text)
        
        # 4. Entity.Property
        def replace_prop(match):
            left = match.group(1)
            right = match.group(2)
            
            # Эвристика: если левая часть уже известна как ENT или выглядит как ENT
            # (Проверяем наличие в реестре с категорией ENT или TBL)
            is_entity = (('ENT', left) in self.map_forward) or (('TBL', left) in self.map_forward)
            
            # Если мы точно знаем, что left это сущность, маскируем
            if is_entity:
                # Пытаемся взять существующую маску, если нет - создаем ENT
                # Но если это TBL, берем TBL. Приоритет у ENT для свойств.
                cat = 'ENT' if ('ENT', left) in self.map_forward else 'TBL'
                mask_l = self.register(left, cat)
                mask_r = self.register(right, 'P')
                return f"{mask_l}.{mask_r}"
            
            # Если это функции типа date_diff(DAY, ...), их трогать нельзя
            # Можно добавить список исключений, если будет нужно.
            return match.group(0)

        text = self.re_dot_prop.sub(replace_prop, text)

        # 5. Остальные литералы 'string' -> OBJ
        def replace_lit(match):
            val = match.group(1)
            # Если это уже похоже на нашу маску (например содержит _\d+), пропускаем
            if val in self.map_reverse:
                return f"'{val}'"
            
            # Проверяем, не является ли это системным словом 'none' в контексте значений
            # Если 'none', маскируем как OBJ (согласно CSV)
            
            mask = self.register(val, 'OBJ')
            return f"'{mask}'"

        text = self.re_literal.sub(replace_lit, text)
        
        return text