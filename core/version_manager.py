import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from config.settings import VERSIONS_FILE
from utils.logger import setup_logger

# Инициализируем логгер
logger = setup_logger(__name__)

class VersionManager:
    """
    Менеджер для работы с версиями системных промптов.
    Сохраняет данные в JSON файл локально.
    """
    
    def __init__(self, file_path: Path = VERSIONS_FILE):
        self.file_path = file_path
        logger.info(f"VersionManager инициализирован. Файл: {file_path.absolute()}")

    def load_versions(self) -> Dict[str, Any]:
        """
        Загружает версии промптов из файла.
        
        Returns:
            Dict: Словарь версий { 'v1.0': { 'prompt': '...', 'created': '...' } }
        """
        logger.info(f"Загрузка версий из: {self.file_path}")
        
        if not self.file_path.exists():
            logger.warning("Файл версий не найден. Будет создан новый при сохранении.")
            return {}
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logger.info("Файл версий пуст.")
                    return {}
                versions = json.loads(content)
                logger.info(f"✅ Успешно загружено {len(versions)} версий.")
                return versions
        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка формата JSON в файле версий: {e}")
            # Возвращаем пустой словарь, чтобы приложение не упало, 
            # но пользователь увидит, что версий нет.
            return {}
        except Exception as e:
            logger.error(f"❌ Критическая ошибка чтения файла версий: {e}")
            return {}

    def save_versions(self, versions: Dict[str, Any]) -> None:
        """
        Сохраняет словарь версий в файл JSON.
        Использует ensure_ascii=False для поддержки кириллицы.
        """
        logger.info(f"Сохранение {len(versions)} версий в файл...")
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(versions, f, indent=2, ensure_ascii=False)
            logger.info("✅ Версии успешно сохранены на диск.")
        except IOError as e:
            logger.error(f"❌ Ошибка записи файла версий: {e}")
            raise

    def save_version(
        self,
        versions: Dict[str, Any],
        version_name: str,
        prompt_text: str
    ) -> Dict[str, Any]:
        """
        Добавляет или обновляет версию промпта и сохраняет изменения.
        
        Args:
            versions: Текущий словарь версий.
            version_name: Имя версии (ключ).
            prompt_text: Содержание промпта.
            
        Returns:
            Dict: Обновленный словарь версий.
        """
        # Текущая метка времени
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        action = "Обновление" if version_name in versions else "Создание"
        logger.info(f"{action} версии '{version_name}' (длина: {len(prompt_text)} симв.)")
        
        if version_name in versions:
            # Обновляем существующую
            versions[version_name]['prompt'] = prompt_text
            versions[version_name]['modified'] = now
        else:
            # Создаем новую запись
            versions[version_name] = {
                'prompt': prompt_text,
                'created': now,
                'modified': now
            }
        
        # Сохраняем на диск
        self.save_versions(versions)
        return versions
    
    def delete_version(self, versions: Dict[str, Any], version_name: str) -> Dict[str, Any]:
        """
        Удаляет версию промпта по имени.
        """
        logger.info(f"Запрос на удаление версии: '{version_name}'")
        
        if version_name in versions:
            del versions[version_name]
            self.save_versions(versions)
            logger.info(f"✅ Версия '{version_name}' удалена.")
        else:
            logger.warning(f"⚠️ Попытка удалить несуществующую версию: '{version_name}'")
        
        return versions