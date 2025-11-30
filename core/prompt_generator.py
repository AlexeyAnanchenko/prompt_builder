from typing import List, Optional
from services.vector_store import VectorStoreManager
from utils.logger import setup_logger

logger = setup_logger(__name__)

class PromptGenerator:
    """Генератор финальных промптов с контекстом"""
    
    def __init__(self):
        self.vector_manager = VectorStoreManager()
        logger.info("PromptGenerator инициализирован")
    
    def generate(
        self,
        system_prompt: str,
        user_query: str,
        namespace: str,
        sql_context: Optional[str] = None
    ) -> str:
        """
        Генерирует финальный промпт с контекстом из векторной БД и SQL
        """
        logger.info(f"Начало генерации промпта для namespace '{namespace}'")
        
        # Получаем релевантные результаты из векторной БД (RAG)
        similar_results = self.vector_manager.search_similar(
            user_query,
            namespace
        )
        logger.info(f"Получено {len(similar_results)} релевантных результатов из RAG")
        
        context_parts: List[str] = []
        for result in similar_results:
            context_parts.append(f"- {result['content']}")
        
        rag_context = "\n".join(context_parts) if context_parts else "Нет релевантного текстового контекста"
        
        # SQL контекст, сгенерированный ContextEngine
        final_sql_context = sql_context if sql_context else "-- Контекст конфигурации не выбран или пуст."
        
        final_prompt = f"""-- Системный промпт:
{system_prompt}

-- Контекст (Knowledge Base / RAG):
{rag_context}

-- Конфигурация (DDL/Insert):
{final_sql_context}

-- Пользовательский запрос:
{user_query}"""
        
        logger.info(f"Промпт сгенерирован. Длина: {len(final_prompt)} символов")
        return final_prompt