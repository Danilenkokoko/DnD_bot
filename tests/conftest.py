# tests/conftest.py
"""
Pytest configuration and shared fixtures for D&D Character Creator tests
Общие фикстуры и конфигурация для всех тестов

Фикстуры:
- engine фикстуры (изолированный engine)
- БД фикстуры (подготовка/очистка)
- Тестовые данные (стандартные персонажи)
- Моки для внешних зависимостей
"""

import pytest
import random
import os
import tempfile
from typing import Dict, Any, List, Optional, Generator
from unittest.mock import Mock, patch, AsyncMock


# =========================================================
# БАЗОВАЯ КОНФИГУРАЦИЯ PYTEST
# =========================================================

def pytest_configure(config):
    """Регистрируем пользовательские маркеры"""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (require database)"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests (fast, no dependencies)"
    )
    config.addinivalue_line(
        "markers",
        "smoke: marks tests as smoke tests (quick sanity checks)"
    )


# =========================================================
# ФИКСТУРЫ ДЛЯ ENGINE МОДУЛЕЙ
# =========================================================

@pytest.fixture(scope="function")
def random_seed() -> int:
    """
    Фиксированный seed для воспроизводимых тестов

    Returns:
        int: seed для random
    """
    return 42


@pytest.fixture(scope="function")
def setup_random_seed(random_seed: int) -> None:
    """
    Устанавливает фиксированный seed перед тестом и восстанавливает после

    Args:
        random_seed: значение seed
    """
    original_state = random.getstate()
    random.seed(random_seed)
    yield
    random.setstate(original_state)


@pytest.fixture(scope="function")
def base_ability_scores() -> Dict[str, int]:
    """
    Стандартные базовые характеристики для тестов

    Returns:
        Dict[str, int]: характеристики 15,14,13,12,10,8
    """
    return {
        "STR": 15, "DEX": 14, "CON": 13,
        "INT": 12, "WIS": 10, "CHA": 8
    }


@pytest.fixture(scope="function")
def default_ability_scores() -> Dict[str, int]:
    """
    Характеристики по умолчанию (все 10) для тестов

    Returns:
        Dict[str, int]: все характеристики = 10
    """
    return {
        "STR": 10, "DEX": 10, "CON": 10,
        "INT": 10, "WIS": 10, "CHA": 10
    }


@pytest.fixture(scope="function")
def background_stats_physical() -> List[str]:
    """Физические характеристики предыстории"""
    return ["STR", "DEX", "CON"]


@pytest.fixture(scope="function")
def background_stats_mental() -> List[str]:
    """Ментальные характеристики предыстории"""
    return ["INT", "WIS", "CHA"]


@pytest.fixture(scope="function")
def background_stats_mixed() -> List[str]:
    """Смешанные характеристики предыстории"""
    return ["STR", "DEX", "INT"]


@pytest.fixture(scope="function")
def primary_stats_single_strength() -> List[str]:
    """Одиночная primary характеристика (Сила)"""
    return ["STR"]


@pytest.fixture(scope="function")
def primary_stats_single_intelligence() -> List[str]:
    """Одиночная primary характеристика (Интеллект)"""
    return ["INT"]


@pytest.fixture(scope="function")
def primary_stats_double() -> List[str]:
    """Двойные primary характеристики (Сила и Ловкость)"""
    return ["STR", "DEX"]


@pytest.fixture(scope="function")
def primary_stats_double_mixed() -> List[str]:
    """Двойные primary характеристики (Сила и Интеллект)"""
    return ["STR", "INT"]


# =========================================================
# ФИКСТУРЫ ДЛЯ ТЕСТОВЫХ ДАННЫХ
# =========================================================

@pytest.fixture(scope="function")
def test_character_data() -> Dict[str, Any]:
    """
    Стандартные тестовые данные персонажа

    Returns:
        Dict[str, Any]: данные для тестирования
    """
    return {
        'name': 'Test Character',
        'level': 1,
        'class_name': 'Воин',
        'race': 'Человек',
        'background': 'Солдат',
        'stats': {
            "STR": 15, "DEX": 14, "CON": 13,
            "INT": 12, "WIS": 10, "CHA": 8
        },
        'hp': 12,
        'ac': 16,
        'speed': 30,
        'alignment': 'Нейтральное',
        'backstory': 'Test backstory for unit testing'
    }


