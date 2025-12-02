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
        # Глобальный словарь для текстового маскирования (System Prompt / User Query)
        # Здесь коллизии неизбежны, хранится "последняя зарегистрированная" версия.
        self.map_forward: Dict[str, str] = {}
        self.map_reverse: Dict[str, str] = {}
        
        # Изолированный реестр: category -> {real_name -> masked_name}
        # Позволяет иметь разные маски для "id" в entities и "id" в parameters.
        self.scoped_registry: Dict[str, Dict[str, str]] = defaultdict(dict)
        
        self.counters = {
            'dataset': 1, 'entity': 1, 'property': 1,
            'table': 1, 'parameter': 1, 'other': 1
        }
        
        self.prefixes = {
            'dataset': 'DS', 'entity': 'ENT', 'property': 'P', 
            'table': 'TBL', 'parameter': 'PARAM', 'other': 'OBJ'
        }
        logger.info("ContextMasker initialized (Scoped mode)")

    def register(self, real_name: str, category: str = 'other') -> str:
        """
        Регистрирует термин в конкретной категории.
        Если термин уже есть в этой категории, возвращает существующую маску.
        Если нет — создает новую.
        """
        if not real_name:
            return str(real_name)
            
        real_name_str = str(real_name)
        
        # 1. Проверяем наличие в конкретной категории (Scope)
        if real_name_str in self.scoped_registry[category]:
            return self.scoped_registry[category][real_name_str]
        
        # 2. Генерируем новую маску
        idx = self.counters.get(category, 1)
        self.counters[category] += 1
        prefix = self.prefixes.get(category, 'OBJ')
        masked_name = f"{prefix}_{idx}"
        
        # 3. Сохраняем в изолированный реестр
        self.scoped_registry[category][real_name_str] = masked_name
        
        # 4. Обновляем глобальный словарь (для mask_text)
        # Примечание: тут может произойти перезапись, если имена совпадают в разных категориях.
        # Это компромисс для маскирования неструктурированного текста.
        self.map_forward[real_name_str] = masked_name
        self.map_reverse[masked_name] = real_name_str
        
        if idx <= 5:
            logger.debug(f"Registered mask [{category}]: {real_name_str} -> {masked_name}")
            
        return masked_name

    def get_known_mask(self, real_name: str, priority_categories: List[str]) -> Optional[str]:
        """
        Ищет маску для термина, проверяя категории в указанном порядке.
        Используется для массивов, где мы не знаем точный тип элемента.
        """
        real_name_str = str(real_name)
        for cat in priority_categories:
            if real_name_str in self.scoped_registry[cat]:
                return self.scoped_registry[cat][real_name_str]
        return None

    def mask_text(self, text: str) -> str:
        """Заменяет реальные имена на маски в произвольном тексте."""
        if not text: return ""
        
        sorted_keys = sorted(self.map_forward.keys(), key=len, reverse=True)
        result = text
        
        for real in sorted_keys:
            if not real: continue
            mask = self.map_forward[real]
            escaped_real = re.escape(real)
            
            # Используем \b только для слов, состоящих из букв/цифр
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