from pathlib import Path
from typing import Dict, Any

# Пути к файлам
VERSIONS_FILE = Path("prompt_versions.json")

# Конфигурация страницы
PAGE_CONFIG: Dict[str, Any] = {
    "page_title": "Prompt Builder",
    "page_icon": "🔨",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

# Лимиты токенов
MAX_TOKENS = 128000
TOKEN_MULTIPLIER = 1.3  # Для упрощённого подсчёта

# UI константы
TEXTAREA_HEIGHTS = {
    "system_prompt": 150,
    "user_query": 400,
    "llm_response": 200,
}

# Сообщения
MESSAGES = {
    "error_no_query": "⛔ Пожалуйста, введите запрос",
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