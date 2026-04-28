# tests/repositories/test_class_repository.py
"""Тесты для ClassRepository"""

import pytest
from repositories.class_repository import ClassRepository


class TestClassRepository:
    """Тесты репозитория классов"""

    def test_get_all_names(self, mock_get_connection):
        """get_all_names возвращает список названий классов"""
        with patch('repositories.class_repository.ClassRepository._fetch_all') as mock_fetch:
            mock_fetch.return_value = [{'name': 'Воин'}, {'name': 'Волшебник'}]

            repo = ClassRepository()
            result = repo.get_all_names()

            assert result == ['Воин', 'Волшебник']

    def test_get_by_name_found(self, mock_get_connection, sample_class_data):
        """get_by_name возвращает данные класса"""
        with patch('repositories.class_repository.ClassRepository._fetch_one') as mock_fetch:
            mock_fetch.return_value = sample_class_data

            repo = ClassRepository()
            result = repo.get_by_name('Воин')

            assert result is not None
            assert result['name'] == 'Воин'
            assert result['hit_die'] == 10

    def test_get_primary_stats(self, mock_get_connection, sample_class_data):
        """get_primary_stats возвращает список основных характеристик"""
        with patch('repositories.class_repository.ClassRepository.get_by_name') as mock_get:
            mock_get.return_value = sample_class_data

            repo = ClassRepository()
            result = repo.get_primary_stats('Воин')

            assert result == ['STR', 'DEX']

    def test_get_hit_die(self, mock_get_connection, sample_class_data):
        """get_hit_die возвращает хитовый кубик"""
        with patch('repositories.class_repository.ClassRepository.get_by_name') as mock_get:
            mock_get.return_value = sample_class_data

            repo = ClassRepository()
            result = repo.get_hit_die('Воин')

            assert result == 10

    def test_get_spell_counts_spellcaster(self, mock_get_connection):
        """get_spell_counts для заклинателя"""
        class_data = {
            'id': 2,
            'name': 'Волшебник',
            'cantrips_count': 3,
            'spells_count_level1': 4
        }

        with patch('repositories.class_repository.ClassRepository.get_by_name') as mock_get:
            mock_get.return_value = class_data

            repo = ClassRepository()
            result = repo.get_spell_counts('Волшебник')

            assert result['cantrips'] == 3
            assert result['level1'] == 4

    def test_get_masteries_count(self, mock_get_connection, sample_class_data):
        """get_masteries_count возвращает количество приёмов"""
        with patch('repositories.class_repository.ClassRepository.get_by_name') as mock_get:
            mock_get.return_value = sample_class_data

            repo = ClassRepository()
            result = repo.get_masteries_count('Воин')

            assert result == 3