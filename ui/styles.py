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
    
    /* Уменьшаем отступы между колонками */
    div[data-testid="column"] {
        padding: 0 5px !important;
    }
    
    /* Все кнопки на всю ширину */
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
        transition: all 0.2s ease !important;
        margin: 20px 0 15px 0 !important;
        letter-spacing: 0.3px;
    }
    
    /* ИСПРАВЛЕНО: Более спокойный hover для кнопок этапов */
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #4a6fa0 0%, #5a7fb8 100%) !important;
        box-shadow: 0 4px 14px rgba(90, 127, 184, 0.25) !important;
        transform: translateY(-1px) scale(1.005) !important;
    }
    
    /* === КНОПКИ ДЕЙСТВИЙ (🚀 Сгенерировать, 🔓 Расшифровать) === */
    .stColumn button[kind="primary"],
    .stColumn .stButton button[kind="primary"] {
        background: #35a85b !important;
        margin: 0 !important;
        padding: 0.6rem 1.2rem !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 10px rgba(53, 168, 91, 0.25) !important;
        letter-spacing: 0.2px;
    }
    
    .stColumn button[kind="primary"]:hover {
        background: #298146 !important;
        box-shadow: 0 4px 14px rgba(53, 168, 91, 0.35) !important;
        transform: translateY(-2px) scale(1.02) !important;
    }
    
    /* === ОБЫЧНЫЕ КНОПКИ (Очистить, Копировать и т.д.) === */
    button[kind="secondary"] {
        background: #f8f9fa !important;
        color: #495057 !important;
        border: 1.5px solid #adb5bd !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    
    button[kind="secondary"]:hover {
        background: #e9ecef !important;
        border-color: #868e96 !important;
        box-shadow: 0 2px 8px rgba(73, 80, 87, 0.12) !important;
        transform: translateY(-1px);
    }
    
    /* === ТЕКСТОВЫЕ ОБЛАСТИ === */
    .stTextArea textarea {
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        background: white !important;
        transition: all 0.3s ease !important;
    }
    
    /* ИСПРАВЛЕНО: Убрана красная рамка, оставлена только синяя */
    .stTextArea textarea:focus {
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.1) !important;
        outline: none !important;
    }
    
    /* Убираем любые другие outline при фокусе */
    .stTextArea textarea:focus-visible {
        outline: none !important;
    }
    
    /* === СЕЛЕКТЫ === */
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        background: white !important;
    }
    
    /* НОВОЕ: Стилизация для multiselect (Datasets и Entities) */
    .stMultiSelect > div > div {
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        background: white !important;
        transition: all 0.3s ease !important;
    }
    
    .stMultiSelect > div > div:focus-within {
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.1) !important;
    }
    
    /* Стилизация тегов в multiselect */
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: #5a7fb8 !important;
        color: white !important;
        border-radius: 6px !important;
        padding: 4px 8px !important;
        font-size: 0.9em !important;
    }
    
    /* === ЧЕКБОКСЫ === */
    .stCheckbox {
        background: white;
        padding: 10px 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    
    /* === EXPANDER === */
    .streamlit-expanderHeader {
        background: white !important;
        border-radius: 10px !important;
        border: 1px solid #dee2e6 !important;
        font-weight: 500 !important;
    }
    
    /* === ПРОГРЕСС БАР === */
    .stProgress > div > div {
        background: linear-gradient(90deg, #5a7fb8 0%, #6b9d7d 100%) !important;
        border-radius: 10px !important;
    }
    
    /* === ЗАГОЛОВКИ === */
    h1, h2, h3 {
        color: #343a40 !important;
        font-weight: 700 !important;
    }
    
    /* === МЕТРИКИ В САЙДБАРЕ === */
    [data-testid="stMetricValue"] {
        color: #5a7fb8 !important;
        font-weight: 600 !important;
    }
    
    /* === САЙДБАР === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%) !important;
    }
    
    /* === УБИРАЕМ КРАСНУЮ РАМКУ У ВСЕХ INPUT-элементов === */
    input:focus, 
    textarea:focus, 
    select:focus,
    [contenteditable]:focus {
        outline: none !important;
    }
    
    /* Убираем стандартный outline браузера */
    *:focus {
        outline: none !important;
    }
    
    /* НОВОЕ: Анимация исчезновения для success-сообщений */
    .stSuccess {
        animation: fadeOut 3s ease-in-out forwards;
        animation-delay: 2s;
    }
    
    @keyframes fadeOut {
        0% {
            opacity: 1;
        }
        80% {
            opacity: 1;
        }
        100% {
            opacity: 0;
            display: none;
        }
    }
</style>
""", unsafe_allow_html=True)