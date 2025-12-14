from typing import Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PromptGenerator:
    """
    Класс для сборки финального текста промпта.
    Объединяет системную инструкцию, SQL-контекст и запрос пользователя.
    """
    
    def __init__(self) -> None:
        logger.debug("PromptGenerator инициализирован")
    
    def generate(
        self,
        system_prompt: str,
        user_query: str,
        namespace: str,
        sql_context: Optional[str] = None
    ) -> str:
        """
        Генерирует финальный промпт по шаблону.
        
        Args:
            system_prompt: Инструкция для LLM (роль, правила).
            user_query: Вопрос пользователя.
            namespace: ID/Имя неймспейса (для логов или метаданных).
            sql_context: Сгенерированный блок INSERT выражений (контекст).
            
        Returns:
            str: Полный текст промпта.
        """

        logger.info(f"Сборка промпта для namespace '{namespace}'")
        
        # Если контекст пустой, пишем заглушку, чтобы было понятно
        final_sql_context = sql_context if sql_context else "-- Контекст конфигурации не выбран или пуст."
        
        # F-string шаблон сборки
        final_prompt = f"""-- СИСТЕМНЫЙ ПРОМПТ:
{system_prompt}


-- КОНТЕКСТ:
--=============================== SQL ===============================
{final_sql_context}
--=============================== SQL ===============================

-- ПОЛЬЗОВАТЕЛЬСКИЙ ЗАПРОС:
{user_query}"""
        
        logger.info(f"✅ Промпт собран. Длина: {len(final_prompt)} символов")
        return final_prompt