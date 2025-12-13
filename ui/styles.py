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
    
    /* ================================================================= */
    /* === УНИВЕРСАЛЬНАЯ СТИЛИЗАЦИЯ ВСЕХ КНОПОК ПРИ НАВЕДЕНИИ ===        */
    /* ================================================================= */
    
    /* Базовая стилизация для всех кнопок */
    button[kind="primary"],
    button[kind="secondary"],
    .stButton button,
    button[data-testid*="stBaseButton"] {
        transition: all 0.3s ease !important;  /* ← ИЗМЕНЕНО с 0.2s на 0.3s */
    }
    
    /* ГЛАВНОЕ ПРАВИЛО: Синяя рамка при наведении на ВСЕ кнопки */
    button[kind="primary"]:hover:not(:disabled),
    button[kind="secondary"]:hover:not(:disabled),
    .stButton button:hover:not(:disabled),
    button[data-testid*="stBaseButton"]:hover:not(:disabled) {
        border: 2px solid #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.15) !important;
    }
    
    /* ================================================================= */
    
    /* === КНОПКИ ЭТАПОВ (1️⃣, 2️⃣, 3️⃣) === */
    button[kind="primary"] {
        background: linear-gradient(135deg, #5a7fb8 0%, #4a6fa0 100%) !important;
        color: white !important;
        border: 2px solid transparent !important;
        padding: 15px 20px !important;
        border-radius: 12px !important;
        font-size: 1.1em !important;
        font-weight: 600 !important;
        box-shadow: 0 3px 12px rgba(90, 127, 184, 0.2) !important;
        margin: 20px 0 15px 0 !important;
        transition: all 0.3s ease !important;  /* ← Явно указываем для уверенности */
    }
    
    button[kind="primary"]:hover:not(:disabled) {
        background: linear-gradient(135deg, #4a6fa0 0%, #5a7fb8 100%) !important;
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.15) !important;
        transform: translateY(-1px) !important;
    }
    
    /* === КНОПКИ ДЕЙСТВИЙ (Зеленые) === */
    .stColumn button[kind="primary"],
    .stColumn .stButton button[kind="primary"] {
        background: #35a85b !important;
        margin: 0 !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 10px rgba(53, 168, 91, 0.25) !important;
        border: 2px solid transparent !important;  /* ← ДОБАВЛЕНО */
        transition: all 0.3s ease !important;  /* ← ДОБАВЛЕНО */
    }
    
    .stColumn button[kind="primary"]:hover:not(:disabled) {
        background: #298146 !important;
        border-color: #5a7fb8 !important;  /* ← ДОБАВЛЕНО явно */
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.15) !important;  /* ← ДОБАВЛЕНО явно */
    }
    
    /* === ВТОРИЧНЫЕ КНОПКИ === */
    button[kind="secondary"] {
        background: #f8f9fa !important;
        color: #495057 !important;
        border: 2px solid #dee2e6 !important;  /* ← Светлая рамка как у других элементов */
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    button[kind="secondary"]:hover:not(:disabled) {
        border-color: #5a7fb8 !important;  /* ← ДОБАВЛЕНО явно */
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.15) !important;  /* ← ДОБАВЛЕНО явно */
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
    
    /* ================================================================= */
    /* === СТИЛИЗАЦИЯ EXPANDER-ОВ === */
    /* ================================================================= */
    
    /* Основной контейнер expander-а */
    div[data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        margin: 5px 0 !important;
        transition: all 0.2s ease !important;
    }
    
    /* При наведении на весь expander */
    div[data-testid="stExpander"]:hover {
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 2px rgba(90, 127, 184, 0.1) !important;
    }
    
    /* Заголовок expander-а */
    div[data-testid="stExpander"] details summary {
        background: #f8f9fa !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        font-weight: 500 !important;
        color: #495057 !important;
        cursor: pointer !important;
        font-size: 0.9em !important;
    }
    
    /* При наведении на заголовок */
    div[data-testid="stExpander"] details summary:hover {
        background: #e9ecef !important;
    }
    
    /* Содержимое expander-а */
    div[data-testid="stExpander"] details[open] {
        background: #ffffff !important;
    }
    
    /* Стрелка раскрытия */
    div[data-testid="stExpander"] details summary svg {
        stroke: #5a7fb8 !important;
        stroke-width: 1.8 !important;
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
    
    /* ================================================================= */
    /* === УМЕНЬШЕНИЕ ШРИФТА В БЛОКАХ КОДА (ПРОМПТЫ) === */
    /* ================================================================= */
    
    /* Перебиваем emotion-классы Streamlit */
    [class*="st-emotion-cache"] pre,
    [class*="st-emotion-cache"] code {
        font-size: 12px !important;
        line-height: 1.5 !important;
    }
    
    /* Более специфичный селектор для кода */
    div[class*="st-emotion-cache"] code[class*="language-"] {
        font-size: 12px !important;
    }
    
    /* Контейнер pre с кодом */
    pre[class*="st-emotion-cache"] {
        font-size: 12px !important;
    }
    
    /* Дополнительно: для всех блоков кода */
    .stCodeBlock pre code,
    .stCodeBlock pre,
    div[data-testid="stCodeBlock"] pre,
    div[data-testid="stCodeBlock"] code {
        font-size: 15px !important;
        line-height: 1.5 !important;
    }
</style>
""", unsafe_allow_html=True)