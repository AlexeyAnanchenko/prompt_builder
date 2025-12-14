import streamlit as st
from typing import Any, Dict
from core.version_manager import VersionManager
from utils.logger import setup_logger

# Инициализируем логгер
logger = setup_logger(__name__)

def init_session_state() -> None:
    """
    Централизованная инициализация st.session_state.
    Вызывается в начале app.py, чтобы гарантировать существование всех ключей.
    
    Session State в Streamlit работает как глобальный словарь, который сохраняется 
    между перезагрузками страницы (reruns).
    """
    
    # Создаем менеджер версий для загрузки истории промптов
    version_manager = VersionManager()
    
    # Словарь значений по умолчанию.
    # Если ключа нет в session_state, он будет создан с этим значением.
    defaults: Dict[str, Any] = {
        # --- Текстовые данные ---
        'system_prompt': "",      # Текущий текст системного промпта
        'user_query': "",         # Текст запроса пользователя
        'final_prompt_masked': "",   # Сгенерированный промпт (замаскированный)
        'final_prompt_original': "", # Сгенерированный промпт (оригинал)
        'generated_sql_context': "", # SQL часть промпта
        
        # --- Словари и структуры ---
        'masking_dictionary': {}, # Словарь замен (ENT_1 -> person)
        'prompt_versions': version_manager.load_versions(), # Загруженные версии из json
        
        # --- Данные Чата (Шаг 3) ---
        'chat_data_human': "",    # Текст в левом окне чата (Human)
        'chat_data_llm': "",      # Текст в правом окне чата (LLM)
        
        # --- Метаданные ---
        'token_count': 0,         # Количество токенов в текущем промпте
        'selected_namespace': "", # Выбранный namespace (строка из selectbox)
        'current_version': None,  # Имя текущей активной версии промпта
        
        # --- UI Флаги (управление видимостью) ---
        'show_step1': True,       # Развернут ли Шаг 1
        'show_step2': False,      # Развернут ли Шаг 2
        'show_step3': False,      # Развернут ли Шаг 3
        'enable_masking': True,   # Включено ли маскирование (по умолчанию да)
        
        # --- Персистентность выбора (Multiselect) ---
        'stored_datasets': [],    # Сохраненный выбор датасетов
        'stored_entities': [],    # Сохраненный выбор сущностей
    }
    
    initialized_count = 0
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            initialized_count += 1
            
    if initialized_count > 0:
        logger.info(f"Инициализировано {initialized_count} новых ключей в session_state")

def get_state(key: str, default: Any = None) -> Any:
    """
    Безопасное получение значения из session_state.
    
    Args:
        key: Имя ключа.
        default: Значение по умолчанию, если ключа нет.
    """
    return st.session_state.get(key, default)

def set_state(key: str, value: Any) -> None:
    """
    Установка значения в session_state.
    Автоматически логирует изменения (полезно для отладки).
    """
    if key in st.session_state and st.session_state[key] != value:
        logger.debug(f"State change: {key} = {value}")
    st.session_state[key] = value

def update_state(updates: Dict[str, Any]) -> None:
    """
    Массовое обновление session_state из словаря.
    """
    logger.debug(f"Массовое обновление session_state: {list(updates.keys())}")
    st.session_state.update(updates)