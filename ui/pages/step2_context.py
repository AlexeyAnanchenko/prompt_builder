import streamlit as st
from ui.components import (
    render_step_toggle_button,
    render_token_counter
)
from core.prompt_generator import PromptGenerator
from core.context_engine import DbDataLoader, ContextResolver, OutputGenerator
from core.masking import ContextMasker
from services.database import DatabaseManager
from config.settings import MESSAGES, TEXTAREA_HEIGHTS, MAX_TOKENS
from utils.logger import setup_logger
from utils.tokenizer import TokenCounter
from utils.helpers import copy_to_clipboard

logger = setup_logger(__name__)

# --- КОЛБЭКИ ---
def _clear_user_query():
    """Очищает поле ввода запроса"""
    st.session_state.user_query = ""

def _update_stored_datasets():
    """Сохраняет выбор датасетов в постоянное хранилище"""
    st.session_state.stored_datasets = st.session_state.selected_datasets

def _update_stored_entities():
    """Сохраняет выбор сущностей в постоянное хранилище"""
    st.session_state.stored_entities = st.session_state.selected_entities

def render_step2() -> None:
    """Рендерит шаг 2: Генерация промпта с маскированием"""
    logger.info("Рендер шага 2: Генерация промпта")
    
    if "masker" not in st.session_state:
        st.session_state["masker"] = ContextMasker()

    render_step_toggle_button(
        step_number=2,
        title="Сбор контекста и Генерация",
        state_key='show_step2'
    )
    
    if not st.session_state.get('show_step2', True):
        return
    
    _render_data_loading_section()
    st.markdown("---")
    
    if "loader" in st.session_state:
        _render_context_selection_section()
    else:
        st.info("👆 Сначала загрузите данные для выбранного Namespace")
    
    st.markdown("---")

    # --- ОСНОВНАЯ РАЗМЕТКА ---
    col_left, col_right = st.columns([30, 70])
    
    with col_left:
        _render_user_query_section()

    with col_right:
         _render_result_tabs_section()


def _render_data_loading_section():
    col_ns, col_btn = st.columns([3, 1])
    with col_ns:
        db_manager = DatabaseManager()
        namespaces = db_manager.get_all_namespaces()
        current_idx = 0
        if st.session_state.get('selected_namespace') and st.session_state.selected_namespace in namespaces:
            current_idx = namespaces.index(st.session_state.selected_namespace)
        selected_ns_str = st.selectbox("📂 Выберите namespace", options=namespaces, index=current_idx, key="namespace_selector")
        st.session_state.selected_namespace = selected_ns_str
    with col_btn:
        st.markdown("<div style='margin-top: 29px;'></div>", unsafe_allow_html=True)
        ns_id = selected_ns_str.split(' ')[0]
        if st.button("📥 Загрузить контекст", type="secondary", use_container_width=True):
            with st.spinner(f"Загрузка схемы для {ns_id}..."):
                try:
                    raw_data = db_manager.fetch_namespace_context(ns_id)
                    st.session_state["loader"] = DbDataLoader(raw_data)
                    st.session_state["current_ns_loaded"] = ns_id
                    
                    # Сброс сохраненных выборов при загрузке нового контекста
                    st.session_state["stored_datasets"] = []
                    st.session_state["stored_entities"] = []
                    
                    st.toast(f"Данные загружены: {sum(len(v) for v in raw_data.values())} записей", icon="✅")
                except Exception as e:
                    st.error(f"Ошибка: {e}")

    if "loader" in st.session_state:
        st.caption(f"Активный контекст в памяти: **{st.session_state.get('current_ns_loaded')}**")


def _render_context_selection_section():
    """Рендеринг выбора контекста с поддержкой персистентности и кнопкой подбора"""
    loader = st.session_state["loader"]
    all_ds_ids = sorted(list(set(k[2] for k in loader.db['datasets'].keys())))
    all_ent_ids = sorted(list(set(k[2] for k in loader.db['entities'].keys())))
    
    st.subheader("🎯 Выбор контекста")
    
    # Инициализация хранилища
    if "stored_datasets" not in st.session_state:
        st.session_state["stored_datasets"] = []
    if "stored_entities" not in st.session_state:
        st.session_state["stored_entities"] = []
    
    # НОВОЕ: Три колонки - datasets, entities, кнопка подбора
    col_ds, col_ent, col_btn = st.columns([5, 5, 2])
    
    with col_ds:
        st.multiselect(
            "📊 Datasets (Наборы данных)", 
            all_ds_ids, 
            placeholder="Выберите датасеты...", 
            key="selected_datasets",
            default=st.session_state["stored_datasets"],
            on_change=_update_stored_datasets,
            help="Выберите наборы данных для включения в контекст"
        )
    
    with col_ent:
        st.multiselect(
            "🔷 Entities (Доп. сущности)", 
            all_ent_ids, 
            placeholder="Выберите сущности...", 
            key="selected_entities",
            default=st.session_state["stored_entities"],
            on_change=_update_stored_entities,
            help="Выберите дополнительные сущности для контекста"
        )
    
    with col_btn:
        # Добавляем отступ сверху для выравнивания с мультиселектами
        st.markdown("<div style='margin-top: 29px;'></div>", unsafe_allow_html=True)
        
        if st.button(
            "🔍 Подобрать контекст",
            type="secondary",
            use_container_width=True,
            help="Подобрать контекст из БД на основе выбранных сущностей и датасетов, сразу с маскированием"
        ):
            _handle_context_pickup()


