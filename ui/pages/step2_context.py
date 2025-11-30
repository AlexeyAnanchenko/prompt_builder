import streamlit as st
from ui.components import (
    render_step_toggle_button,
    render_button_pair,
    render_token_counter
)
from core.prompt_generator import PromptGenerator
from core.context_engine import DbDataLoader, ContextResolver, OutputGenerator
from core.masking import ContextMasker
from services.database import DatabaseManager
from config.settings import MESSAGES, TEXTAREA_HEIGHTS, MAX_TOKENS
from utils.logger import setup_logger

logger = setup_logger(__name__)

def render_step2() -> None:
    """Рендерит шаг 2: Генерация промпта с маскированием"""
    logger.info("Рендер шага 2: Генерация промпта")
    
    # Инициализация маскера
    if "masker" not in st.session_state:
        st.session_state["masker"] = ContextMasker()

    # CSS для зеленой кнопки
    st.markdown("""
        <style>
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
        div[data-testid="stButton"] > button[key="btn_generate_final_prompt"]:active {
            background-color: #1e7e34 !important;
            color: white !important;
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
    
    # 1. Загрузка данных
    _render_data_loading_section()
    st.markdown("---")
    
    # 2. Выбор сущностей
    if "loader" in st.session_state:
        _render_context_selection_section()
    else:
        st.info("👆 Сначала загрузите данные для выбранного Namespace")
    
    st.markdown("---")

    # 3. Рабочая область: Запрос (слева) -> Результат (справа)
    col_left, col_right = st.columns(2)
    
    with col_left:
        _render_user_query_section()
        
        # Кнопка генерации под полем ввода
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
    st.subheader("💬 Мой запрос")
    st.text_area(
        "Введите ваш запрос", 
        height=TEXTAREA_HEIGHTS["user_query"], 
        placeholder="Опишите, что нужно сделать с конфигурацией (например: 'Добавь фильтр по salaryAmount')...", 
        key='user_query', 
        label_visibility="collapsed"
    )


def _render_result_tabs_section():
    st.subheader("✨ Результат")
    
    # Проверяем, есть ли сгенерированный промпт
    if not st.session_state.get('final_prompt_masked'):
        st.info("Введите запрос и нажмите кнопку 'Сгенерировать' слева.")
        return

    # Показываем успех сразу
    st.success("Промпт успешно сгенерирован!")

    # Табы для переключения
    tab_masked, tab_original = st.tabs(["🎭 Замаскированный (Safe)", "👁️ Оригинальный"])
    
    masker = st.session_state.get("masker")
    
    # --- TAB 1: MASKED ---
    with tab_masked:
        masked_text = st.session_state.final_prompt_masked
        
        # Счетчик токенов показываем сразу (это полезная мета-информация)
        render_token_counter(len(masked_text.split()), MAX_TOKENS)
        
        st.caption("Этот текст безопасен для отправки в публичную LLM.")

        # Прячем огромный текст под кат
        with st.expander("📄 Показать текст промпта и кнопки", expanded=False):
            st.code(masked_text, language="sql", line_numbers=True)
            render_button_pair("clear_masked", "copy_masked", masked_text)
        
        # Словарь замен отдельным экспандером
        if masker and masker.map_forward:
             with st.expander(f"🔐 Словарь замен ({len(masker.map_forward)} элементов)", expanded=False):
                st.table([
                    {"Real Name": k, "Mask": v} 
                    for k, v in masker.map_forward.items()
                ])

    # --- TAB 2: ORIGINAL ---
    with tab_original:
        orig_text = st.session_state.final_prompt_original
        
        render_token_counter(len(orig_text.split()), MAX_TOKENS)
        st.caption("Внимание! Содержит реальные названия полей и конфигураций.")
        
        # Прячем оригинал под кат
        with st.expander("📄 Показать оригинальный промпт", expanded=False):
            st.code(orig_text, language="sql", line_numbers=True)
            render_button_pair("clear_orig", "copy_orig", orig_text)


def _handle_generate_combined():
    if not st.session_state.get('user_query'):
        st.error(MESSAGES["error_no_query"])
        return
        
    ns_id = st.session_state.selected_namespace.split(' ')[0]
    masker = st.session_state["masker"]
    
    # 1. Очищаем маскер перед генерацией
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
        # A. Строим контекст (Граф зависимостей)
        # Это нужно сделать один раз, так как граф зависимостей одинаков
        resolver = ContextResolver(loader)
        if datasets or entities:
            for ds in datasets: resolver.resolve_by_dataset(ds)
            for ent in entities: resolver.resolve_by_entity(ent)
        
        # B. Генерируем SQL в ДВУХ вариантах
        
        # Вариант 1: Замаскированный (Заполняет masker словарь)
        gen_masked = OutputGenerator(loader, resolver.context, masker=masker)
        sql_masked = gen_masked.generate_sql()
        
        # Вариант 2: Оригинальный (masker=None)
        gen_orig = OutputGenerator(loader, resolver.context, masker=None)
        sql_original = gen_orig.generate_sql()
        
        # C. Маскируем текстовые части промпта (User Query, System Prompt)
        # Теперь, когда SQL сгенерирован, словарь маскера полон ID-шников.
        # Можем прогнать через него текст вопроса.
        system_prompt_masked = masker.mask_text(system_prompt_orig)
        user_query_masked = masker.mask_text(user_query_orig)
        
        # D. Собираем финальные промпты через PromptGenerator
        generator = PromptGenerator()
        
        # Промпт 1: Полностью замаскированный
        final_prompt_masked = generator.generate(
            system_prompt=system_prompt_masked,
            user_query=user_query_masked,
            namespace=ns_id, # Namespace ID можно не маскировать или замаскировать отдельно, если критично
            sql_context=sql_masked
        )
        
        # Промпт 2: Полностью оригинальный
        final_prompt_original = generator.generate(
            system_prompt=system_prompt_orig,
            user_query=user_query_orig,
            namespace=ns_id,
            sql_context=sql_original
        )
        
        # Сохраняем в Session State
        st.session_state.final_prompt_masked = final_prompt_masked
        st.session_state.final_prompt_original = final_prompt_original
        st.session_state.generated_sql_context = sql_original # На всякий случай
        
        st.success("Готово! Выберите вкладку справа.")
        st.rerun()