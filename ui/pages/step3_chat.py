import streamlit as st
from ui.components import render_step_toggle_button, render_button_pair
from config.settings import TEXTAREA_HEIGHTS
from utils.logger import setup_logger

logger = setup_logger(__name__)

def render_step3() -> None:
    """Рендерит шаг 3: Чат-транслятор"""
    logger.info("Рендер шага 3: Чат-транслятор")
    
    render_step_toggle_button(
        step_number=3,
        title="Диалог с LLM (Чат-транслятор)",
        state_key='show_step3'
    )
    
    if not st.session_state.get('show_step3', True):
        return

    # Проверка наличия маскера
    masker = st.session_state.get("masker")
    if not masker or not masker.map_forward:
        st.warning("⚠️ Словарь замен пуст. Сначала выполните генерацию на Шаге 2.")
        return

    # Инициализация ключей
    if "chat_human" not in st.session_state:
        st.session_state.chat_human = ""
    if "chat_llm" not in st.session_state:
        st.session_state.chat_llm = ""

    # ==========================================
    # CALLBACKS (Функции обратного вызова)
    # ==========================================
    
    def on_encrypt_click():
        """Callback: Шифрует Human -> LLM"""
        text = st.session_state.chat_human
        if text and masker:
            masked = masker.mask_text(text)
            st.session_state.chat_llm = masked
            logger.info(f"Зашифровано {len(text)} символов")

    def on_decrypt_click():
        """Callback: Расшифровывает LLM -> Human"""
        text = st.session_state.chat_llm
        if text and masker:
            unmasked = masker.unmask_text(text)
            st.session_state.chat_human = unmasked
            logger.info(f"Расшифровано {len(text)} символов")

    def on_clear_human():
        st.session_state.chat_human = ""

    def on_clear_llm():
        st.session_state.chat_llm = ""

    # ==========================================
    # UI LAYOUT
    # ==========================================

    st.caption("Пишите слева — шифруйте направо. Вставляйте ответ LLM справа — расшифровывайте налево.")

    col_human, col_actions, col_llm = st.columns([10, 2, 10])

    # --- ЛЕВАЯ КОЛОНКА (HUMAN) ---
    with col_human:
        st.subheader("👨‍💻 Реальные данные")
        
        st.text_area(
            "Ваш вопрос / Расшифрованный ответ",
            height=400,
            key="chat_human", 
            placeholder="Пишите здесь ваш вопрос с реальными названиями..."
        )
        
        render_button_pair(
            clear_key="clear_human_btn",
            copy_key="copy_human_btn",
            text_to_copy=st.session_state.chat_human,
            clear_callback=on_clear_human
        )

    # --- ЦЕНТРАЛЬНАЯ КОЛОНКА (КНОПКИ) ---
    with col_actions:
        st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)
        
        st.button(
            "➡️\nEncrypt", 
            key="btn_encrypt", 
            use_container_width=True, 
            help="Зашифровать текст слева",
            on_click=on_encrypt_click
        )
            
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        st.button(
            "⬅️\nDecrypt", 
            key="btn_decrypt", 
            use_container_width=True, 
            help="Расшифровать текст справа",
            on_click=on_decrypt_click
        )

    # --- ПРАВАЯ КОЛОНКА (LLM) ---
    with col_llm:
        st.subheader("🤖 Маски (Для LLM)")
        
        st.text_area(
            "Текст для LLM / Ответ от LLM",
            height=400,
            key="chat_llm",
            placeholder="Здесь появится зашифрованный текст..."
        )
        
        render_button_pair(
            clear_key="clear_llm_btn",
            copy_key="copy_llm_btn",
            text_to_copy=st.session_state.chat_llm,
            clear_callback=on_clear_llm
        )