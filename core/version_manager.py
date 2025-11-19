import json
from datetime import datetime
from pathlib import Path
from typing import Dict
from config.settings import VERSIONS_FILE
from utils.logger import setup_logger


# Настраиваем логгер для модуля
logger = setup_logger(__name__)


class VersionManager:
    """Менеджер версий системных промптов"""
    
    def __init__(self, file_path: Path = VERSIONS_FILE):
        self.file_path = file_path
        logger.info(f"VersionManager инициализирован с файлом: {file_path}")
    
    def load_versions(self) -> Dict:
        """Загружает версии промптов из файла"""
        logger.info(f"Попытка загрузки версий из файла: {self.file_path}")
        
        if not self.file_path.exists():
            logger.info("Файл версий не существует, возвращаем пустой словарь")
            return {}
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    logger.info("Файл версий пуст, возвращаем пустой словарь")
                    return {}
                versions = json.loads(content)
                logger.info(f"Успешно загружено {len(versions)} версий")
                return versions
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка формата JSON в файле версий: {str(e)}")
            raise ValueError(f"Ошибка формата файла версий: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка загрузки версий: {str(e)}")
            raise IOError(f"Ошибка загрузки версий: {str(e)}")
    
    def save_versions(self, versions: Dict) -> None:
        """Сохраняет версии промптов в файл"""
        logger.info(f"Сохранение {len(versions)} версий в файл: {self.file_path}")
        
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(versions, f, indent=2, ensure_ascii=False)
            logger.info("Версии успешно сохранены")
        except Exception as e:
            logger.error(f"Ошибка сохранения версий: {str(e)}")
            raise IOError(f"Ошибка сохранения версий: {str(e)}")
    
    def save_version(
        self,
        versions: Dict,
        version_name: str,
        prompt_text: str
    ) -> Dict:
        """
        Сохраняет новую версию промпта
        
        Args:
            versions: Текущий словарь версий
            version_name: Название версии
            prompt_text: Текст промпта
            
        Returns:
            Dict: Обновлённый словарь версий
        """
        logger.info(f"Сохранение версии '{version_name}' с промптом длиной {len(prompt_text)} символов")
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if version_name in versions:
            logger.info(f"Обновление существующей версии '{version_name}'")
            versions[version_name]['prompt'] = prompt_text
            versions[version_name]['modified'] = now
        else:
            logger.info(f"Создание новой версии '{version_name}'")
            versions[version_name] = {
                'prompt': prompt_text,
                'created': now,
                'modified': now
            }
        
        self.save_versions(versions)
        logger.info(f"Версия '{version_name}' успешно сохранена")
        return versions
    
    def delete_version(self, versions: Dict, version_name: str) -> Dict:
        """
        Удаляет версию промпта
        
        Args:
            versions: Текущий словарь версий
            version_name: Название версии для удаления
            
        Returns:
            Dict: Обновлённый словарь версий
        """
        logger.info(f"Попытка удаления версии '{version_name}'")
        
        if version_name in versions:
            del versions[version_name]
            self.save_versions(versions)
            logger.info(f"Версия '{version_name}' успешно удалена")
        else:
            logger.warning(f"Версия '{version_name}' не найдена для удаления")
        
        return versions