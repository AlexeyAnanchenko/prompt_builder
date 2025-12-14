import streamlit as st
from typing import Optional, Dict, Any

from ui.components import (
    render_step_toggle_button,
    render_token_counter
)
from core.context_engine import DbDataLoader
from core.masking import ContextMasker
from services.database import DatabaseManager
from services.context_service import ContextService
from config.settings import TEXTAREA_HEIGHTS, MAX_TOKENS
from utils.logger import setup_logger
from utils.helpers import copy_to_clipboard

# Настройка логгера
logger = setup_logger(__name__)

# --- CALLBACKS (Функции обратного вызова) ---

def _clear_user_query() -> None:
    """Очищает поле ввода пользовательского запроса."""
    st.session_state.user_query = ""

def _update_stored_datasets() -> None:
    """
    Сохраняет выбор датасетов в постоянное хранилище session_state.
    """
    st.session_state.stored_datasets = st.session_state.selected_datasets

def _update_stored_entities() -> None:
    """
    Сохраняет выбор сущностей в постоянное хранилище session_state.
    """
    st.session_state.stored_entities = st.session_state.selected_entities


# --- MAIN RENDER FUNCTION ---

def render_step2() -> None:
    """
    Рендерит Шаг 2: Сбор контекста и Генерация.
    """
    logger.debug("Рендер шага 2")
    
    # Гарантируем наличие объекта маскера в сессии
    if "masker" not in st.session_state:
        st.session_state["masker"] = ContextMasker()

    # Кнопка сворачивания/разворачивания шага
    render_step_toggle_button(
        step_number=2,
        title="Сбор контекста и Генерация",
        state_key='show_step2'
    )
    
    # Если шаг свернут, прекращаем рендер
    if not st.session_state.get('show_step2', True):
        return
    
    # --- Секция 1: Загрузка данных из БД ---
    _render_data_loading_section()
    st.markdown("---")
    
    # --- Секция 2: Выбор контекста (только если данные загружены) ---
    if "loader" in st.session_state:
        _render_context_selection_section()
    else:
        st.info("👆 Сначала загрузите данные для выбранного Namespace")
    
    st.markdown("---")

    # --- Секция 3: Запрос и Результаты (Разделение экрана 30/70) ---
    col_left, col_right = st.columns([30, 70])
    
    with col_left:
        _render_user_query_section()

    with col_right:
         _render_result_tabs_section()


def _render_data_loading_section() -> None:
    """Рендерит выбор Namespace и кнопку загрузки контекста."""
    col_ns, col_btn = st.columns([3, 1])
    
    with col_ns:
        try:
            db_manager = DatabaseManager()
            namespaces = db_manager.get_all_namespaces()
            
            # Пытаемся восстановить ранее выбранное значение
            current_idx = 0
            if st.session_state.get('selected_namespace') and st.session_state.selected_namespace in namespaces:
                current_idx = namespaces.index(st.session_state.selected_namespace)
            
            selected_ns_str = st.selectbox(
                "📂 Выберите namespace", 
                options=namespaces, 
                index=current_idx, 
                key="namespace_selector"
            )
            st.session_state.selected_namespace = selected_ns_str
            
        except Exception as e:
            logger.error(f"Ошибка получения namespaces: {e}", exc_info=True)
            st.error(f"Ошибка подключения к БД: {e}")
            return

    with col_btn:
        st.markdown("<div style='margin-top: 29px;'></div>", unsafe_allow_html=True)
        
        ns_id = selected_ns_str.split(' ')[0] if selected_ns_str else None
        
        if st.button("📥 Загрузить контекст", type="secondary", use_container_width=True, disabled=not ns_id):
            if ns_id:
                with st.spinner(f"Загрузка схемы для {ns_id}..."):
                    try:
                        raw_data = db_manager.fetch_namespace_context(ns_id)
                        
                        st.session_state["loader"] = DbDataLoader(raw_data)
                        st.session_state["current_ns_loaded"] = ns_id
                        
                        # Сброс выбранных датасетов/сущностей
                        st.session_state["stored_datasets"] = []
                        st.session_state["stored_entities"] = []
                        # Явно обнуляем ключи виджетов, чтобы очистить выбор визуально
                        st.session_state["selected_datasets"] = []
                        st.session_state["selected_entities"] = []
                        
                        logger.info(f"Контекст загружен для namespace {ns_id}")
                        st.toast(f"Данные загружены: {sum(len(v) for v in raw_data.values())} записей", icon="✅")
                        
                    except Exception as e:
                        logger.error(f"Ошибка загрузки контекста: {e}", exc_info=True)
                        st.error(f"Ошибка: {e}")

    if "loader" in st.session_state:
        st.caption(f"Активный namespace в памяти: **{st.session_state.get('current_ns_loaded')}**")


