import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict


# Загружаем переменные из .env
load_dotenv()

# Пути к файлам
VERSIONS_FILE: Path = Path("prompt_versions.json")

# Конфигурация страницы
PAGE_CONFIG: Dict = {
    "page_title": "Prompt Builder",
    "page_icon": "🖊",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

# Лимиты токенов
MAX_TOKENS: int = 128000
TOKEN_MULTIPLIER: float = 1.3  # Для упрощённого подсчёта

# UI константы
TEXTAREA_HEIGHTS: Dict[str, int] = {
    "system_prompt": 150,
    "user_query": 400,
    "llm_response": 200,
}

# Сообщения
MESSAGES: Dict[str, str] = {
    "error_no_mapping": "⚠️ Нет словаря для расшифровки. Сначала сгенерируйте замаскированный промпт.",
    "error_no_llm_response": "⚠️ Введите ответ LLM",
    "success_version_saved": "✅ Версия '{}' сохранена!",
    "success_version_loaded": "✅ Загружена версия '{}'",
    "success_version_deleted": "✅ Версия '{}' удалена",
    "success_prompt_generated": "✅ Промпт успешно сгенерирован!",
    "success_masked_elements": "✅ Промпт сгенерирован! Замаскировано {} элементов",
    "success_unmasked": "✅ Ответ расшифрован!",
    "info_no_confidential": "ℹ️ Конфиденциальные данные не обнаружены",
    "info_no_versions": "🔭 Нет сохранённых версий",
    "warning_no_namespaces": "⚠️ Нет доступных namespace",
    "warning_enter_version_name": "⚠️ Введите название версии",
    "toast_copied": "✅ Скопировано!",
}

class DatabaseConfig:
    """Конфигурация базы данных"""
    
    HOST = os.getenv("DB_HOST", "localhost")
    PORT = int(os.getenv("DB_PORT", "5432"))
    USER = os.getenv("DB_USER", "postgres")
    PASSWORD = os.getenv("DB_PASSWORD")
    NAME = os.getenv("DB_NAME", "query_db")
    
    POOL_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "2"))
    POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "10"))
    
    @classmethod
    def get_connection_string(cls) -> str:
        """Возвращает строку подключения к БД"""
        return f"postgresql://{cls.USER}:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.NAME}"
    
    @classmethod
    def validate(cls):
        """Проверяет наличие обязательных параметров"""
        if not cls.PASSWORD:
            raise ValueError("DB_PASSWORD не установлен в переменных окружения")
        if not cls.NAME:
            raise ValueError("DB_NAME не установлен в переменных окружения")