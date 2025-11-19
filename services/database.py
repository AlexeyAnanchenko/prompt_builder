from typing import List
from utils.logger import setup_logger


# Настраиваем логгер для модуля
logger = setup_logger(__name__)


class DatabaseManager:
    """Mock-класс для работы с базой данных"""
    
    def __init__(self):
        logger.info("DatabaseManager инициализирован")
    
    def get_all_namespaces(self) -> List[str]:
        """Возвращает список всех namespace"""
        logger.info("Получение списка всех namespace")
        # TODO: Заменить на реальную логику получения namespace из БД
        namespaces = ["AN", "INS", "DEMO"]
        logger.info(f"Найдено {len(namespaces)} namespace: {namespaces}")
        return namespaces
    
    def fetch_all_data_by_namespace(self, namespace: str) -> List[dict]:
        """Получает все данные по namespace"""
        logger.info(f"Получение данных для namespace: {namespace}")
        # TODO: Заменить на реальную логику выборки данных из БД
        data = [{"id": 1, "content": f"Sample data from {namespace}"}]
        logger.info(f"Получено {len(data)} записей для namespace {namespace}")
        return data