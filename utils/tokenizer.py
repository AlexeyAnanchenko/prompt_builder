from pathlib import Path
from typing import Optional
from utils.logger import setup_logger

from tokenizers import Tokenizer

logger = setup_logger(__name__)

class TokenCounter:
    """Быстрый подсчет токенов через Rust-библиотеку tokenizers"""
    
    _tokenizer: Optional[Tokenizer] = None
    _tokenizer_path = Path(__file__).parent.parent / "deepseek_tokenizer" / "tokenizer.json"
    print(_tokenizer_path)
    
    @classmethod
    def get_tokenizer(cls) -> Tokenizer:
        if cls._tokenizer is None:
            try:
                if cls._tokenizer_path.exists():
                    cls._tokenizer = Tokenizer.from_file(str(cls._tokenizer_path))
                    logger.info("✅ Токенизатор (fast-rust) загружен")
                else:
                    logger.warning(f"❌ Файл {cls._tokenizer_path} не найден")
                    raise FileNotFoundError(f"tokenizer.json не найден")
            except Exception as e:
                logger.error(f"Ошибка загрузки токенизатора: {e}")
                raise
        # После успешной загрузки _tokenizer гарантированно не None
        assert cls._tokenizer is not None
        return cls._tokenizer
    
    @classmethod
    def count_tokens(cls, text: str) -> int:
        try:
            tokenizer = cls.get_tokenizer()
            if tokenizer is None:
                raise RuntimeError("Токенизатор не загружен")
            # encode возвращает объект Encoding, у которого есть ids
            encoded = tokenizer.encode(text)
            return len(encoded.ids)
        except Exception as e:
            logger.error(f"Ошибка токенизации: {e}")
            # Fallback
            return int(len(text.split()) / 0.75)