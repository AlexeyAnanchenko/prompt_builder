from pathlib import Path
from typing import Optional, Any
from utils.logger import setup_logger

# Пытаемся импортировать библиотеку для Rust-токенизации.
# Если её нет, мы не должны падать, а просто переключимся на упрощенный подсчет.
try:
    from tokenizers import Tokenizer
except ImportError:
    # Если импорт не удался, переменная Tokenizer будет недоступна.
    # Мы обработаем это внутри класса TokenCounter.
    Tokenizer = None

logger = setup_logger(__name__)

class TokenCounter:
    """
    Класс для подсчета токенов. 
    Использует библиотеку `tokenizers` (Fast Rust implementation) для точности.
    
    Если библиотека не установлена или файл модели не найден, 
    автоматически переключается на простой метод подсчета по словам.
    """
    
    # Используем тип Any, так как класс Tokenizer может не существовать,
    # если библиотека не установлена. Это предотвращает ошибку Pylance.
    _tokenizer: Any = None
    
    # Путь к файлу tokenizer.json. 
    # parent.parent поднимает нас из utils/ в корень проекта.
    _tokenizer_path: Path = Path(__file__).parent.parent / "deepseek_tokenizer" / "tokenizer.json"
    
    @classmethod
    def get_tokenizer(cls) -> Any:
        """
        Ленивая загрузка токенизатора (Singleton).
        Загружает файл только при первом обращении.
        
        Returns:
            Any: Объект Tokenizer или None, если загрузка не удалась.
        """
        if cls._tokenizer is None:
            # 1. Проверяем, установлена ли библиотека
            if Tokenizer is None:
                logger.warning("Библиотека `tokenizers` не установлена. Используется упрощенный подсчет.")
                return None
                
            # 2. Пробуем загрузить файл
            try:
                if cls._tokenizer_path.exists():
                    cls._tokenizer = Tokenizer.from_file(str(cls._tokenizer_path))
                    logger.info(f"✅ Токенизатор успешно загружен из {cls._tokenizer_path}")
                else:
                    logger.warning(f"⚠️ Файл токенизатора не найден: {cls._tokenizer_path}")
                    # Не выбрасываем исключение, чтобы приложение продолжило работать
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации токенизатора: {e}")
                
        return cls._tokenizer
    
    @classmethod
    def count_tokens(cls, text: str) -> int:
        """
        Основной метод подсчета токенов.
        Безопасно выбирает метод (точный или приближенный).
        
        Args:
            text (str): Входной текст.
            
        Returns:
            int: Количество токенов.
        """
        if not text:
            return 0
            
        try:
            tokenizer = cls.get_tokenizer()
            if tokenizer is not None:
                # encode возвращает объект Encoding, у которого есть свойство ids
                encoded = tokenizer.encode(text)
                return len(encoded.ids)
            else:
                # Fallback: Если токенизатор недоступен
                return cls._fallback_count(text)
                
        except Exception as e:
            logger.error(f"Ошибка при токенизации: {e}")
            return cls._fallback_count(text)

    @staticmethod
    def _fallback_count(text: str) -> int:
        """
        Запасной метод подсчета (эвристика).
        1 слово ≈ 0.75 токена (или 1 токен ≈ 0.75 слова).
        Коэффициент 1.3 подобран эмпирически для кода и русского языка.
        """
        from config.settings import TOKEN_MULTIPLIER
        return int(len(text.split()) * TOKEN_MULTIPLIER)