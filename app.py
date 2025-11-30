import streamlit as st
from config.settings import PAGE_CONFIG
from utils.session import init_session_state
from utils.logger import setup_logger
from ui.styles import inject_custom_styles
from ui.components import render_animated_header, render_sidebar_info

# Импорт страниц
from ui.pages.step1_system_prompt import render_step1
from ui.pages.step2_context import render_step2
from ui.pages.step3_chat import render_step3  # <--- ИЗМЕНЕНИЕ ЗДЕСЬ

logger = setup_logger(__name__, log_file='logs/app.log')

def main():
    """Главная функция приложения"""
    try:
        st.set_page_config(**PAGE_CONFIG)
        init_session_state()
        inject_custom_styles()
        
        render_animated_header()
        
        # Шаги
        render_step1()
        render_step2()
        render_step3() # <--- ВЫЗОВ
        
        render_sidebar_info()
        logger.info("UI успешно отрендерен")
        
    except Exception as e:
        logger.error(f"Критическая ошибка в main(): {e}", exc_info=True)
        st.error("⛔ Произошла критическая ошибка. Проверьте логи.")

if __name__ == "__main__":
    main()