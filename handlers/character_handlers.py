# handlers/character_handlers.py
"""
Обработчики для создания персонажа
Используют сервисы для бизнес-логики
"""

import logging
import os
import re
import tempfile
from typing import Optional

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, FSInputFile, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from states.character_states import CreateCharacter
from keyboards.character_keyboards import (
    create_class_keyboard,
    create_race_keyboard,
    create_background_keyboard,
    create_character_list_keyboard,
    create_delete_keyboard,
    create_skills_keyboard,
    cancel_kb,
    skip_kb,
    continue_kb_for_spells,
    main_menu
)

from services.character_service import CharacterStatsService, CharacterFinalizationService
from services.progression_service import ProgressionService
from services.spell_service import SpellSelectionService
from repositories.character_repository import CharacterRepository
from repositories.race_repository import RaceRepository
from repositories.class_repository import ClassRepository
from repositories.background_repository import BackgroundRepository
from repositories.equipment_repository import EquipmentRepository, FightingStyleRepository, InvocationRepository
from repositories.spell_repository import SpellRepository

from pdf_generator import generate_pdf  # теперь generate_pdf создаёт HTML-файл
from engine.validators import validate_name as engine_validate_name

logger = logging.getLogger(__name__)

router = Router()

# Репозитории
_race_repo = RaceRepository()
_class_repo = ClassRepository()
_bg_repo = BackgroundRepository()
_equip_repo = EquipmentRepository()
_fighting_repo = FightingStyleRepository()
_inv_repo = InvocationRepository()
_spell_repo = SpellRepository()
_char_repo = CharacterRepository()


# =========================================================
# СОБСТВЕННЫЕ КЛАВИАТУРЫ (БЕЗ КНОПОК "ПРОПУСТИТЬ")
# =========================================================

