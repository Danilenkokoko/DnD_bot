# tests/repositories/test_race_repository.py
"""Тесты для RaceRepository"""

import pytest
from unittest.mock import patch, MagicMock
from repositories.race_repository import RaceRepository


class TestRaceRepository:
    """Тесты репозитория рас"""

    def test_get_all_names(self, mock_get_connection, sample_race_list):
        """get_all_names возвращает список названий"""
        with patch('repositories.race_repository.RaceRepository._fetch_all') as mock_fetch:
            mock_fetch.return_value = [{'name': r['name']} for r in sample_race_list]

            repo = RaceRepository()
            result = repo.get_all_names()

            assert result == ['Человек', 'Эльф']
            mock_fetch.assert_called_once()

    def test_get_by_name_found(self, mock_get_connection, sample_race_data):
        """get_by_name возвращает данные при нахождении"""
        with patch('repositories.race_repository.RaceRepository._fetch_one') as mock_fetch:
            mock_fetch.return_value = sample_race_data

            repo = RaceRepository()
            result = repo.get_by_name('Человек')

            assert result is not None
            assert result['name'] == 'Человек'
            assert result['speed'] == 30

    def test_get_by_name_not_found(self, mock_get_connection):
        """get_by_name возвращает None если раса не найдена"""
        with patch('repositories.race_repository.RaceRepository._fetch_one') as mock_fetch:
            mock_fetch.return_value = None

            repo = RaceRepository()
            result = repo.get_by_name('НесуществующаяРаса')

            assert result is None

    def test_has_subraces_true(self, mock_get_connection):
        """has_subraces возвращает True если есть подрасы"""
        with patch('repositories.race_repository.RaceRepository.get_by_name') as mock_get:
            mock_get.return_value = {'id': 1, 'name': 'Эльф'}

            with patch('repositories.race_repository.RaceRepository._fetch_value') as mock_value:
                mock_value.return_value = 3  # есть подрасы

                repo = RaceRepository()
                result = repo.has_subraces('Эльф')

                assert result is True

    def test_has_subraces_false(self, mock_get_connection):
        """has_subraces возвращает False если нет подрас"""
        with patch('repositories.race_repository.RaceRepository.get_by_name') as mock_get:
            mock_get.return_value = {'id': 2, 'name': 'Человек'}

            with patch('repositories.race_repository.RaceRepository._fetch_value') as mock_value:
                mock_value.return_value = 0

                repo = RaceRepository()
                result = repo.has_subraces('Человек')

                assert result is False

    def test_get_subraces(self, mock_get_connection):
        """get_subraces возвращает список подрас"""
        sample_subraces = [
            {'id': 1, 'name': 'Лесной эльф', 'trait': 'Скрытность', 'description': '', 'extra_speed': 0,
             'extra_traits': []},
            {'id': 2, 'name': 'Высший эльф', 'trait': 'Магия', 'description': '', 'extra_speed': 0, 'extra_traits': []},
        ]

        with patch('repositories.race_repository.RaceRepository.get_by_name') as mock_get:
            mock_get.return_value = {'id': 1, 'name': 'Эльф'}

            with patch('repositories.race_repository.RaceRepository._fetch_all') as mock_fetch:
                mock_fetch.return_value = sample_subraces

                repo = RaceRepository()
                result = repo.get_subraces('Эльф')

                assert len(result) == 2
                assert result[0]['name'] == 'Лесной эльф'