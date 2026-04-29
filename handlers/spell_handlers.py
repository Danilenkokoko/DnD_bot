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
from spell_selector import SpellSelector

logger = logging.getLogger(__name__)

router = Router()


# ==================== CANTRIPS ====================

@router.callback_query(lambda c: c.data.startswith("cantrip_cat_"))
async def show_cantrips_in_category(callback: CallbackQuery, state: FSMContext):
    # Удаляем текущее сообщение с категориями, если оно есть, чтобы начать чисто
    # В методе сервиса будет отправлено новое сообщение
    await callback.message.delete()
    await SpellSelectionService.show_cantrips_in_category(callback, state)


@router.callback_query(lambda c: c.data.startswith("cantrip_view_"))
async def view_cantrip_detail(callback: CallbackQuery, state: FSMContext):
    # Не удаляем, а редактируем (показываем детали) — это нормально
    await SpellSelectionService.view_cantrip_detail(callback, state)


@router.callback_query(lambda c: c.data.startswith("cantrip_add_"))
async def add_cantrip(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.add_cantrip(callback, state)


@router.callback_query(lambda c: c.data.startswith("cantrip_remove_"))
async def remove_cantrip(callback: CallbackQuery, state: FSMContext):
    await SpellSelectionService.remove_cantrip(callback, state)


@router.callback_query(lambda c: c.data == "cantrip_back_list")
async def back_to_cantrip_list(callback: CallbackQuery, state: FSMContext):
    # Возврат к списку заклинаний в категории – обычно редактируем текущее сообщение,
    # но для надёжности удалим и отправим новое (или доверимся сервису)
    await callback.message.delete()
    await SpellSelectionService.back_to_cantrip_list(callback, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "cantrip_back_categories")
async def back_to_cantrip_categories(callback: CallbackQuery, state: FSMContext):
    # При возврате к категориям удаляем текущее сообщение (список заклинаний)
    await callback.message.delete()
    await SpellSelectionService.back_to_cantrip_categories(callback, state)
    await callback.answer()


# ==================== LEVEL 1 SPELLS ====================

@router.callback_query(lambda c: c.data.startswith("level1_cat_"))
async def show_level1_in_category(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
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
    await callback.message.delete()
    await SpellSelectionService.back_to_level1_list(callback, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "level1_back_categories")
async def back_to_level1_categories(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await SpellSelectionService.back_to_level1_categories(callback, state)
    await callback.answer()


# ==================== CONTINUE BUTTON ====================

@router.message(F.text == "✅ Продолжить")
async def continue_after_spells(message: Message, state: FSMContext):
    """Обработчик кнопки 'Продолжить' после выбора заклинаний"""
    logger.info("🔵 Кнопка 'Продолжить' нажата")
    await message.delete()   # удаляем сообщение с кнопкой

    current_state = await state.get_state()
    logger.info(f"Текущее состояние FSM: {current_state}")

    data = await state.get_data()
    selector_data = data.get("spell_selector")

    if selector_data:
        selector = SpellSelector.from_dict(selector_data)

        if selector.cantrip_state and selector.cantrip_state.remaining_count != 0:
            await message.answer("⚠️ Вы не выбрали все заговоры. Пожалуйста, завершите выбор.")
            return

        if selector.level1_state and selector.level1_state.remaining_count != 0:
            logger.info("Переход к выбору заклинаний 1 уровня")
            await SpellSelectionService.start_level1_selection(message, state)
            return

        logger.info("Все заклинания выбраны, переход к боевому стилю")
        await go_to_fighting_style(message, state)
        return

    logger.info("Нет данных о заклинаниях, переход к боевому стилю")
    await go_to_fighting_style(message, state)