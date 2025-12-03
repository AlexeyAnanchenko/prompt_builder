import re
from collections import defaultdict
from typing import Dict, List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ContextMasker:
    def __init__(self):
        self.map_forward: Dict[str, str] = {}
        self.map_reverse: Dict[str, str] = {}
        
        # Изолированный реестр
        self.scoped_registry: Dict[str, Dict[str, str]] = defaultdict(dict)
        
        # Запоминаем, какая категория "владеет" текущим маппингом в map_forward
        self.map_owner: Dict[str, str] = {}

        self.counters = {
            'dataset': 1, 'entity': 1, 'property': 1,
            'table': 1, 'parameter': 1, 'other': 1,
            'physical_table': 1, 'dictionary': 1,
            'path': 1, 'entity_name': 1, 'column': 1
        }
        
        self.prefixes = {
            'dataset': 'DS', 'entity': 'ENT', 'property': 'P', 
            'table': 'TBL', 'parameter': 'PARAM', 'other': 'OBJ',
            'physical_table': 'DB.TBL', 'dictionary': 'DB.DICT',
            'path': 'PATH', 'entity_name': 'ENT_NAME', 'column': 'COL'
        }
        
        # --- НОВОЕ: Приоритеты категорий ---
        # Чем выше число, тем сложнее перезаписать этот тип.
        # Property (90) не даст себя перезаписать Path (10).
        self.category_priority = {
            'entity': 100,
            'property': 90,
            'parameter': 80,
            'dataset': 60,
            'table': 50,
            'dictionary': 40,
            'path': 10,       # Низкий приоритет, так как часто пересекается с пропертями
            'other': 0
        }
        
        logger.info("ContextMasker initialized (Scoped + Priority Support)")

    def register(self, real_name: str, category: str = 'other') -> str:
        if not real_name: return str(real_name)  
        real_name_str = str(real_name)
        
        # 1. Логика Scoped Registry (получаем маску для конкретной категории)
        if real_name_str in self.scoped_registry[category]:
            masked_name = self.scoped_registry[category][real_name_str]
        else:
            idx = self.counters.get(category, 1)
            self.counters[category] += 1
            prefix = self.prefixes.get(category, 'OBJ')
            masked_name = f"{prefix}_{idx}"
            self.scoped_registry[category][real_name_str] = masked_name
        
        # 2. Логика обновления глобального словаря с учетом ПРИОРИТЕТОВ
        current_owner = self.map_owner.get(real_name_str)
        new_prio = self.category_priority.get(category, 0)
        
        should_update = False
        
        if current_owner is None:
            # Если записи нет - пишем смело
            should_update = True
        else:
            old_prio = self.category_priority.get(current_owner, 0)
            # Обновляем только если новая категория важнее или равна по важности
            # Например: Property(90) >= Path(10) -> FALSE (не обновляем)
            # Например: Path(10) >= Property(90) -> FALSE
            # Правильно: если мы сейчас регистрируем Property, а было Path -> обновляем.
            if new_prio >= old_prio:
                should_update = True
        
        if should_update:
            self.map_forward[real_name_str] = masked_name
            self.map_reverse[masked_name] = real_name_str
            self.map_owner[real_name_str] = category
        
        return masked_name

    def add_manual_mapping(self, real_name: str, masked_name: str):
        if not real_name or not masked_name: return
        self.map_forward[real_name] = masked_name
        self.map_reverse[masked_name] = real_name
        # Ручной маппинг считаем наивысшим приоритетом
        self.map_owner[real_name] = 'manual'

    def get_known_mask(self, real_name: str, priority_categories: List[str]) -> Optional[str]:
        real_name_str = str(real_name)
        for cat in priority_categories:
            if real_name_str in self.scoped_registry[cat]:
                return self.scoped_registry[cat][real_name_str]
        return None

    def mask_text(self, text: str) -> str:
        if not text: return ""
        
        result = text
        
        # Приоритетная обработка {PARAM}
        def replace_param_in_braces(match):
            content = match.group(1)
            if content in self.scoped_registry.get('parameter', {}):
                mask = self.scoped_registry['parameter'][content]
                return f"{{{mask}}}"
            return match.group(0)

        result = re.sub(r'\{([a-zA-Z0-9_]+)\}', replace_param_in_braces, result)

        sorted_keys = sorted(self.map_forward.keys(), key=len, reverse=True)
        for real in sorted_keys:
            if not real: continue
            mask = self.map_forward[real]
            escaped_real = re.escape(real)
            
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
        self.map_owner = {}
        self.scoped_registry = defaultdict(dict)
        for k in self.counters: self.counters[k] = 1
        logger.info("ContextMasker cleared")