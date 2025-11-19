"""
Тестовый скрипт для диагностики циклического импорта
"""
import sys
import os

def test_import_chain():
    """Тестирует цепочку импортов для выявления проблемы"""
    print("=== ТЕСТ ЦИКЛИЧЕСКОГО ИМПОРТА ===")
    
    # Тест 1: Прямой импорт config.settings
    try:
        print("1. Тестируем импорт config.settings...")
        from config.settings import VERSIONS_FILE
        print(f"   ✅ Успешно: VERSIONS_FILE = {VERSIONS_FILE}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # Тест 2: Импорт utils.logger
    try:
        print("2. Тестируем импорт utils.logger...")
        from utils.logger import setup_logger
        print("   ✅ Успешно: setup_logger импортирован")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # Тест 3: Импорт utils.session
    try:
        print("3. Тестируем импорт utils.session...")
        from utils.session import init_session_state
        print("   ✅ Успешно: init_session_state импортирован")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # Тест 4: Импорт core.version_manager
    try:
        print("4. Тестируем импорт core.version_manager...")
        from core.version_manager import VersionManager
        print("   ✅ Успешно: VersionManager импортирован")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    # Тест 5: Полная цепочка как в app.py
    try:
        print("5. Тестируем полную цепочку импортов...")
        import config.settings
        import utils.session
        import core.version_manager
        print("   ✅ Успешно: все модули импортированы")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False
    
    print("=== ВСЕ ТЕСТЫ ПРОЙДЕНЫ ===")
    return True

if __name__ == "__main__":
    success = test_import_chain()
    sys.exit(0 if success else 1)