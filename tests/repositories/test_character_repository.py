# tests/repositories/test_character_repository.py
"""Тесты для CharacterRepository"""

import pytest
from repositories.character_repository import CharacterRepository


class TestCharacterRepository:
    """Тесты репозитория персонажей"""

    def test_create_character(self, mock_get_connection):
        """create создаёт персонажа и возвращает ID"""
        character_data = {
            'user_id': 123,
            'name': 'Тестовый персонаж',
            'class_id': 1,
            'race_id': 1,
            'level': 1,
            'stats': {'STR': 15, 'DEX': 14, 'CON': 13, 'INT': 10, 'WIS': 10, 'CHA': 10},
            'hp': 12,
            'ac': 16
        }

        with patch('repositories.character_repository.CharacterRepository._fetch_one') as mock_fetch:
            mock_fetch.return_value = {'id': 999}

            repo = CharacterRepository()
            char_id = repo.create(character_data)

            assert char_id == 999

    def test_get_by_id_found(self, mock_get_connection):
        """get_by_id возвращает персонажа"""
        character_row = {
            'id': 1,
            'user_id': 123,
            'name': 'Тест',
            'str': 15, 'dex': 14, 'con': 13, 'int': 10, 'wis': 10, 'cha': 10,
            'hp': 12, 'ac': 16,
            'selected_skills': '["Атлетика"]',
            'selected_spells': '[]'
        }

        with patch('repositories.character_repository.CharacterRepository._fetch_one') as mock_fetch:
            mock_fetch.return_value = character_row

            repo = CharacterRepository()
            result = repo.get_by_id(1, user_id=123)

            assert result is not None
            assert result['name'] == 'Тест'
            assert 'stats' in result

    def test_get_by_user_id(self, mock_get_connection):
        """get_by_user_id возвращает список персонажей пользователя"""
        characters = [
            {'id': 1, 'name': 'Персонаж1', 'class_name': 'Воин'},
            {'id': 2, 'name': 'Персонаж2', 'class_name': 'Волшебник'}
        ]

        with patch('repositories.character_repository.CharacterRepository._fetch_all') as mock_fetch:
            mock_fetch.return_value = characters

            repo = CharacterRepository()
            result = repo.get_by_user_id(123)

            assert len(result) == 2

    def test_delete_character_ownership(self, mock_get_connection):
        """delete проверяет права и удаляет"""
        with patch('repositories.character_repository.CharacterRepository._check_ownership') as mock_check:
            mock_check.return_value = True

            with patch('repositories.character_repository.CharacterRepository._execute_query') as mock_exec:
                repo = CharacterRepository()
                result = repo.delete(1, 123)

                assert result is True
                mock_exec.assert_called_once()

    def test_delete_character_no_ownership(self, mock_get_connection):
        """delete возвращает False если нет прав"""
        with patch('repositories.character_repository.CharacterRepository._check_ownership') as mock_check:
            mock_check.return_value = False

            repo = CharacterRepository()
            result = repo.delete(1, 123)

            assert result is False