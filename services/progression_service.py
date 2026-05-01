# services/progression_service.py
"""
Сервис управления порядком шагов создания персонажа
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message
    from aiogram.fsm.context import FSMContext

from repositories.class_repository import ClassRepository

logger = logging.getLogger(__name__)

_class_repo = ClassRepository()


class ProgressionService:
    """Определяет следующий шаг в создании персонажа"""

    @staticmethod
    def is_spellcaster(class_name: str) -> bool:
        """Проверяет, является ли класс заклинателем на 1 уровне"""
        return _class_repo.is_spellcaster(class_name)

    @staticmethod
    def should_select_fighting_style(class_name: str) -> bool:
        """
        Проверяет, нужно ли выбирать боевой стиль.
        В D&D 5.5e (2024) боевой стиль на 1 уровне получают только:
        - Воин
        - Паладин
        - Следопыт
        """
        return class_name in ["Воин", "Паладин", "Следопыт"]

    @staticmethod
    async def go_to_spells(message: "Message", state: "FSMContext") -> None:
        """Переход к выбору заклинаний"""
        from services.spell_service import SpellSelectionService
        await SpellSelectionService.start_cantrips_selection(message, state)

    @staticmethod
    async def go_to_fighting_style(message: "Message", state: "FSMContext") -> None:
        """Переход к выбору боевого стиля (заглушка)"""
        from services.character_service import CharacterStatsService
        data = await state.get_data()
        class_name = data.get("class_name")
        if ProgressionService.should_select_fighting_style(class_name):
            styles = CharacterStatsService.get_fighting_styles_for_class(class_name)
            if not styles:
                await message.answer(f"⚠️ Для класса {class_name} нет доступных боевых стилей.\n\nПереходим к следующему шагу...")
                await ProgressionService.go_to_background(message, state)
                return
            # Здесь должен быть вызов создания клавиатуры и установки состояния
            await message.answer(f"⚔️ Выберите боевой стиль для {class_name}")
        else:
            await ProgressionService.go_to_background(message, state)

    @staticmethod
    async def go_to_background(message: "Message", state: "FSMContext") -> None:
        """Переход к выбору предыстории"""
        from handlers.character_handlers import go_to_background as _go_to_background
        await _go_to_background(message, state)