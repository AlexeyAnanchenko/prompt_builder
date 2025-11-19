from typing import List
from services.vector_store import VectorStoreManager


class PromptGenerator:
    """Генератор финальных промптов с контекстом"""
    
    def __init__(self):
        self.vector_manager = VectorStoreManager()
    
    def generate(
        self, 
        system_prompt: str, 
        user_query: str, 
        namespace: str
    ) -> str:
        """
        Генерирует финальный промпт с контекстом из векторной БД
        
        Args:
            system_prompt: Системный промпт
            user_query: Запрос пользователя
            namespace: Namespace для поиска
            
        Returns:
            str: Финальный промпт
        """
        # Получаем релевантные результаты из векторной БД
        similar_results = self.vector_manager.search_similar(
            user_query, 
            namespace
        )
        
        # Формируем контекст
        context_parts: List[str] = []
        for result in similar_results:
            context_parts.append(f"- {result['content']}")
        
        context = "\n".join(context_parts) if context_parts else "Нет релевантного контекста"
        
        # TODO: Интегрировать core_logic.generate_sql_inserts()
        sql_example = f"SELECT * FROM data WHERE query LIKE '%{user_query}%';"
        
        # Формируем финальный промпт
        return f"""-- Системный промпт:
{system_prompt}

-- Контекст из векторной БД (namespace: {namespace}):
{context}

-- SQL запрос:
-- TODO: Интегрировать с core_logic.generate_sql_inserts()
{sql_example}

-- Пользовательский запрос:
{user_query}"""