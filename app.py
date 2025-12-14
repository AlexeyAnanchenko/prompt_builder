import streamlit as st

# Импорт конфигурации и утилит
from config.settings import PAGE_CONFIG
from utils.session import init_session_state
from utils.logger import setup_logger
from ui.styles import inject_custom_styles
from ui.components import render_animated_header, render_sidebar_info

# Импорт страниц (шагов)
from ui.pages.step1_system_prompt import render_step1
from ui.pages.step2_context import render_step2
from ui.pages.step3_chat import render_step3

# Настройка логгера для главного файла
logger = setup_logger(__name__, log_file='logs/app.log')

def main() -> None:
    """
    Главная функция запуска приложения Streamlit.
    """
    try:
        # 1. Базовая настройка страницы (должна быть первой командой Streamlit)
        st.set_page_config(**PAGE_CONFIG)
        
        # 2. Инициализация состояния сессии (создание переменных)
        init_session_state()
        
        # 3. Применение CSS стилей
        inject_custom_styles()
        
        # 4. Рендер заголовка
        render_animated_header()
        
        # 5. Рендер основных этапов
        render_step1() # Системный промпт
        render_step2() # Контекст и генерация
        render_step3() # Чат
        
        # 6. Рендер сайдбара
        render_sidebar_info()
        
        logger.info("UI успешно отрисован")
        
    except Exception as e:
        # Глобальный перехват ошибок.
        # Если что-то пошло не так, приложение не упадет с Traceback пользователю,
        # а запишет лог и покажет аккуратное сообщение.
        logger.critical(f"🔥 Критическая ошибка в main(): {e}", exc_info=True)
        st.error("⛔ Произошла критическая ошибка. Пожалуйста, проверьте логи или перезагрузите страницу.")
        
        # Опционально: показать детали ошибки в expander для отладки
        with st.expander("Детали ошибки (для разработчика)"):
            st.exception(e)

if __name__ == "__main__":
    main()