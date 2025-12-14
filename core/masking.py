import re
from collections import defaultdict
from typing import Dict, Any, Optional, Set, Tuple

from utils.logger import setup_logger

# Настраиваем логгер
logger = setup_logger(__name__)

class ContextMasker:
    """
    Класс, отвечающий за маскирование чувствительных данных.
    Работает в двух направлениях:
    1. Masking: Реальные данные -> Маски (person -> ENT_1)
    2. Unmasking: Маски -> Реальные данные (ENT_1 -> person)
    """

    def __init__(self) -> None:
        # Прямой словарь: {(категория, реальное_значение): 'MASK_ID'}
        # Пример: {('ENT', 'person'): 'ENT_1'}
        self.map_forward: Dict[Tuple[str, str], str] = {}
        
        # Обратный словарь: {'MASK_ID': 'реальное_значение'}
        # Пример: {'ENT_1': 'person'}
        self.map_reverse: Dict[str, str] = {}
        
        # Счетчики для генерации уникальных ID масок (ENT_1, ENT_2...)
        self.counters: Dict[str, int] = defaultdict(int)
        
        # Множество известных параметров, загружаемых из БД.
        # Нужен для корректного парсинга Java-условий, где параметры пишутся без спецсимволов.
        self.known_parameters: Set[str] = set()

        # Список слов, которые НЕЛЬЗЯ маскировать (ключевые слова ClickHouse, SQL, типы данных).
        # Если случайно замаскировать 'sum' или 'count', сломается логика запроса.
        self.reserved_literals: Set[str] = {
            # Агрегатные функции ClickHouse
            'groupUniqArray', 'uniq', 'uniqExact', 'groupArray', 
            'sum', 'min', 'max', 'avg', 'count', 'any', 'anyLast', 'argMin', 'argMax',
            'topK', 'quantiles', 'quantilesExact', 'median',
            # Типы данных
            'String', 'Int64', 'UInt64', 'Float64', 'Date', 'DateTime',
            # Специальные значения
            'none', 'null', 'true', 'false', '', '%d.%m', 'MONTH', 'DAY', 'YEAR',
            # Форматы данных
            'JSON', 'CSV', 'TSV'
        }
        
        # --- КОМПИЛЯЦИЯ РЕГУЛЯРНЫХ ВЫРАЖЕНИЙ (Pre-compiled Regex) ---
        # Компилируем один раз при инициализации для ускорения работы.
        
        # 1. dictGet с кортежем: dictGet('dictionary_name', tuple('col1', 'col2'))
        # Ищет вызовы словарей со сложными ключами.
        self.re_dict_tuple = re.compile(r"dictGet\s*\(\s*'([^']+)'\s*,\s*tuple\s*\((.*?)\)", re.DOTALL)
        
        # 2. dictGet одиночный: dictGet('dictionary_name', 'key_column')
        self.re_dict_single = re.compile(r"dictGet\s*\(\s*'([^']+)'\s*,\s*'([^']+)'", re.DOTALL)
        
        # 3. tupleElement: tupleElement(tuple_obj, 'columnName')
        # Извлечение элемента из кортежа по имени.
        self.re_tuple_element = re.compile(r"(?i)tupleElement\s*\(\s*([a-zA-Z0-9_\.]+)\s*,\s*'((?:''|[^'])*)'\s*\)", re.DOTALL)
        
        # 4. Параметры в фигурных скобках: {parameter_name}
        self.re_param_braces = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')
        
        # 5. Свойства через точку: EntityName.PropertyName
        # \b - граница слова, чтобы не захватить часть другого слова.
        self.re_dot_prop = re.compile(r"\b([a-zA-Z][a-zA-Z0-9_]*)\.([a-zA-Z0-9_]+)\b")
        
        # 6. Литералы в одинарных кавычках: 'some_value'
        # Паттерн (?:''|[^'])* обрабатывает экранированные кавычки в SQL (два апострофа '').
        self.re_literal = re.compile(r"'((?:''|[^'])*)'")
        
        # 7. Отдельные слова (для Java-style условий): variable != null
        self.re_word = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b")

    def clear(self) -> None:
        """Сброс состояния маскера (очистка всех словарей)."""
        logger.debug("Очистка словарей маскирования")
        self.map_forward.clear()
        self.map_reverse.clear()
        self.counters.clear()
        self.known_parameters.clear()

    def set_known_parameters(self, params: Set[str]) -> None:
        """
        Загружает список известных ID параметров.
        Это помогает отличить параметр 'client_id' от простого слова в условии 'if client_id != null'.
        """
        self.known_parameters = params

    def _is_generated_mask(self, val: str) -> bool:
        """
        Проверяет, является ли строка уже сгенерированной маской.
        Нужно, чтобы не маскировать маски повторно (ENT_1 -> ENT_2).
        
        Форматы масок: ENT_1, PARAM_2, DB.DICT_1, DB.TBL_5
        """
        if not val:
            return False
            
        # Regex проверяет: Начало строки, (Префикс или DB.Префикс), подчеркивание, цифры, Конец строки.
        return bool(re.match(r'^(DB\.[A-Z]+|[A-Z]+)_\d+$', val))

    def register(self, value: Any, category: str) -> str:
        """
        Главный метод: регистрирует значение и возвращает его маску.
        Если значение уже было зарегистрировано, возвращает существующую маску.
        """
        if value is None: return "null"
        val_str = str(value)
        if not val_str: return val_str

        # Защита от двойного маскирования: если это уже маска, возвращаем как есть.
        if self._is_generated_mask(val_str):
            return val_str
            
        key = (category, val_str)
        
        # Если уже есть в словаре - возвращаем сохраненное
        if key in self.map_forward:
            return self.map_forward[key]
        
        # Генерируем новую маску
        self.counters[category] += 1
        mask = f"{category}_{self.counters[category]}"
        
        # Сохраняем в оба словаря
        self.map_forward[key] = mask
        self.map_reverse[mask] = val_str
        
        return mask

    def mask_text(self, text: str) -> str:
        """
        Маскирует обычный текст (не код).
        Просто заменяет все найденные в словаре значения на их маски.
        Используется для маскирования System Prompt и User Query.
        """
        if not text: return ""
        
        # Сортируем замены от длинных к коротким.
        # Это важно! Если есть 'user_id' и 'user', сначала надо заменить 'user_id'.
        # Иначе 'user_id' превратится в 'ENT_1_id'.
        sorted_items = sorted(self.map_forward.items(), key=lambda x: len(x[0][1]), reverse=True)
        
        masked_text = text
        for (cat, val), mask in sorted_items:
            # Не заменяем системные слова (null, true), если они вдруг попали в словарь
            if val.lower() in ['null', 'true', 'false']: continue
            
            # Используем границы слов (\b), чтобы менять только целые слова
            pattern = r'\b' + re.escape(val) + r'\b'
            masked_text = re.sub(pattern, mask, masked_text)
            
        return masked_text

    def unmask_text(self, text: str) -> str:
        """
        Расшифровывает текст: заменяет маски обратно на реальные значения.
        Используется на Шаге 3 для расшифровки ответа LLM.
        """
        if not text:
            return ""
        
        if not self.map_reverse:
            return text
        
        # Сортируем маски по убыванию длины (DB.DICT_10 раньше, чем P_1)
        sorted_masks = sorted(self.map_reverse.items(), key=lambda x: len(x[0]), reverse=True)
        
        unmasked_text = text
        for mask, original_value in sorted_masks:
            pattern = r'\b' + re.escape(mask) + r'\b'
            unmasked_text = re.sub(pattern, original_value, unmasked_text)
        
        return unmasked_text

    def mask_json(self, data: Any) -> Any:
        """
        Рекурсивно обходит JSON (dict/list) и маскирует ключи и значения
        согласно эвристике имен полей.
        """
        if isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                # Пытаемся понять категорию по имени ключа (entity -> ENT)
                category = self._infer_json_category(k)
                
                # Специальная обработка для полей с формулами
                if k in ['valueExpr', 'condition', 'expression'] and isinstance(v, str):
                     new_dict[k] = self.mask_formula(v)
                # Если нашли категорию и значение - строка -> маскируем
                elif category and isinstance(v, str):
                    new_dict[k] = self.register(v, category)
                # Рекурсия для вложенных объектов
                elif isinstance(v, (dict, list)):
                    new_dict[k] = self.mask_json(v)
                else:
                    new_dict[k] = v
            return new_dict
        elif isinstance(data, list):
            return [self.mask_json(item) for item in data]
        return data

    def _infer_json_category(self, key: str) -> Optional[str]:
        """Определяет категорию маски по имени поля в JSON."""
        mapping = {
            'entity': 'ENT', 'entity_type': 'ENT',
            'property': 'P', 'property_id': 'P', 
            'parameter': 'PARAM',
            'dataset': 'DS',
            'ordering': 'ORD', 'limitation': 'LIM', 'aggregation': 'AGG',
            'table': 'TBL', 'physical_name': 'DB.TBL',
        }
        return mapping.get(key)

    def mask_formula(self, text: str) -> str:
        """
        Интеллектуальное маскирование SQL/Code формул.
        Использует набор регулярных выражений для поиска сущностей, параметров и функций.
        """
        if not text: return text
        
        # 1. dictGet с TUPLE (Сложные вызовы словарей)
        def replace_tuple_dict(match):
            d_name = match.group(1)
            tuple_content = match.group(2)
            mask_d = self.register(d_name, 'DB.DICT')
            
            # Внутри кортежа аргументы - это обычно имена колонок (COL)
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

        # 3. tupleElement
        def replace_tuple_elem(match):
            prefix = match.group(1)
            col_name = match.group(2)
            mask_c = self.register(col_name, 'COL')
            return f"tupleElement({prefix}, '{mask_c}')"

        text = self.re_tuple_element.sub(replace_tuple_elem, text)
        
        # 4. Параметры {param}
        def replace_param_braces(match):
            p_val = match.group(1)
            return f"{{{self.register(p_val, 'PARAM')}}}"
        text = self.re_param_braces.sub(replace_param_braces, text)

        # 5. Entity.Property (Точечная нотация)
        def replace_prop(match):
            left = match.group(1)
            right = match.group(2)
            
            # Проверяем, похоже ли левое слово на сущность или таблицу
            is_entity = (('ENT', left) in self.map_forward) or \
                        (('TBL', left) in self.map_forward) or \
                        left.startswith('ENT_') or left.startswith('TBL_')
            
            if is_entity:
                # Если мы точно знаем, что слева сущность, маскируем правую часть как свойство (P)
                cat = 'ENT' if ('ENT', left) in self.map_forward or left.startswith('ENT_') else 'TBL'
                mask_l = self.register(left, cat)
                mask_r = self.register(right, 'P')
                return f"{mask_l}.{mask_r}"
            
            return match.group(0)
        text = self.re_dot_prop.sub(replace_prop, text)
        
        # 6. Java-style параметры (просто слова, если они есть в known_parameters)
        def replace_java_var(match):
            word = match.group(1)
            if word in self.known_parameters:
                return self.register(word, 'PARAM')
            return word
        
        text = self.re_word.sub(replace_java_var, text)

        # 7. Литералы в кавычках 'value'
        def replace_lit(match):
            val = match.group(1)
            
            # Пропускаем зарезервированные слова
            if val in self.reserved_literals:
                return f"'{val}'"

            # Пропускаем сложные конструкции (содержат скобки или запятые)
            if ')' in val or '(' in val or (',' in val and ' ' not in val):
                 return f"'{val}'"

            # Если похоже на имя таблицы схемы (schema.name), маскируем как словарь
            if '.' in val and '_' in val and ' ' not in val:
                 return f"'{self.register(val, 'DB.DICT')}'"

            # Если это значение уже было зарегистрировано где-то ранее, используем эту маску.
            # Это сохраняет целостность данных.
            for (cat, real_val), mask in self.map_forward.items():
                if real_val == val:
                    return f"'{mask}'"

            return f"'{val}'"

        text = self.re_literal.sub(replace_lit, text)
        
        return text