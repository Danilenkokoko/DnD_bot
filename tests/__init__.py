# tests/__init__.py
"""
D&D Character Creator - Test Suite
Набор тестов для всех модулей проекта

Структура тестов:
- tests/engine/         # Тесты игрового движка
- tests/services/       # Тесты сервисного слоя
- tests/handlers/       # Тесты обработчиков (требуют моков)
- tests/conftest.py     # Общие фикстуры для всех тестов

Запуск тестов:
    pytest tests/ -v                    # Все тесты
    pytest tests/engine/ -v             # Только engine
    pytest tests/engine/test_stats.py -v # Конкретный файл
    pytest -m slow                      # Только медленные тесты
    pytest --cov=engine --cov-report=term  # С покрытием

Версия: 1.0.0
"""

__version__ = "1.0.0"

# Экспортируем основные типы для использования в тестах
from typing import Tuple, Dict, Any, List, Optional

# Маркеры для pytest (определяются в conftest.py)
# - slow: медленные тесты (интеграционные)
# - unit: быстрые тесты (модульные)
# - integration: интеграционные тесты
# - smoke: дымовые тесты (быстрая проверка)

# Константы для тестов
TEST_SEED = 42  # Фиксированный seed для воспроизводимости

# Стандартные тестовые данные
DEFAULT_ABILITY_SCORES = {
    "STR": 15, "DEX": 14, "CON": 13,
    "INT": 12, "WIS": 10, "CHA": 8
}

DEFAULT_ABILITY_SCORES_ALL_10 = {
    "STR": 10, "DEX": 10, "CON": 10,
    "INT": 10, "WIS": 10, "CHA": 10
}

# Валидные комбинации primary и background stats для тестов
TEST_PRIMARY_STATS_CASES = [
    (["STR"], ["STR", "DEX", "CON"]),  # 1 primary, входит
    (["INT"], ["INT", "WIS", "CHA"]),  # 1 primary, входит
    (["STR"], ["INT", "WIS", "CHA"]),  # 1 primary, не входит
    (["STR", "DEX"], ["STR", "DEX", "CON"]),  # 2 primary, оба входят
    (["STR", "DEX"], ["STR", "CON", "WIS"]),  # 2 primary, один входит
    (["STR", "DEX"], ["INT", "WIS", "CHA"]),  # 2 primary, ни один не входит
]

# Ожидаемые суммы бонусов для каждого случая
EXPECTED_BONUS_SUMS = {
    "primary_in": 3,
    "primary_not_in": 3,
    "both_primary_in": 3,
    "one_primary_in": 3,
    "none_primary_in": 3
}


def get_test_seed() -> int:
    """
    Возвращает фиксированный seed для воспроизводимых тестов

    Returns:
        int: seed для random
    """
    return TEST_SEED


def is_ci_environment() -> bool:
    """
    Проверяет, запущены ли тесты в CI среде

    Returns:
        bool: True если в CI, False иначе
    """
    import os
    return os.environ.get('CI', 'false').lower() == 'true'


def skip_if_no_db() -> bool:
    """
    Проверяет, нужно ли пропустить тесты, требующие БД

    Returns:
        bool: True если БД недоступна
    """
    import os
    # В CI среде обычно есть БД
    if is_ci_environment():
        return False

    # В локальной среде проверяем наличие .env
    return not os.path.exists('.env')


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ТЕСТОВ
# =========================================================

def assert_bonus_sum(bonuses: Dict, expected: int = 3) -> None:
    """
    Проверяет, что сумма бонусов равна ожидаемому значению

    Args:
        bonuses: словарь с бонусами
        expected: ожидаемая сумма (по умолчанию 3)

    Raises:
        AssertionError: если сумма не совпадает
    """
    total = sum(bonuses.values())
    assert total == expected, f"Сумма бонусов = {total}, ожидалось {expected}"