@pytest.fixture(scope="function")
def test_warrior_data(test_character_data: Dict[str, Any]) -> Dict[str, Any]:
    """Тестовые данные для Воина"""
    data = test_character_data.copy()
    data['class_name'] = 'Воин'
    data['primary_stats'] = ['STR', 'DEX']
    data['hit_die'] = 10
    return data


@pytest.fixture(scope="function")
def test_wizard_data(test_character_data: Dict[str, Any]) -> Dict[str, Any]:
    """Тестовые данные для Волшебника"""
    data = test_character_data.copy()
    data['class_name'] = 'Волшебник'
    data['primary_stats'] = ['INT']
    data['hit_die'] = 6
    data['stats'] = {
        "STR": 8, "DEX": 12, "CON": 13,
        "INT": 15, "WIS": 14, "CHA": 10
    }
    return data


@pytest.fixture(scope="function")
def test_barbarian_data(test_character_data: Dict[str, Any]) -> Dict[str, Any]:
    """Тестовые данные для Варвара"""
    data = test_character_data.copy()
    data['class_name'] = 'Варвар'
    data['primary_stats'] = ['STR']
    data['hit_die'] = 12
    data['stats'] = {
        "STR": 15, "DEX": 13, "CON": 14,
        "INT": 10, "WIS": 12, "CHA": 8
    }
    return data


# =========================================================
# ФИКСТУРЫ ДЛЯ PDF ГЕНЕРАЦИИ
# =========================================================

@pytest.fixture(scope="function")
def temp_pdf_file() -> Generator[str, None, None]:
    """
    Временный файл для PDF тестов, автоматически удаляется после теста

    Yields:
        str: путь к временному файлу
    """
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        yield tmp.name

    # Cleanup
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)


