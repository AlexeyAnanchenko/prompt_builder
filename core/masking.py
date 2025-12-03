import re
from collections import defaultdict
from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ContextMasker:
    """
    Класс для управления маскированием контекста с поддержкой областей видимости (Scope).
    """
    def __init__(self):
        # Глобальный словарь для текстового маскирования
        self.map_forward: Dict[str, str] = {}
        self.map_reverse: Dict[str, str] = {}
        
        # Изолированный реестр: category -> {real_name -> masked_name}
        self.scoped_registry: Dict[str, Dict[str, str]] = defaultdict(dict)
        
        self.counters = {
            'dataset': 1, 'entity': 1, 'property': 1,
            'table': 1, 'parameter': 1, 'other': 1,
            'physical_table': 1, 'dictionary': 1,
            'path': 1,
            'entity_name': 1,
            'column': 1
        }
        
        self.prefixes = {
            'dataset': 'DS', 
            'entity': 'ENT', 
            'property': 'P', 
            'table': 'TBL', 
            'parameter': 'PARAM', 
            'other': 'OBJ',
            'physical_table': 'DB.TBL', 
            'dictionary': 'DB.DICT',
            'path': 'PATH',
            'entity_name': 'ENT_NAME',
            'column': 'COL'
        }
        logger.info("ContextMasker initialized (Scoped + FQN Support)")

    def register(self, real_name: str, category: str = 'other') -> str:
        """
        Регистрирует термин.
        Важно: Глобальный словарь map_forward перезаписывается последним вызовом.
        Это позволяет приоритезировать категории через порядок регистрации.
        """
        if not real_name:
            return str(real_name)
            
        real_name_str = str(real_name)
        
        # 1. Проверяем наличие в конкретной категории (Scope)
        if real_name_str in self.scoped_registry[category]:
            masked_name = self.scoped_registry[category][real_name_str]
        else:
            # 2. Генерируем новую маску
            idx = self.counters.get(category, 1)
            self.counters[category] += 1
            prefix = self.prefixes.get(category, 'OBJ')
            masked_name = f"{prefix}_{idx}"
            self.scoped_registry[category][real_name_str] = masked_name
        
        # 3. Обновляем глобальный словарь (ВСЕГДА перезаписываем)
        # Это гарантирует, что Property перезапишет Parameter для bare-words
        self.map_forward[real_name_str] = masked_name
        self.map_reverse[masked_name] = real_name_str
        
        return masked_name

    def add_manual_mapping(self, real_name: str, masked_name: str):
        """
        Ручная регистрация маппинга (например, для составных имен Entity.Property).
        Такие маппинги имеют приоритет в mask_text, так как они длиннее.
        """
        if not real_name or not masked_name: return
        self.map_forward[real_name] = masked_name
        self.map_reverse[masked_name] = real_name

    def get_known_mask(self, real_name: str, priority_categories: List[str]) -> Optional[str]:
        real_name_str = str(real_name)
        for cat in priority_categories:
            if real_name_str in self.scoped_registry[cat]:
                return self.scoped_registry[cat][real_name_str]
        return None

    def mask_text(self, text: str) -> str:
        if not text: return ""
        
        result = text
        
        # 0. Приоритетная обработка для {текста} в фигурных скобках.
        # Если слово внутри скобок известно как параметр, принудительно ставим маску PARAM.
        def replace_param_in_braces(match):
            content = match.group(1)
            # Проверяем напрямую в изолированном реестре параметров
            if content in self.scoped_registry.get('parameter', {}):
                mask = self.scoped_registry['parameter'][content]
                return f"{{{mask}}}"
            return match.group(0)

        # Заменяем {word} используя приоритет параметров
        result = re.sub(r'\{([a-zA-Z0-9_]+)\}', replace_param_in_braces, result)

        # Сортировка по длине критически важна:
        # "User.status" (длиннее) заменится раньше, чем "User" или "status"
        sorted_keys = sorted(self.map_forward.keys(), key=len, reverse=True)
        
        for real in sorted_keys:
            if not real: continue
            
            # Если слово уже было заменено на шаге 0 (например, стало {PARAM_1}),
            # то основной цикл его не тронет, так как ищет оригинальное имя (например, "userId")
            
            mask = self.map_forward[real]
            escaped_real = re.escape(real)
            
            # \b используем только для "чистых" слов
            if re.match(r'^\w+$', real):
                pattern = re.compile(rf'\b{escaped_real}\b')
            else:
                pattern = re.compile(escaped_real)
                
            new_text, n = pattern.subn(mask, result)
            if n > 0:
                result = new_text
        return result

    def unmask_text(self, text: str) -> str:
        if not text: return ""
        sorted_keys = sorted(self.map_reverse.keys(), key=len, reverse=True)
        result = text
        for mask in sorted_keys:
            real = self.map_reverse[mask]
            pattern = re.compile(rf'\b{re.escape(mask)}\b')
            new_text, n = pattern.subn(real, result)
            if n > 0:
                result = new_text
        return result
        
    def clear(self):
        self.map_forward = {}
        self.map_reverse = {}
        self.scoped_registry = defaultdict(dict)
        for k in self.counters: self.counters[k] = 1
        logger.info("ContextMasker cleared")