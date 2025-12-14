import json
import streamlit as st
import streamlit.components.v1 as components
from typing import Optional
from utils.logger import setup_logger

# Инициализируем логгер для этого модуля
logger = setup_logger(__name__)

def count_tokens(text: str) -> int:
    """
    Выполняет приблизительный подсчет токенов ("грязный" метод).
    Используется как запасной вариант (fallback), если Rust-токенизатор не загрузился.
    
    Алгоритм: Разбиваем текст на слова (по пробелам) и умножаем на коэффициент.
    Для русского языка и кода 1 слово ≈ 1.3 токена.
    
    Args:
        text (str): Входной текст.
        
    Returns:
        int: Оценочное количество токенов.
    """
    from config.settings import TOKEN_MULTIPLIER
    if not text:
        return 0
    # split() разбивает строку по пробелам на список слов
    token_count = int(len(text.split()) * TOKEN_MULTIPLIER)
    return token_count

def copy_to_clipboard(text: str, button_key: str) -> None:
    """
    Копирует текст в буфер обмена пользователя.
    Использует JavaScript хак, так как Streamlit (backend) не имеет доступа к буферу (frontend).
    
    Args:
        text (str): Текст для копирования.
        button_key (str): ID кнопки, вызвавшей действие (для логов).
    """
    # ℹ️ ЛОГИРОВАНИЕ: Фиксируем действие пользователя
    logger.info(f"Запущено копирование в буфер (кнопка: {button_key})")
    
    if not text:
        logger.warning(f"Попытка скопировать пустой текст (кнопка: {button_key})")
        return

    # Сериализуем текст в JSON, чтобы экранировать спецсимволы (кавычки, переносы строк)
    safe_text = json.dumps(text)
    
    # JS-скрипт, который будет исполнен в браузере.
    # 1. Проверяем наличие Clipboard API (navigator.clipboard).
    # 2. Если недоступно (нет HTTPS), создаем невидимый <textarea>, выделяем текст и жмем 'copy'.
    js_code = f"""
    <script>
        function copyText() {{
            const text = {safe_text};
            
            // Метод 1: Modern API (требует HTTPS или localhost)
            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(text).then(() => {{
                    console.log('Copied via Clipboard API');
                }}).catch(err => {{
                    console.error('Clipboard API failed', err);
                    fallbackCopy(text); // Если ошибка, идем к методу 2
                }});
            }} else {{
                // Метод 2: Fallback (старый способ)
                fallbackCopy(text);
            }}
        }}
        
        function fallbackCopy(text) {{
            const parentDoc = window.parent.document;
            const textArea = parentDoc.createElement("textarea");
            textArea.value = text;
            
            // Делаем элемент невидимым
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
        
        // Запуск функции сразу при рендере
        copyText();
    </script>
    """
    
    # Вставляем JS в сайдбар, чтобы не ломать верстку основной страницы (избежать пустых отступов)
    with st.sidebar:
        components.html(js_code, height=0, width=0)
        
    logger.info("JS-код копирования отправлен в браузер")


def safe_strip(value: Optional[str]) -> str:
    """
    Безопасная очистка строки от пробелов.
    Защищает от ошибки "AttributeError: 'NoneType' object has no attribute 'strip'".
    
    Args:
        value: Строка или None.
        
    Returns:
        str: Очищенная строка или пустая строка "".
    """
    # (value or "") -> если value None, вернет "", иначе value. Потом вызываем strip().
    result = (value or "").strip()
    return result