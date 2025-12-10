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

def render_step2() -> None:
    """Рендерит шаг 2: Генерация промпта с маскированием"""
    logger.info("Рендер шага 2: Генерация промпта")
    
    if "masker" not in st.session_state:
        st.session_state["masker"] = ContextMasker()

    # CSS для кнопок
    st.markdown("""
        <style>
        /* Стиль зеленой кнопки генерации */
        div[data-testid="stButton"] > button[key="btn_generate_final_prompt"] {
            background-color: #28a745 !important;
            color: white !important;
            border-color: #28a745 !important;
        }
        div[data-testid="stButton"] > button[key="btn_generate_final_prompt"]:hover {
            background-color: #218838 !important;
            border-color: #1e7e34 !important;
            color: white !important;
        }
        
        /* Выравнивание кнопок в заголовке запроса */
        .query-toolbar-btn {
            margin-top: -5px;
        }
        </style>
    """, unsafe_allow_html=True)

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

    # --- НАСТРОЙКА ИНТЕРФЕЙСА (СЛАЙДЕР) ---
    # Позволяет пользователю менять ширину колонок
    with st.expander("⚙️ Настройки отображения (ширина колонок)", expanded=False):
        col_ratio = st.slider(
            "Ширина левой части (Запрос) %", 
            min_value=20, 
            max_value=80, 
            value=30, 
            step=5,
            help="Подвиньте, чтобы увеличить место для промпта (справа) или для ввода (слева)."
        )
    
    # Разделяем экран в пропорции, заданной слайдером
    col_left, col_right = st.columns([col_ratio, 100 - col_ratio])
    
    with col_left:
        _render_user_query_section()
        
        st.write("") 
        if st.button("🚀 Сгенерировать промпт", key="btn_generate_final_prompt", use_container_width=True):
            _handle_generate_combined()

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
                    st.toast(f"Данные загружены: {sum(len(v) for v in raw_data.values())} записей", icon="✅")
                except Exception as e:
                    st.error(f"Ошибка: {e}")

    if "loader" in st.session_state:
        st.caption(f"Активный контекст в памяти: **{st.session_state.get('current_ns_loaded')}**")


def _render_context_selection_section():
    loader = st.session_state["loader"]
    all_ds_ids = sorted(list(set(k[2] for k in loader.db['datasets'].keys())))
    all_ent_ids = sorted(list(set(k[2] for k in loader.db['entities'].keys())))
    
    col_ds, col_ent = st.columns(2)
    with col_ds:
        st.multiselect("Datasets (Наборы данных)", all_ds_ids, placeholder="Выберите датасеты...", key="selected_datasets")
    with col_ent:
        st.multiselect("Entities (Доп. сущности)", all_ent_ids, placeholder="Выберите сущности...", key="selected_entities")


def _render_user_query_section():
    # Создаем строку с заголовком и кнопками
    col_title, col_btns = st.columns([2, 1])
    
    with col_title:
        st.subheader("💬 Мой запрос")
        
    with col_btns:
        # Выравниваем кнопки вправо
        sub_c1, sub_c2 = st.columns([1, 1])
        with sub_c1:
            if st.button("🗑️", key="clear_query_btn", help="Очистить запрос", on_click=_clear_user_query, use_container_width=True):
                pass
        with sub_c2:
            # Для копирования берем текст из state
            text_to_copy = st.session_state.get('user_query', '')
            if st.button("📋", key="copy_query_btn", help="Копировать запрос", disabled=not text_to_copy, use_container_width=True):
                copy_to_clipboard(text_to_copy, "copy_query_btn")
                st.toast("Запрос скопирован!")

    st.text_area(
        "Введите ваш запрос", 
        height=TEXTAREA_HEIGHTS["user_query"], 
        placeholder="Опишите, что нужно сделать с конфигурацией (например: 'Добавь фильтр по salaryAmount')...", 
        key='user_query', 
        label_visibility="collapsed"
    )


def _render_result_tabs_section():
    st.subheader("✨ Результат")
    
    if not st.session_state.get('final_prompt_masked'):
        st.info("Введите запрос и нажмите кнопку 'Сгенерировать' слева.")
        return

    st.success("Промпт успешно сгенерирован!")

    tab_masked, tab_original = st.tabs(["🎭 Замаскированный (Safe)", "👁️ Оригинальный"])
    
    masker = st.session_state.get("masker")
    token_count = st.session_state.get('token_count', 0)
    
    # Высота прокручиваемой области в пикселях
    SCROLL_HEIGHT = 500
    
    # --- TAB 1: MASKED ---
    with tab_masked:
        masked_text = st.session_state.final_prompt_masked
        
        render_token_counter(token_count, MAX_TOKENS)
        st.caption("Этот текст безопасен для отправки в публичную LLM.")

        with st.expander("📄 Показать текст промпта", expanded=True):
            # Контейнер с фиксированной высотой = скролл всегда активен, если контент больше
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
                
                # ИСПРАВЛЕНИЕ: use_container_width=True -> width="stretch"
                st.dataframe(
                    df_data, 
                    height=400, 
                    width="stretch", # Исправлено согласно ошибке
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
            # Контейнер с фиксированной высотой
            with st.container(height=SCROLL_HEIGHT):
                st.code(orig_text, language="sql", line_numbers=True)


def _handle_generate_combined():

    ns_id = st.session_state.selected_namespace.split(' ')[0]
    masker = st.session_state["masker"]
    
    masker.clear()
    
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
        
        st.success("Готово! Выберите вкладку справа.")
        st.rerun()