import streamlit as st
from config.settings import PAGE_CONFIG
from utils.session import init_session_state
from ui.styles import inject_custom_styles
from ui.components import render_animated_header
from ui.pages.step1_system_prompt import render_step1
from ui.pages.step2_generation import render_step2
from ui.pages.step3_unmask import render_step3
from ui.components import render_sidebar_info


def main():
    """Главная функция приложения"""
    # Настройка страницы
    st.set_page_config(**PAGE_CONFIG)
    
    # Инициализация состояния
    init_session_state()
    
    # Применение стилей
    inject_custom_styles()
    
    # Заголовок с анимацией
    render_animated_header()
    
    # Рендер трёх основных шагов
    render_step1()
    render_step2()
    render_step3()
    
    # Сайдбар с информацией
    render_sidebar_info()


if __name__ == "__main__":
    main()