def _render_context_selection_section() -> None:
    """Рендерит мультиселекты для выбора Datasets и Entities."""
    loader: DbDataLoader = st.session_state["loader"]
    
    all_ds_ids = sorted(list(set(k[2] for k in loader.db['datasets'].keys())))
    all_ent_ids = sorted(list(set(k[2] for k in loader.db['entities'].keys())))
    
    # Инициализация хранилища выбора (если еще нет)
    if "stored_datasets" not in st.session_state: st.session_state["stored_datasets"] = []
    if "stored_entities" not in st.session_state: st.session_state["stored_entities"] = []

    # === ИСПРАВЛЕНИЕ WARNING ===
    # Если ключа виджета нет в session_state, инициализируем его сохраненным значением.
    # Если ключ уже есть (например, после _render_data_loading_section), оставляем как есть.
    if "selected_datasets" not in st.session_state:
        st.session_state.selected_datasets = st.session_state.stored_datasets
    
    if "selected_entities" not in st.session_state:
        st.session_state.selected_entities = st.session_state.stored_entities
    
    col_ds, col_ent, col_btn = st.columns([5, 5, 2])
    
    with col_ds:
        st.multiselect(
            "📊 Datasets (Наборы данных)", 
            all_ds_ids, 
            placeholder="Выберите датасеты...", 
            key="selected_datasets", # Виджет работает с этим ключом
            # default=...  <-- УДАЛЕНО: Default конфликтует с session_state, инициализируем вручную выше
            on_change=_update_stored_datasets,
            help="Выберите наборы данных для включения в контекст"
        )
    
    with col_ent:
        st.multiselect(
            "👥 Entities (Сущности)",
            all_ent_ids, 
            placeholder="Выберите сущности...", 
            key="selected_entities",
            on_change=_update_stored_entities,
            help="Выберите дополнительные сущности для контекста"
        )
    
    with col_btn:
        st.markdown("<div style='margin-top: 29px;'></div>", unsafe_allow_html=True)
        if st.button(
            "🔍 Подобрать контекст",
            type="secondary",
            use_container_width=True,
            help="Подобрать контекст из БД на основе выбранных сущностей и датасетов"
        ):
            _handle_context_pickup()


def _handle_context_pickup() -> None:
    """Обработчик логики подбора контекста."""
    loader: Optional[DbDataLoader] = st.session_state.get("loader")
    masker: Optional[ContextMasker] = st.session_state.get("masker")
    
    if loader is None or masker is None:
        st.error("Ошибка состояния: Данные не загружены.")
        return
    
    datasets = st.session_state.get("selected_datasets", [])
    entities = st.session_state.get("selected_entities", [])
    
    if not datasets and not entities:
        st.warning("⚠️ Выберите хотя бы один датасет или сущность.")
        return
    
    with st.spinner("Анализ графа и построение масок..."):
        try:
            sql_masked, mask_map = ContextService.pick_context(
                loader, masker, datasets, entities
            )
            
            st.session_state.context_sql_masked = sql_masked
            st.session_state.masking_dictionary = mask_map
            st.session_state.enable_masking = len(mask_map) > 0
            
            logger.info(f"Контекст подобран: {len(mask_map)} масок.")
            st.toast(f"✅ Контекст подобран! Создано масок: {len(mask_map)}")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Ошибка при подборе контекста: {e}", exc_info=True)
            st.error(f"Ошибка при подборе контекста: {e}")


