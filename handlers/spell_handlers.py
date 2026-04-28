# handlers/spell_handlers.py
"""
Обработчики для выбора заклинаний (кантрипов и 1 уровня)
"""

import logging
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from states.character_states import CreateCharacter
from services.spell_service import SpellSelectionService

logger = logging.getLogger(__name__)

router = Router()


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


@router.callback_query(lambda c: c.data.startswith("cantrip_back_list"))
async def back_to_cantrip_list(callback: CallbackQuery, state: FSMContext):
    # Реализуйте при необходимости
    await callback.answer("Возврат к списку заклинаний (реализуйте)")
    # Лучше перенести логику из SpellSelectionService
    # Для простоты можно вызвать соответствующий метод сервиса, но его пока нет.
    # Рекомендуется дописать метод в SpellSelectionService и вызвать его.
    # Пока что просто заглушка.
    await callback.message.answer("Функция в разработке")


@router.callback_query(lambda c: c.data.startswith("cantrip_back_categories"))
async def back_to_cantrip_categories(callback: CallbackQuery, state: FSMContext):
    # Вернуться к выбору категорий заговоров
    from services.spell_service import SpellSelectionService
    await SpellSelectionService.start_cantrips_selection(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("level1_cat_"))
async def show_level1_in_category(callback: CallbackQuery, state: FSMContext):
    # Аналогично для заклинаний 1 уровня (допишите, если нужно)
    await callback.answer("Выбор заклинаний 1 уровня (в разработке)")


@router.callback_query(lambda c: c.data == "cancel_creation")
async def cancel_creation_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Создание персонажа отменено")
    await callback.answer()