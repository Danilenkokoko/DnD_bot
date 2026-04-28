#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для комплексной проверки готовности бота к запуску.
Запуск: python check_bot_ready.py
"""

import sys
import os
import importlib
import logging
from typing import Tuple, List

# Настройка логирования для теста
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def print_header(text: str):
    print("\n" + "=" * 70)
    print(f" {text}")
    print("=" * 70)


def print_ok(msg: str):
    print(f"✅ {msg}")


def print_error(msg: str):
    print(f"❌ {msg}")


def print_warning(msg: str):
    print(f"⚠️ {msg}")


def check_import(module_name: str, name: str = None) -> bool:
    """Проверяет импорт модуля или атрибута"""
    try:
        if name:
            module = importlib.import_module(module_name)
            getattr(module, name)
            print_ok(f"Импорт {module_name}.{name} успешен")
        else:
            importlib.import_module(module_name)
            print_ok(f"Импорт {module_name} успешен")
        return True
    except ImportError as e:
        print_error(f"Не удалось импортировать {module_name}{'.' + name if name else ''}: {e}")
        return False
    except AttributeError:
        print_error(f"Атрибут {name} не найден в модуле {module_name}")
        return False


def check_file_exists(filepath: str) -> bool:
    """Проверяет существование файла"""
    exists = os.path.exists(filepath)
    if exists:
        print_ok(f"Файл {filepath} найден")
    else:
        print_error(f"Файл {filepath} отсутствует")
    return exists


def check_env_variable(var_name: str) -> bool:
    """Проверяет наличие переменной окружения"""
    value = os.getenv(var_name)
    if value:
        print_ok(f"Переменная {var_name} установлена")
        return True
    else:
        print_error(f"Переменная {var_name} не установлена")
        return False


def test_database_connection():
    """Проверяет подключение к БД"""
    try:
        from db import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                print_ok("Подключение к базе данных успешно")
                return True
    except Exception as e:
        print_error(f"Ошибка подключения к БД: {e}")
        return False


def test_engine_functions():
    """Проверяет базовые функции engine"""
    try:
        from engine import calculate_proficiency_bonus, calculate_hp_at_level, validate_name
        bonus = calculate_proficiency_bonus(5)
        hp = calculate_hp_at_level(10, 15, 1)
        valid, msg = validate_name("Тест")
        if bonus == 3 and hp >= 10 and valid:
            print_ok("Базовые функции engine работают")
            return True
        else:
            print_error("Результаты engine не соответствуют ожидаемым")
            return False
    except Exception as e:
        print_error(f"Ошибка в engine: {e}")
        return False


def test_repositories():
    """Проверяет инициализацию репозиториев"""
    try:
        from repositories import RaceRepository, ClassRepository, BackgroundRepository
        race_repo = RaceRepository()
        class_repo = ClassRepository()
        bg_repo = BackgroundRepository()
        # Просто проверяем, что объекты создались
        print_ok("Репозитории инициализируются без ошибок")
        return True
    except Exception as e:
        print_error(f"Ошибка инициализации репозиториев: {e}")
        return False


def test_services():
    """Проверяет инициализацию сервисов"""
    try:
        from services.character_service import CharacterStatsService, CharacterFinalizationService
        from services.progression_service import ProgressionService
        # Проверяем простой вызов статического метода (без БД)
        primary = CharacterStatsService.get_class_primary_stats("Воин")
        if isinstance(primary, list):
            print_ok("Сервисы работают (базовые методы)")
        else:
            print_error("Сервисы вернули некорректный результат")
            return False
        return True
    except Exception as e:
        print_error(f"Ошибка в сервисах: {e}")
        return False


def test_handlers():
    """Проверяет импорт обработчиков"""
    try:
        from handlers import character_router
        print_ok("Обработчики импортируются")
        return True
    except Exception as e:
        print_error(f"Ошибка импорта обработчиков: {e}")
        return False


def test_keyboards():
    """Проверяет импорт клавиатур"""
    try:
        from keyboards import main_menu, create_class_keyboard
        print_ok("Клавиатуры импортируются")
        return True
    except Exception as e:
        print_error(f"Ошибка импорта клавиатур: {e}")
        return False


def test_states():
    """Проверяет импорт состояний FSM"""
    try:
        from states import CreateCharacter
        # Проверяем наличие атрибутов состояний
        required_states = ['class_select', 'name_input', 'race_select']
        for state in required_states:
            if not hasattr(CreateCharacter, state):
                print_error(f"Отсутствует состояние {state} в CreateCharacter")
                return False
        print_ok("FSM состояния корректны")
        return True
    except Exception as e:
        print_error(f"Ошибка импорта состояний: {e}")
        return False


def test_dnd_logic_facade():
    """Проверяет, что dnd_logic работает как фасад (без ошибок импорта)"""
    try:
        import dnd_logic
        # Проверяем одну из перенаправленных функций
        classes = dnd_logic.get_class_list()
        if isinstance(classes, list):
            print_ok("dnd_logic работает как фасад")
            return True
        else:
            print_error("dnd_logic вернул некорректный результат")
            return False
    except Exception as e:
        print_error(f"Ошибка в dnd_logic: {e}")
        return False


def main():
    print_header("ПРОВЕРКА ГОТОВНОСТИ БОТА К ЗАПУСКУ")

    # 1. Проверка окружения
    print_header("1. ПРОВЕРКА ОКРУЖЕНИЯ")
    success_env = check_env_variable("BOT_TOKEN")

    # 2. Проверка критических файлов
    print_header("2. ПРОВЕРКА КЛЮЧЕВЫХ ФАЙЛОВ")
    files_to_check = [
        "bot.py",
        "db.py",
        "dnd_logic.py",
        "pdf_generator.py",
        "spell_selector.py",
        "engine/__init__.py",
        "engine/hp.py",
        "engine/ac.py",
        "engine/proficiency.py",
        "engine/dice.py",
        "engine/validators.py",
        "repositories/__init__.py",
        "services/__init__.py",
        "handlers/__init__.py",
        "keyboards/__init__.py",
        "states/__init__.py",
    ]
    files_ok = all(check_file_exists(f) for f in files_to_check)

    # 3. Проверка импортов
    print_header("3. ПРОВЕРКА ИМПОРТОВ")
    imports_ok = True
    imports_ok &= check_import("engine")
    imports_ok &= check_import("engine.stats")
    imports_ok &= check_import("engine.hp")
    imports_ok &= check_import("engine.ac")
    imports_ok &= check_import("engine.proficiency")
    imports_ok &= check_import("engine.dice")
    imports_ok &= check_import("engine.validators", "validate_name")
    imports_ok &= check_import("repositories")
    imports_ok &= check_import("services")
    imports_ok &= check_import("handlers")
    imports_ok &= check_import("keyboards")
    imports_ok &= check_import("states")

    # 4. Проверка функциональности модулей
    print_header("4. ПРОВЕРКА ФУНКЦИОНАЛЬНОСТИ")
    engine_ok = test_engine_functions()
    repos_ok = test_repositories()
    services_ok = test_services()
    handlers_ok = test_handlers()
    keyboards_ok = test_keyboards()
    states_ok = test_states()
    facade_ok = test_dnd_logic_facade()

    # 5. Проверка базы данных (опционально, может требовать реальной БД)
    print_header("5. ПРОВЕРКА БАЗЫ ДАННЫХ")
    db_ok = test_database_connection()

    # Итог
    print_header("ИТОГОВЫЙ РЕЗУЛЬТАТ")
    all_ok = (
            success_env and files_ok and imports_ok and engine_ok and repos_ok and
            services_ok and handlers_ok and keyboards_ok and states_ok and facade_ok
    )

    if all_ok:
        print_ok("Все проверки пройдены успешно!")
        print_ok("Бот готов к запуску.")
        if not db_ok:
            print_warning("Проблемы с БД могут ограничить функционал, но бот может запуститься.")
        return 0
    else:
        print_error("Обнаружены критические ошибки. Бот не готов к запуску.")
        print("\nРекомендации:")
        if not success_env:
            print("  - Убедитесь, что в файле .env задан BOT_TOKEN")
        if not files_ok:
            print("  - Проверьте наличие всех необходимых файлов")
        if not imports_ok:
            print("  - Проверьте корректность структуры пакетов (наличие __init__.py)")
        if not engine_ok:
            print("  - Проверьте установку зависимостей и корректность кода в engine/")
        if not repos_ok or not services_ok:
            print("  - Проверьте импорты внутри repositories и services")
        if not handlers_ok or not keyboards_ok or not states_ok:
            print("  - Проверьте импорты в handlers/, keyboards/, states/")
        if not facade_ok:
            print("  - Проверьте dnd_logic.py на наличие ошибок")
        return 1


if __name__ == "__main__":
    sys.exit(main())