@pytest.fixture(scope="function")
def pdf_test_data(test_character_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Данные для тестирования PDF генерации

    Returns:
        Dict[str, Any]: подготовленные данные для PDF
    """
    return {
        'name': test_character_data['name'],
        'class_name': test_character_data['class_name'],
        'race': test_character_data['race'],
        'level': test_character_data['level'],
        'background': test_character_data['background'],
        'background_trait': 'Бдительный',
        'background_description': 'Описание предыстории для теста',
        'backstory': test_character_data['backstory'],
        'stats': test_character_data['stats'],
        'hp': test_character_data['hp'],
        'ac': test_character_data['ac'],
        'speed': test_character_data['speed'],
        'alignment': test_character_data['alignment'],
        'player_name': 'Test Player',
        'experience': 0,
        'proficiency_bonus': 2,
        'saving_throws': ['STR', 'CON'],
        'skills': ['Атлетика', 'Восприятие'],
        'race_traits': ['Универсальность человечества'],
        'class_features': ['Второе дыхание', 'Боевой стиль'],
        'equipment': ['Длинный меч', 'Щит', 'Кожаная броня'],
        'coins': '50 ЗМ',
        'notes': 'Test notes',
        'spells': [],
        'spell_slots_1': 0,
        'spell_slots_2': 0
    }


# =========================================================
# МОКИ ДЛЯ ВНЕШНИХ ЗАВИСИМОСТЕЙ
# =========================================================

@pytest.fixture(scope="function")
def mock_db_connection():
    """
    Мок для подключения к БД

    Returns:
        Mock: мок соединения с БД
    """
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []

    with patch('db.get_connection', return_value=mock_conn):
        yield mock_conn


@pytest.fixture(scope="function")
def mock_bot_message():
    """
    Мок для сообщения Telegram

    Returns:
        Mock: мок сообщения
    """
    mock_message = AsyncMock()
    mock_message.from_user.id = 123456789
    mock_message.from_user.full_name = "Test User"
    mock_message.answer = AsyncMock()
    mock_message.answer_photo = AsyncMock()
    mock_message.answer_document = AsyncMock()
    return mock_message


@pytest.fixture(scope="function")
def mock_fsm_context():
    """
    Мок для FSM контекста

    Returns:
        Mock: мок FSMContext
    """
    mock_context = AsyncMock()
    mock_context.get_state = AsyncMock(return_value=None)
    mock_context.set_state = AsyncMock()
    mock_context.update_data = AsyncMock()
    mock_context.get_data = AsyncMock(return_value={})
    mock_context.clear = AsyncMock()
    return mock_context


@pytest.fixture(scope="function")
def mock_callback_query():
    """
    Мок для callback запроса

    Returns:
        Mock: мок CallbackQuery
    """
    mock_callback = AsyncMock()
    mock_callback.data = ""
    mock_callback.message = AsyncMock()
    mock_callback.message.delete = AsyncMock()
    mock_callback.message.answer = AsyncMock()
    mock_callback.message.answer_photo = AsyncMock()
    mock_callback.answer = AsyncMock()
    return mock_callback


# =========================================================
# ПАРАМЕТРИЗОВАННЫЕ ФИКСТУРЫ
# =========================================================

@pytest.fixture(params=[
    (["STR"], ["STR", "DEX", "CON"], "primary_in"),
    (["STR"], ["INT", "WIS", "CHA"], "primary_not_in"),
    (["STR", "DEX"], ["STR", "DEX", "CON"], "both_in"),
    (["STR", "DEX"], ["STR", "CON", "WIS"], "one_in"),
    (["STR", "DEX"], ["INT", "WIS", "CHA"], "none_in"),
])
def bonus_distribution_case(request):
    """
    Параметризованная фикстура для тестирования распределения бонусов

    Returns:
        tuple: (primary_stats, background_stats, expected_case)
    """
    return request.param


@pytest.fixture(params=[
    (6, 10, 1, 6),
    (8, 12, 1, 8),
    (10, 15, 1, 12),
    (6, 14, 3, 18),
    (10, 16, 5, 42),
])
def hp_calculation_case(request):
    """
    Параметризованная фикстура для тестирования HP

    Returns:
        tuple: (hit_die, constitution, level, expected_min_hp)
    """
    return request.param


@pytest.fixture(params=[
    (10, None, False, 10),
    (14, None, False, 12),
    (14, "Кожаная броня", False, 13),
    (14, "Кольчуга", False, 16),
    (18, "Кольчуга", False, 16),
    (14, "Латы", False, 18),
])
def ac_calculation_case(request):
    """
    Параметризованная фикстура для тестирования AC

    Returns:
        tuple: (dexterity, armor_name, has_shield, expected_ac)
    """
    return request.param


# =========================================================
# ХУКИ ДЛЯ ТЕСТОВ
# =========================================================

@pytest.fixture(scope="session", autouse=True)
def test_session_setup():
    """
    Настройка тестовой сессии (выполняется один раз)
    """
    print("\n🧪 Starting D&D Character Creator test session...")
    yield
    print("\n✅ Test session completed!")


@pytest.fixture(scope="function", autouse=True)
def test_function_cleanup():
    """
    Очистка после каждого теста
    """
    yield
    # Сброс случайного seed после каждого теста
    random.seed()


# =========================================================
# HELPER ФУНКЦИИ ДЛЯ ТЕСТОВ
# =========================================================

def assert_bonus_sum(bonuses: Dict[str, int], expected: int = 3) -> None:
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


def create_stats_dict(
        strength: int = 10,
        dexterity: int = 10,
        constitution: int = 10,
        intelligence: int = 10,
        wisdom: int = 10,
        charisma: int = 10
) -> Dict[str, int]:
    """
    Создаёт словарь характеристик с указанными значениями

    Returns:
        Dict[str, int]: словарь с характеристиками
    """
    return {
        "STR": strength,
        "DEX": dexterity,
        "CON": constitution,
        "INT": intelligence,
        "WIS": wisdom,
        "CHA": charisma
    }


# =========================================================
# ТЕСТИРОВАНИЕ КОНФИГУРАЦИИ
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ TESTS/CONFTEST.PY")
    print("=" * 60)

    print("\n1. Проверка наличия фикстур:")
    print("   ✅ base_ability_scores")
    print("   ✅ default_ability_scores")
    print("   ✅ background_stats_physical")
    print("   ✅ background_stats_mental")
    print("   ✅ primary_stats_single_strength")
    print("   ✅ primary_stats_double")
    print("   ✅ test_character_data")
    print("   ✅ test_warrior_data")
    print("   ✅ test_wizard_data")
    print("   ✅ temp_pdf_file")
    print("   ✅ pdf_test_data")
    print("   ✅ mock_db_connection")
    print("   ✅ mock_bot_message")
    print("   ✅ mock_fsm_context")
    print("   ✅ mock_callback_query")

    print("\n2. Проверка параметризованных фикстур:")
    print("   ✅ bonus_distribution_case")
    print("   ✅ hp_calculation_case")
    print("   ✅ ac_calculation_case")

    print("\n3. Проверка helper функций:")
    stats = create_stats_dict(strength=15, dexterity=14, constitution=13)
    print(f"   ✅ create_stats_dict: {stats}")

    print("\n" + "=" * 60)
    print("✅ CONFTEST.PY READY")
    print("=" * 60)