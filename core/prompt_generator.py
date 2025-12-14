from typing import List, Optional
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PromptGenerator:
    """Генератор финальных промптов с контекстом"""
    
    def __init__(self) -> None:
        logger.info("PromptGenerator инициализирован")
    
    def generate(
        self,
        system_prompt: str,
        user_query: str,
        namespace: str,
        sql_context: Optional[str] = None
    ) -> str:
        """
        Генерирует финальный промпт с контекстом из БД приложения.
        """

        logger.info(f"Начало генерации промпта для namespace '{namespace}'")
        
        final_sql_context = sql_context if sql_context else "-- Контекст конфигурации не выбран или пуст."
        
        final_prompt = f"""-- СИСТЕМНЫЙ ПРОМПТ:
{system_prompt}


-- КОНТЕКСТ:
--=============================== SQL ===============================
{final_sql_context}
--=============================== SQL ===============================

-- ПОЛЬЗОВАТЕЛЬСКИЙ ЗАПРОС:
{user_query}"""
        
        logger.info(f"Промпт сгенерирован. Длина: {len(final_prompt)} символов")
        return final_prompt