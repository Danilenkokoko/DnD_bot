# services/spell_service.py
"""
Сервис для работы с заклинаниями
Использует репозитории и SpellSelector, с удалением предыдущих сообщений.
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
)
from keyboards.character_keyboards import continue_kb_for_spells
from states.character_states import CreateCharacter

# Импортируем вспомогательные функции из character_handlers для удаления и отправки
from utils.message_utils import send_new_from_callback, delete_previous, send_new

logger = logging.getLogger(__name__)

_spell_repo = SpellRepository()
_class_repo = ClassRepository()


class SpellSelectionService:
    """Сервис управления выбором заклинаний"""

    # ========== ЗАГОВОРЫ (CANTRIPS) ==========
    @staticmethod
    async def start_cantrips_selection(callback: CallbackQuery, state: FSMContext) -> None:
        """Начинает выбор заговоров (вызывается из character_handlers после класса)"""
        data = await state.get_data()
        selector_data = data.get("spell_selector")
        class_name = data.get("class_name")

        class_info = _class_repo.get_by_name(class_name)
        is_spellcaster = class_info.get('is_spellcaster', False) if class_info else False
        spell_counts = _class_repo.get_spell_counts(class_name)
        has_cantrips = spell_counts.get('cantrips', 0) > 0
        has_level1 = spell_counts.get('level1', 0) > 0

        if not is_spellcaster:
            from handlers.character_handlers import go_to_fighting_style
            await go_to_fighting_style(callback, state)
            return

        if not has_cantrips and has_level1:
            await SpellSelectionService.start_level1_selection(callback, state)
            return

        if not has_cantrips and not has_level1:
            from handlers.character_handlers import go_to_fighting_style
            await go_to_fighting_style(callback, state)
            return

        if not selector_data:
            selector = SpellSelector(class_name)
            await state.update_data(spell_selector=selector.to_dict())
        else:
            selector = SpellSelector.from_dict(selector_data)

        if not selector.has_cantrips:
            await SpellSelectionService.start_level1_selection(callback, state)
            return

        categories = selector.get_cantrip_categories()
        selected_count, required = selector.get_cantrip_progress()

        if not categories:
            from handlers.character_handlers import go_to_fighting_style
            await go_to_fighting_style(callback, state)
            return

        await state.set_state(CreateCharacter.spells_cantrips_category)
        text = (f"📖 Выбор заговоров\n\n"
                f"Класс {selector.class_name} может выбрать {required} заговор(а).\n"
                f"Осталось выбрать: {required - selected_count}\n\n"
                f"Выбери категорию для просмотра заговоров:")
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_category_keyboard(categories, "cantrip", selected_count, required))
        await callback.answer()

    @staticmethod
    async def show_cantrips_in_category(callback: CallbackQuery, state: FSMContext) -> None:
        category = callback.data.replace("cantrip_cat_", "")
        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        if not selector_data:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        selector = SpellSelector.from_dict(selector_data)

        spells = selector.get_cantrips_in_category(category)
        selected_spells = selector.get_selected_cantrips()
        await state.update_data(current_category=category)
        await state.set_state(CreateCharacter.spells_cantrips_list)

        if not spells:
            await send_new_from_callback(callback, state, f"📖 В категории {category} нет заговоров для этого класса.")
            await callback.answer()
            return

        text = f"📖 Категория: {category}\n\nВыбери заговор для просмотра:"
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_spell_list_keyboard(spells, "cantrip", selected_spells, category))
        await callback.answer()

    @staticmethod
    async def view_cantrip_detail(callback: CallbackQuery, state: FSMContext) -> None:
        spell_id = int(callback.data.replace("cantrip_view_", ""))
        spell = _spell_repo.get_by_id(spell_id)
        if not spell:
            await callback.answer("❌ Заговор не найден")
            return

        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        if not selector_data:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        selector = SpellSelector.from_dict(selector_data)

        is_selected = spell['name'] in selector.get_selected_cantrips()
        remaining = selector.cantrip_state.remaining_count if selector.cantrip_state else 0

        await state.update_data(current_spell_id=spell_id, current_spell_name=spell['name'])
        await state.set_state(CreateCharacter.spells_cantrips_detail)

        description = spell.get('description', 'Описание отсутствует')
        category = spell.get('category', 'Прочее')
        icon = get_category_icon(category)

        text = (f"{icon} {spell['name']}\n\n📖 Описание:\n{description}\n\n"
                f"🏷️ Категория: {category}\n"
                f"📊 Уровень: {spell.get('level', 0)} (заговор)\n\n"
                f"{'✅ Уже выбран' if is_selected else '❌ Не выбран'}")
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_spell_detail_keyboard(spell_id, spell['name'], "cantrip", is_selected, remaining))
        await callback.answer()

    @staticmethod
    async def add_cantrip(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        if not selector_data:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        selector = SpellSelector.from_dict(selector_data)

        spell_name = data.get("current_spell_name")
        category = data.get("current_category")

        if not spell_name:
            await callback.answer("❌ Ошибка: название заговора не найдено")
            return

        success, msg = selector.add_cantrip(spell_name)
        await callback.answer(msg, show_alert=not success)

        if success:
            await state.update_data(spell_selector=selector.to_dict())

            if selector.cantrip_state and selector.cantrip_state.remaining_count == 0:
                if selector.has_level1_spells:
                    await SpellSelectionService.start_level1_selection(callback, state)
                else:
                    from handlers.character_handlers import go_to_fighting_style
                    await go_to_fighting_style(callback, state)
            else:
                await state.set_state(CreateCharacter.spells_cantrips_list)
                spells = selector.get_cantrips_in_category(category)
                selected_spells = selector.get_selected_cantrips()
                text = f"📖 Категория: {category}\n\nВыбери заговор для просмотра:"
                await send_new_from_callback(callback, state, text,
                                             reply_markup=create_spell_list_keyboard(spells, "cantrip", selected_spells, category))
        await callback.answer()

    @staticmethod
    async def remove_cantrip(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        if not selector_data:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        selector = SpellSelector.from_dict(selector_data)

        spell_name = data.get("current_spell_name")
        category = data.get("current_category")

        if not spell_name:
            await callback.answer("❌ Ошибка: название заговора не найдено")
            return

        success, msg = selector.remove_cantrip(spell_name)
        await callback.answer(msg)

        if success:
            await state.update_data(spell_selector=selector.to_dict())
            await state.set_state(CreateCharacter.spells_cantrips_list)
            spells = selector.get_cantrips_in_category(category)
            selected_spells = selector.get_selected_cantrips()
            text = f"📖 Категория: {category}\n\nВыбери заговор для просмотра:"
            await send_new_from_callback(callback, state, text,
                                         reply_markup=create_spell_list_keyboard(spells, "cantrip", selected_spells, category))
        await callback.answer()

    @staticmethod
    async def back_to_cantrip_categories(callback: CallbackQuery, state: FSMContext) -> None:
        await SpellSelectionService.start_cantrips_selection(callback, state)
        await callback.answer()

    @staticmethod
    async def back_to_cantrip_list(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        category = data.get("current_category")
        if not category:
            await SpellSelectionService.start_cantrips_selection(callback, state)
            return

        await state.set_state(CreateCharacter.spells_cantrips_list)
        selector_data = data.get("spell_selector", {})
        if not selector_data:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        selector = SpellSelector.from_dict(selector_data)
        spells = selector.get_cantrips_in_category(category)
        selected_spells = selector.get_selected_cantrips()
        text = f"📖 Категория: {category}\n\nВыбери заговор для просмотра:"
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_spell_list_keyboard(spells, "cantrip", selected_spells, category))
        await callback.answer()

    # ========== ЗАКЛИНАНИЯ 1 УРОВНЯ ==========
    @staticmethod
    async def start_level1_selection(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        selector_data = data.get("spell_selector")
        class_name = data.get("class_name")

        if not selector_data:
            selector = SpellSelector(class_name)
            await state.update_data(spell_selector=selector.to_dict())
        else:
            selector = SpellSelector.from_dict(selector_data)

        if not selector.has_level1_spells:
            from handlers.character_handlers import go_to_fighting_style
            await go_to_fighting_style(callback, state)
            return

        categories = selector.get_level1_categories()
        selected_count, required = selector.get_level1_progress()

        if not categories:
            from handlers.character_handlers import go_to_fighting_style
            await go_to_fighting_style(callback, state)
            return

        await state.set_state(CreateCharacter.spells_level1_category)
        text = (f"🔮 Выбор заклинаний 1 уровня\n\n"
                f"Класс {selector.class_name} может выбрать {required} заклинание(й).\n"
                f"Осталось выбрать: {required - selected_count}\n\n"
                f"Выбери категорию для просмотра заклинаний:")
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_category_keyboard(categories, "level1", selected_count, required))
        await callback.answer()

    @staticmethod
    async def show_level1_in_category(callback: CallbackQuery, state: FSMContext) -> None:
        category = callback.data.replace("level1_cat_", "")
        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        selector = SpellSelector.from_dict(selector_data)

        spells = selector.get_level1_spells_in_category(category)
        selected_spells = selector.get_selected_level1_spells()
        await state.update_data(current_category=category)
        await state.set_state(CreateCharacter.spells_level1_list)

        if not spells:
            await send_new_from_callback(callback, state, f"🔮 В категории {category} нет заклинаний 1 уровня для этого класса.")
            await callback.answer()
            return

        text = f"🔮 Категория: {category}\n\nВыбери заклинание для просмотра:"
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_spell_list_keyboard(spells, "level1", selected_spells, category))
        await callback.answer()

    @staticmethod
    async def view_level1_detail(callback: CallbackQuery, state: FSMContext) -> None:
        spell_id = int(callback.data.replace("level1_view_", ""))
        spell = _spell_repo.get_by_id(spell_id)
        if not spell:
            await callback.answer("❌ Заклинание не найдено")
            return

        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        selector = SpellSelector.from_dict(selector_data)

        is_selected = spell['name'] in selector.get_selected_level1_spells()
        remaining = selector.level1_state.remaining_count if selector.level1_state else 0

        await state.update_data(current_spell_id=spell_id, current_spell_name=spell['name'])
        await state.set_state(CreateCharacter.spells_level1_detail)

        description = spell.get('description', 'Описание отсутствует')
        category = spell.get('category', 'Прочее')
        icon = get_category_icon(category)

        text = (f"{icon} {spell['name']}\n\n📖 Описание:\n{description}\n\n"
                f"🏷️ Категория: {category}\n"
                f"📊 Уровень: {spell.get('level', 1)}\n\n"
                f"{'✅ Уже выбрано' if is_selected else '❌ Не выбрано'}")
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_spell_detail_keyboard(spell_id, spell['name'], "level1", is_selected, remaining))
        await callback.answer()

    @staticmethod
    async def add_level1_spell(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        selector = SpellSelector.from_dict(selector_data)

        spell_name = data.get("current_spell_name")
        category = data.get("current_category")

        if not spell_name:
            await callback.answer("❌ Ошибка: название заклинания не найдено")
            return

        success, msg = selector.add_level1_spell(spell_name)
        await callback.answer(msg, show_alert=not success)

        if success:
            await state.update_data(spell_selector=selector.to_dict())

            if selector.level1_state and selector.level1_state.remaining_count == 0:
                # Все заклинания выбраны → переходим к боевому стилю
                from handlers.character_handlers import go_to_fighting_style
                await go_to_fighting_style(callback, state)
            else:
                await state.set_state(CreateCharacter.spells_level1_list)
                spells = selector.get_level1_spells_in_category(category)
                selected_spells = selector.get_selected_level1_spells()
                text = f"🔮 Категория: {category}\n\nВыбери заклинание для просмотра:"
                await send_new_from_callback(callback, state, text,
                                             reply_markup=create_spell_list_keyboard(spells, "level1", selected_spells, category))
        await callback.answer()

    @staticmethod
    async def remove_level1_spell(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        selector_data = data.get("spell_selector", {})
        selector = SpellSelector.from_dict(selector_data)

        spell_name = data.get("current_spell_name")
        category = data.get("current_category")

        if not spell_name:
            await callback.answer("❌ Ошибка: название заклинания не найдено")
            return

        success, msg = selector.remove_level1_spell(spell_name)
        await callback.answer(msg)

        if success:
            await state.update_data(spell_selector=selector.to_dict())
            await state.set_state(CreateCharacter.spells_level1_list)
            spells = selector.get_level1_spells_in_category(category)
            selected_spells = selector.get_selected_level1_spells()
            text = f"🔮 Категория: {category}\n\nВыбери заклинание для просмотра:"
            await send_new_from_callback(callback, state, text,
                                         reply_markup=create_spell_list_keyboard(spells, "level1", selected_spells, category))
        await callback.answer()

    @staticmethod
    async def back_to_level1_categories(callback: CallbackQuery, state: FSMContext) -> None:
        await SpellSelectionService.start_level1_selection(callback, state)
        await callback.answer()

    @staticmethod
    async def back_to_level1_list(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        category = data.get("current_category")
        if not category:
            await SpellSelectionService.start_level1_selection(callback, state)
            return

        await state.set_state(CreateCharacter.spells_level1_list)
        selector_data = data.get("spell_selector", {})
        selector = SpellSelector.from_dict(selector_data)
        spells = selector.get_level1_spells_in_category(category)
        selected_spells = selector.get_selected_level1_spells()
        text = f"🔮 Категория: {category}\n\nВыбери заклинание для просмотра:"
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_spell_list_keyboard(spells, "level1", selected_spells, category))
        await callback.answer()