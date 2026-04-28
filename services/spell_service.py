# services/spell_service.py
"""
Сервис для работы с заклинаниями
Использует репозитории и SpellSelector
"""

import logging
from typing import Dict, Any, Optional, Tuple
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from spell_selector import SpellSelector, get_category_icon
from repositories.spell_repository import SpellRepository
from repositories.class_repository import ClassRepository
from keyboards.spell_keyboards import (
    create_category_keyboard,
    create_spell_list_keyboard,
    create_spell_detail_keyboard,
    continue_kb_for_spells
)
from states.character_states import CreateCharacter

logger = logging.getLogger(__name__)

_spell_repo = SpellRepository()
_class_repo = ClassRepository()


class SpellSelectionService:
    """Сервис управления выбором заклинаний"""

    @staticmethod
    async def start_cantrips_selection(message: Message, state: FSMContext) -> None:
        """Начало выбора заговоров"""
        data = await state.get_data()
        selector_data = data.get("spell_selector")
        class_name = data.get("class_name")

        # Проверка, является ли класс заклинателем
        class_info = _class_repo.get_by_name(class_name)
        is_spellcaster = class_info.get('is_spellcaster', False) if class_info else False
        spell_counts = _class_repo.get_spell_counts(class_name)
        has_cantrips = spell_counts.get('cantrips', 0) > 0

        if not is_spellcaster or not has_cantrips:
            from services.progression_service import ProgressionService
            await ProgressionService.go_to_fighting_style(message, state)
            return

        if not selector_data:
            selector = SpellSelector(class_name)
            await state.update_data(spell_selector=selector.to_dict())
        else:
            selector = SpellSelector.from_dict(selector_data)

        if not selector.has_cantrips:
            await SpellSelectionService.start_level1_selection(message, state)
            return

        categories = selector.get_cantrip_categories()
        selected_count, required = selector.get_cantrip_progress()

        await state.set_state(CreateCharacter.spells_cantrips_category)
        await message.answer(
            f"📖 **Шаг 3/12: Выбор ЗАГОВОРОВ**\n\n"
            f"Класс **{selector.class_name}** может выбрать {required} заговор(а).\n"
            f"Осталось выбрать: {required - selected_count}\n\n"
            f"Выберите категорию для просмотра заговоров:",
            parse_mode=None,
            reply_markup=create_category_keyboard(categories, "cantrip", selected_count, required)
        )

    @staticmethod
    async def start_level1_selection(message: Message, state: FSMContext) -> None:
        """Начало выбора заклинаний 1 уровня"""
        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        selector = SpellSelector.from_dict(selector_data)

        if not selector.has_level1_spells:
            from services.progression_service import ProgressionService
            await ProgressionService.go_to_fighting_style(message, state)
            return

        categories = selector.get_level1_categories()
        selected_count, required = selector.get_level1_progress()

        await state.set_state(CreateCharacter.spells_level1_category)
        await message.answer(
            f"🔮 **Шаг 4/12: Выбор ЗАКЛИНАНИЙ 1 УРОВНЯ**\n\n"
            f"Класс **{selector.class_name}** может выбрать {required} заклинание(й).\n"
            f"Осталось выбрать: {required - selected_count}\n\n"
            f"Выберите категорию для просмотра заклинаний:",
            parse_mode=None,
            reply_markup=create_category_keyboard(categories, "level1", selected_count, required)
        )

    @staticmethod
    async def show_cantrips_in_category(callback: CallbackQuery, state: FSMContext) -> None:
        """Показать заговоры в категории"""
        category = callback.data.replace("cantrip_cat_", "")
        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        selector = SpellSelector.from_dict(selector_data)
        spells = selector.get_cantrips_in_category(category)
        selected_spells = selector.get_selected_cantrips()
        await state.update_data(current_category=category)
        await state.set_state(CreateCharacter.spells_cantrips_list)
        if not spells:
            await callback.message.edit_text(f"📖 В категории **{category}** нет заговоров для этого класса.")
            return
        await callback.message.edit_text(
            f"📖 **Категория: {category}**\n\nВыберите заговор для просмотра:",
            reply_markup=create_spell_list_keyboard(spells, "cantrip", selected_spells, category)
        )
        await callback.answer()

    @staticmethod
    async def view_cantrip_detail(callback: CallbackQuery, state: FSMContext) -> None:
        """Показать детали заговора"""
        spell_id = int(callback.data.replace("cantrip_view_", ""))
        spell = _spell_repo.get_by_id(spell_id)
        if not spell:
            await callback.answer("❌ Заклинание не найдено")
            return
        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        selector = SpellSelector.from_dict(selector_data)
        is_selected = spell['name'] in selector.get_selected_cantrips()
        remaining = selector.cantrip_state.remaining_count if selector.cantrip_state else 0
        await state.update_data(current_spell_id=spell_id, current_spell_name=spell['name'])
        await state.set_state(CreateCharacter.spells_cantrips_detail)
        description = spell.get('description', 'Описание отсутствует')
        category = spell.get('category', 'Прочее')
        icon = get_category_icon(category)
        await callback.message.edit_text(
            f"{icon} **{spell['name']}**\n\n📖 **Описание:**\n{description}\n\n"
            f"🏷️ **Категория:** {category}\n"
            f"📊 **Уровень:** {'Заговор' if spell.get('is_cantrip') else f'{spell.get('level')} уровень'}\n\n"
            f"{'✅ Уже выбран' if is_selected else '❌ Не выбран'}",
            reply_markup=create_spell_detail_keyboard(spell_id, spell['name'], "cantrip", is_selected, remaining)
        )
        await callback.answer()

    @staticmethod
    async def add_cantrip(callback: CallbackQuery, state: FSMContext) -> None:
        """Добавить заговор"""
        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        selector = SpellSelector.from_dict(selector_data)
        spell_name = data.get("current_spell_name")
        category = data.get("current_category")

        if not spell_name:
            await callback.answer("❌ Ошибка: название заклинания не найдено")
            return
        success, msg = selector.add_cantrip(spell_name)
        await callback.answer(msg, show_alert=not success)
        if success:
            await state.update_data(spell_selector=selector.to_dict())
            if selector.cantrip_state and selector.cantrip_state.remaining_count == 0:
                await callback.message.delete()
                await callback.message.answer(
                    f"✅ **Все заговоры выбраны!**\n\n"
                    f"Выбрано заговоров: {len(selector.get_selected_cantrips())}\n\n"
                    f"Нажмите «Продолжить» для выбора заклинаний 1 уровня.",
                    reply_markup=continue_kb_for_spells()
                )
                await state.set_state(CreateCharacter.spells_cantrips_complete)
            else:
                await state.set_state(CreateCharacter.spells_cantrips_list)
                spells = selector.get_cantrips_in_category(category)
                selected_spells = selector.get_selected_cantrips()
                await callback.message.edit_text(
                    f"📖 **Категория: {category}**\n\nВыберите заговор для просмотра:",
                    reply_markup=create_spell_list_keyboard(spells, "cantrip", selected_spells, category)
                )
        await callback.answer()

    @staticmethod
    async def remove_cantrip(callback: CallbackQuery, state: FSMContext) -> None:
        """Удалить заговор"""
        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        selector = SpellSelector.from_dict(selector_data)
        spell_name = data.get("current_spell_name")
        category = data.get("current_category")

        if not spell_name:
            await callback.answer("❌ Ошибка: название заклинания не найдено")
            return
        success, msg = selector.remove_cantrip(spell_name)
        await callback.answer(msg)
        if success:
            await state.update_data(spell_selector=selector.to_dict())
            await state.set_state(CreateCharacter.spells_cantrips_list)
            spells = selector.get_cantrips_in_category(category)
            selected_spells = selector.get_selected_cantrips()
            await callback.message.edit_text(
                f"📖 **Категория: {category}**\n\nВыберите заговор для просмотра:",
                reply_markup=create_spell_list_keyboard(spells, "cantrip", selected_spells, category)
            )
        await callback.answer()