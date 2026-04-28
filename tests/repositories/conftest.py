# tests/repositories/conftest.py
"""Фикстуры для тестирования репозиториев"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List


@pytest.fixture
def mock_cursor():
    """Мок для курсора БД"""
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    return cursor


@pytest.fixture
def mock_connection(mock_cursor):
    """Мок для соединения с БД"""
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = mock_cursor
    conn.cursor.return_value.__exit__.return_value = None
    return conn


@pytest.fixture
def mock_get_connection(mock_connection):
    """Мок для get_connection контекстного менеджера"""
    with patch('db.get_connection') as mock:
        mock.return_value.__enter__.return_value = mock_connection
        yield mock


# =========================================================
# ТЕСТОВЫЕ ДАННЫЕ
# =========================================================

@pytest.fixture
def sample_race_data() -> Dict[str, Any]:
    """Пример данных расы"""
    return {
        'id': 1,
        'name': 'Человек',
        'speed': 30,
        'size': 'Средний',
        'description': 'Универсальная раса',
        'image_path': 'images/races/man.jpg'
    }


@pytest.fixture
def sample_race_list() -> List[Dict[str, Any]]:
    """Список рас для тестов"""
    return [
        {'id': 1, 'name': 'Человек', 'speed': 30, 'size': 'Средний',
         'description': 'Универсальная раса', 'image_path': 'images/races/man.jpg'},
        {'id': 2, 'name': 'Эльф', 'speed': 30, 'size': 'Средний',
         'description': 'Грациозная раса', 'image_path': 'images/races/elf.jpg'},
    ]


@pytest.fixture
def sample_class_data() -> Dict[str, Any]:
    """Пример данных класса"""
    return {
        'id': 1,
        'name': 'Воин',
        'hit_die': 10,
        'primary_stats': '["STR", "DEX"]',
        'saving_throws': '["STR", "CON"]',
        'skill_choices': 2,
        'description': 'Мастер боя',
        'image_path': 'images/classes/fighter.jpg',
        'is_spellcaster': False,
        'spellcasting_ability': None,
        'cantrips_count': 0,
        'spells_count_level1': 0,
        'masteries_count': 3
    }


@pytest.fixture
def sample_background_data() -> Dict[str, Any]:
    """Пример данных предыстории"""
    return {
        'id': 1,
        'name': 'Солдат',
        'characteristic1': 'STR',
        'characteristic2': 'DEX',
        'characteristic3': 'CON',
        'trait': 'Бдительный',
        'skills': '["Атлетика", "Запугивание"]',
        'tools': 'Игровой набор',
        'equipment_a': 'Копьё, Лёгкий арбалет, 20 Болтов',
        'equipment_b': '50 ЗМ',
        'description': 'Опытный воин'
    }