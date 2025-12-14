import streamlit as st
from ui.components import (
    render_step_toggle_button,
    render_button_pair,
    render_version_preview
)
from core.version_manager import VersionManager
from config.settings import MESSAGES, TEXTAREA_HEIGHTS
from utils.logger import setup_logger

# Настраиваем логгер для этого модуля
logger = setup_logger(__name__)

def render_step1() -> None:
    """
    Рендерит Шаг 1: Настройка системного промпта.
    Включает в себя:
    1. Текстовое поле для ввода промпта.
    2. Панель управления версиями (Сохранить/Загрузить/Удалить).
    """
    logger.debug("Рендер шага 1: Настройка системного промпта")
    
    # ==========================================
    # 1. ОБРАБОТКА ОТЛОЖЕННОЙ ЗАГРУЗКИ (State Management)
    # ==========================================
    # Механизм решения проблемы цикла обновления Streamlit.
    # Если на прошлом шаге (в списке версий) нажали "Загрузить", мы сохранили данные в _pending_version_load
    # и сделали rerun. Теперь мы применяем эти данные.
    if '_pending_version_load' in st.session_state:
        pending = st.session_state._pending_version_load
        
        # Применяем значения
        st.session_state.system_prompt = pending['prompt']
        st.session_state.current_version = pending['name']
        
        # Синхронизируем виджеты (input keys)
        st.session_state.sys_prompt_widget = pending['prompt']
        st.session_state.save_version_ui_input = pending['name']
        
        logger.info(f"Применена отложенная загрузка версии: {pending['name']}")
        
        # Удаляем временный флаг и показываем уведомление
        del st.session_state._pending_version_load
        st.success(MESSAGES["success_version_loaded"].format(pending['name']))
    
    # ==========================================
    # 2. ИНИЦИАЛИЗАЦИЯ STATE
    # ==========================================
    if 'system_prompt' not in st.session_state:
        st.session_state.system_prompt = ""
    if 'current_version' not in st.session_state:
        st.session_state.current_version = ""
    if 'sys_prompt_widget' not in st.session_state:
        st.session_state.sys_prompt_widget = st.session_state.system_prompt
    if 'save_version_ui_input' not in st.session_state:
        st.session_state.save_version_ui_input = st.session_state.get('current_version', '')

    # Кнопка сворачивания/разворачивания
    render_step_toggle_button(
        step_number=1,
        title="Настройка системного промпта",
        state_key='show_step1'
    )
    
    # Если шаг свернут - прерываем рендер
    if not st.session_state.get('show_step1', True):
        return
    
    # Инициализируем менеджер для работы с файлом версий
    version_manager = VersionManager()
    
    # ==========================================
    # 3. ПАНЕЛЬ ВЕРСИЙ (Tabs)
    # ==========================================
    with st.expander("📚 Управление версиями системного промпта", expanded=False):
        tab_save, tab_load = st.tabs(["💾 Сохранить", "📂 Загрузить"])
        
        with tab_save:
            _render_save_version_tab(version_manager)
        
        with tab_load:
            _render_load_version_tab(version_manager)
    
    # ==========================================
    # 4. ТЕКСТОВОЕ ПОЛЕ
    # ==========================================
    _render_system_prompt_textarea()
    
    st.markdown("---")


