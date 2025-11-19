from typing import Optional
import streamlit.components.v1 as components


def count_tokens(text: str) -> int:
    """
    Подсчёт токенов в тексте (упрощённая версия)
    
    Args:
        text: Текст для подсчёта
        
    Returns:
        Примерное количество токенов
    """
    from config.settings import TOKEN_MULTIPLIER
    return int(len(text.split()) * TOKEN_MULTIPLIER)


def copy_to_clipboard(text: str, button_key: str) -> None:
    """
    Универсальная функция для копирования текста в буфер обмена
    
    Args:
        text: Текст для копирования
        button_key: Уникальный ключ для элемента
    """
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


def safe_strip(value: Optional[str]) -> str:
    """
    Безопасная обрезка строки с обработкой None
    
    Args:
        value: Строка или None
        
    Returns:
        Обрезанная строка или пустая строка
    """
    return (value or "").strip()