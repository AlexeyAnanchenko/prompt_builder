import logging
import sys
from pathlib import Path


def setup_logger(
    name: str,
    log_file: str = 'app.log',
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Настраивает и возвращает логгер с файловым и консольным выводом
    
    Args:
        name: Имя логгера (обычно __name__ модуля)
        log_file: Путь к файлу логов
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Выводить ли логи в консоль
        
    Returns:
        logging.Logger: Настроенный логгер
        
    Пример использования:
        logger = setup_logger(__name__)
        logger.info("Приложение запущено")
        logger.error("Произошла ошибка", exc_info=True)
    """
    # Получаем логгер
    logger = logging.getLogger(name)
    
    # Если у логгера уже есть обработчики, не добавляем новые
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Формат сообщений
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Файловый обработчик
    try:
        # Создаём директорию logs, если её нет
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"⚠️ Не удалось создать файл логов: {e}")
    
    # Консольный обработчик
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Получает существующий логгер или создаёт новый
    
    Args:
        name: Имя логгера
        
    Returns:
        logging.Logger: Логгер
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger