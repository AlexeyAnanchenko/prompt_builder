import json
import streamlit as st
import streamlit.components.v1 as components
from typing import Optional
from utils.logger import setup_logger

# Настраиваем логгер для модуля
logger = setup_logger(__name__)

def count_tokens(text: str) -> int:
    """
    Подсчёт токенов в тексте (упрощённая версия)
    """
    from config.settings import TOKEN_MULTIPLIER
    token_count = int(len(text.split()) * TOKEN_MULTIPLIER)
    return token_count

def copy_to_clipboard(text: str, button_key: str) -> None:
    """
    Копирует текст в буфер обмена.
    
    ВАЖНО: Компонент вставляется в st.sidebar, чтобы избежать 
    сдвига верстки (появления отступов) в основной части экрана.
    """
    logger.info(f"Копирование текста (ключ: {button_key})")
    
    safe_text = json.dumps(text)
    
    # Современный и надежный способ копирования через Clipboard API
    # с фоллбэком для старых браузеров
    js_code = f"""
    <script>
        function copyText() {{
            const text = {safe_text};
            
            // 1. Попытка через современный API (работает в HTTPS)
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(text).then(() => {{
                    console.log('Copied via Clipboard API');
                }}).catch(err => {{
                    console.error('Clipboard API failed', err);
                    fallbackCopy(text);
                }});
            }} else {{
                // 2. Фоллбэк через textarea
                fallbackCopy(text);
            }}
        }}
        
        function fallbackCopy(text) {{
            const parentDoc = window.parent.document;
            const textArea = parentDoc.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed";
            textArea.style.left = "-9999px";
            parentDoc.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {{
                parentDoc.execCommand('copy');
            }} catch (err) {{
                console.error('Fallback copy failed', err);
            }}
            parentDoc.body.removeChild(textArea);
        }}
        
        // Запуск
        copyText();
    </script>
    """
    
    # === МАГИЯ ЗДЕСЬ ===
    # Мы рендерим компонент внутри sidebar. 
    # Это убирает визуальный "скачок" в основной колонке.
    with st.sidebar:
        components.html(js_code, height=0, width=0)
        
    logger.info("JS отправлен в сайдбар")


def safe_strip(value: Optional[str]) -> str:
    """Безопасная обрезка строки"""
    result = (value or "").strip()
    return result