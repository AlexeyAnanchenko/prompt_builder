import streamlit as st
from ui.components import (
    render_step_toggle_button,
    render_button_pair,
    render_token_counter
)
from core.prompt_generator import PromptGenerator
from core.masking import MaskingService
from services.database import DatabaseManager
from services.vector_store import VectorStoreManager
from utils.helpers import count_tokens, safe_strip
from config.settings import MESSAGES, TEXTAREA_HEIGHTS, MAX_TOKENS


def render_step2() -> None:
    """Рендерит шаг 2: Генерация промпта с контекстом"""
    render_step_toggle_button(
        step_number=2,
        title="Генерация промпта с контекстом",
        state_key='show_step2'
    )
    
    if not st.session_state.get('show_step2', True):
        return
    
    # Настройки: namespace и маскирование
    _render_settings_row()
    
    st.markdown("---")
    
    # Две колонки: запрос и готовый промпт
    col_left, col_right = st.columns(2)
    
    with col_left:
        _render_user_query_section()
    
    with col_right:
        _render_final_prompt_section()
    
    st.markdown("---")
    
    # Нижняя панель с кнопками
    _render_action_buttons()


def _render_settings_row() -> None:
    """Рендерит строку настроек (namespace + маскирование)"""
    col_namespace, col_masking = st.columns([2, 1])
    
    with col_namespace:
        db_manager = DatabaseManager()
        namespaces = db_manager.get_all_namespaces()
        
        if namespaces:
            if st.session_state.selected_namespace not in namespaces:
                st.session_state.selected_namespace = namespaces[0]
            
            selected = st.selectbox(
                "📂 Выберите namespace",
                options=namespaces,
                index=namespaces.index(st.session_state.selected_namespace),
                key="namespace_selector"
            )
            st.session_state.selected_namespace = selected
        else:
            st.warning(MESSAGES["warning_no_namespaces"])
    
    with col_masking:
        st.markdown("<div style='margin-top: 29px;'></div>", unsafe_allow_html=True)
        masking_enabled = st.checkbox(
            "🎭 Включить маскирование",
            value=st.session_state.enable_masking,
            key="enable_masking_checkbox",
            help="Автоматически маскирует конфиденциальные данные в промпте"
        )
        st.session_state.enable_masking = masking_enabled


def _render_user_query_section() -> None:
    """Рендерит секцию пользовательского запроса"""
    st.subheader("💬 Мой запрос")
    
    st.text_area(
        "Введите ваш запрос",
        height=TEXTAREA_HEIGHTS["user_query"],
        placeholder="Введите ваш запрос здесь...",
        key='user_query',
        label_visibility="collapsed"
    )
    
    render_button_pair(
        clear_key="clear_user",
        copy_key="copy_user",
        text_to_copy=st.session_state.get('user_query'),
        clear_callback=lambda: st.session_state.update({'user_query': ''})
    )


def _render_final_prompt_section() -> None:
    """Рендерит секцию готового промпта"""
    st.subheader("✨ Готовый промпт")
    
    if st.session_state.get('final_prompt'):
        if st.session_state.enable_masking and st.session_state.get('masked_prompt'):
            _render_masked_prompt_tabs()
        else:
            st.code(
                st.session_state.final_prompt,
                language="sql",
                line_numbers=True
            )
    else:
        st.info("👈 Введите запрос и нажмите 'Сгенерировать'")
    
    _render_final_prompt_buttons()
    
    # Счётчик токенов
    render_token_counter(
        st.session_state.get('token_count', 0),
        MAX_TOKENS
    )


def _render_masked_prompt_tabs() -> None:
    """Рендерит табы для оригинального и замаскированного промпта"""
    tab_masked, tab_original = st.tabs([
        "🎭 Замаскированный (отправить в LLM)",
        "👁️ Оригинальный"
    ])
    
    with tab_masked:
        st.code(
            st.session_state.masked_prompt,
            language="sql",
            line_numbers=True
        )
        
        # Показываем статистику маскирования
        if st.session_state.masking_dictionary:
            with st.expander("🔐 Словарь замен", expanded=False):
                for mask, original in st.session_state.masking_dictionary.items():
                    st.text(f"{mask} → {original}")
    
    with tab_original:
        st.code(
            st.session_state.final_prompt,
            language="sql",
            line_numbers=True
        )


