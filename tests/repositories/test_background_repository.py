# tests/repositories/test_background_repository.py
"""Тесты для BackgroundRepository"""

import pytest
from repositories.background_repository import BackgroundRepository


class TestBackgroundRepository:
    """Тесты репозитория предысторий"""

    def test_get_all_names(self, mock_get_connection):
        """get_all_names возвращает список названий"""
        with patch('repositories.background_repository.BackgroundRepository._fetch_all') as mock_fetch:
            mock_fetch.return_value = [{'name': 'Солдат'}, {'name': 'Мудрец'}]

            repo = BackgroundRepository()
            result = repo.get_all_names()

            assert result == ['Солдат', 'Мудрец']

    def test_get_by_name_found(self, mock_get_connection, sample_background_data):
        """get_by_name возвращает данные предыстории"""
        with patch('repositories.background_repository.BackgroundRepository._fetch_one') as mock_fetch:
            mock_fetch.return_value = sample_background_data

            repo = BackgroundRepository()
            result = repo.get_by_name('Солдат')

            assert result is not None
            assert result['name'] == 'Солдат'
            assert result['characteristics'] == ['STR', 'DEX', 'CON']

    def test_get_characteristics(self, mock_get_connection, sample_background_data):
        """get_characteristics возвращает список характеристик"""
        with patch('repositories.background_repository.BackgroundRepository.get_by_name') as mock_get:
            mock_get.return_value = {
                'name': 'Солдат',
                'characteristics': ['STR', 'DEX', 'CON']
            }

            repo = BackgroundRepository()
            result = repo.get_characteristics('Солдат')

            assert result == ['STR', 'DEX', 'CON']

    def test_get_trait(self, mock_get_connection, sample_background_data):
        """get_trait возвращает черту предыстории"""
        with patch('repositories.background_repository.BackgroundRepository.get_by_name') as mock_get:
            mock_get.return_value = {'trait': 'Бдительный'}

            repo = BackgroundRepository()
            result = repo.get_trait('Солдат')

            assert result == 'Бдительный'

    def test_get_equipment_choice_a(self, mock_get_connection, sample_background_data):
        """get_equipment_choice возвращает вариант А"""
        with patch('repositories.background_repository.BackgroundRepository.get_by_name') as mock_get:
            mock_get.return_value = {
                'equipment_a': 'Копьё, Лёгкий арбалет, 20 Болтов',
                'equipment_b': '50 ЗМ'
            }

            repo = BackgroundRepository()
            result = repo.get_equipment_choice('Солдат', 'A')

            assert 'Копьё' in result
            assert '50 ЗМ' not in result