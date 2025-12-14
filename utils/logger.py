import logging
import sys
from pathlib import Path

def setup_logger(
    name: str,
    log_file: str = 'logs/app.log',
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Настраивает и возвращает логгер с файловым и консольным выводом.
    Реализует паттерн Singleton для логгера (если уже настроен, возвращает существующий).

    Args:
        name (str): Имя логгера (обычно передается __name__ модуля).
        log_file (str): Путь к файлу, куда будут писаться логи.
        level (int): Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        console_output (bool): Если True, дублирует логи в stdout (консоль).
        
    Returns:
        logging.Logger: Настроенный объект логгера.
        
    Пример использования:
        logger = setup_logger(__name__)
        logger.info("Приложение запущено")
    """
    # Получаем или создаем логгер с указанным именем
    logger = logging.getLogger(name)
    
    # Проверка: если у логгера уже есть обработчики (handlers), значит он уже был настроен.
    # Возвращаем его как есть, чтобы не плодить дублирующиеся строки в логах.
    if logger.handlers:
        return logger
    
    # Устанавливаем минимальный уровень логирования
    logger.setLevel(level)
    
    # Формат сообщений: [Дата Время] - [Имя модуля] - [Уровень] - [Сообщение]
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # --- 1. Настройка записи в файл ---
    try:
        # Используем pathlib для создания объекта пути
        log_path = Path(log_file)
        # Создаём директорию logs (и родительские, если надо), если её нет
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Обработчик для записи в файл с кодировкой utf-8 (важно для кириллицы)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Если не удалось создать файл (например, нет прав), пишем в консоль
        print(f"⚠️ Не удалось создать файл логов: {e}")
    
    # --- 2. Настройка вывода в консоль ---
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Вспомогательная функция. Получает существующий логгер или создаёт новый 
    с настройками по умолчанию, если он еще не инициализирован.
    
    Args:
        name (str): Имя логгера.
        
    Returns:
        logging.Logger: Объект логгера.
    """
    logger = logging.getLogger(name)
    # Если логгер "пустой" (нет обработчиков), инициализируем его
    if not logger.handlers:
        return setup_logger(name)
    return logger