def _render_final_prompt_buttons() -> None:
    """Рендерит кнопки для финального промпта"""
    prompt_to_copy = (
        st.session_state.masked_prompt
        if (st.session_state.enable_masking and st.session_state.get('masked_prompt'))
        else st.session_state.get('final_prompt', '')
    )
    
    render_button_pair(
        clear_key="clear_final",
        copy_key="copy_final",
        text_to_copy=prompt_to_copy,
        clear_callback=lambda: st.session_state.update({
            'final_prompt': '',
            'masked_prompt': '',
            'token_count': 0
        })
    )


def _render_action_buttons() -> None:
    """Рендерит кнопки действий (обновить БД, сгенерировать)"""
    col_refresh, col_gen, col_info = st.columns([1, 2, 1])
    
    with col_refresh:
        if st.button("🔄 Обновить векторную БД", use_container_width=True):
            _handle_rebuild_database()
    
    with col_gen:
        if st.button(
            "🚀 Сгенерировать промпт",
            type="primary",
            use_container_width=True
        ):
            _handle_generate_prompt()
    
    with col_info:
        _render_info_popover()


def _handle_rebuild_database() -> None:
    """Обработчик обновления векторной БД"""
    with st.spinner('Обновление базы...'):
        try:
            db_manager = DatabaseManager()
            vector_manager = VectorStoreManager()
            
            data = db_manager.fetch_all_data_by_namespace(
                st.session_state.selected_namespace
            )
            result = vector_manager.rebuild_database(
                data,
                st.session_state.selected_namespace
            )
            
            st.success(f"✅ Векторная база успешно обновлена! {result}")
        except Exception as e:
            st.error(f"⛔ Ошибка при обновлении: {str(e)}")


def _handle_generate_prompt() -> None:
    """Обработчик генерации промпта"""
    if not safe_strip(st.session_state.get('user_query')):
        st.error(MESSAGES["error_no_query"])
        return
    
    with st.spinner("⏳ Генерация промпта..."):
        try:
            # Генерируем оригинальный промпт
            generator = PromptGenerator()
            st.session_state.final_prompt = generator.generate(
                st.session_state.system_prompt or "",
                st.session_state.user_query or "",
                st.session_state.selected_namespace
            )
            
            # Маскируем при необходимости
            if st.session_state.enable_masking:
                masking_service = MaskingService()
                masked, mapping = masking_service.mask_text(
                    st.session_state.final_prompt
                )
                st.session_state.masked_prompt = masked
                st.session_state.masking_dictionary = mapping
                st.session_state.token_count = count_tokens(masked)
                
                if mapping:
                    st.success(
                        MESSAGES["success_masked_elements"].format(len(mapping))
                    )
                else:
                    st.info(MESSAGES["info_no_confidential"])
            else:
                st.session_state.masked_prompt = ""
                st.session_state.masking_dictionary = {}
                st.session_state.token_count = count_tokens(
                    st.session_state.final_prompt
                )
                st.success(MESSAGES["success_prompt_generated"])
            
            st.rerun()
        except Exception as e:
            st.error(f"⛔ Ошибка при генерации промпта: {str(e)}")


def _render_info_popover() -> None:
    """Рендерит popover со справкой"""
    with st.popover("ℹ️ Справка"):
        st.markdown("""
**Как использовать:**

**Этап 1: Системный промпт**
- Создайте или загрузите версию системного промпта

**Этап 2: Генерация промпта**
- Выберите namespace
- Включите маскирование (если нужно)
- Введите свой запрос
- При необходимости обновите векторную БД
- Нажмите "Сгенерировать промпт"
- Скопируйте замаскированный промпт и отправьте в LLM

**Этап 3: Расшифровка ответа**
- Вставьте ответ от LLM
- Нажмите "Расшифровать"
- Получите ответ с реальными данными

**TODO для интеграции:**
- Замените функцию `mask_text()` на свою логику маскирования
- Замените функцию `unmask_text()` на свою логику расшифровки
""")