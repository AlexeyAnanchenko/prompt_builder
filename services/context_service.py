from typing import List, Dict, Any, Tuple
from core.context_engine import DbDataLoader, ContextResolver, OutputGenerator
from core.masking import ContextMasker
from core.prompt_generator import PromptGenerator
from utils.logger import setup_logger
from utils.tokenizer import TokenCounter

logger = setup_logger(__name__)

class ContextService:
    """
    Сервисный слой.
    Оркестрирует работу компонентов Core (Loader, Resolver, Masker, Generator).
    Вызывается напрямую из UI (Step 2).
    """

    @staticmethod
    def pick_context(
        loader: DbDataLoader,
        masker: ContextMasker,
        datasets: List[str],
        entities: List[str]
    ) -> Tuple[str, Dict[Any, Any]]:
        """
        Только подбирает контекст и маскирует его (без генерации полного промпта).
        Используется для кнопки "Подобрать контекст" в UI.
        
        Args:
            loader: Загрузчик данных БД.
            masker: Объект маскера.
            datasets: Список ID выбранных датасетов.
            entities: Список ID выбранных сущностей.
            
        Returns:
            Tuple[str, Dict]: (SQL-текст, Словарь масок)
        """
        logger.info(f"Запуск подбора контекста: Datasets={len(datasets)}, Entities={len(entities)}")
        
        # 1. Сбрасываем состояние маскера (начинаем нумерацию ENT_1 заново)
        masker.clear()
        
        # 2. Резолвинг зависимостей (строим граф объектов)
        resolver = ContextResolver(loader)
        for ds in datasets:
            resolver.resolve_by_dataset(ds)
        for ent in entities:
            resolver.resolve_by_entity(ent)
        
        # 3. Генерация SQL с маскированием
        # OutputGenerator будет вызывать masker.register() для каждого поля
        gen_masked = OutputGenerator(loader, resolver.context, masker=masker)
        sql_masked = gen_masked.generate_sql()
        
        logger.info(f"Контекст подобран. Размер SQL: {len(sql_masked)} символов.")
        
        # Возвращаем SQL и копию словаря масок (чтобы UI мог его отобразить)
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
        Генерирует два варианта промптов: Маскированный (для LLM) и Оригинальный (для проверки).
        Используется для кнопки "Сгенерировать промпт".
        """
        logger.info("Начало полной генерации промптов")
        
        # 1. Резолвинг (строим контекст заново для надежности)
        resolver = ContextResolver(loader)
        if datasets or entities:
            for ds in datasets: resolver.resolve_by_dataset(ds)
            for ent in entities: resolver.resolve_by_entity(ent)
        
        # 2. Генерация МАСКИРОВАННОГО SQL
        # Предполагаем, что masker уже содержит нужные маски (после pick_context),
        # либо наполняем его сейчас.
        gen_masked = OutputGenerator(loader, resolver.context, masker=masker)
        sql_masked = gen_masked.generate_sql()
        
        # 3. Генерация ОРИГИНАЛЬНОГО SQL (передаем masker=None)
        gen_orig = OutputGenerator(loader, resolver.context, masker=None)
        sql_original = gen_orig.generate_sql()
        
        # 4. Маскирование текстовых полей (System Prompt и User Query)
        system_prompt_masked = masker.mask_text(system_prompt)
        user_query_masked = masker.mask_text(user_query)
        
        # 5. Сборка финальных текстов
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
        
        # 6. Подсчет токенов (для маскированного промпта)
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