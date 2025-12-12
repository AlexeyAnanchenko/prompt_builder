import json
from typing import Optional
import streamlit.components.v1 as components
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
    Копирует текст и СКРЫВАЕТ контейнер скрипта, чтобы не было отступов.
    """
    logger.info(f"Копирование текста (ключ: {button_key})")
    
    safe_text = json.dumps(text)
    
    js_code = f"""
    <script>
        // 1. Функция копирования
        function copyToClipboard() {{
            try {{
                const parentDoc = window.parent.document;
                const textArea = parentDoc.createElement("textarea");
                textArea.value = {safe_text};
                textArea.style.position = "fixed";
                textArea.style.left = "-9999px";
                textArea.style.top = "0";
                parentDoc.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                parentDoc.execCommand('copy');
                parentDoc.body.removeChild(textArea);
            }} catch (err) {{
                console.error('Copy failed', err);
            }}
        }}

        // 2. Функция "Самоуничтожения" контейнера (убирает отступы)
        function hideMyContainer() {{
            try {{
                // Получаем iframe, в котором выполняется этот скрипт
                const iframe = window.frameElement;
                if (!iframe) return;

                // Ищем родительский контейнер Streamlit (обычно имеет класс element-container)
                // Поднимаемся на несколько уровней вверх, чтобы найти блок, занимающий место
                let el = iframe;
                while (el) {{
                    // Проверяем классы контейнеров Streamlit
                    if (el.classList && (el.classList.contains('element-container') || el.classList.contains('stElementContainer'))) {{
                        el.style.display = 'none'; // Полностью убираем из верстки
                        break;
                    }}
                    // Ограничитель, чтобы не скрыть всё приложение
                    if (el.tagName === 'BODY') break;
                    
                    el = el.parentElement;
                }}
            }} catch (e) {{
                console.error('Hide container failed', e);
            }}
        }}

        // Запуск
        copyToClipboard();
        hideMyContainer();
    </script>
    """
    
    # Высота 0 все равно нужна для инициализации
    components.html(js_code, height=0, width=0)
    logger.info("JS отправлен")

def safe_strip(value: Optional[str]) -> str:
    """
    Безопасная обрезка строки
    """
    result = (value or "").strip()
    return result