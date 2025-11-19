from typing import List, Optional
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from config.settings import DatabaseConfig
from utils.logger import setup_logger


# Настраиваем логгер для модуля
logger = setup_logger(__name__)


class DatabaseManager:
    """Менеджер для работы с PostgreSQL"""

    _connection_pool: Optional[pool.SimpleConnectionPool] = None


    def __init__(self):
        """Инициализация менеджера БД"""

        logger.info("DatabaseManager инициализирован")
        if DatabaseManager._connection_pool is None:
            self._init_connection_pool()


    def _init_connection_pool(self):
        """Создает пул соединений с БД"""

        try:
            DatabaseConfig.validate()
            
            DatabaseManager._connection_pool = pool.SimpleConnectionPool(
                DatabaseConfig.POOL_MIN_SIZE,
                DatabaseConfig.POOL_MAX_SIZE,
                host=DatabaseConfig.HOST,
                port=DatabaseConfig.PORT,
                user=DatabaseConfig.USER,
                password=DatabaseConfig.PASSWORD,
                database=DatabaseConfig.NAME
            )
            logger.info(
                f"Пул соединений создан: {DatabaseConfig.HOST}:{DatabaseConfig.PORT}/{DatabaseConfig.NAME}"
            )
        except Exception as e:
            logger.error(f"Ошибка создания пула соединений: {e}")
            raise


    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для получения соединения из пула"""

        if DatabaseManager._connection_pool is None:
            raise RuntimeError("Connection pool не инициализирован")
        conn = None
        try:
            conn = DatabaseManager._connection_pool.getconn()
            logger.debug("Соединение получено из пула")
            yield conn
        except Exception as e:
            logger.error(f"Ошибка при работе с соединением: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn and DatabaseManager._connection_pool is not None:
                DatabaseManager._connection_pool.putconn(conn)
                logger.debug("Соединение возвращено в пул")


    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Контекстный менеджер для получения курсора"""

        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Ошибка выполнения запроса: {e}")
                raise
            finally:
                cursor.close()


    def get_all_namespaces(self) -> List[str]:
        """Возвращает список всех namespace из БД"""

        logger.info("Получение списка всех namespace")
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT
                        namespace_id,
                        namespace_name
                    FROM qe_config.namespaces
                """)
                namespaces = [
                    f"{row['namespace_id']} ({row['namespace_name']})" for row in cursor.fetchall()
                ]
                logger.info(f"Найдено {len(namespaces)} namespace: {namespaces}")
                return namespaces
        except Exception as e:
            logger.error(f"Ошибка получения namespace: {e}")
            return []


    def fetch_all_data_by_namespace(self, namespace: str) -> List[dict]:
        """Получает все данные по namespace"""

        logger.info(f"Получение данных для namespace: {namespace}")
        # TODO: Заменить на реальную логику выборки данных из БД
        data = [{"id": 1, "content": f"Sample data from {namespace}"}]
        logger.info(f"Получено {len(data)} записей для namespace {namespace}")
        return data
    

    def close_all_connections(self):
        """Закрывает все соединения в пуле"""

        if DatabaseManager._connection_pool is not None:
            DatabaseManager._connection_pool.closeall()
            DatabaseManager._connection_pool = None
            logger.info("Все соединения закрыты")


    def __del__(self):
        """Деструктор для закрытия соединений"""

        self.close_all_connections()