def _render_user_query_section() -> None:
    """Рендерит область ввода пользовательского запроса."""
    st.subheader("💬 Мой запрос")
    
    st.text_area(
        "Введите ваш запрос", 
        height=TEXTAREA_HEIGHTS["user_query"], 
        placeholder="Опишите, что нужно сделать с конфигурацией...", 
        key='user_query', 
        label_visibility="collapsed"
    )
    
    col_clear, col_copy = st.columns([1, 1])
    with col_clear:
        st.button("🗑️ Очистить", key="clear_query_btn", on_click=_clear_user_query, use_container_width=True)
    with col_copy:
        text_to_copy = st.session_state.get('user_query', '')
        if st.button("📋 Копировать", key="copy_query_btn", disabled=not text_to_copy, use_container_width=True):
            copy_to_clipboard(text_to_copy, "copy_query_btn")
            st.toast("Текст скопирован!", icon="✅")
    
    if st.button("🚀 Сгенерировать промпт", key="btn_generate_final_prompt", use_container_width=True):
        _handle_generate_combined()


def _render_result_tabs_section() -> None:
    """Рендерит правую часть: табы с результатами или словарь масок."""
    st.subheader("✨ Результат")
    
    masker = st.session_state.get("masker")
    has_final_prompt = bool(st.session_state.get('final_prompt_masked'))
    
    if masker and masker.map_forward and not has_final_prompt:
        with st.expander(f"🔐 Словарь замен ({len(masker.map_forward)} элементов)", expanded=True):
            st.caption("✨ Контекст подобран! Используйте эти маски в вашем запросе.")
            _render_masking_dictionary(masker.map_forward)
        return
    
    if not has_final_prompt:
        st.info("Введите запрос и нажмите кнопку 'Сгенерировать' слева.")
        return

    tab_masked, tab_original = st.tabs(["🎭 Замаскированный", "📜 Оригинальный"])
    token_count = st.session_state.get('token_count', 0)
    SCROLL_HEIGHT = 500
    
    with tab_masked:
        masked_text = st.session_state.final_prompt_masked
        render_token_counter(token_count, MAX_TOKENS)
        st.caption("Этот текст безопасен для отправки в публичную LLM.")

        with st.expander("📄 Показать текст промпта", expanded=True):
            with st.container(height=SCROLL_HEIGHT):
                st.code(masked_text, language="sql", line_numbers=True)
        
        if masker and masker.map_forward:
            with st.expander(f"🔐 Словарь замен ({len(masker.map_forward)} элементов)", expanded=False):
                _render_masking_dictionary(masker.map_forward)

    with tab_original:
        orig_text = st.session_state.final_prompt_original
        render_token_counter(token_count, MAX_TOKENS)
        st.caption("Внимание! Содержит реальные названия полей и конфигураций.")
        
        with st.expander("📄 Показать оригинальный промпт", expanded=True):
            with st.container(height=SCROLL_HEIGHT):
                st.code(orig_text, language="sql", line_numbers=True)


def _render_masking_dictionary(mask_map: Dict[Any, Any]) -> None:
    """Вспомогательная функция для отрисовки таблицы масок."""
    
    def natural_sort_key(item):
        mask_val = item[1]
        try:
            prefix, num = mask_val.rsplit('_', 1)
            return (prefix, int(num))
        except ValueError:
            return (mask_val, 0)

    sorted_items = sorted(mask_map.items(), key=natural_sort_key)
    
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


def _handle_generate_combined() -> None:
    """Обработчик полной генерации промпта."""
    loader: Optional[DbDataLoader] = st.session_state.get("loader")
    if loader is None:
        st.error("Данные не загружены.")
        return
    
    ns_id = st.session_state.selected_namespace.split(' ')[0]
    masker: ContextMasker = st.session_state["masker"]
    
    datasets = st.session_state.get("selected_datasets", [])
    entities = st.session_state.get("selected_entities", [])
    system_prompt = st.session_state.get('system_prompt', '')
    user_query = st.session_state.get('user_query', '')
    
    with st.spinner("Генерация промпта и маскирование..."):
        try:
            result = ContextService.generate_final_prompts(
                loader, masker, ns_id, datasets, entities, system_prompt, user_query
            )
            
            st.session_state.final_prompt_masked = result["final_prompt_masked"]
            st.session_state.final_prompt_original = result["final_prompt_original"]
            st.session_state.generated_sql_context = result["sql_original"]
            st.session_state.token_count = result["token_count"]
            st.session_state.masking_dictionary = result["masking_dict"]
            st.session_state.enable_masking = len(result["masking_dict"]) > 0
            
            logger.info(f"Промпт сгенерирован. Токенов: {result['token_count']}")
            st.toast("✅ Промпт успешно сгенерирован!")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Ошибка генерации промпта: {e}", exc_info=True)
            st.error(f"Ошибка при генерации: {e}")