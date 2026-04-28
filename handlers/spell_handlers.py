# handlers/spell_handlers.py
"""
Обработчики для выбора заклинаний (кантрипов и 1 уровня)
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from states.character_states import CreateCharacter
from services.spell_service import SpellSelectionService
from handlers.character_handlers import go_to_fighting_style

logger = logging.getLogger(__name__)

router = Router()


# ==================== CANTRIPS ====================

@router.callback_query(lambda c: c.data.startswith("cantrip_cat_"))
async def show_cantrips_in_category(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.show_cantrips_in_category(callback, state)


@router.callback_query(lambda c: c.data.startswith("cantrip_view_"))
async def view_cantrip_detail(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.view_cantrip_detail(callback, state)


@router.callback_query(lambda c: c.data.startswith("cantrip_add_"))
async def add_cantrip(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.add_cantrip(callback, state)


@router.callback_query(lambda c: c.data.startswith("cantrip_remove_"))
async def remove_cantrip(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.remove_cantrip(callback, state)


@router.callback_query(lambda c: c.data == "cantrip_back_list")
async def back_to_cantrip_list(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.back_to_cantrip_list(callback, state)


@router.callback_query(lambda c: c.data == "cantrip_back_categories")
async def back_to_cantrip_categories(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.back_to_cantrip_categories(callback, state)


# ==================== LEVEL 1 SPELLS ====================

@router.callback_query(lambda c: c.data.startswith("level1_cat_"))
async def show_level1_in_category(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.show_level1_in_category(callback, state)


@router.callback_query(lambda c: c.data.startswith("level1_view_"))
async def view_level1_detail(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.view_level1_detail(callback, state)


@router.callback_query(lambda c: c.data.startswith("level1_add_"))
async def add_level1_spell(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.add_level1_spell(callback, state)


@router.callback_query(lambda c: c.data.startswith("level1_remove_"))
async def remove_level1_spell(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.remove_level1_spell(callback, state)


@router.callback_query(lambda c: c.data == "level1_back_list")
async def back_to_level1_list(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.back_to_level1_list(callback, state)


@router.callback_query(lambda c: c.data == "level1_back_categories")
async def back_to_level1_categories(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.back_to_level1_categories(callback, state)


# ==================== CONTINUE BUTTON ====================

@router.message(F.text == "✅ Продолжить")
async def continue_after_spells(message: Message, state: FSMContext):
    """Обработчик кнопки 'Продолжить' после выбора заклинаний"""
    current_state = await state.get_state()
    if current_state == CreateCharacter.spells_cantrips_complete.state:
        await SpellSelectionService.start_level1_selection(message, state)
    elif current_state == CreateCharacter.spells_level1_complete.state:
        await go_to_fighting_style(message, state)
    else:
        await message.answer("⏳ Пожалуйста, следуйте инструкциям.")