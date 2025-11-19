import streamlit as st
from typing import Any, Dict
from core.version_manager import VersionManager


def init_session_state() -> None:
    """Централизованная инициализация session_state"""
    version_manager = VersionManager()
    
    defaults: Dict[str, Any] = {
        # Промпты и тексты
        'system_prompt': "",
        'user_query': "",
        'final_prompt': "",
        'masked_prompt': "",
        'masking_dictionary': {},
        'llm_response': "",
        'unmasked_response': "",
        
        # Метаданные
        'token_count': 0,
        'selected_namespace': "",
        'current_version': None,
        
        # Управление версиями
        'prompt_versions': version_manager.load_versions(),
        
        # UI состояния
        'show_step1': False,
        'show_step2': True,
        'show_step3': False,
        'enable_masking': True,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(key: str, default: Any = None) -> Any:
    """Безопасное получение значения из session_state"""
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """Установка значения в session_state"""
    st.session_state[key] = value


def update_state(updates: Dict[str, Any]) -> None:
    """Массовое обновление session_state"""
    st.session_state.update(updates)