def _handle_context_pickup():
    """Обработчик кнопки 'Подобрать контекст' - генерирует SQL и создаёт словарь масок"""
    
    if "loader" not in st.session_state:
        st.error("Данные не загружены.")
        return
    
    loader = st.session_state["loader"]
    masker = st.session_state["masker"]
    
    # Очищаем предыдущий словарь масок
    masker.clear()
    
    # Читаем выбранные датасеты и сущности
    datasets = st.session_state.get("selected_datasets", [])
    entities = st.session_state.get("selected_entities", [])
    
    if not datasets and not entities:
        st.warning("⚠️ Выберите хотя бы один датасет или сущность для подбора контекста.")
        return
    
    with st.spinner("Анализ графа, генерация контекста и построение словаря масок..."):
        try:
            # Резолвим контекст
            resolver = ContextResolver(loader)
            for ds in datasets:
                resolver.resolve_by_dataset(ds)
            for ent in entities:
                resolver.resolve_by_entity(ent)
            
            # Генерируем SQL с маскированием
            gen_masked = OutputGenerator(loader, resolver.context, masker=masker)
            sql_masked = gen_masked.generate_sql()
            
            # Сохраняем результаты в session_state
            st.session_state.context_sql_masked = sql_masked
            st.session_state.masking_dictionary = masker.map_forward.copy()
            st.session_state.enable_masking = len(masker.map_forward) > 0
            
            # Информируем пользователя
            mask_count = len(masker.map_forward)
            st.toast(f"✅ Контекст подобран! Создано масок: {mask_count}")
            
            logger.info(f"Контекст подобран: {mask_count} элементов замаскировано")
            
            # ВАЖНО: Перерисовываем интерфейс, чтобы показать словарь
            st.rerun()
            
        except Exception as e:
            logger.error(f"Ошибка при подборе контекста: {e}")
            st.error(f"Ошибка при подборе контекста: {e}")


def _render_user_query_section():
    """Рендеринг секции пользовательского запроса"""
    
    # Заголовок
    st.subheader("💬 Мой запрос")
    
    # Текстовое поле
    st.text_area(
        "Введите ваш запрос", 
        height=TEXTAREA_HEIGHTS["user_query"], 
        placeholder="Опишите, что нужно сделать с конфигурацией (например: 'Добавь фильтр по salaryAmount')...", 
        key='user_query', 
        label_visibility="collapsed"
    )
    
    # НОВОЕ: Кнопки Очистить/Копировать НИЖЕ текстового поля, но ВЫШЕ кнопки генерации
    col_clear, col_copy = st.columns([1, 1])
    
    with col_clear:
        if st.button(
            "🗑️ Очистить", 
            key="clear_query_btn", 
            help="Очистить запрос", 
            on_click=_clear_user_query, 
            use_container_width=True
        ):
            pass
    
    with col_copy:
        text_to_copy = st.session_state.get('user_query', '')
        if st.button(
            "📋 Копировать", 
            key="copy_query_btn", 
            help="Копировать запрос", 
            disabled=not text_to_copy, 
            use_container_width=True
        ):
            copy_to_clipboard(text_to_copy, "copy_query_btn")
            st.toast("Текст скопирован!", icon="✅")
    
    # Небольшой отступ перед кнопкой генерации
    st.write("")
    
    # Кнопка генерации внизу
    if st.button("🚀 Сгенерировать промпт", key="btn_generate_final_prompt", use_container_width=True):
        _handle_generate_combined()


