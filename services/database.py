from typing import List


class DatabaseManager:
    """Mock-класс для работы с базой данных"""
    
    def get_all_namespaces(self) -> List[str]:
        """Возвращает список всех namespace"""
        # TODO: Заменить на реальную логику получения namespace из БД
        return ["AN", "INS", "DEMO"]
    
    def fetch_all_data_by_namespace(self, namespace: str) -> List[dict]:
        """Получает все данные по namespace"""
        # TODO: Заменить на реальную логику выборки данных из БД
        return [{"id": 1, "content": f"Sample data from {namespace}"}]