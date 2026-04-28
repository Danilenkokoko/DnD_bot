# tests/repositories/test_spell_repository.py
"""Тесты для SpellRepository"""

import pytest
from repositories.spell_repository import SpellRepository


class TestSpellRepository:
    """Тесты репозитория заклинаний"""

    def test_get_by_id(self, mock_get_connection):
        """get_by_id возвращает заклинание по ID"""
        spell_data = {
            'id': 1,
            'name': 'Огненный снаряд',
            'description': 'Сгусток огня',
            'level': 0,
            'is_cantrip': True,
            'category': 'Урон',
            'school': 'Вызов'
        }

        with patch('repositories.spell_repository.SpellRepository._fetch_one') as mock_fetch:
            mock_fetch.return_value = spell_data

            repo = SpellRepository()
            result = repo.get_by_id(1)

            assert result is not None
            assert result['name'] == 'Огненный снаряд'

    def test_get_cantrips_for_class(self, mock_get_connection):
        """get_cantrips_for_class возвращает заговоры"""
        cantrips = [
            {'id': 1, 'name': 'Огненный снаряд', 'level': 0, 'is_cantrip': True, 'category': 'Урон', 'description': ''}
        ]

        with patch('repositories.spell_repository.SpellRepository.get_for_class') as mock_get:
            mock_get.return_value = cantrips

            repo = SpellRepository()
            result = repo.get_cantrips_for_class('Волшебник')

            assert len(result) == 1

    def test_get_spells_grouped_by_category(self, mock_get_connection):
        """get_categories_for_class группирует заклинания по категориям"""
        spells = [
            {'id': 1, 'name': 'Огненный снаряд', 'category': 'Урон'},
            {'id': 2, 'name': 'Щит', 'category': 'Защита'}
        ]

        with patch('repositories.spell_repository.SpellRepository.get_for_class') as mock_get:
            mock_get.return_value = spells

            repo = SpellRepository()
            result = repo.get_categories_for_class('Волшебник', is_cantrip=True)

            assert 'Урон' in result
            assert 'Защита' in result
            assert len(result['Урон']) == 1