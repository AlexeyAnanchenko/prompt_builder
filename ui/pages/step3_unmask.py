import streamlit as st
from ui.components import render_step_toggle_button, render_button_pair
from core.masking import MaskingService
from config.settings import MESSAGES, TEXTAREA_HEIGHTS
from utils.logger import setup_logger


# Настраиваем логгер для модуля
logger = setup_logger(__name__)


def render_step3() -> None:
    """Рендерит шаг 3: Расшифровка ответа LLM"""
    logger.info("Рендер шага 3: Расшифровка ответа LLM")
    render_step_toggle_button(
        step_number=3,
        title="Расшифровка ответа LLM",
        state_key='show_step3'
    )
    
    if not st.session_state.get('show_step3', False):
        logger.debug("Шаг 3 скрыт, пропускаем рендер")
        return
    
    # Две колонки: замаскированный ответ и расшифрованный
    col_llm_left, col_llm_right = st.columns(2)
    
    with col_llm_left:
        _render_llm_response_input()
    
    with col_llm_right:
        _render_unmasked_response()


def _render_llm_response_input() -> None:
    """Рендерит область ввода ответа LLM"""
    st.markdown("**Ответ LLM (замаскированный)**")
    
    st.text_area(
        "Вставьте ответ LLM",
        height=TEXTAREA_HEIGHTS["llm_response"],
        placeholder="Вставьте сюда ответ от LLM...",
        key='llm_response',
        label_visibility="collapsed"
    )
    
    col_unmask, col_clear_llm = st.columns([1, 1])
    
    with col_unmask:
        if st.button("🔓 Расшифровать", type="primary", use_container_width=True):
            _handle_unmask()
    
    with col_clear_llm:
        if st.button(
            "🗑️ Очистить",
            key="clear_llm",
            use_container_width=True,
            disabled=not st.session_state.get('llm_response'),
            on_click=lambda: st.session_state.update({
                'llm_response': '',
                'unmasked_response': ''
            })
        ):
            pass


def _render_unmasked_response() -> None:
    """Рендерит расшифрованный ответ"""
    st.markdown("**Расшифрованный ответ**")
    
    if st.session_state.get('unmasked_response'):
        st.text_area(
            "Расшифрованный текст",
            value=st.session_state.unmasked_response,
            height=TEXTAREA_HEIGHTS["llm_response"],
            disabled=True,
            label_visibility="collapsed"
        )
        
        render_button_pair(
            clear_key="clear_unmasked",
            copy_key="copy_unmasked",
            text_to_copy=st.session_state.unmasked_response,
            clear_callback=lambda: st.session_state.update({
                'unmasked_response': ''
            })
        )
    else:
        st.info("👈 Вставьте ответ LLM и нажмите 'Расшифровать'")


def _handle_unmask() -> None:
    """Обработчик расшифровки ответа"""
    logger.info("Начало расшифровки ответа LLM")
    if not st.session_state.get('llm_response'):
        logger.warning("Попытка расшифровки без ответа LLM")
        st.warning(MESSAGES["error_no_llm_response"])
        return
    
    if not st.session_state.get('masking_dictionary'):
        logger.warning("Попытка расшифровки без словаря замен")
        st.warning(MESSAGES["error_no_mapping"])
        return
    
    try:
        masking_service = MaskingService()
        st.session_state.unmasked_response = masking_service.unmask_text(
            st.session_state.llm_response,
            st.session_state.masking_dictionary
        )
        logger.info(f"Ответ успешно расшифрован. Длина: {len(st.session_state.unmasked_response)} символов")
        st.success(MESSAGES["success_unmasked"])
        st.rerun()
    except Exception as e:
        logger.error(f"Ошибка при расшифровке ответа LLM: {str(e)}")
        st.error(f"⛔ Ошибка при расшифровке: {str(e)}")