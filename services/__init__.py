# services/__init__.py
"""
Сервисы для бизнес-логики бота
"""

from services.character_service import CharacterStatsService, CharacterFinalizationService
from services.progression_service import ProgressionService
from services.spell_service import SpellSelectionService

__all__ = [
    'CharacterStatsService',
    'CharacterFinalizationService',
    'ProgressionService',
    'SpellSelectionService',
]