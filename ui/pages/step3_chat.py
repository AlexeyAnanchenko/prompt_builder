import streamlit as st
from ui.components import render_step_toggle_button, render_button_pair
from utils.logger import setup_logger

logger = setup_logger(__name__)

def render_step3() -> None:
    """Рендерит шаг 3: Диалог с LLM"""
    logger.info("Рендер шага 3: Диалог с LLM")
    
    render_step_toggle_button(
        step_number=3,
        title="Диалог с LLM",
        state_key='show_step3'
    )
    
    if not st.session_state.get('show_step3', True):
        return

    # Проверка наличия маскера
    masker = st.session_state.get("masker")
    if not masker or not masker.map_forward:
        st.warning("⚠️ Словарь замен пуст. Сначала выполните генерацию на Шаге 2.")
        return

    # === ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ ===
    # Хранилище данных (не зависит от виджетов)
    if "chat_data_human" not in st.session_state:
        st.session_state.chat_data_human = ""
    if "chat_data_llm" not in st.session_state:
        st.session_state.chat_data_llm = ""
        
    # Настройки UI
    if "chat_view_mode" not in st.session_state:
        st.session_state.chat_view_mode = "edit"
    if "chat_textarea_height" not in st.session_state:
        st.session_state.chat_textarea_height = 600
    if "show_visual_settings" not in st.session_state:
        st.session_state.show_visual_settings = False
    if "chat_column_ratio" not in st.session_state:
        st.session_state.chat_column_ratio = 50

    # Ключи для виджетов
    KEY_WIDGET_HUMAN = "widget_chat_human"
    KEY_WIDGET_LLM = "widget_chat_llm"

    # === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

    def sync_state():
        """
        Синхронизация: Виджет -> Переменная.
        Вызывается при любом вводе текста пользователем.
        """
        if KEY_WIDGET_HUMAN in st.session_state:
            st.session_state.chat_data_human = st.session_state[KEY_WIDGET_HUMAN]
        
        if KEY_WIDGET_LLM in st.session_state:
            st.session_state.chat_data_llm = st.session_state[KEY_WIDGET_LLM]

    def update_widget_state(key: str, value: str):
        """
        Принудительное обновление: Переменная -> Виджет.
        Используется кнопками для изменения текста в полях.
        """
        st.session_state[key] = value

    # === ОБРАБОТЧИКИ КНОПОК (CALLBACKS) ===

    def on_encrypt_click():
        """Шифруем: Human -> LLM"""
        # 1. Берем актуальный текст из Human (даже если только что ввели)
        text = st.session_state.get(KEY_WIDGET_HUMAN, st.session_state.chat_data_human)
        
        if text and masker:
            masked = masker.mask_text(text)
            # 2. Обновляем хранилище LLM
            st.session_state.chat_data_llm = masked
            # 3. Принудительно обновляем виджет LLM
            update_widget_state(KEY_WIDGET_LLM, masked)
            logger.info(f"Зашифровано {len(text)} символов")
        else:
            st.toast("Нечего шифровать (поле пустое)", icon="⚠️")

    def on_decrypt_click():
        """Расшифровываем: LLM -> Human"""
        # 1. Берем актуальный текст из LLM
        text = st.session_state.get(KEY_WIDGET_LLM, st.session_state.chat_data_llm)
        
        if text and masker:
            unmasked = masker.unmask_text(text)
            # 2. Обновляем хранилище Human
            st.session_state.chat_data_human = unmasked
            # 3. Принудительно обновляем виджет Human
            update_widget_state(KEY_WIDGET_HUMAN, unmasked)
            logger.info(f"Расшифровано {len(text)} символов")
        else:
            st.toast("Нечего расшифровывать (поле пустое)", icon="⚠️")

    def on_clear_human():
        st.session_state.chat_data_human = ""
        update_widget_state(KEY_WIDGET_HUMAN, "")

    def on_clear_llm():
        st.session_state.chat_data_llm = ""
        update_widget_state(KEY_WIDGET_LLM, "")

    def on_clear_both():
        on_clear_human()
        on_clear_llm()

    def toggle_view_mode():
        # Перед переключением сохраняем текущее состояние виджетов
        sync_state()
        st.session_state.chat_view_mode = "preview" if st.session_state.chat_view_mode == "edit" else "edit"

    # === ОТРИСОВКА ИНТЕРФЕЙСА ===

    # 1. Визуальные настройки
    with st.expander("⚙️ Визуальные настройки (Размер и Пропорции)", expanded=st.session_state.show_visual_settings):
        col_set_1, col_set_2 = st.columns([1, 1])
        with col_set_1:
            new_height = st.slider(
                "Высота окон (px)", 300, 1200, 
                st.session_state.chat_textarea_height, 50
            )
            if new_height != st.session_state.chat_textarea_height:
                st.session_state.chat_textarea_height = new_height
                
        with col_set_2:
            new_ratio = st.slider(
                "Баланс колонок (Лево % / Право %)", 20, 80, 
                st.session_state.chat_column_ratio, 5
            )
            if new_ratio != st.session_state.chat_column_ratio:
                st.session_state.chat_column_ratio = new_ratio
                st.rerun()

    # 2. Верхняя панель управления
    col_mode, col_clear = st.columns([1, 1])
    with col_mode:
        view_icon = "📝" if st.session_state.chat_view_mode == "preview" else "📖"
        view_label = "Редактировать" if st.session_state.chat_view_mode == "preview" else "Просмотр (Markdown)"
        if st.button(f"{view_icon} {view_label}", key="toggle_view_mode", use_container_width=True):
            toggle_view_mode()
            st.rerun()
    
    with col_clear:
        if st.button("🗑️ Очистить всё", key="clear_both_btn", use_container_width=True):
            on_clear_both()
            st.rerun() # Важно сделать реран для визуального обновления

    st.markdown("---")

    # 3. Расчет ширины колонок
    # Используем относительные веса. Центральная колонка узкая (фиксированный вес 1).
    # Остальное распределяем по ratio.
    ratio = st.session_state.chat_column_ratio / 100.0
    total_flex = 20 # Условная общая ширина
    center_flex = 1.5
    
    left_flex = (total_flex - center_flex) * ratio
    right_flex = (total_flex - center_flex) * (1 - ratio)
    
    col_human, col_actions, col_llm = st.columns([left_flex, center_flex, right_flex])

    is_preview = st.session_state.chat_view_mode == "preview"
    height = st.session_state.chat_textarea_height

    # === ЛЕВАЯ КОЛОНКА (HUMAN) ===
    with col_human:
        st.subheader("👨‍💻 Реальные данные")
        
        if not is_preview:
            # Важно: value берем из session_state, если ключа виджета еще нет
            # Если ключ есть, Streamlit сам управляет value, но мы обновляем его через update_widget_state
            if KEY_WIDGET_HUMAN not in st.session_state:
                st.session_state[KEY_WIDGET_HUMAN] = st.session_state.chat_data_human
                
            st.text_area(
                "Human Input",
                key=KEY_WIDGET_HUMAN,
                height=height,
                on_change=sync_state, # Сохраняем при вводе
                label_visibility="collapsed",
                placeholder="Введите текст с реальными данными..."
            )
            
            render_button_pair(
                clear_key="clr_h", copy_key="cpy_h",
                text_to_copy=st.session_state.chat_data_human,
                clear_callback=on_clear_human
            )
        else:
            # Preview Mode
            with st.container(height=height, border=True):
                if st.session_state.chat_data_human:
                    st.markdown(st.session_state.chat_data_human)
                else:
                    st.caption("Пусто")

    # === ЦЕНТРАЛЬНАЯ КОЛОНКА (КНОПКИ) ===
    with col_actions:
        if not is_preview:
            # Центрирование по вертикали
            st.markdown(f"<div style='height: {height // 2 - 40}px;'></div>", unsafe_allow_html=True)
            
            st.button("➡️", key="btn_enc", use_container_width=True, help="Зашифровать", on_click=on_encrypt_click)
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            st.button("⬅️", key="btn_dec", use_container_width=True, help="Расшифровать", on_click=on_decrypt_click)

    # === ПРАВАЯ КОЛОНКА (LLM) ===
    with col_llm:
        st.subheader("🎭 Замаскированный текст (Для LLM)")
        
        if not is_preview:
            if KEY_WIDGET_LLM not in st.session_state:
                st.session_state[KEY_WIDGET_LLM] = st.session_state.chat_data_llm

            st.text_area(
                "LLM Input",
                key=KEY_WIDGET_LLM,
                height=height,
                on_change=sync_state,
                label_visibility="collapsed",
                placeholder="Здесь появится зашифрованный текст..."
            )
            
            render_button_pair(
                clear_key="clr_l", copy_key="cpy_l",
                text_to_copy=st.session_state.chat_data_llm,
                clear_callback=on_clear_llm
            )
        else:
            # Preview Mode
            with st.container(height=height, border=True):
                if st.session_state.chat_data_llm:
                    st.markdown(st.session_state.chat_data_llm)
                else:
                    st.caption("Пусто")