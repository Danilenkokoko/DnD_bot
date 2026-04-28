# repositories/__init__.py
"""
Репозитории для доступа к базе данных
"""

from repositories.base_repository import BaseRepository
from repositories.race_repository import RaceRepository
from repositories.class_repository import ClassRepository
from repositories.background_repository import BackgroundRepository
from repositories.equipment_repository import (
    EquipmentRepository,
    FightingStyleRepository,
    InvocationRepository
)
from repositories.spell_repository import (
    SpellRepository,
    ClassSpellLinkRepository
)
from repositories.character_repository import CharacterRepository

__all__ = [
    'BaseRepository',
    'RaceRepository',
    'ClassRepository',
    'BackgroundRepository',
    'EquipmentRepository',
    'FightingStyleRepository',
    'InvocationRepository',
    'SpellRepository',
    'ClassSpellLinkRepository',
    'CharacterRepository',
]