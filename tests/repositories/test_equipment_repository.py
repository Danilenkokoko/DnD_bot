# tests/repositories/test_equipment_repository.py
"""Тесты для EquipmentRepository, FightingStyleRepository, InvocationRepository"""

import pytest
from repositories.equipment_repository import (
    EquipmentRepository,
    FightingStyleRepository,
    InvocationRepository
)


class TestEquipmentRepository:
    """Тесты репозитория снаряжения"""

    def test_get_class_equipment_with_choice(self, mock_get_connection):
        """get_class_equipment с выбором варианта"""
        sample_equipment = [{
            'class_id': 1,
            'choice': 'A',
            'armor': 'Кольчуга',
            'weapon': 'Длинный меч',
            'secondary_weapon': 'Кинжал',
            'other_items': 'Походный набор',
            'coins': 10
        }]

        with patch('repositories.equipment_repository.EquipmentRepository._get_class_id') as mock_id:
            mock_id.return_value = 1

            with patch('repositories.equipment_repository.EquipmentRepository._fetch_all') as mock_fetch:
                mock_fetch.return_value = sample_equipment

                repo = EquipmentRepository()
                result = repo.get_class_equipment('Воин', 'A')

                assert len(result) == 1
                assert result[0]['weapon'] == 'Длинный меч'

    def test_get_armor_by_name(self, mock_get_connection):
        """get_armor_by_name возвращает броню"""
        armor_data = {
            'id': 1,
            'name': 'Кожаная броня',
            'ac_base': 11,
            'ac_modifier': 'dex',
            'has_shield': False
        }

        with patch('repositories.equipment_repository.EquipmentRepository._fetch_one') as mock_fetch:
            mock_fetch.return_value = armor_data

            repo = EquipmentRepository()
            result = repo.get_armor_by_name('Кожаная броня')

            assert result is not None
            assert result['ac_base'] == 11

    def test_auto_assign_masteries(self, mock_get_connection):
        """auto_assign_masteries выбирает приёмы"""
        masteries = [
            {'name': 'Тяжёлое', 'optimal': True},
            {'name': 'Грейз', 'optimal': False}
        ]

        with patch('repositories.equipment_repository.EquipmentRepository.get_detailed_masteries_for_weapon') as mock_m:
            mock_m.return_value = masteries

            with patch('repositories.equipment_repository.EquipmentRepository._get_class_id') as mock_id:
                mock_id.return_value = 1

                with patch('repositories.class_repository.ClassRepository.get_masteries_count') as mock_count:
                    mock_count.return_value = 1

                    repo = EquipmentRepository()
                    result = repo.auto_assign_masteries('Двуручный меч', 'Воин')

                    assert 'Тяжёлое' in result


class TestFightingStyleRepository:
    """Тесты репозитория боевых стилей"""

    def test_get_all(self, mock_get_connection):
        """get_all возвращает все стили"""
        styles = [
            {'id': 1, 'name': 'Оборона', 'description': '+1 AC'},
            {'id': 2, 'name': 'Дуэлянт', 'description': '+2 урон'}
        ]

        with patch('repositories.equipment_repository.FightingStyleRepository._fetch_all') as mock_fetch:
            mock_fetch.return_value = styles

            repo = FightingStyleRepository()
            result = repo.get_all()

            assert len(result) == 2

    def test_get_for_class(self, mock_get_connection):
        """get_for_class возвращает стили для класса"""
        styles = [{'id': 1, 'name': 'Оборона', 'description': '+1 AC'}]

        with patch('repositories.equipment_repository.FightingStyleRepository._fetch_all') as mock_fetch:
            mock_fetch.return_value = styles

            with patch('repositories.class_repository.ClassRepository.get_by_name') as mock_class:
                mock_class.return_value = {'id': 1}

                repo = FightingStyleRepository()
                result = repo.get_for_class('Воин')

                assert len(result) == 1


class TestInvocationRepository:
    """Тесты репозитория возваний"""

    def test_get_all(self, mock_get_connection):
        """get_all возвращает возвания для уровня"""
        invocations = [
            {'id': 1, 'name': 'Леденящая хватка', 'level_required': 1, 'effect': 'Замедление',
             'requires_pact_boon': False, 'pact_boon_type': None}
        ]

        with patch('repositories.equipment_repository.InvocationRepository._fetch_all') as mock_fetch:
            mock_fetch.return_value = invocations

            repo = InvocationRepository()
            result = repo.get_all(level=1)

            assert len(result) == 1
            assert result[0]['name'] == 'Леденящая хватка'