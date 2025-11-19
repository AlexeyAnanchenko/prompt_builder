from typing import Dict, Tuple


class MaskingService:
    """Сервис для маскирования и демаскирования конфиденциальных данных"""
    
    def mask_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Маскирует конфиденциальные данные в тексте
        
        TODO: Интегрировать твою логику маскирования
        
        Args:
            text: Исходный текст для маскирования
            
        Returns:
            Tuple[str, Dict[str, str]]: (замаскированный_текст, словарь_замен)
            где словарь_замен = {маска: оригинальное_значение}
        """
        masked_text = text
        mapping: Dict[str, str] = {}
        
        # TODO: Реализовать твою логику маскирования
        # Пример:
        # mapping = {
        #     "MASK_001": "original_value_1",
        #     "MASK_002": "original_value_2"
        # }
        
        return masked_text, mapping
    
    def unmask_text(self, text: str, mapping: Dict[str, str]) -> str:
        """
        Восстанавливает оригинальные данные из замаскированного текста
        
        TODO: Интегрировать твою логику расшифровки
        
        Args:
            text: Замаскированный текст
            mapping: Словарь замен {маска: оригинальное_значение}
            
        Returns:
            str: Расшифрованный текст
        """
        unmasked_text = text
        
        # TODO: Реализовать твою логику расшифровки
        for mask, original in mapping.items():
            unmasked_text = unmasked_text.replace(mask, original)
        
        return unmasked_text