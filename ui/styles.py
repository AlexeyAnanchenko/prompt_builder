import streamlit as st
from utils.logger import setup_logger

# Настраиваем логгер для модуля стилей
logger = setup_logger(__name__)

def inject_custom_styles() -> None:
    """
    Применяет все кастомные CSS стили для приложения.
    Использует st.markdown c unsafe_allow_html=True для инъекции стилей в <head>.
    
    Содержит настройки:
    - Фона приложения
    - Кнопок (обычных, primary и внутри колонок)
    - Полей ввода (Input, Textarea)
    - Мультиселектов (исправление рамок)
    - Экспандеров и блоков кода
    """
    logger.info("Применение кастомных CSS стилей")
    
    st.markdown("""
<style>
    /* ================================================================= */
    /* 1. ГЛОБАЛЬНЫЕ НАСТРОЙКИ (ФОН, ОТСТУПЫ)                            */
    /* ================================================================= */
    
    /* Градиентный фон всего приложения */
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    
    /* Уменьшение отступов в колонках для компактности */
    div[data-testid="column"] {
        padding: 0 5px !important;
    }
    
    /* Растягивание кнопок на всю ширину контейнера */
    .stButton button {
        width: 100%;
    }
    
    /* ================================================================= */
    /* 2. АНИМАЦИИ И НАВЕДЕНИЕ (ВСЕ КНОПКИ)                              */
    /* ================================================================= */
    
    /* Базовая анимация переходов для всех типов кнопок */
    button[kind="primary"],
    button[kind="secondary"],
    .stButton button,
    button[data-testid*="stBaseButton"] {
        transition: all 0.3s ease !important;
    }
    
    /* Эффект наведения: синяя рамка и легкое свечение */
    button[kind="primary"]:hover:not(:disabled),
    button[kind="secondary"]:hover:not(:disabled),
    .stButton button:hover:not(:disabled),
    button[data-testid*="stBaseButton"]:hover:not(:disabled) {
        border: 2px solid #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.15) !important;
    }
    
    /* ================================================================= */
    /* 3. СТИЛИ КНОПОК ПО ТИПАМ                                          */
    /* ================================================================= */
    
    /* PRIMARY (Основные синие кнопки этапов 1, 2, 3) */
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
        transition: all 0.3s ease !important;
    }
    
    button[kind="primary"]:hover:not(:disabled) {
        background: linear-gradient(135deg, #4a6fa0 0%, #5a7fb8 100%) !important;
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.15) !important;
        transform: translateY(-1px) !important;
    }
    
    /* ACTION BUTTONS (Зеленые кнопки действий внутри колонок) */
    .stColumn button[kind="primary"],
    .stColumn .stButton button[kind="primary"] {
        background: #35a85b !important;
        margin: 0 !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 10px rgba(53, 168, 91, 0.25) !important;
        border: 2px solid transparent !important;
        transition: all 0.3s ease !important;
    }
    
    .stColumn button[kind="primary"]:hover:not(:disabled) {
        background: #298146 !important;
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.15) !important;
    }
    
    /* SECONDARY (Второстепенные светлые кнопки) */
    button[kind="secondary"] {
        background: #f8f9fa !important;
        color: #495057 !important;
        border: 2px solid #dee2e6 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    button[kind="secondary"]:hover:not(:disabled) {
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.15) !important;
    }

    /* ================================================================= */
    /* 4. ПОЛЯ ВВОДА (INPUTS & TEXTAREAS)                                */
    /* ================================================================= */

    /* Само поле ввода (текст, фон, каретка) */
    .stTextArea textarea, 
    .stTextInput input {
        color: #31333F !important;
        background-color: #ffffff !important;
        border: none !important;
        box-shadow: none !important;
        caret-color: #5a7fb8 !important;
    }
    
    /* Убираем серый фон автозаполнения браузера */
    .stTextArea textarea:-webkit-autofill,
    .stTextInput input:-webkit-autofill {
        -webkit-box-shadow: 0 0 0 30px white inset !important;
    }

    /* Контейнер поля (рисует рамку) */
    div[data-baseweb="textarea"], 
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        transition: all 0.3s ease !important;
    }

    /* Состояние фокуса (синяя рамка) */
    div[data-baseweb="textarea"]:focus-within, 
    div[data-baseweb="input"]:focus-within {
        border-color: #5a7fb8 !important; 
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.1) !important;
    }

    /* ================================================================= */
    /* 5. ВЫПАДАЮЩИЕ СПИСКИ (SELECTBOX)                                  */
    /* ================================================================= */
    
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        background: white !important;
    }
    
    /* ================================================================= */
    /* 6. МУЛЬТИСЕЛЕКТЫ (MULTISELECT) - FIX                              */
    /* ================================================================= */
    
    /* Убираем внешнюю рамку контейнера (fix двойных границ) */
    .stMultiSelect > div {
        border: none !important;
        background: transparent !important;
    }
    
    /* Стилизуем внутренний контейнер */
    .stMultiSelect > div > div,
    div[data-baseweb="select"] > div {
        border-radius: 10px !important;
        border: 2px solid #dee2e6 !important;
        background: white !important;
        transition: all 0.3s ease !important;
    }
    
    /* Исправление отображения состояний ошибки/валидации */
    .stMultiSelect > div > div[aria-invalid="true"],
    .stMultiSelect > div > div[data-invalid="true"],
    div[data-baseweb="select"][aria-invalid="true"] > div,
    div[data-baseweb="select"][data-invalid="true"] > div {
        border-color: #dee2e6 !important;
        box-shadow: none !important;
    }
    
    /* Фокус на мультиселекте */
    .stMultiSelect > div > div:focus-within,
    div[data-baseweb="select"]:focus-within > div {
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.1) !important;
    }
    
    /* Фокус даже при состоянии invalid */
    .stMultiSelect > div > div[aria-invalid="true"]:focus-within,
    div[data-baseweb="select"][aria-invalid="true"]:focus-within > div {
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 3px rgba(90, 127, 184, 0.1) !important;
    }

    /* Теги выбранных элементов (синий фон) */
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: #5a7fb8 !important;
        color: white !important;
    }
    
    /* Уборка лишних границ внутри */
    .stMultiSelect [role="button"],
    .stMultiSelect [role="combobox"] {
        border: none !important;
        outline: none !important;
    }
    
    .stMultiSelect > div > div > div {
        border: none !important;
    }
    
    /* ================================================================= */
    /* 7. ЧЕКБОКСЫ И ПРОЧЕЕ                                              */
    /* ================================================================= */
    
    .stCheckbox {
        background: white;
        padding: 10px 15px;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    
    /* ================================================================= */
    /* 8. EXPANDER (РАСКРЫВАЮЩИЕСЯ БЛОКИ)                                */
    /* ================================================================= */
    
    /* Контейнер */
    div[data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        margin: 5px 0 !important;
        transition: all 0.2s ease !important;
    }
    
    div[data-testid="stExpander"]:hover {
        border-color: #5a7fb8 !important;
        box-shadow: 0 0 0 2px rgba(90, 127, 184, 0.1) !important;
    }
    
    /* Заголовок (Summary) */
    div[data-testid="stExpander"] details summary {
        background: #f8f9fa !important;
        border-radius: 6px !important;
        padding: 8px 12px !important;
        font-weight: 500 !important;
        color: #495057 !important;
        cursor: pointer !important;
        font-size: 0.9em !important;
    }
    
    div[data-testid="stExpander"] details summary:hover {
        background: #e9ecef !important;
    }
    
    /* Открытое состояние */
    div[data-testid="stExpander"] details[open] {
        background: #ffffff !important;
    }
    
    /* Стрелка иконки */
    div[data-testid="stExpander"] details summary svg {
        stroke: #5a7fb8 !important;
        stroke-width: 1.8 !important;
    }
    
    /* ================================================================= */
    /* 9. УТИЛИТЫ И АНИМАЦИИ                                             */
    /* ================================================================= */
    
    /* Цвет цифр в метриках */
    [data-testid="stMetricValue"] {
        color: #5a7fb8 !important;
    }
    
    /* Убираем синюю обводку браузера при фокусе (outline) */
    *:focus-visible {
        outline: none !important;
    }
    
    /* Анимация исчезновения сообщения об успехе (Toast/Success) */
    .stSuccess {
        animation: fadeOut 3s ease-in-out forwards;
        animation-delay: 2s;
    }
    
    @keyframes fadeOut {
        to { opacity: 0; display: none; }
    }
    
    /* ================================================================= */
    /* 10. БЛОКИ КОДА (ШРИФТЫ)                                           */
    /* ================================================================= */
    
    /* Принудительное уменьшение шрифта для компактности промптов */
    [class*="st-emotion-cache"] pre,
    [class*="st-emotion-cache"] code {
        font-size: 12px !important;
        line-height: 1.5 !important;
    }
    
    div[class*="st-emotion-cache"] code[class*="language-"] {
        font-size: 12px !important;
    }
    
    pre[class*="st-emotion-cache"] {
        font-size: 12px !important;
    }
    
    .stCodeBlock pre code,
    .stCodeBlock pre,
    div[data-testid="stCodeBlock"] pre,
    div[data-testid="stCodeBlock"] code {
        font-size: 15px !important;
        line-height: 1.5 !important;
    }
</style>
""", unsafe_allow_html=True)