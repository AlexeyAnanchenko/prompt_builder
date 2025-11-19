from typing import Optional
import streamlit.components.v1 as components
from utils.logger import setup_logger


# Настраиваем логгер для модуля
logger = setup_logger(__name__)


def count_tokens(text: str) -> int:
    """
    Подсчёт токенов в тексте (упрощённая версия)
    
    Args:
        text: Текст для подсчёта
        
    Returns:
        Примерное количество токенов
    """
    from config.settings import TOKEN_MULTIPLIER
    token_count = int(len(text.split()) * TOKEN_MULTIPLIER)
    logger.debug(f"Подсчёт токенов: {len(text.split())} слов → {token_count} токенов")
    return token_count


def copy_to_clipboard(text: str, button_key: str) -> None:
    """
    Универсальная функция для копирования текста в буфер обмена
    
    Args:
        text: Текст для копирования
        button_key: Уникальный ключ для элемента
    """
    logger.info(f"Копирование текста длиной {len(text)} символов в буфер обмена (ключ: {button_key})")
    import streamlit as st
    
    st.write(
        f'<textarea id="{button_key}" style="position: absolute; left: -9999px;">{text}</textarea>',
        unsafe_allow_html=True
    )
    components.html(f"""
        <script>
            var copyText = window.parent.document.getElementById("{button_key}");
            if (copyText) {{
                copyText.select();
                window.parent.document.execCommand("copy");
            }}
        </script>
    """, height=0)
    logger.info("Текст успешно скопирован в буфер обмена")


def safe_strip(value: Optional[str]) -> str:
    """
    Безопасная обрезка строки с обработкой None
    
    Args:
        value: Строка или None
        
    Returns:
        Обрезанная строка или пустая строка
    """
    result = (value or "").strip()
    logger.debug(f"Безопасная обрезка: '{value}' → '{result}'")
    return result