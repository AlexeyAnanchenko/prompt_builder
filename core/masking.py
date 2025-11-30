import re
from typing import Dict, List, Tuple, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ContextMasker:
    """
    Класс для управления маскированием контекста.
    Хранит словари соответствия (Real <-> Masked) и выполняет замены.
    """
    def __init__(self):
        # real_name -> masked_name
        self.map_forward: Dict[str, str] = {}
        # masked_name -> real_name
        self.map_reverse: Dict[str, str] = {}
        
        # Счетчики для генерации уникальных имен
        self.counters = {
            'dataset': 1,
            'entity': 1,
            'property': 1,
            'table': 1,
            'parameter': 1,
            'other': 1
        }
        
        # Префиксы для разных типов
        self.prefixes = {
            'dataset': 'DS',
            'entity': 'ENT',
            'property': 'P', 
            'table': 'TBL',
            'parameter': 'PARAM',
            'other': 'OBJ'
        }
        logger.info("ContextMasker initialized")

    def register(self, real_name: str, category: str = 'other') -> str:
        """Регистрирует термин и выдает ему маску (или возвращает существующую)."""
        if not real_name:
            return str(real_name)
            
        real_name_str = str(real_name)
        
        # Если уже есть - возвращаем
        if real_name_str in self.map_forward:
            return self.map_forward[real_name_str]
        
        # Генерируем новое имя: ENT_1, P_25, DS_3
        idx = self.counters.get(category, 1)
        self.counters[category] += 1
        prefix = self.prefixes.get(category, 'OBJ')
        masked_name = f"{prefix}_{idx}"
        
        self.map_forward[real_name_str] = masked_name
        self.map_reverse[masked_name] = real_name_str
        
        # Логируем только первые 5 регистраций каждого типа, чтобы не спамить
        if idx <= 5:
            logger.debug(f"Registered mask: {real_name_str} -> {masked_name}")
            
        return masked_name

    def mask_text(self, text: str) -> str:
        """Заменяет реальные имена на маски в произвольном тексте (промпте)."""
        if not text:
            return ""
            
        # Сортируем ключи по длине (сначала длинные), чтобы не заменить часть слова
        # Например, чтобы не заменить 'person' внутри 'personPosition'
        sorted_keys = sorted(self.map_forward.keys(), key=len, reverse=True)
        
        result = text
        count_replaced = 0
        
        for real in sorted_keys:
            if not real: continue
            mask = self.map_forward[real]
            
            # Экранируем спецсимволы в реальном имени
            escaped_real = re.escape(real)
            
            # Используем \b только если реальное имя состоит из букв/цифр
            # Если там есть точки (table.col), \b может работать некорректно
            if re.match(r'^\w+$', real):
                pattern = re.compile(rf'\b{escaped_real}\b')
            else:
                pattern = re.compile(escaped_real)
                
            new_text, n = pattern.subn(mask, result)
            if n > 0:
                result = new_text
                count_replaced += n
                
        logger.info(f"Masked text: replaced {count_replaced} occurrences.")
        return result

    def unmask_text(self, text: str) -> str:
        """Заменяет маски обратно на реальные имена."""
        if not text:
            return ""
            
        # Здесь проще: маски у нас уникальные и предсказуемые (ENT_1, P_2)
        sorted_keys = sorted(self.map_reverse.keys(), key=len, reverse=True)
        
        result = text
        count_replaced = 0
        
        for mask in sorted_keys:
            real = self.map_reverse[mask]
            # Для масок (ENT_1) границы слов важны
            pattern = re.compile(rf'\b{re.escape(mask)}\b')
            new_text, n = pattern.subn(real, result)
            if n > 0:
                result = new_text
                count_replaced += n
                
        logger.info(f"Unmasked text: restored {count_replaced} occurrences.")
        return result
        
    def clear(self):
        """Сброс состояния"""
        self.map_forward = {}
        self.map_reverse = {}
        for k in self.counters: self.counters[k] = 1
        logger.info("ContextMasker cleared")