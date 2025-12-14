from typing import List, Dict, Any, Tuple
from core.context_engine import DbDataLoader, ContextResolver, OutputGenerator
from core.masking import ContextMasker
from core.prompt_generator import PromptGenerator
from utils.logger import setup_logger
from utils.tokenizer import TokenCounter

logger = setup_logger(__name__)

class ContextService:
    """Сервис для оркестрации подбора контекста и генерации промптов"""

    @staticmethod
    def pick_context(
        loader: DbDataLoader,
        masker: ContextMasker,
        datasets: List[str],
        entities: List[str]
    ) -> Tuple[str, Dict[Any, Any]]:
        """
        Подбирает контекст и возвращает замаскированный SQL и словарь масок.
        """
        logger.info(f"Подбор контекста для {len(datasets)} datasets и {len(entities)} entities")
        
        # 1. Сброс маскера
        masker.clear()
        
        # 2. Резолвинг зависимостей
        resolver = ContextResolver(loader)
        for ds in datasets:
            resolver.resolve_by_dataset(ds)
        for ent in entities:
            resolver.resolve_by_entity(ent)
        
        # 3. Генерация SQL с маскированием
        # Примечание: OutputGenerator заполняет masker внутри generate_sql
        gen_masked = OutputGenerator(loader, resolver.context, masker=masker)
        sql_masked = gen_masked.generate_sql()
        
        # Возвращаем SQL и копию словаря масок
        return sql_masked, masker.map_forward.copy()

    @staticmethod
    def generate_final_prompts(
        loader: DbDataLoader,
        masker: ContextMasker,
        namespace_id: str,
        datasets: List[str],
        entities: List[str],
        system_prompt: str,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Генерирует финальные промпты (маскированный и оригинальный).
        """
        logger.info("Начало генерации финальных промптов")
        
        # 1. Повторный резолвинг (чтобы гарантировать чистоту для orig и masked генерации)
        # В идеале можно передать resolver извне, но ContextService stateless
        resolver = ContextResolver(loader)
        if datasets or entities:
            for ds in datasets: resolver.resolve_by_dataset(ds)
            for ent in entities: resolver.resolve_by_entity(ent)
        
        # 2. Генерация Маскированного SQL (заполняет masker)
        # Важно: если masker не был очищен до этого, он продолжит нумерацию. 
        # В рамках этого флоу предполагается, что он уже содержит нужные маски, 
        # или мы их обновляем.
        gen_masked = OutputGenerator(loader, resolver.context, masker=masker)
        sql_masked = gen_masked.generate_sql()
        
        # 3. Генерация Оригинального SQL
        gen_orig = OutputGenerator(loader, resolver.context, masker=None)
        sql_original = gen_orig.generate_sql()
        
        # 4. Маскирование текстовых инпутов
        system_prompt_masked = masker.mask_text(system_prompt)
        user_query_masked = masker.mask_text(user_query)
        
        # 5. Сборка промптов
        generator = PromptGenerator()
        
        final_prompt_masked = generator.generate(
            system_prompt=system_prompt_masked,
            user_query=user_query_masked,
            namespace=namespace_id,
            sql_context=sql_masked
        )
        
        final_prompt_original = generator.generate(
            system_prompt=system_prompt,
            user_query=user_query,
            namespace=namespace_id,
            sql_context=sql_original
        )
        
        # 6. Подсчет токенов
        try:
            token_count = TokenCounter.count_tokens(final_prompt_masked)
        except Exception as e:
            logger.error(f"Ошибка подсчета токенов: {e}")
            token_count = 0
            
        return {
            "final_prompt_masked": final_prompt_masked,
            "final_prompt_original": final_prompt_original,
            "sql_original": sql_original,
            "token_count": token_count,
            "masking_dict": masker.map_forward.copy()
        }