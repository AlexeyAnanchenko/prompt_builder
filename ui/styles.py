import streamlit as st
from utils.logger import setup_logger


# Настраиваем логгер для модуля
logger = setup_logger(__name__)


def inject_custom_styles() -> None:
    """Применяет все кастомные CSS стили для приложения"""
    logger.info("Применение кастомных CSS стилей")
    st.markdown("""
<style>
    /* === ОБЩИЙ ФОН И БАЗОВЫЕ НАСТРОЙКИ === */
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    div[data-testid="column"] {
        padding: 0 5px !important;
    }
    
    .stButton button {
        width: 100%;
    }
    
    /* === КНОПКИ ЭТАПОВ (1️⃣, 2️⃣, 3️⃣) === */
    button[kind="primary"] {
        background: linear-gradient(135deg, #5a7fb8 0%, #4a6fa0 100%) !important;
        color: white !important;
        border: none !important;
        padding: 15px 20px !important;
        border-radius: 12px !important;
        font-size: 1.1em !important;
        font-weight: 600 !important;
        box-shadow: 0 3px 12px rgba(90, 127, 184, 0.2) !important;
        margin: 20px 0 15px 0 !important;
    }
    
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #4a6fa0 0%, #5a7fb8 100%) !important;
        transform: translateY(-1px) scale(1.005) !important;
    }
    
    /* === КНОПКИ ДЕЙСТВИЙ (Зеленые) === */
    .stColumn button[kind="primary"],
    .stColumn .stButton button[kind="primary"] {
        background: #35a85b !important;
        margin: 0 !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 10px rgba(53, 168, 91, 0.25) !important;
    }
    
    .stColumn button[kind="primary"]:hover {
        background: #298146 !important;
        transform: translateY(-2px) scale(1.02) !important;
    }
    
    /* === ВТОРИЧНЫЕ КНОПКИ === */
    button[kind="secondary"] {
        background: #f8f9fa !important;
        color: #495057 !important;
        border: 1.5px solid #adb5bd !important;
        border-radius: 8px !important;
    }

    /* ================================================================= */
    /* !!! ВАЖНОЕ ИСПРАВЛЕНИЕ РАМОК (INPUTS & TEXTAREAS) !!!             */
    /* ================================================================= */

    /* 1. Стилизуем САМО ПОЛЕ ВВОДА (где курсор). 
          Убираем прозрачность и ставим жесткий белый фон + цвет текста. */
    .stTextArea textarea, 
    .stTextInput input {
        color: #31333F !important;
        background-color: #ffffff !important;
        border: none !important;
        box-shadow: none !important;
        caret-color: #5a7fb8 !important;
    }
    
    /* Дополнительно: убираем серый фон при автозаполнении браузером (если есть) */
    .stTextArea textarea:-webkit-autofill,
    .stTextInput input:-webkit-autofill {
        -webkit-box-shadow: 0 0 0 30px white inset !important;
    }

    /* 2. Стилизуем КОНТЕЙНЕР (wrapper), который дает рамку. */
    div[data-baseweb="textarea"], 
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        transition: all 0.3s ease !important;
    }

    /* 3. Красим КОНТЕЙНЕР при фокусе (синяя рамка) */
    div[data-baseweb="textarea"]:focus-within, 
    div[data-baseweb="input"]:focus-within {
        border-color: #5a7fb8 !important; 
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.1) !important;
    }

    /* ================================================================= */

    /* === СЕЛЕКТЫ (Dropdowns) === */
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        background: white !important;
    }
    
    /* ================================================================= */
    /* !!! ИСПРАВЛЕНИЕ MULTISELECT (убираем красные и двойные рамки) !!! */
    /* ================================================================= */
    
    /* ВНЕШНИЙ контейнер - убираем его рамку полностью */
    .stMultiSelect > div {
        border: none !important;
        background: transparent !important;
    }
    
    /* ВНУТРЕННИЙ контейнер - здесь рисуем единственную рамку */
    .stMultiSelect > div > div,
    div[data-baseweb="select"] > div {
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        background: white !important;
        transition: all 0.3s ease !important;
    }
    
    /* КРИТИЧНО: Переопределяем все возможные состояния error/invalid */
    .stMultiSelect > div > div[aria-invalid="true"],
    .stMultiSelect > div > div[data-invalid="true"],
    div[data-baseweb="select"][aria-invalid="true"] > div,
    div[data-baseweb="select"][data-invalid="true"] > div {
        border-color: #dee2e6 !important;
        box-shadow: none !important;
    }
    
    /* При фокусе - только синяя рамка */
    .stMultiSelect > div > div:focus-within,
    div[data-baseweb="select"]:focus-within > div {
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.1) !important;
    }
    
    /* Даже если есть invalid + focus - только синий */
    .stMultiSelect > div > div[aria-invalid="true"]:focus-within,
    div[data-baseweb="select"][aria-invalid="true"]:focus-within > div {
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.1) !important;
    }

    /* Теги внутри мультиселекта */
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: #5a7fb8 !important;
        color: white !important;
    }
    
    /* Убираем border у внутренних элементов */
    .stMultiSelect [role="button"],
    .stMultiSelect [role="combobox"] {
        border: none !important;
        outline: none !important;
    }
    
    /* Убираем все дополнительные рамки у вложенных div */
    .stMultiSelect > div > div > div {
        border: none !important;
    }
    
    /* ================================================================= */
    
    /* === ЧЕКБОКСЫ === */
    .stCheckbox {
        background: white;
        padding: 10px 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    
    /* === МЕТРИКИ И ТЕКСТ === */
    [data-testid="stMetricValue"] {
        color: #5a7fb8 !important;
    }
    
    /* Глобально убираем outline (синюю обводку браузера) */
    *:focus-visible {
        outline: none !important;
    }
    
    /* Анимация успеха */
    .stSuccess {
        animation: fadeOut 3s ease-in-out forwards;
        animation-delay: 2s;
    }
    
    @keyframes fadeOut {
        to { opacity: 0; display: none; }
    }
</style>
""", unsafe_allow_html=True)