def _create_subclass_keyboard(class_name: str) -> Optional[InlineKeyboardMarkup]:
    """Клавиатура выбора подкласса (без кнопки пропуска)"""
    from services.character_service import CharacterStatsService
    subclasses = CharacterStatsService.get_subclasses_for_class(class_name, level=1)
    if not subclasses:
        return None
    buttons = []
    for sub in subclasses:
        buttons.append([InlineKeyboardButton(
            text=f"📖 {sub['name']} — {sub['description'][:40]}...",
            callback_data=f"subclass_{sub['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к классам", callback_data="back_to_classes")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _create_subrace_keyboard(race: str) -> Optional[InlineKeyboardMarkup]:
    """Клавиатура выбора подрасы (без кнопки пропуска)"""
    from services.character_service import CharacterStatsService
    subraces = CharacterStatsService.get_subraces(race)
    if not subraces:
        return None
    buttons = []
    for subrace in subraces:
        buttons.append([InlineKeyboardButton(text=subrace, callback_data=f"subrace_{subrace}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к расам", callback_data="back_to_races")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _create_fighting_style_keyboard(class_name: str) -> Optional[InlineKeyboardMarkup]:
    """Клавиатура выбора боевого стиля (без кнопки пропуска)"""
    styles = CharacterStatsService.get_fighting_styles_for_class(class_name)
    if not styles:
        return None
    buttons = []
    for s in styles:
        buttons.append([InlineKeyboardButton(
            text=f"⚔️ {s['name']}",
            callback_data=f"style_{s['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_spells")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _create_invocations_keyboard(level: int = 1, selected_names: list = None) -> Optional[InlineKeyboardMarkup]:
    """Клавиатура выбора возваний с отображением выбранных (без кнопки пропуска)"""
    from services.character_service import CharacterStatsService
    invocations = CharacterStatsService.get_all_invocations(level)
    if not invocations:
        return None
    if selected_names is None:
        selected_names = []
    buttons = []
    for inv in invocations[:12]:
        check = "✅ " if inv['name'] in selected_names else ""
        buttons.append([InlineKeyboardButton(
            text=f"{check}{inv['name']}",
            callback_data=f"inv_{inv['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_fighting")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _create_background_equipment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора снаряжения от предыстории (короткие кнопки)"""
    buttons = [
        [InlineKeyboardButton(text="📦 Вариант А", callback_data="bg_equip_A")],
        [InlineKeyboardButton(text="🎒 Вариант Б", callback_data="bg_equip_B")],
        [InlineKeyboardButton(text="⬅️ Назад к предыстории", callback_data="back_to_background")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# =========================================================
# КОМАНДЫ
# =========================================================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🎲 Добро пожаловать в D&D Character Creator 5.5e (2024)!\n\n"
        "Я проведу тебя через все этапы создания персонажа.\n\n"
        "🗺 Маршрут:\n"
        "1️⃣ Класс\n"
        "2️⃣ Навыки класса\n"
        "3️⃣ Снаряжение\n"
        "4️⃣ Заклинания\n"
        "5️⃣ Боевой стиль (для воинов, паладинов, следопытов)\n"
        "6️⃣ Предыстория\n"
        "7️⃣ Раса\n"
        "8️⃣ Имя и история\n"
        "9️⃣ Готовый PDF\n\n"
        "Жми «🎲 Создать персонажа» — и погнали!",
        reply_markup=main_menu(),
        parse_mode=None
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Главное меню", reply_markup=main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 Справка по шагам создания персонажа:\n\n"
        "1. КЛАСС — боевые умения и стиль игры\n"
        "2. НАВЫКИ КЛАССА — что персонаж умеет лучше всего\n"
        "3. СНАРЯЖЕНИЕ КЛАССА — стартовый арсенал\n"
        "4. ЗАКЛИНАНИЯ (если есть) — магический арсенал\n"
        "5. БОЕВОЙ СТИЛЬ (Воину/Паладину/Следопыту) — тактика в бою\n"
        "6. ПРЕДЫСТОРИЯ — прошлое и бонусы к характеристикам\n"
        "7. РАСА — врождённые способности\n"
        "8. ИМЯ — как к тебе обращаться\n"
        "9. ИСТОРИЯ — твоя легенда\n"
        "10. ИЗОБРАЖЕНИЕ — портрет (можно пропустить)\n"
        "11. PDF — готовый лист персонажа\n\n"
        "🔹 Команды:\n"
        "/start — начать заново\n"
        "/menu — главное меню\n"
        "/help — эта справка",
        parse_mode=None
    )


# =========================================================
# КНОПКИ ГЛАВНОГО МЕНЮ
# =========================================================

@router.message(F.text == "🎲 Создать персонажа")
async def create_character_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CreateCharacter.class_select)
    await message.answer(
        "🏰 Твой класс\n\n"
        "Класс = стиль игры, умения и стартовое снаряжение.\n\n"
        "Выбери класс:",
        parse_mode=None,
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("Выберите класс:", reply_markup=create_class_keyboard())


@router.message(F.text == "📋 Мои персонажи")
async def list_characters(message: Message):
    characters = _char_repo.get_by_user_id(message.from_user.id)
    if not characters:
        await message.answer("📭 У тебя пока нет ни одного персонажа.\n\nНажми «🎲 Создать персонажа», чтобы исправить это.")
        return
    await message.answer("📋 Твои персонажи (нажми на имя, чтобы посмотреть):", reply_markup=create_character_list_keyboard(message.from_user.id))


@router.message(F.text == "🗑 Удалить персонажа")
async def delete_character_menu(message: Message):
    characters = _char_repo.get_by_user_id(message.from_user.id)
    if not characters:
        await message.answer("📭 Некого удалять — список пуст.")
        return
    await message.answer(
        "🗑 Выбери, кого отправить в легенды…\n\n⚠️ Это навсегда. Восстановить будет нельзя.",
        reply_markup=create_delete_keyboard(characters)
    )


@router.message(F.text == "ℹ️ О боте")
async def info_button(message: Message):
    await message.answer(
        "🧙‍♂️ D&D Character Creator 5.5e (2024)\n\n"
        "Что внутри:\n"
        "• 16 рас (с подрасами)\n"
        "• 13 классов\n"
        "• 16 предысторий\n"
        "• 50+ заклинаний\n"
        "• 30+ видов оружия\n"
        "• Авторасчёт характеристик\n"
        "• Генерация PDF\n\n"
        "⚙️ Фишки:\n"
        "• Умные бонусы от предыстории\n"
        "• Заклинания по категориям\n"
        "• Оружейные приёмы (Weapon Mastery)\n"
        "• Боевые стили и возвания колдуна\n\n"
        "🐉 Создай героя — и в бой!",
        parse_mode=None
    )


@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    await cmd_help(message)


@router.message(F.text == "❌ Отмена")
async def cancel_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Создание прервано.\n\nХочешь попробовать снова? Жми «🎲 Создать персонажа».",
        reply_markup=main_menu()
    )


# =========================================================
# ШАГ 1: ВЫБОР КЛАССА
# =========================================================

@router.callback_query(lambda c: c.data.startswith("class_") and not c.data.startswith("class_skill"))
async def select_class(callback: CallbackQuery, state: FSMContext):
    class_name = callback.data.replace("class_", "")
    await state.update_data(class_name=class_name)
    logger.info(f"[FLOW] Выбран класс: {class_name}")

    class_desc = CharacterStatsService.get_class_description(class_name)
    class_info = CharacterStatsService.get_class_info(class_name)
    subclasses = _class_repo.get_subclasses(class_name, level=1)

    # Базовый текст
    text = (f"🎭 {class_name}\n\n"
            f"{class_desc}\n\n"
            f"📊 Данные класса:\n"
            f"• Кость хитов: d{class_info.get('hit_die', 6)}\n"
            f"• Основные характеристики: {', '.join(class_info.get('primary_stats', []))}\n"
            f"• Спасброски: {', '.join(class_info.get('saving_throws', []))}\n"
            f"• Заклинания: {'Да' if class_info.get('spellcasting', False) else 'Нет'}\n")

    img_path = CharacterStatsService.get_class_image_path(class_name)
    try:
        await callback.message.delete()
    except Exception:
        pass

    class_data = _class_repo.get_by_name(class_name)
    available_skills = class_data.get('skills', []) if class_data else []
    skill_choices = class_data.get('skill_choices', 2) if class_data else 2
    if not available_skills:
        available_skills = [
            "Акробатика", "Атлетика", "Восприятие", "Выживание", "Выступление",
            "Запугивание", "История", "Ловкость рук", "Медицина", "Обман",
            "Обращение с животными", "Природа", "Проницательность", "Расследование",
            "Религия", "Скрытность", "Тайная магия", "Убеждение"
        ]

    if subclasses and class_name in ["Жрец", "Друид", "Колдун"]:
        text += f"\n📖 На 1-м уровне нужно выбрать путь — подкласс:\n"
        for sub in subclasses:
            text += f"   • {sub['name']} — {sub['description'][:60]}...\n"
        if img_path and os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None)
        else:
            await callback.message.answer(text, parse_mode=None)
        reply_markup = _create_subclass_keyboard(class_name)
        await callback.message.answer("Выбери подкласс:", reply_markup=reply_markup)
        await state.set_state(CreateCharacter.subclass_select)
        await callback.answer()
        return

    # НЕТ ПОДКЛАССА
    if img_path and os.path.exists(img_path):
        photo = FSInputFile(img_path)
        await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None)
    else:
        await callback.message.answer(text, parse_mode=None)

    await state.set_state(CreateCharacter.skills_select)
    selected_skills = []
    await state.update_data(selected_class_skills=selected_skills)
    keyboard = create_skills_keyboard(available_skills, skill_choices, selected_skills)
    text_skills = (f"📚 Навыки класса {class_name}\n\n"
                   f"Ты можешь выбрать {skill_choices} навыка(ов). Отмеченные ✅ войдут в лист.\n\n"
                   f"Когда наберёшь нужное количество, жми «✅ Готово».")
    await callback.message.answer(text_skills, parse_mode=None, reply_markup=keyboard)
    await callback.answer()


# =========================================================
# ВЫБОР ПОДКЛАССА
# =========================================================

@router.callback_query(lambda c: c.data.startswith("subclass_"))
async def select_subclass(callback: CallbackQuery, state: FSMContext):
    subclass_id = int(callback.data.replace("subclass_", ""))
    await state.update_data(subclass_id=subclass_id)
    logger.info(f"[FLOW] Выбран подкласс ID: {subclass_id}")
    await callback.message.delete()

    data = await state.get_data()
    class_name = data.get("class_name")
    class_data = _class_repo.get_by_name(class_name)
    available_skills = class_data.get('skills', []) if class_data else []
    skill_choices = class_data.get('skill_choices', 2) if class_data else 2
    if not available_skills:
        available_skills = [
            "Акробатика", "Атлетика", "Восприятие", "Выживание", "Выступление",
            "Запугивание", "История", "Ловкость рук", "Медицина", "Обман",
            "Обращение с животными", "Природа", "Проницательность", "Расследование",
            "Религия", "Скрытность", "Тайная магия", "Убеждение"
        ]
    await state.set_state(CreateCharacter.skills_select)
    selected_skills = []
    await state.update_data(selected_class_skills=selected_skills)
    keyboard = create_skills_keyboard(available_skills, skill_choices, selected_skills)
    text_skills = (f"📚 Навыки класса {class_name}\n\n"
                   f"Ты можешь выбрать {skill_choices} навыка(ов). Отмеченные ✅ войдут в лист.\n\n"
                   f"Когда наберёшь нужное количество, жми «✅ Готово».")
    await callback.message.answer(text_skills, parse_mode=None, reply_markup=keyboard)
    await callback.answer()


# =========================================================
# ШАГ 2: ВЫБОР НАВЫКОВ КЛАССА
# =========================================================

@router.callback_query(lambda c: c.data.startswith(
    "class_skill_toggle_") or c.data == "class_skills_ready" or c.data == "class_skills_info")
async def handle_skills_selection(callback: CallbackQuery, state: FSMContext):
    logger.info(f"🟢 Обработчик навыков вызван, data={callback.data}")
    data = callback.data
    user_data = await state.get_data()
    class_name = user_data.get("class_name")

    class_info = _class_repo.get_by_name(class_name)
    if not class_info:
        await callback.answer("❌ Ошибка: класс не найден")
        return

    available_skills = class_info.get('skills', [])
    if not available_skills:
        available_skills = [
            "Акробатика", "Атлетика", "Восприятие", "Выживание", "Выступление",
            "Запугивание", "История", "Ловкость рук", "Медицина", "Обман",
            "Обращение с животными", "Природа", "Проницательность", "Расследование",
            "Религия", "Скрытность", "Тайная магия", "Убеждение"
        ]
    skill_choices = class_info.get('skill_choices', 2)
    selected_skills = user_data.get("selected_class_skills", [])

    if data == "class_skills_ready":
        if len(selected_skills) == skill_choices:
            await state.update_data(selected_class_skills=selected_skills)
            await state.set_state(CreateCharacter.class_equipment_select)
            await callback.message.delete()
            await show_class_equipment(callback.message, state)
            await callback.answer("✅ Навыки класса выбраны!")
        else:
            await callback.answer(f"❌ Нужно выбрать ровно {skill_choices} навыка(ов). Сейчас выбрано: {len(selected_skills)}",
                                  show_alert=True)
        return

    if data == "class_skills_info":
        await callback.answer(f"Выбрано {len(selected_skills)} из {skill_choices}", show_alert=False)
        return

    if data.startswith("class_skill_toggle_"):
        skill_name = data.replace("class_skill_toggle_", "")
        if skill_name in selected_skills:
            selected_skills.remove(skill_name)
        else:
            if len(selected_skills) >= skill_choices:
                await callback.answer(f"❌ Нельзя взять больше {skill_choices} навыков.", show_alert=True)
                return
            selected_skills.append(skill_name)
        await state.update_data(selected_class_skills=selected_skills)
        keyboard = create_skills_keyboard(available_skills, skill_choices, selected_skills)
        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
            logger.info(f"✅ Клавиатура обновлена, выбрано {len(selected_skills)}")
        except Exception as e:
            logger.error(f"❌ Ошибка обновления клавиатуры: {e}")
            await callback.answer(f"⚠️ Что-то пошло не так. Попробуй ещё раз.", show_alert=True)
        await callback.answer()
        return


# =========================================================
# ШАГ 3: ВЫБОР СНАРЯЖЕНИЯ КЛАССА
# =========================================================

async def show_class_equipment(message: Message, state: FSMContext, class_name: str = None):
    if class_name is None:
        data = await state.get_data()
        class_name = data.get("class_name")
    if not class_name:
        logger.error("❌ class_name не найден в state при вызове show_class_equipment")
        return

    equipment = CharacterStatsService.get_class_equipment(class_name)
    if not equipment:
        logger.error(f"❌ Нет снаряжения для класса {class_name} в БД")
        await message.answer(f"⚠️ Для класса {class_name} нет готового набора снаряжения. Переходим к следующему шагу.")
        await go_to_spells(message, state)
        return

    has_equipment_choice = len(equipment) > 1
    if has_equipment_choice:
        text = f"⚔️ Снаряжение для {class_name}\n\n"
        text += "Выбери один стартовый набор:\n"
        for eq in equipment:
            choice = eq.get('choice', 'A')
            weapon = eq.get('weapon', 'нет оружия')
            armor = eq.get('armor', 'нет брони')
            secondary = eq.get('secondary_weapon', '')
            other = eq.get('other_items', '')
            coins = eq.get('coins', 0)
            text += f"\n📦 Вариант {choice}: {weapon}, {armor}"
            if secondary:
                text += f", {secondary}"
            if other:
                text += f", {other}"
            if coins:
                text += f", {coins} зм"
        text += "\n\nНажми на кнопку с подходящим вариантом."

        buttons = []
        for eq in equipment:
            choice = eq.get('choice', 'A')
            buttons.append([InlineKeyboardButton(text=f"📦 Вариант {choice}", callback_data=f"equip_{choice}")])
        buttons.append([InlineKeyboardButton(text="⬅️ Назад к классам", callback_data="back_to_classes")])
        reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(text, parse_mode=None, reply_markup=reply_markup)
    else:
        if equipment:
            eq = equipment[0]
            await state.update_data(
                selected_armor=eq.get('armor'),
                selected_weapon=eq.get('weapon'),
                selected_secondary_weapon=eq.get('secondary_weapon'),
                selected_other_items=eq.get('other_items'),
                selected_coins=eq.get('coins', 0)
            )
        await go_to_spells(message, state)


@router.callback_query(lambda c: c.data.startswith("equip_"))
async def select_class_equipment(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("equip_", "")
    data = await state.get_data()
    class_name = data.get("class_name")
    logger.info(f"[FLOW] Выбор снаряжения: class_name='{class_name}', choice='{choice}'")

    await state.update_data(equipment_choice=choice)
    equipment = CharacterStatsService.get_class_equipment(class_name, choice)
    if equipment:
        eq = equipment[0]
        await state.update_data(
            selected_armor=eq.get('armor'),
            selected_weapon=eq.get('weapon'),
            selected_secondary_weapon=eq.get('secondary_weapon'),
            selected_other_items=eq.get('other_items'),
            selected_coins=eq.get('coins', 0)
        )
        weapon_name = eq.get('weapon')
        if weapon_name:
            masteries = CharacterStatsService.auto_assign_masteries(weapon_name, class_name)
            await state.update_data(selected_masteries=masteries)

    await callback.message.delete()
    await callback.message.answer(f"✅ Взят вариант {choice}")
    await go_to_spells(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_classes")
async def back_to_classes(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.class_select)
    await callback.message.delete()
    await callback.message.answer("Выбери класс заново:", parse_mode=None, reply_markup=create_class_keyboard())
    await callback.answer()


# =========================================================
# ПЕРЕХОДЫ МЕЖДУ ШАГАМИ
# =========================================================

async def go_to_spells(message: Message, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    is_spellcaster = ProgressionService.is_spellcaster(class_name)
    logger.info(f"[FLOW] go_to_spells: class={class_name}, is_spellcaster={is_spellcaster}")
    if is_spellcaster:
        await SpellSelectionService.start_cantrips_selection(message, state)
    else:
        await go_to_fighting_style(message, state)


async def go_to_fighting_style(message: Message, state: FSMContext):
    logger.info("=" * 50)
    logger.info("🔧 go_to_fighting_style ВЫЗВАНА!")
    logger.info("=" * 50)
    data = await state.get_data()
    class_name = data.get("class_name")
    logger.info(f"   class_name = {class_name}")

    if ProgressionService.should_select_fighting_style(class_name):
        styles = CharacterStatsService.get_fighting_styles_for_class(class_name)
        logger.info(f"   Найдено стилей: {len(styles) if styles else 0}")
        if not styles:
            logger.warning(f"⚠️ Нет боевых стилей для класса {class_name}")
            await message.answer(f"⚠️ У класса {class_name} нет боевых стилей. Пропускаем шаг.")
            await go_to_invocations(message, state)
            return

        text = f"⚔️ Боевой стиль\n\n"
        text += f"Класс {class_name} позволяет взять один стиль.\n\n"
        text += "Доступно:\n"
        for s in styles:
            text += f"• {s['name']} – {s['description']}\n"
        text += "\nНажми на название, чтобы выбрать."

        await state.set_state(CreateCharacter.fighting_style_select)
        await message.answer(text, parse_mode=None, reply_markup=_create_fighting_style_keyboard(class_name))
    else:
        logger.info(f"   Класс {class_name} не в списке, идём к invocations")
        await go_to_invocations(message, state)


async def go_to_invocations(message: Message, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    logger.info(f"🔧 go_to_invocations вызвана для класса: {class_name}")

    if ProgressionService.should_select_invocations(class_name):
        await state.set_state(CreateCharacter.invocations_select)
        invocations = CharacterStatsService.get_all_invocations(level=1)
        if invocations:
            selected_names = data.get("selected_invocations", [])
            text = f"🔮 Таинственные возвания (колдун)\n\n"
            text += "На 1-м уровне можно взять до 2 возваний.\n\n"
            text += "Список:\n"
            for inv in invocations:
                level_req = inv.get('level_required', 1)
                effect = inv.get('effect', 'Нет описания')
                text += f"• {inv['name']} (мин. ур. {level_req}) – {effect}\n"
            text += "\nКликни по названию, чтобы добавить/убрать. ✅ = выбрано."

            keyboard = _create_invocations_keyboard(level=1, selected_names=selected_names)
            if keyboard:
                await message.answer(text, parse_mode=None, reply_markup=keyboard)
            else:
                await message.answer("📖 Для твоего уровня возвания не предусмотрены. Идём дальше.")
                await go_to_background(message, state)
        else:
            await message.answer("📖 Для твоего уровня возвания не предусмотрены. Идём дальше.")
            await go_to_background(message, state)
    else:
        logger.info(f"   Переход к выбору предыстории для {class_name}")
        await go_to_background(message, state)


async def go_to_background(message: Message, state: FSMContext):
    logger.info("🔧 go_to_background вызвана")
    await state.set_state(CreateCharacter.background_select)
    await message.answer(
        f"📜 Твоё прошлое (предыстория)\n\n"
        f"Предыстория даёт бонусы к характеристикам, черты и снаряжение.\n\n"
        f"Выбери одну:",
        parse_mode=None,
        reply_markup=create_background_keyboard()
    )


# =========================================================
# БОЕВОЙ СТИЛЬ И ВОЗВАНИЯ (ОБРАБОТЧИКИ)
# =========================================================

@router.callback_query(lambda c: c.data.startswith("style_"))
async def select_fighting_style(callback: CallbackQuery, state: FSMContext):
    style_id = int(callback.data.replace("style_", ""))
    style = _fighting_repo.get_by_id(style_id)
    style_name = style.get('name') if style else None
    if style_name:
        await state.update_data(selected_fighting_style=style_name)
        await callback.answer(f"✅ Выбран стиль: {style_name}")
        logger.info(f"[FLOW] Выбран боевой стиль: {style_name}")
    await callback.message.delete()
    await go_to_invocations(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("inv_") and c.data not in ("inv_skip", "inv_continue"))
async def select_invocation(callback: CallbackQuery, state: FSMContext):
    inv_id = int(callback.data.replace("inv_", ""))
    invocation = _inv_repo.get_by_id(inv_id)
    inv_name = invocation.get('name') if invocation else None
    if not inv_name:
        await callback.answer("❌ Возвание не найдено")
        return
    data = await state.get_data()
    selected = data.get("selected_invocations", [])
    if inv_name in selected:
        selected.remove(inv_name)
        await callback.answer(f"❌ Возвание «{inv_name}» снято")
    else:
        if len(selected) >= 2:
            await callback.answer("⚠️ Не больше двух возваний!", show_alert=True)
            return
        selected.append(inv_name)
        await callback.answer(f"✅ Возвание «{inv_name}» добавлено")
    await state.update_data(selected_invocations=selected)

    keyboard = _create_invocations_keyboard(level=1, selected_names=selected)
    if keyboard:
        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except Exception as e:
            if "message is not modified" not in str(e):
                logger.warning(f"Ошибка обновления клавиатуры: {e}")

    if len(selected) == 2:
        await callback.message.delete()
        logger.info("[FLOW] Выбрано 2 возвания, переходим к следующему шагу")
        await go_to_background(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "inv_continue")
async def continue_invocations(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await go_to_background(callback.message, state)
    await callback.answer()


# =========================================================
# ПРЕДЫСТОРИЯ
# =========================================================

@router.callback_query(lambda c: c.data.startswith("bg_") and not c.data.startswith("bg_equip_"))
async def select_background(callback: CallbackQuery, state: FSMContext):
    background = callback.data.replace("bg_", "")
    await state.update_data(background=background)
    logger.info(f"[FLOW] Выбрана предыстория: {background}")

    bg_info = _bg_repo.get_by_name(background)
    if not bg_info:
        await callback.message.answer(f"❌ Ошибка: предыстория '{background}' не найдена.", reply_markup=main_menu())
        await state.clear()
        return

    await state.update_data(
        selected_skills_bg=bg_info.get('skills', []),
        background_trait=bg_info.get('trait', 'Нет'),
        background_origin_feat=bg_info.get('origin_feat', '')
    )
    await state.set_state(CreateCharacter.background_equipment_select)

    equip_a = bg_info.get('equipment_a', 'Нет описания')[:120]
    equip_b = bg_info.get('equipment_b', 'Нет описания')[:120]
    origin_feat = bg_info.get('origin_feat', '')
    origin_feat_text = f"✨ Черта происхождения: {origin_feat}\n\n" if origin_feat else ""

    await callback.message.delete()
    await callback.message.answer(
        f"📜 {background}\n\n"
        f"📖 {bg_info.get('description', 'Нет описания')[:300]}...\n\n"
        f"{origin_feat_text}"
        f"✨ Бонусы характеристик: +2 {bg_info['characteristics'][0]}, +1 {bg_info['characteristics'][1]}\n\n"
        f"🔧 Черта: {bg_info.get('trait', 'Нет')}\n"
        f"📚 Навыки: {', '.join(bg_info.get('skills', []))}\n"
        f"🛠️ Инструменты: {bg_info.get('tools', 'Нет')}\n\n"
        f"Снаряжение от предыстории\n\n"
        f"Выбери один стартовый набор:\n"
        f"📦 Вариант А: {equip_a}\n\n"
        f"🎒 Вариант Б: {equip_b}\n\n"
        f"Нажми на кнопку с нужным вариантом.",
        parse_mode=None,
        reply_markup=_create_background_equipment_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("bg_equip_"))
async def select_background_equipment(callback: CallbackQuery, state: FSMContext):
    equipment_choice = callback.data.replace("bg_equip_", "")
    data = await state.get_data()
    background = data.get("background")
    if not background or background in ["equip_A", "equip_B", "equip_", "A", "B", None]:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: background = '{background}'")
        await callback.message.answer(
            "❌ Ошибка: данные о предыстории потеряны.\nПожалуйста, начните создание заново: /start",
            reply_markup=main_menu())
        await state.clear()
        return
    await state.update_data(background_equipment_choice=equipment_choice)
    await calculate_and_show_stats(callback.message, state)
    await callback.message.delete()
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_background")
async def back_to_background_list(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.background_select)
    await callback.message.delete()
    await callback.message.answer("Выбери предысторию заново:", parse_mode=None,
                                  reply_markup=create_background_keyboard())
    await callback.answer()


# =========================================================
# РАСЧЁТ ХАРАКТЕРИСТИК
# =========================================================

async def calculate_and_show_stats(message: Message, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    background = data.get("background")
    equipment_choice = data.get("equipment_choice", "A")
    selected_armor = data.get("selected_armor")

    stats_result = CharacterStatsService.calculate_and_format_stats(
        class_name=class_name,
        background=background,
        base_stats_dict=None,
        equipment_choice=equipment_choice
    )

    await state.update_data(
        final_stats=stats_result['stats'],
        stats=stats_result['stats'],
        hp=stats_result['hp'],
        ac=stats_result['ac']
    )

    stats = stats_result['stats']
    def mod(s): return (s-10)//2

    await message.answer(
        f"📊 Твои характеристики\n\n"
        f"Класс: {class_name}\n"
        f"Предыстория: {background}\n\n"
        f"✨ Бонусы предыстории: +2 к {stats_result['bg_chars'][0]}, +1 к {stats_result['bg_chars'][1]}\n\n"
        f"📈 Итоговые значения (модификатор):\n"
        f"💪 Сила (STR): {stats['STR']} ({mod(stats['STR']):+d})\n"
        f"🤸 Ловкость (DEX): {stats['DEX']} ({mod(stats['DEX']):+d})\n"
        f"🏋️ Телосложение (CON): {stats['CON']} ({mod(stats['CON']):+d})\n"
        f"🧠 Интеллект (INT): {stats['INT']} ({mod(stats['INT']):+d})\n"
        f"🧙 Мудрость (WIS): {stats['WIS']} ({mod(stats['WIS']):+d})\n"
        f"✨ Харизма (CHA): {stats['CHA']} ({mod(stats['CHA']):+d})\n\n"
        f"❤️ Хиты (HP): {stats_result['hp']}\n"
        f"🛡️ Класс брони (AC): {stats_result['ac']}\n\n"
        f"А теперь выбери расу:",
        parse_mode=None,
        reply_markup=create_race_keyboard()
    )
    await state.set_state(CreateCharacter.race_select)


# =========================================================
# РАСА
# =========================================================

@router.callback_query(lambda c: c.data.startswith("race_"))
async def select_race(callback: CallbackQuery, state: FSMContext):
    race = callback.data.replace("race_", "")
    await state.update_data(race=race)
    logger.info(f"[FLOW] Выбрана раса: {race}")

    race_desc = CharacterStatsService.get_race_description(race)
    race_speed = CharacterStatsService.get_race_speed(race)
    race_size = CharacterStatsService.get_race_size(race)
    has_sub = CharacterStatsService.has_subraces(race)
    subraces_list = CharacterStatsService.get_subraces(race) if has_sub else []

    text = f"🧝 Раса: {race}\n\n📖 {race_desc}\n\n🏃 Скорость: {race_speed} футов\n📏 Размер: {race_size}\n"
    img_path = CharacterStatsService.get_race_image_path(race)

    try:
        await callback.message.delete()
    except Exception:
        pass

    if has_sub and subraces_list:
        text += f"\n🌟 Доступные подрасы:\n"
        for sub in subraces_list:
            sub_trait = CharacterStatsService.get_subrace_trait(race, sub)
            text += f"   • {sub} — {sub_trait[:50] + '...' if len(sub_trait) > 50 else sub_trait}\n"
        if img_path and os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None)
        else:
            await callback.message.answer(text, parse_mode=None)
        reply_markup = _create_subrace_keyboard(race)
        await callback.message.answer("Твой выбор:", reply_markup=reply_markup)
        await state.set_state(CreateCharacter.subrace_select)
    else:
        if img_path and os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None)
        else:
            await callback.message.answer(text, parse_mode=None)
        await go_to_name(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("subrace_"))
async def select_subrace(callback: CallbackQuery, state: FSMContext):
    subrace = callback.data.replace("subrace_", "")
    await state.update_data(subrace=subrace)
    data = await state.get_data()
    race = data.get("race")
    sub_desc = CharacterStatsService.get_subrace_description(race, subrace)
    sub_trait = CharacterStatsService.get_subrace_trait(race, subrace)
    text = f"🧝 {race} — {subrace}\n\n📖 {sub_desc}\n\n✨ Особенность: {sub_trait}\n\nПереходим к имени…"
    await callback.message.delete()
    await go_to_name(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_races")
async def back_to_races(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.race_select)
    await callback.message.delete()
    await callback.message.answer("Выбери расу заново:", parse_mode=None, reply_markup=create_race_keyboard())
    await callback.answer()


# =========================================================
# ИМЯ И ИСТОРИЯ
# =========================================================

async def go_to_name(message: Message, state: FSMContext):
    logger.info("🔧 go_to_name вызвана")
    await state.set_state(CreateCharacter.name_input)
    await message.answer(
        "📛 Как зовут твоего героя?\n\n"
        "Имя: от 2 до 50 символов. Любое на твой вкус.\n\n"
        "Введи имя:",
        parse_mode=None,
        reply_markup=cancel_kb()
    )


async def go_to_backstory(message: Message, state: FSMContext):
    logger.info("🔧 go_to_backstory вызвана")
    await state.set_state(CreateCharacter.backstory_input)
    await message.answer(
        "📖 История персонажа\n\n"
        "Коротко расскажи:\n"
        "• Откуда он родом?\n"
        "• Что привело его к приключениям?\n"
        "• Какая цель движет им?\n\n"
        "Введи текст (до 2000 символов):",
        parse_mode=None,
        reply_markup=cancel_kb()
    )


@router.message(CreateCharacter.name_input)
async def set_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_creation(message, state)
        return
    valid, msg = engine_validate_name(message.text)
    if not valid:
        await message.answer(f"{msg}\nПопробуй другое имя:", reply_markup=cancel_kb())
        return
    await state.update_data(name=message.text.strip())
    logger.info(f"✅ Имя сохранено: {message.text.strip()}")
    await message.answer(f"✅ Принято: {message.text.strip()}", reply_markup=ReplyKeyboardRemove())
    await go_to_backstory(message, state)


@router.message(CreateCharacter.backstory_input)
async def set_backstory(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_creation(message, state)
        return
    backstory = message.text.strip()
    if len(backstory) > 2000:
        await message.answer("❌ История не помещается — максимум 2000 символов. Сократи немного.", reply_markup=cancel_kb())
        return
    await state.update_data(backstory=backstory)
    await state.set_state(CreateCharacter.image_input)
    await message.answer(
        f"📖 История сохранена!\n\n🖼️ Теперь портрет\n\nЗагрузи изображение (можно пропустить кнопкой «⏩ Пропустить»).",
        parse_mode=None,
        reply_markup=skip_kb()
    )


# =========================================================
# ИЗОБРАЖЕНИЕ И ФИНАЛИЗАЦИЯ
# =========================================================

@router.message(F.text == "⏩ Пропустить")
async def skip_image(message: Message, state: FSMContext):
    await finalize_character(message, state, image_file_id=None)


@router.message(CreateCharacter.image_input, F.photo)
async def set_image(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    await finalize_character(message, state, image_file_id=file_id)


async def finalize_character(message: Message, state: FSMContext, image_file_id: Optional[str] = None):
    temp_file_path = None
    try:
        await message.answer("⏳ Собираю героя в HTML… пару секунд.", reply_markup=ReplyKeyboardRemove())

        data = await state.get_data()
        char_data = CharacterFinalizationService.prepare_character_data(data, message.from_user.id)
        char_data['image_file_id'] = image_file_id

        name = char_data['name']
        if not name:
            await message.answer("❌ Что-то с именем — не сохранилось. Начни создание заново.", reply_markup=main_menu())
            await state.clear()
            return

        class_skills = data.get("selected_class_skills", [])
        bg_skills = data.get("selected_skills_bg", [])
        all_skills = list(set(class_skills + bg_skills))
        char_data['selected_skills'] = all_skills
        char_data['origin_feat'] = data.get("background_origin_feat", "")

        char_id = CharacterFinalizationService.save_character(char_data)

        bg_info = _bg_repo.get_by_name(char_data['background']) if char_data['background'] else None
        stats = char_data['stats']
        class_info = CharacterStatsService.get_class_info(char_data['class_name'])

        # Подготовка данных для HTML-шаблона
        pdf_data = {
            "name": name,
            "class_name": char_data['class_name'],
            "race": f"{char_data['race']} ({char_data['subrace']})" if char_data['subrace'] else char_data['race'],
            "level": 1,
            "stats": stats,
            "hp": char_data['hp'],
            "ac": char_data['ac'],
            "speed": 30,
            "skills": all_skills,
            "equipment": [item for item in [char_data['selected_weapon'], char_data['selected_armor']] if item],
            "spells": char_data['selected_spells'],
            "proficiency_bonus": CharacterStatsService.calculate_proficiency_bonus(1),
            "background": char_data['background'],
            "background_trait": bg_info.get('trait', '') if bg_info else '',
            "background_description": bg_info.get('description', '') if bg_info else '',
            "origin_feat": char_data.get('origin_feat', ''),
            "race_traits": [],
            "class_features": class_info.get('features', []),
            "backstory": char_data['backstory'],
            "alignment": "Нейтральное",
            "player_name": message.from_user.full_name,
            "experience": 0,
            "saving_throws": class_info.get('saving_throws', []),
            "notes": "",
            "coins": data.get("selected_coins", 0),
            "spell_slots_1": 0,
            "spell_slots_2": 0,
            "appearance": ""
        }

        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{safe_name}.html")
        temp_file_path = temp_file.name
        temp_file.close()

        # Генерация HTML
        html_file = generate_pdf(pdf_data, temp_file_path)  # generate_pdf возвращает путь к HTML

        if html_file and os.path.exists(html_file):
            await message.answer_document(
                FSInputFile(html_file, filename=f"{safe_name}_character_sheet.html"),
                caption="📄 Лист персонажа (HTML) – нажмите на кнопку в файле или используйте печать браузера (Ctrl+P), чтобы сохранить как PDF."
            )
        else:
            logger.error(f"HTML не создан: {html_file}")
            await message.answer("⚠️ Не удалось создать файл листа персонажа, но персонаж сохранён в базе!")

        # Короткое сообщение с основными характеристиками
        def mod(s): return (s-10)//2
        spells_preview = ""
        if char_data.get('selected_spells'):
            spells_list = ", ".join(char_data['selected_spells'][:5])
            if len(char_data['selected_spells']) > 5:
                spells_list += f" и ещё {len(char_data['selected_spells'])-5}"
            spells_preview = f"\n\n🔮 Заклинания: {spells_list}"

        caption = (f"✅ Персонаж готов!\n\n"
                   f"📛 {name}\n"
                   f"⚔️ Класс: {char_data['class_name']}\n"
                   f"📜 Предыстория: {char_data['background']}\n"
                   f"🧝 Раса: {char_data['race']}{f' ({char_data['subrace']})' if char_data['subrace'] else ''}\n\n"
                   f"❤️ HP: {char_data['hp']} | 🛡️ AC: {char_data['ac']}\n\n"
                   f"📊 Характеристики (мод.):\n"
                   f"💪 Сила {stats['STR']} ({mod(stats['STR']):+d}) | 🤸 Ловкость {stats['DEX']} ({mod(stats['DEX']):+d}) | 🏋️ Телосложение {stats['CON']} ({mod(stats['CON']):+d})\n"
                   f"🧠 Интеллект {stats['INT']} ({mod(stats['INT']):+d}) | 🧙 Мудрость {stats['WIS']} ({mod(stats['WIS']):+d}) | ✨ Харизма {stats['CHA']} ({mod(stats['CHA']):+d})"
                   f"{spells_preview}\n\n"
                   f"📄 HTML-лист персонажа загружен выше – откройте его в браузере и сохраните как PDF.")

        if image_file_id:
            await message.answer_photo(photo=image_file_id, caption=caption, parse_mode=None)
        else:
            await message.answer(caption, parse_mode=None)

        await message.answer("🏠 Главное меню", reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при создании персонажа: {e}", exc_info=True)
        await message.answer(f"❌ Произошла ошибка: {str(e)[:200]}\n\nПерсонаж может быть сохранён, но PDF не создан.",
                             reply_markup=main_menu())
        await state.clear()
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except:
                pass


# =========================================================
# ПРОСМОТР И УДАЛЕНИЕ ПЕРСОНАЖЕЙ
# =========================================================

@router.callback_query(lambda c: c.data.startswith("view_"))
async def view_character(callback: CallbackQuery):
    char_id = int(callback.data.replace("view_", ""))
    character = _char_repo.get_by_id(char_id, callback.from_user.id)
    if not character:
        await callback.answer("❌ Персонаж не найден")
        return
    info = (f"📛 {character['name']}\n\n"
            f"🧝 Раса: {character.get('race_name', 'Неизвестно')}\n"
            f"⚔️ Класс: {character.get('class_name', 'Неизвестно')}\n"
            f"📜 Предыстория: {character.get('background_name', 'Нет')}\n"
            f"📊 Уровень: {character['level']}\n"
            f"❤️ HP: {character['hp']} | 🛡️ AC: {character['ac']}\n\n"
            f"Характеристики:\n"
            f"Сила {character['str']} | Ловкость {character['dex']} | Телосложение {character['con']} | "
            f"Интеллект {character['int']} | Мудрость {character['wis']} | Харизма {character['cha']}")
    if character.get('image_file_id'):
        await callback.message.answer_photo(photo=character['image_file_id'], caption=info, parse_mode=None)
    else:
        await callback.message.answer(info, parse_mode=None)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("delete_"))
async def confirm_delete(callback: CallbackQuery):
    char_id = int(callback.data.replace("delete_", ""))
    character = _char_repo.get_by_id(char_id, callback.from_user.id)
    if not character:
        await callback.answer("❌ Персонаж не найден")
        return
    if _char_repo.delete(char_id, callback.from_user.id):
        await callback.message.edit_text(f"✅ {character['name']} навсегда ушёл в прошлое.", parse_mode=None)
    else:
        await callback.message.edit_text("❌ Не получилось удалить. Попробуй позже.")
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.edit_text("❌ Удаление отменено")
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_creation")
async def cancel_creation_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ Создание отменено.\n\nНачать заново? Кнопка «🎲 Создать персонажа».",
        reply_markup=main_menu()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "progress_info")
async def progress_info(callback: CallbackQuery):
    await callback.answer("Это информационное сообщение", show_alert=False)


# =========================================================
# НЕИЗВЕСТНЫЕ КОМАНДЫ
# =========================================================

@router.message()
async def unknown_command(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await message.answer(
            "⏳ Ты сейчас создаёшь персонажа. Продолжай по шагам или нажми «❌ Отмена».",
            reply_markup=cancel_kb()
        )
    else:
        await message.answer(
            "❓ Не знаю такой команды.\n\nПопробуй кнопки меню или /help.",
            reply_markup=main_menu()
        )