def _render_result_tabs_section():
    st.subheader("✨ Результат")
    
    # НОВОЕ: Показываем словарь замен, если он уже создан (после "Подобрать контекст")
    masker = st.session_state.get("masker")
    if masker and masker.map_forward and not st.session_state.get('final_prompt_masked'):
        with st.expander(f"🔐 Словарь замен ({len(masker.map_forward)} элементов)", expanded=True):
            st.caption("✨ Контекст подобран! Используйте эти названия в вашем запросе.")
            
            def natural_sort_key(item):
                mask_val = item[1]
                try:
                    prefix, num = mask_val.rsplit('_', 1)
                    return (prefix, int(num))
                except ValueError:
                    return (mask_val, 0)

            sorted_items = sorted(masker.map_forward.items(), key=natural_sort_key)
            
            df_data = [
                {"Category": k[0], "Real Name": k[1], "Mask": v} 
                for k, v in sorted_items
            ]
            
            st.dataframe(
                df_data, 
                height=400, 
                width='stretch',
                hide_index=True,
                column_config={
                    "Category": st.column_config.TextColumn("Категория", width="small"),
                    "Real Name": st.column_config.TextColumn("Реальное имя"),
                    "Mask": st.column_config.TextColumn("Маска", width="small"),
                }
            )
        return
    
    if not st.session_state.get('final_prompt_masked'):
        st.info("Введите запрос и нажмите кнопку 'Сгенерировать' слева.")
        return

    tab_masked, tab_original = st.tabs(["🎭 Замаскированный (Safe)", "👁️ Оригинальный"])
    
    token_count = st.session_state.get('token_count', 0)
    
    # Высота прокручиваемой области в пикселях
    SCROLL_HEIGHT = 500
    
    # --- TAB 1: MASKED ---
    with tab_masked:
        masked_text = st.session_state.final_prompt_masked
        
        render_token_counter(token_count, MAX_TOKENS)
        st.caption("Этот текст безопасен для отправки в публичную LLM.")

        with st.expander("📄 Показать текст промпта", expanded=True):
            with st.container(height=SCROLL_HEIGHT):
                st.code(masked_text, language="sql", line_numbers=True)
        
        if masker and masker.map_forward:
            with st.expander(f"🔐 Словарь замен ({len(masker.map_forward)} элементов)", expanded=False):
                
                def natural_sort_key(item):
                    mask_val = item[1]
                    try:
                        prefix, num = mask_val.rsplit('_', 1)
                        return (prefix, int(num))
                    except ValueError:
                        return (mask_val, 0)

                sorted_items = sorted(masker.map_forward.items(), key=natural_sort_key)
                
                df_data = [
                    {"Category": k[0], "Real Name": k[1], "Mask": v} 
                    for k, v in sorted_items
                ]
                
                st.dataframe(
                    df_data, 
                    height=400, 
                    width='stretch',
                    hide_index=True,
                    column_config={
                        "Category": st.column_config.TextColumn("Категория", width="small"),
                        "Real Name": st.column_config.TextColumn("Реальное имя"),
                        "Mask": st.column_config.TextColumn("Маска", width="small"),
                    }
                )

    # --- TAB 2: ORIGINAL ---
    with tab_original:
        orig_text = st.session_state.final_prompt_original
        
        render_token_counter(token_count, MAX_TOKENS)
        st.caption("Внимание! Содержит реальные названия полей и конфигураций.")
        
        with st.expander("📄 Показать оригинальный промпт", expanded=True):
            with st.container(height=SCROLL_HEIGHT):
                st.code(orig_text, language="sql", line_numbers=True)


def _handle_generate_combined():
    """Обработчик генерации финального промпта"""

    ns_id = st.session_state.selected_namespace.split(' ')[0]
    masker = st.session_state["masker"]
    
    if "loader" not in st.session_state:
        st.error("Данные не загружены.")
        return

    loader = st.session_state["loader"]
    
    datasets = st.session_state.get("selected_datasets", [])
    entities = st.session_state.get("selected_entities", [])
    
    system_prompt_orig = st.session_state.get('system_prompt', '')
    user_query_orig = st.session_state.get('user_query', '')
    
    with st.spinner("Анализ графа, генерация SQL и маскирование..."):
        resolver = ContextResolver(loader)
        if datasets or entities:
            for ds in datasets: resolver.resolve_by_dataset(ds)
            for ent in entities: resolver.resolve_by_entity(ent)
        
        gen_masked = OutputGenerator(loader, resolver.context, masker=masker)
        sql_masked = gen_masked.generate_sql()
        
        gen_orig = OutputGenerator(loader, resolver.context, masker=None)
        sql_original = gen_orig.generate_sql()
        
        system_prompt_masked = masker.mask_text(system_prompt_orig)
        user_query_masked = masker.mask_text(user_query_orig)
        
        generator = PromptGenerator()
        
        final_prompt_masked = generator.generate(
            system_prompt=system_prompt_masked,
            user_query=user_query_masked,
            namespace=ns_id,
            sql_context=sql_masked
        )
        
        final_prompt_original = generator.generate(
            system_prompt=system_prompt_orig,
            user_query=user_query_orig,
            namespace=ns_id,
            sql_context=sql_original
        )
        
        st.session_state.final_prompt_masked = final_prompt_masked
        st.session_state.final_prompt_original = final_prompt_original
        st.session_state.generated_sql_context = sql_original
        
        try:
            token_count = TokenCounter.count_tokens(final_prompt_masked)
            st.session_state.token_count = token_count
            logger.info(f"Токенов в промпте: {token_count}")
        except Exception as e:
            logger.error(f"Ошибка подсчета токенов: {e}")
            st.session_state.token_count = 0
        
        st.session_state.masking_dictionary = masker.map_forward.copy()
        st.session_state.enable_masking = len(masker.map_forward) > 0
        
        st.toast("✅ Промпт успешно сгенерирован!", icon="✅")
        st.rerun()