def _render_save_version_tab(version_manager: VersionManager) -> None:
    """Рендерит вкладку сохранения текущей версии промпта."""
    col_save_name, col_save_btn = st.columns([4, 1])
    
    with col_save_name:
        # ВАЖНО: Используем кастомный HTML заголовок, как в оригинале, для точного сохранения стиля
        st.markdown('<p style="font-size: 18px; margin-bottom: 5px;">Название версии</p>', unsafe_allow_html=True)
        
        # Инициализация ключа перед созданием виджета (защита от KeyErrors)
        if 'save_version_ui_input' not in st.session_state:
            st.session_state.save_version_ui_input = st.session_state.get('current_version', '')
        
        st.text_input(
            "Название версии", # label (скрыт, но нужен для a11y)
            placeholder="Например: v1.0",
            key="save_version_ui_input",
            label_visibility="collapsed" # Скрываем стандартный лейбл, т.к. нарисовали свой выше
        )
    
    with col_save_btn:
        st.write("") # Визуальный отступ
        st.write("")
        if st.button("💾 Сохранить", use_container_width=True):
            current_prompt = st.session_state.system_prompt
            save_name = st.session_state.save_version_ui_input
            
            # Валидация
            if save_name and save_name.strip():
                if not current_prompt:
                    st.warning("Нельзя сохранить пустой промпт.")
                    return
                
                try:
                    # Сохранение через менеджер
                    versions = version_manager.save_version(
                        st.session_state.prompt_versions,
                        save_name.strip(),
                        current_prompt
                    )
                    # Обновление состояния
                    st.session_state.prompt_versions = versions
                    st.session_state.current_version = save_name.strip()
                    
                    logger.info(f"Версия сохранена: {save_name.strip()}")
                    st.success(MESSAGES["success_version_saved"].format(save_name))
                    st.rerun()
                except Exception as e:
                    logger.error(f"Ошибка сохранения версии: {e}", exc_info=True)
                    st.error(f"Не удалось сохранить версию: {e}")
            else:
                st.warning(MESSAGES["warning_enter_version_name"])


def _render_load_version_tab(version_manager: VersionManager) -> None:
    """Рендерит список доступных версий для загрузки или удаления."""
    if st.session_state.prompt_versions:
        # Итерируемся по словарю версий
        for version_name, version_data in st.session_state.prompt_versions.items():
            # Компонент render_version_preview возвращает действие ('load' / 'delete')
            action = render_version_preview(version_name, version_data)
            
            if action == "load":
                # Устанавливаем флаг и перезагружаем страницу, чтобы обновить виджеты на следующем проходе
                st.session_state._pending_version_load = {
                    'name': version_name,
                    'prompt': version_data['prompt']
                }
                st.rerun()
                
            elif action == "delete":
                try:
                    versions = version_manager.delete_version(st.session_state.prompt_versions, version_name)
                    st.session_state.prompt_versions = versions
                    
                    # Если удалили текущую активную версию, сбрасываем отображение
                    if st.session_state.current_version == version_name:
                        st.session_state.current_version = ""
                        
                    logger.info(f"Версия удалена: {version_name}")
                    st.success(MESSAGES["success_version_deleted"].format(version_name))
                    st.rerun()
                except Exception as e:
                    logger.error(f"Ошибка удаления версии: {e}", exc_info=True)
                    st.error(f"Не удалось удалить версию: {e}")
    else:
        st.info(MESSAGES["info_no_versions"])


def _render_system_prompt_textarea() -> None:
    """Рендерит основное поле ввода промпта."""
    
    # Формируем заголовок с индикацией активной версии
    version_label = "📝 Системный промпт"
    if st.session_state.get('current_version'):
        version_label += f" (💡 {st.session_state['current_version']})"
    
    # Callback для синхронизации виджета с переменной состояния
    def on_text_change():
        st.session_state.system_prompt = st.session_state.sys_prompt_widget

    st.text_area(
        version_label,
        height=TEXTAREA_HEIGHTS["system_prompt"],
        placeholder="Введите системный промпт здесь...",
        key='sys_prompt_widget', # Виджет привязан к этому ключу
        on_change=on_text_change,
        help="Этот текст будет добавлен в начало финального промпта"
    )
    
    # Callback для кнопки очистки
    def clear_sys_prompt():
        st.session_state.system_prompt = ""
        st.session_state.sys_prompt_widget = ""
    
    # Рендер кнопок под полем
    render_button_pair(
        clear_key="clear_sys",
        copy_key="copy_sys",
        text_to_copy=st.session_state.system_prompt,
        clear_callback=clear_sys_prompt
    )