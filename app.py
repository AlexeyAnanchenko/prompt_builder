import streamlit as st
from config.settings import PAGE_CONFIG
from utils.session import init_session_state
from utils.logger import setup_logger
from ui.styles import inject_custom_styles
from ui.components import render_animated_header
from ui.pages.step1_system_prompt import render_step1
from ui.pages.step2_generation import render_step2
from ui.pages.step3_unmask import render_step3
from ui.components import render_sidebar_info

# Настраиваем главный логгер при запуске приложения
logger = setup_logger(__name__, log_file='logs/app.log')

def main():
    """Главная функция приложения"""

    try:
        # Настройка страницы
        st.set_page_config(**PAGE_CONFIG)
        
        # Инициализация состояния
        init_session_state()
        
        # Рендер UI
        inject_custom_styles()
        render_animated_header()
        render_step1()
        render_step2()
        render_step3()
        render_sidebar_info()
        
        logger.info("UI успешно отрендерен")
        
    except Exception as e:
        logger.error(f"Критическая ошибка в main(): {e}", exc_info=True)
        st.error("⛔ Произошла критическая ошибка. Проверьте логи.")


if __name__ == "__main__":
    main()