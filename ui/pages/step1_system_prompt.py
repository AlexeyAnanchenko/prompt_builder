import streamlit as st
from ui.components import (
    render_step_toggle_button,
    render_button_pair,
    render_version_preview
)
from core.version_manager import VersionManager
from config.settings import MESSAGES, TEXTAREA_HEIGHTS
from utils.logger import setup_logger

logger = setup_logger(__name__)

def render_step1() -> None:
    """Рендерит шаг 1: Настройка системного промпта"""
    logger.info("Рендер шага 1: Настройка системного промпта")
    
    # ✅ ОБРАБОТКА ОТЛОЖЕННОЙ ЗАГРУЗКИ ВЕРСИИ
    if '_pending_version_load' in st.session_state:
        pending = st.session_state._pending_version_load
        st.session_state.system_prompt = pending['prompt']
        st.session_state.current_version = pending['name']
        st.session_state.sys_prompt_widget = pending['prompt']
        st.session_state.save_version_ui_input = pending['name']
        
        # Удаляем флаг
        del st.session_state._pending_version_load
        st.success(MESSAGES["success_version_loaded"].format(pending['name']))
    
    # 1. Инициализация ХРАНИЛИЩА ДАННЫХ
    if 'system_prompt' not in st.session_state:
        st.session_state.system_prompt = ""
    if 'current_version' not in st.session_state:
        st.session_state.current_version = ""
    if 'sys_prompt_widget' not in st.session_state:
        st.session_state.sys_prompt_widget = st.session_state.system_prompt
    if 'save_version_ui_input' not in st.session_state:
        st.session_state.save_version_ui_input = st.session_state.get('current_version', '')

    render_step_toggle_button(
        step_number=1,
        title="Настройка системного промпта",
        state_key='show_step1'
    )
    
    if not st.session_state.get('show_step1', True):
        return
    
    version_manager = VersionManager()
    
    with st.expander("📚 Управление версиями системного промпта", expanded=False):
        tab_save, tab_load = st.tabs(["💾 Сохранить", "📂 Загрузить"])
        
        with tab_save:
            _render_save_version_tab(version_manager)
        
        with tab_load:
            _render_load_version_tab(version_manager)
    
    _render_system_prompt_textarea()
    
    st.markdown("---")


def _render_save_version_tab(version_manager: VersionManager) -> None:
    col_save_name, col_save_btn = st.columns([4, 1])
    
    with col_save_name:
        st.markdown('<p style="font-size: 18px; margin-bottom: 5px;">Название версии</p>', unsafe_allow_html=True)
        
        # ✅ КРИТИЧНО: Инициализируем ключ ДО создания виджета
        if 'save_version_ui_input' not in st.session_state:
            st.session_state.save_version_ui_input = st.session_state.get('current_version', '')
        
        st.text_input(
            "Название версии",
            placeholder="Например: v1.0",
            key="save_version_ui_input",
            label_visibility="collapsed"
        )
    
    with col_save_btn:
        st.write("")
        st.write("")
        if st.button("💾 Сохранить", use_container_width=True):
            current_prompt = st.session_state.system_prompt
            save_name = st.session_state.save_version_ui_input  # Читаем из session_state
            
            if save_name and save_name.strip():
                if not current_prompt:
                    st.warning("Нельзя сохранить пустой промпт.")
                    return
                
                versions = version_manager.save_version(
                    st.session_state.prompt_versions,
                    save_name.strip(),
                    current_prompt
                )
                st.session_state.prompt_versions = versions
                st.session_state.current_version = save_name.strip()
                st.success(MESSAGES["success_version_saved"].format(save_name))
                st.rerun()
            else:
                st.warning(MESSAGES["warning_enter_version_name"])


def _render_load_version_tab(version_manager: VersionManager) -> None:
    if st.session_state.prompt_versions:
        for version_name, version_data in st.session_state.prompt_versions.items():
            action = render_version_preview(version_name, version_data)
            
            if action == "load":
                # ✅ ИСПОЛЬЗУЕМ СПЕЦИАЛЬНЫЙ ФЛАГ для отложенного обновления
                st.session_state._pending_version_load = {
                    'name': version_name,
                    'prompt': version_data['prompt']
                }
                st.rerun()
                
            elif action == "delete":
                versions = version_manager.delete_version(st.session_state.prompt_versions, version_name)
                st.session_state.prompt_versions = versions
                if st.session_state.current_version == version_name:
                    st.session_state.current_version = ""
                st.success(MESSAGES["success_version_deleted"].format(version_name))
                st.rerun()
    else:
        st.info(MESSAGES["info_no_versions"])


def _render_system_prompt_textarea() -> None:
    """Рендерит текстовую область"""
    
    version_label = "📝 Системный промпт"
    if st.session_state.get('current_version'):
        version_label += f" (🟢 {st.session_state['current_version']})"
    
    # --- СИНХРОНИЗАЦИЯ UI <-> DATA ---
    
    def on_text_change():
        """Копируем из виджета в 'вечное' хранилище"""
        st.session_state.system_prompt = st.session_state.sys_prompt_widget

    st.text_area(
        version_label,
        height=TEXTAREA_HEIGHTS["system_prompt"],
        placeholder="Введите системный промпт здесь...",
        key='sys_prompt_widget',
        on_change=on_text_change,
        help="Этот текст будет добавлен в начало финального промпта"
    )
    
    def clear_sys_prompt():
        st.session_state.system_prompt = ""
        st.session_state.sys_prompt_widget = ""
    
    # Кнопки
    render_button_pair(
        clear_key="clear_sys",
        copy_key="copy_sys",
        text_to_copy=st.session_state.system_prompt,
        clear_callback=clear_sys_prompt
    )