import json
from datetime import datetime
from pathlib import Path
from typing import Dict
from config.settings import VERSIONS_FILE


class VersionManager:
    """Менеджер версий системных промптов"""
    
    def __init__(self, file_path: Path = VERSIONS_FILE):
        self.file_path = file_path
    
    def load_versions(self) -> Dict:
        """Загружает версии промптов из файла"""
        if not self.file_path.exists():
            return {}
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Ошибка формата файла версий: {str(e)}")
        except Exception as e:
            raise IOError(f"Ошибка загрузки версий: {str(e)}")
    
    def save_versions(self, versions: Dict) -> None:
        """Сохраняет версии промптов в файл"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(versions, f, indent=2, ensure_ascii=False)
        except Exception as e:
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
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if version_name in versions:
            versions[version_name]['prompt'] = prompt_text
            versions[version_name]['modified'] = now
        else:
            versions[version_name] = {
                'prompt': prompt_text,
                'created': now,
                'modified': now
            }
        
        self.save_versions(versions)
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
        if version_name in versions:
            del versions[version_name]
            self.save_versions(versions)
        return versions