def create_test_character_data(
        name: str = "Test Character",
        level: int = 1,
        class_name: str = "Воин",
        race: str = "Человек",
        background: str = "Солдат",
        stats: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Создаёт тестовые данные персонажа

    Args:
        name: имя персонажа
        level: уровень
        class_name: класс
        race: раса
        background: предыстория
        stats: характеристики (если None, используются стандартные)

    Returns:
        Dict[str, Any]: тестовые данные персонажа
    """
    if stats is None:
        stats = DEFAULT_ABILITY_SCORES.copy()

    return {
        'name': name,
        'level': level,
        'class_name': class_name,
        'race': race,
        'background': background,
        'stats': stats,
        'hp': 10,
        'ac': 15,
        'speed': 30,
        'alignment': 'Нейтральное'
    }


# =========================================================
# ТЕСТОВЫЕ ДАННЫЕ ДЛЯ РАЗНЫХ МОДУЛЕЙ
# =========================================================

# Тестовые данные для HP модуля
TEST_HP_CASES = [
    # (hit_die, constitution, level, expected_min, expected_max)
    (6, 10, 1, 6, 6),  # Волшебник, CON=10
    (8, 12, 1, 8, 8),  # Жрец, CON=12
    (10, 15, 1, 10, 10),  # Воин, CON=15
    (12, 8, 1, 12, 12),  # Варвар, CON=8 (минимальный бонус)
    (6, 14, 3, 18, 30),  # Волшебник 3 уровня
    (10, 16, 5, 42, 70),  # Воин 5 уровня
]

# Тестовые данные для AC модуля
TEST_AC_CASES = [
    # (dexterity, armor_name, has_shield, expected_ac)
    (10, None, False, 10),  # Без брони
    (14, None, False, 12),  # Без брони, DEX=14
    (14, "Кожаная броня", False, 13),  # Лёгкая броня
    (14, "Кольчуга", False, 16),  # Средняя броня (max DEX 2)
    (18, "Кольчуга", False, 16),  # Средняя броня (DEX=18, бонус только +2)
    (14, "Латы", False, 18),  # Тяжёлая броня (без DEX)
    (14, "Кожаная броня", True, 15),  # Лёгкая броня + щит
]

# Тестовые данные для Proficiency модуля
TEST_PROFICIENCY_CASES = [
    (1, 2), (2, 2), (3, 2), (4, 2),
    (5, 3), (6, 3), (7, 3), (8, 3),
    (9, 4), (10, 4), (11, 4), (12, 4),
    (13, 5), (14, 5), (15, 5), (16, 5),
    (17, 6), (18, 6), (19, 6), (20, 6),
]

# Тестовые данные для Dice модуля
TEST_DICE_EXPRESSIONS = [
    ("d6", (6, 1, 0)),
    ("2d8", (8, 2, 0)),
    ("d20+5", (20, 1, 5)),
    ("3d10-2", (10, 3, -2)),
]

# =========================================================
# ТЕСТИРОВАНИЕ ТЕСТОВОГО МОДУЛЯ
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ TESTS/__INIT__.PY")
    print("=" * 60)

    # Тест 1: Константы
    print("\n1. Проверка констант:")
    print(f"   TEST_SEED: {TEST_SEED}")
    print(f"   DEFAULT_ABILITY_SCORES: {DEFAULT_ABILITY_SCORES}")

    # Тест 2: Вспомогательные функции
    print("\n2. Проверка вспомогательных функций:")

    # assert_bonus_sum
    try:
        assert_bonus_sum({"STR": 2, "DEX": 1}, 3)
        print("   ✅ assert_bonus_sum - OK (сумма 3)")
    except AssertionError as e:
        print(f"   ❌ assert_bonus_sum - {e}")

    try:
        assert_bonus_sum({"STR": 2, "DEX": 2}, 3)
        print("   ❌ assert_bonus_sum - не поймал ошибку")
    except AssertionError:
        print("   ✅ assert_bonus_sum - поймал ошибку (сумма 4)")

    # create_test_character_data
    char_data = create_test_character_data()
    print(f"   create_test_character_data: {char_data['name']}, {char_data['class_name']}")

    # Тест 3: Проверка окружения
    print("\n3. Проверка окружения:")
    print(f"   CI среда: {is_ci_environment()}")
    print(f"   Пропустить тесты с БД: {skip_if_no_db()}")

    # Тест 4: Тестовые данные
    print("\n4. Проверка тестовых данных:")
    print(f"   TEST_HP_CASES: {len(TEST_HP_CASES)} случаев")
    print(f"   TEST_AC_CASES: {len(TEST_AC_CASES)} случаев")
    print(f"   TEST_PROFICIENCY_CASES: {len(TEST_PROFICIENCY_CASES)} случаев")
    print(f"   TEST_DICE_EXPRESSIONS: {len(TEST_DICE_EXPRESSIONS)} случаев")
    print(f"   TEST_PRIMARY_STATS_CASES: {len(TEST_PRIMARY_STATS_CASES)} случаев")

    print("\n" + "=" * 60)
    print("✅ TESTS MODULE READY")
    print("=" * 60)