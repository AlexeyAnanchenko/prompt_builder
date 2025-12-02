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
            'physical_table': 1, 'dictionary': 1 # Новые счетчики
        }
        
        self.prefixes = {
            'dataset': 'DS', 
            'entity': 'ENT', 
            'property': 'P', 
            'table': 'TBL', # Логические таблицы конфигурации
            'parameter': 'PARAM', 
            'other': 'OBJ',
            'physical_table': 'DB.TBL', # Физические таблицы БД
            'dictionary': 'DB.DICT'     # Словари
        }
        logger.info("ContextMasker initialized (Scoped mode + DB formats)")

    def register(self, real_name: str, category: str = 'other') -> str:
        if not real_name:
            return str(real_name)
            
        real_name_str = str(real_name)
        
        # 1. Проверяем наличие в конкретной категории
        if real_name_str in self.scoped_registry[category]:
            return self.scoped_registry[category][real_name_str]
        
        # 2. Генерируем новую маску
        idx = self.counters.get(category, 1)
        self.counters[category] += 1
        prefix = self.prefixes.get(category, 'OBJ')
        masked_name = f"{prefix}_{idx}"
        
        # 3. Сохраняем
        self.scoped_registry[category][real_name_str] = masked_name
        self.map_forward[real_name_str] = masked_name
        self.map_reverse[masked_name] = real_name_str
        
        return masked_name

    def get_known_mask(self, real_name: str, priority_categories: List[str]) -> Optional[str]:
        real_name_str = str(real_name)
        for cat in priority_categories:
            if real_name_str in self.scoped_registry[cat]:
                return self.scoped_registry[cat][real_name_str]
        return None

    def mask_text(self, text: str) -> str:
        if not text: return ""
        
        # Сортируем по длине, чтобы избежать частичных замен
        sorted_keys = sorted(self.map_forward.keys(), key=len, reverse=True)
        result = text
        
        for real in sorted_keys:
            if not real: continue
            mask = self.map_forward[real]
            escaped_real = re.escape(real)
            
            # \b используем только для "чистых" слов. Для имен с точкой (DB.Table) границы слов работают иначе.
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
            # Для масок (ENT_1, DB.TBL_1) границы слов важны, но точка в DB.TBL требует внимания
            # Экранируем маску, она безопасна
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