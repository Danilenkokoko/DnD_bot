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

# Импорт строковых констант
from strings import (
    CANTRIP_SELECTION_START, CANTRIP_CATEGORY_EMPTY, CANTRIP_LIST_TITLE,
    CANTRIP_DETAIL_TEMPLATE, CANTRIP_STATUS_SELECTED, CANTRIP_STATUS_NOT_SELECTED,
    LEVEL1_SPELL_SELECTION_START, LEVEL1_CATEGORY_EMPTY, LEVEL1_LIST_TITLE,
    LEVEL1_DETAIL_TEMPLATE, LEVEL1_STATUS_SELECTED, LEVEL1_STATUS_NOT_SELECTED
)

from utils.message_utils import send_new_from_callback, delete_previous, send_new

logger = logging.getLogger(__name__)

_spell_repo = SpellRepository()
_class_repo = ClassRepository()


class SpellSelectionService:
    """Сервис управления выбором заклинаний"""

    @staticmethod
    async def _ensure_selector(state: FSMContext, class_name: str = None) -> Optional[SpellSelector]:
        """Гарантирует наличие селектора в состоянии. Возвращает селектор или None."""
        data = await state.get_data()
        selector_data = data.get("spell_selector")
        if not selector_data:
            if not class_name:
                class_name = data.get("class_name")
            if not class_name:
                logger.error("Не удалось определить class_name для создания селектора")
                return None
            selector = SpellSelector(class_name)
            await state.update_data(spell_selector=selector.to_dict())
            logger.info(f"Создан новый SpellSelector для класса {class_name}")
            return selector
        return SpellSelector.from_dict(selector_data)

    # ========== ЗАГОВОРЫ (CANTRIPS) ==========
    @staticmethod
    async def start_cantrips_selection(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        class_name = data.get("class_name")
        class_info = _class_repo.get_by_name(class_name)
        is_spellcaster = class_info.get('is_spellcaster', False) if class_info else False
        if not is_spellcaster:
            from handlers.character_handlers import go_to_fighting_style
            await go_to_fighting_style(callback, state)
            return

        # Автоматические заклинания / модификации количества
        auto_cantrips = []
        auto_level1 = []
        extra_cantrips = 0
        if class_name == "Артефактор":
            auto_cantrips.append("Починка")
        elif class_name == "Друид":
            auto_level1.append("Разговор с животными")
            druid_order = data.get("druid_order")
            if druid_order == "guide":
                extra_cantrips = 1
        elif class_name == "Жрец":
            cleric_order = data.get("cleric_order")
            if cleric_order == "miracle":
                extra_cantrips = 1
        elif class_name == "Следопыт":
            auto_level1.append("Метка охотника")

        spell_counts = _class_repo.get_spell_counts(class_name)
        base_cantrips = spell_counts.get('cantrips', 0)
        base_level1 = spell_counts.get('level1', 0)
        if class_name == "Волшебник":
            base_level1 = 6
        cantrips_required = base_cantrips + extra_cantrips
        level1_required = base_level1

        if cantrips_required == 0 and level1_required == 0:
            from handlers.character_handlers import go_to_fighting_style
            await go_to_fighting_style(callback, state)
            return
        if cantrips_required == 0 and level1_required > 0:
            await SpellSelectionService.start_level1_selection(callback, state)
            return

        # Сохраняем авто-списки в state
        await state.update_data(auto_cantrips=auto_cantrips, auto_level1=auto_level1)

        # Создаём селектор
        selector = await SpellSelectionService._ensure_selector(state, class_name)
        if not selector:
            await callback.answer("❌ Ошибка инициализации выбора заклинаний", show_alert=True)
            return
        selector.cantrip_state.required_count = cantrips_required
        await state.update_data(spell_selector=selector.to_dict())

        categories = selector.get_cantrip_categories()
        selected_count, required = selector.get_cantrip_progress()
        if not categories:
            from handlers.character_handlers import go_to_fighting_style
            await go_to_fighting_style(callback, state)
            return

        await state.set_state(CreateCharacter.spells_cantrips_category)
        text = CANTRIP_SELECTION_START.format(
            class_name=selector.class_name,
            required=required,
            remaining=required - selected_count
        )
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_category_keyboard(categories, "cantrip", selected_count, required))
        await callback.answer()

    @staticmethod
    async def show_cantrips_in_category(callback: CallbackQuery, state: FSMContext) -> None:
        category = callback.data.replace("cantrip_cat_", "")
        selector = await SpellSelectionService._ensure_selector(state)
        if not selector:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        data = await state.get_data()
        auto_cantrips = data.get("auto_cantrips", [])
        spells = selector.get_cantrips_in_category(category)
        spells = [s for s in spells if s['name'] not in auto_cantrips]
        selected_spells = selector.get_selected_cantrips()
        await state.update_data(current_category=category)
        await state.set_state(CreateCharacter.spells_cantrips_list)
        if not spells:
            text = CANTRIP_CATEGORY_EMPTY.format(category=category)
            await send_new_from_callback(callback, state, text)
            await callback.answer()
            return
        text = CANTRIP_LIST_TITLE.format(category=category)
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
        selector = await SpellSelectionService._ensure_selector(state)
        if not selector:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        is_selected = spell['name'] in selector.get_selected_cantrips()
        remaining = selector.cantrip_state.remaining_count if selector.cantrip_state else 0
        await state.update_data(current_spell_id=spell_id, current_spell_name=spell['name'])
        await state.set_state(CreateCharacter.spells_cantrips_detail)
        description = spell.get('description', 'Описание отсутствует')
        category = spell.get('category', 'Прочее')
        icon = get_category_icon(category)
        status = CANTRIP_STATUS_SELECTED if is_selected else CANTRIP_STATUS_NOT_SELECTED
        text = CANTRIP_DETAIL_TEMPLATE.format(
            icon=icon,
            spell_name=spell['name'],
            description=description,
            category=category,
            status=status
        )
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_spell_detail_keyboard(spell_id, spell['name'], "cantrip", is_selected, remaining))
        await callback.answer()

    @staticmethod
    async def add_cantrip(callback: CallbackQuery, state: FSMContext) -> None:
        selector = await SpellSelectionService._ensure_selector(state)
        if not selector:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        data = await state.get_data()
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
                auto_cantrips = data.get("auto_cantrips", [])
                spells = selector.get_cantrips_in_category(category)
                spells = [s for s in spells if s['name'] not in auto_cantrips]
                selected_spells = selector.get_selected_cantrips()
                text = CANTRIP_LIST_TITLE.format(category=category)
                await send_new_from_callback(callback, state, text,
                                             reply_markup=create_spell_list_keyboard(spells, "cantrip", selected_spells, category))
        await callback.answer()

    @staticmethod
    async def remove_cantrip(callback: CallbackQuery, state: FSMContext) -> None:
        selector = await SpellSelectionService._ensure_selector(state)
        if not selector:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        data = await state.get_data()
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
            auto_cantrips = data.get("auto_cantrips", [])
            spells = selector.get_cantrips_in_category(category)
            spells = [s for s in spells if s['name'] not in auto_cantrips]
            selected_spells = selector.get_selected_cantrips()
            text = CANTRIP_LIST_TITLE.format(category=category)
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
        selector = await SpellSelectionService._ensure_selector(state)
        if not selector:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        auto_cantrips = data.get("auto_cantrips", [])
        spells = selector.get_cantrips_in_category(category)
        spells = [s for s in spells if s['name'] not in auto_cantrips]
        selected_spells = selector.get_selected_cantrips()
        text = CANTRIP_LIST_TITLE.format(category=category)
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_spell_list_keyboard(spells, "cantrip", selected_spells, category))
        await callback.answer()

    # ========== ЗАКЛИНАНИЯ 1 УРОВНЯ ==========
    @staticmethod
    async def start_level1_selection(callback: CallbackQuery, state: FSMContext) -> None:
        data = await state.get_data()
        class_name = data.get("class_name")
        selector = await SpellSelectionService._ensure_selector(state, class_name)
        if not selector:
            await callback.answer("❌ Ошибка инициализации выбора заклинаний", show_alert=True)
            return
        auto_level1 = data.get("auto_level1", [])
        for spell in auto_level1:
            if spell not in selector.get_selected_level1_spells():
                selector.add_level1_spell(spell)
        await state.update_data(spell_selector=selector.to_dict())
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
        text = LEVEL1_SPELL_SELECTION_START.format(
            class_name=selector.class_name,
            required=required,
            remaining=required - selected_count
        )
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_category_keyboard(categories, "level1", selected_count, required))
        await callback.answer()

    @staticmethod
    async def show_level1_in_category(callback: CallbackQuery, state: FSMContext) -> None:
        category = callback.data.replace("level1_cat_", "")
        selector = await SpellSelectionService._ensure_selector(state)
        if not selector:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        data = await state.get_data()
        auto_level1 = data.get("auto_level1", [])
        spells = selector.get_level1_spells_in_category(category)
        spells = [s for s in spells if s['name'] not in auto_level1]
        selected_spells = selector.get_selected_level1_spells()
        await state.update_data(current_category=category)
        await state.set_state(CreateCharacter.spells_level1_list)
        if not spells:
            text = LEVEL1_CATEGORY_EMPTY.format(category=category)
            await send_new_from_callback(callback, state, text)
            await callback.answer()
            return
        text = LEVEL1_LIST_TITLE.format(category=category)
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
        selector = await SpellSelectionService._ensure_selector(state)
        if not selector:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        is_selected = spell['name'] in selector.get_selected_level1_spells()
        remaining = selector.level1_state.remaining_count if selector.level1_state else 0
        await state.update_data(current_spell_id=spell_id, current_spell_name=spell['name'])
        await state.set_state(CreateCharacter.spells_level1_detail)
        description = spell.get('description', 'Описание отсутствует')
        category = spell.get('category', 'Прочее')
        icon = get_category_icon(category)
        status = LEVEL1_STATUS_SELECTED if is_selected else LEVEL1_STATUS_NOT_SELECTED
        text = LEVEL1_DETAIL_TEMPLATE.format(
            icon=icon,
            spell_name=spell['name'],
            description=description,
            category=category,
            status=status
        )
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_spell_detail_keyboard(spell_id, spell['name'], "level1", is_selected, remaining))
        await callback.answer()

    @staticmethod
    async def add_level1_spell(callback: CallbackQuery, state: FSMContext) -> None:
        selector = await SpellSelectionService._ensure_selector(state)
        if not selector:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        data = await state.get_data()
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
                from handlers.character_handlers import go_to_fighting_style
                await go_to_fighting_style(callback, state)
            else:
                await state.set_state(CreateCharacter.spells_level1_list)
                auto_level1 = data.get("auto_level1", [])
                spells = selector.get_level1_spells_in_category(category)
                spells = [s for s in spells if s['name'] not in auto_level1]
                selected_spells = selector.get_selected_level1_spells()
                text = LEVEL1_LIST_TITLE.format(category=category)
                await send_new_from_callback(callback, state, text,
                                             reply_markup=create_spell_list_keyboard(spells, "level1", selected_spells, category))
        await callback.answer()

    @staticmethod
    async def remove_level1_spell(callback: CallbackQuery, state: FSMContext) -> None:
        selector = await SpellSelectionService._ensure_selector(state)
        if not selector:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        data = await state.get_data()
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
            auto_level1 = data.get("auto_level1", [])
            spells = selector.get_level1_spells_in_category(category)
            spells = [s for s in spells if s['name'] not in auto_level1]
            selected_spells = selector.get_selected_level1_spells()
            text = LEVEL1_LIST_TITLE.format(category=category)
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
        selector = await SpellSelectionService._ensure_selector(state)
        if not selector:
            await callback.answer("❌ Ошибка: данные о заклинаниях не найдены", show_alert=True)
            return
        auto_level1 = data.get("auto_level1", [])
        spells = selector.get_level1_spells_in_category(category)
        spells = [s for s in spells if s['name'] not in auto_level1]
        selected_spells = selector.get_selected_level1_spells()
        text = LEVEL1_LIST_TITLE.format(category=category)
        await send_new_from_callback(callback, state, text,
                                     reply_markup=create_spell_list_keyboard(spells, "level1", selected_spells, category))
        await callback.answer()