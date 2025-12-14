from typing import List, Optional, Dict, Generator, Any
from psycopg2 import pool
from psycopg2.extensions import connection as pg_connection
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from config.settings import DatabaseConfig
from utils.logger import setup_logger

# Настраиваем логгер для этого модуля
logger = setup_logger(__name__)

class DatabaseManager:
    """
    Менеджер для работы с PostgreSQL.
    Реализует паттерн Singleton для пула соединений (SimpleConnectionPool),
    чтобы не открывать новое TCP-соединение на каждый запрос (это дорого).
    """

    # Статическая переменная для хранения пула соединений (один на всё приложение)
    _connection_pool: Optional[pool.SimpleConnectionPool] = None

    def __init__(self) -> None:
        """Инициализация менеджера. Создает пул соединений, если его еще нет."""
        logger.info("Инициализация DatabaseManager")
        if DatabaseManager._connection_pool is None:
            self._init_connection_pool()

    def _init_connection_pool(self) -> None:
        """
        Создает пул соединений с параметрами из настроек.
        Если база недоступна, выбросит исключение, которое поймает вызывающий код (app.py).
        """
        try:
            # Валидация переменных окружения перед попыткой подключения
            DatabaseConfig.validate()
            
            # Создание пула. minconn - минимальное кол-во соединений, maxconn - максимальное.
            DatabaseManager._connection_pool = pool.SimpleConnectionPool(
                minconn=DatabaseConfig.POOL_MIN_SIZE,
                maxconn=DatabaseConfig.POOL_MAX_SIZE,
                host=DatabaseConfig.HOST,
                port=DatabaseConfig.PORT,
                user=DatabaseConfig.USER,
                password=DatabaseConfig.PASSWORD,
                database=DatabaseConfig.NAME
            )
            logger.info(
                f"✅ Пул соединений создан успешно: {DatabaseConfig.HOST}:{DatabaseConfig.PORT}/{DatabaseConfig.NAME}"
            )
        except Exception as e:
            logger.critical(f"🔥 Критическая ошибка создания пула соединений: {e}", exc_info=True)
            raise

    @contextmanager
    def get_connection(self) -> Generator[pg_connection, None, None]:
        """
        Контекстный менеджер для безопасного получения соединения из пула.
        Гарантирует, что соединение вернется в пул (putconn) даже при ошибке.
        
        Использование:
            with db.get_connection() as conn:
                ...
        """
        if DatabaseManager._connection_pool is None:
            logger.error("Попытка получить соединение, но пул не инициализирован")
            raise RuntimeError("Connection pool не инициализирован")
        
        conn = None
        try:
            # Берем свободное соединение из пула
            conn = DatabaseManager._connection_pool.getconn()
            logger.debug("Соединение получено из пула")
            yield conn
        except Exception as e:
            logger.error(f"Ошибка при работе с соединением: {e}")
            # Если транзакция была начата, но произошла ошибка, откатываем её
            if conn:
                conn.rollback()
            raise
        finally:
            # Возвращаем соединение обратно в пул, чтобы его могли использовать другие
            if conn and DatabaseManager._connection_pool is not None:
                DatabaseManager._connection_pool.putconn(conn)
                logger.debug("Соединение возвращено в пул")

    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor) -> Generator[Any, None, None]:
        """
        Контекстный менеджер для получения курсора.
        Автоматически делает commit при успехе и rollback при ошибке.
        
        Args:
            cursor_factory: Фабрика курсоров. По умолчанию RealDictCursor, 
            который возвращает результаты как словари (dict), а не кортежи.
            
        Использование:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT ...")
                result = cursor.fetchall()
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                # Фиксируем транзакцию, если не было ошибок
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Ошибка выполнения SQL-запроса: {e}")
                raise
            finally:
                cursor.close()

    def get_all_namespaces(self) -> List[str]:
        """
        Возвращает форматированный список всех namespace из БД.
        Пример: ["1 (Main Namespace)", "2 (Test Namespace)"]
        """
        logger.info("Запрос списка всех namespace")
        try:
            with self.get_cursor() as cursor:
                cursor.execute("""
                    SELECT
                        namespace_id,
                        namespace_name
                    FROM qe_config.namespaces
                """)
                # Форматируем результат для отображения в UI (ID + Имя)
                namespaces = [
                    f"{row['namespace_id']} ({row['namespace_name']})" for row in cursor.fetchall()
                ]
                logger.info(f"Найдено {len(namespaces)} namespace")
                return namespaces
        except Exception as e:
            logger.error(f"Не удалось получить namespaces: {e}")
            return []
    
    def fetch_namespace_context(self, namespace_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Выгружает все данные схемы для конкретного namespace_id.
        Это "тяжелый" запрос, который наполняет кэш приложения.
        
        Args:
            namespace_id (str): ID неймспейса (например, "1").
            
        Returns:
            Dict: Словарь {'table_name': [rows...]}, содержащий дампы всех таблиц.
        """
        logger.info(f"Начало загрузки контекста для namespace_id: {namespace_id}")
        context_data = {}
        
        # 1. Список таблиц, которые зависят от namespace (фильтруем по namespace_id)
        namespace_tables = [
            'namespaces', 'clients', 'entities', 'composed_entities', 
            'entity_properties', 'tables', 'table_fields', 'parameters', 
            'constraints', 'composed_constraints', 'vertices', 
            'vertex_functions', 'edges', 'filters', 'datasets',
            'aggregation', 'limitation', 'ordering', 'group_by', 'order_by'
        ]
        
        # 2. Глобальные таблицы (справочники), которые общие для всех
        global_tables = [
            'tenants'
        ]

        try:
            with self.get_cursor() as cursor:
                # А. Грузим глобальные данные (без фильтрации)
                for table in global_tables:
                    query = f"SELECT * FROM qe_config.{table}"
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    context_data[table] = rows
                    logger.debug(f"Загружено {len(rows)} строк из глобальной таблицы {table}")

                # Б. Грузим данные конкретного namespace
                for table in namespace_tables:
                    query = f"SELECT * FROM qe_config.{table} WHERE namespace_id = %s"
                    cursor.execute(query, (namespace_id,))
                    rows = cursor.fetchall()
                    context_data[table] = rows
                    logger.debug(f"Загружено {len(rows)} строк из {table} для ns={namespace_id}")
                    
            logger.info(f"✅ Контекст успешно загружен. Таблиц в памяти: {len(context_data)}")
            return context_data
            
        except Exception as e:
            logger.error(f"🔥 Ошибка загрузки контекста namespace {namespace_id}: {e}", exc_info=True)
            raise e

    def close_all_connections(self) -> None:
        """Закрывает пул соединений (при остановке приложения)"""
        if DatabaseManager._connection_pool is not None:
            DatabaseManager._connection_pool.closeall()
            DatabaseManager._connection_pool = None
            logger.info("Пул соединений закрыт")

    def __del__(self):
        """Деструктор: попытка закрыть соединения при удалении объекта"""
        self.close_all_connections()