#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot.py - D&D Character Creator Bot for D&D 5.5e (2024)
Полностью исправленная версия с поддержкой картинок, описаний и новой БД
"""

import asyncio
import logging
import os
import re
import tempfile
from typing import Dict, Any, Optional, List

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, FSInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from dotenv import load_dotenv

from db import (
    save_character,
    get_user_characters,
    get_character_by_id,
    delete_character,
    get_user_characters_count,
    get_connection
)
from dnd_logic import (
    # Основные функции
    modifier, calculate_proficiency_bonus, calc_hp, calc_ac,

    # Расы
    get_race_list, get_race_info, get_race_description,
    get_race_speed, get_race_size, has_subraces, get_subraces,
    get_subrace_description, get_subrace_trait, get_race_traits_list,
    get_race_image_path,

    # Классы
    get_class_list, get_class_info, get_class_description,
    get_class_hit_die, get_class_skill_choices, get_class_by_name,
    get_subclasses_for_class, get_class_image_path,

    # Предыстории (КЛЮЧЕВОЕ для 5.5e!)
    get_background_list, get_background_data, get_background_by_name,
    get_background_characteristics, get_background_trait,
    get_background_skills, get_background_tools,
    get_background_description, get_equipment_choice,
    format_background_for_display,

    # Характеристики
    get_standard_stats, apply_background_bonuses, get_initial_stats,

    # Заклинания
    get_cantrips_for_class, get_level1_spells_for_class,

    # Оружейные приёмы
    get_all_weapon_masteries, get_weapon_mastery_by_name,

    # Боевые стили
    get_all_fighting_styles, get_fighting_style_by_name,

    # Возвания колдуна
    get_all_invocations, get_invocation_by_name,

    # Валидация
    validate_character, validate_name,

    # Вспомогательные
    get_class_features,
)
from pdf_generator import generate_pdf

# ---------------- CONFIG ----------------
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ---------------- FSM STATES (НОВЫЙ ПОРЯДОК ДЛЯ 5.5e!) ----------------
class CreateCharacter(StatesGroup):
    # Шаг 1: КЛАСС (теперь первый!)
    class_select = State()
    subclass_select = State()  # 1a. Подкласс (если есть на 1-3 уровне)

    # Шаг 2: ПРЕДЫСТОРИЯ (теперь даёт бонусы к статам!)
    background_select = State()

    # Шаг 3: РАСА (без бонусов к статам)
    race_select = State()
    subrace_select = State()  # 3a. Подраса

    # Шаг 4: РАСПРЕДЕЛЕНИЕ ХАРАКТЕРИСТИК
    stats_assign = State()

    # Шаг 5: ИМЯ
    name_input = State()

    # Шаг 6: ЗАКЛИНАНИЯ (для заклинателей)
    spells_cantrips_select = State()
    spells_level1_select = State()

    # Шаг 7: ОРУЖЕЙНЫЕ ПРИЁМЫ (для воинских классов)
    masteries_select = State()

    # Шаг 8: БОЕВОЙ СТИЛЬ (для воинов, паладинов, следопытов)
    fighting_style_select = State()

    # Шаг 9: ВОЗВАНИЯ (для колдуна)
    invocations_select = State()

    # Шаг 10: СНАРЯЖЕНИЕ
    equipment_select = State()

    # Шаг 11: ИСТОРИЯ
    backstory_input = State()

    # Шаг 12: ИЗОБРАЖЕНИЕ
    image_input = State()


# ---------------- MENU ----------------
def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        [KeyboardButton(text="🎲 Создать персонажа")],
        [KeyboardButton(text="📋 Мои персонажи")],
        [KeyboardButton(text="🗑 Удалить персонажа")],
        [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


# ---------------- INLINE KEYBOARDS ----------------
def create_class_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора класса (теперь первый шаг!)"""
    classes = get_class_list()
    buttons = []
    row = []

    for i, class_name in enumerate(classes):
        row.append(InlineKeyboardButton(text=class_name, callback_data=f"class_{class_name}"))
        if len(row) == 2 or i == len(classes) - 1:
            buttons.append(row)
            row = []

    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_subclass_keyboard(class_name: str) -> Optional[InlineKeyboardMarkup]:
    """Создаёт клавиатуру выбора подкласса (если есть)"""
    subclasses = get_subclasses_for_class(class_name)

    if not subclasses:
        return None

    buttons = []
    for sub in subclasses:
        buttons.append([InlineKeyboardButton(
            text=f"📖 {sub['name']} (ур. {sub['level_acquired']})",
            callback_data=f"subclass_{sub['id']}"
        )])

    buttons.append([InlineKeyboardButton(text="➡️ Пропустить (выбрать позже)", callback_data="subclass_skip")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к классам", callback_data="back_to_classes")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_background_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора предыстории"""
    backgrounds = get_background_list()
    buttons = []
    row = []

    for i, bg in enumerate(backgrounds):
        row.append(InlineKeyboardButton(text=bg, callback_data=f"bg_{bg}"))
        if len(row) == 2 or i == len(backgrounds) - 1:
            buttons.append(row)
            row = []

    buttons.append([InlineKeyboardButton(text="⬅️ Назад к классам", callback_data="back_to_classes")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_race_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора расы"""
    races = get_race_list()
    buttons = []
    row = []

    for i, race in enumerate(races):
        row.append(InlineKeyboardButton(text=race, callback_data=f"race_{race}"))
        if len(row) == 2 or i == len(races) - 1:
            buttons.append(row)
            row = []

    buttons.append([InlineKeyboardButton(text="⬅️ Назад к предыстории", callback_data="back_to_background")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_subrace_keyboard(race: str) -> Optional[InlineKeyboardMarkup]:
    """Создаёт клавиатуру выбора подрасы"""
    subraces = get_subraces(race)

    if not subraces:
        return None

    buttons = []
    for subrace in subraces:
        buttons.append([InlineKeyboardButton(text=subrace, callback_data=f"subrace_{subrace}")])

    buttons.append([InlineKeyboardButton(text="➡️ Пропустить", callback_data="subrace_skip")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к расам", callback_data="back_to_races")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_stats_keyboard(stats: Dict[str, int]) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для распределения характеристик"""
    buttons = []
    stat_names = {"STR": "💪 Сила", "DEX": "🤸 Ловкость", "CON": "🏋️ Телосложение",
                  "INT": "🧠 Интеллект", "WIS": "🧙 Мудрость", "CHA": "✨ Харизма"}

    for stat, name in stat_names.items():
        buttons.append([InlineKeyboardButton(
            text=f"{name}: {stats.get(stat, 10)} ({modifier(stats.get(stat, 10)):+d})",
            callback_data=f"stat_{stat}"
        )])

    buttons.append([InlineKeyboardButton(text="✅ Подтвердить характеристики", callback_data="stats_confirm")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_equipment_keyboard(background: str) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора снаряжения А или Б"""
    bg_info = get_background_data(background)
    equipment_a = bg_info.get("equipment_a", "Нет описания")[:60]
    equipment_b = bg_info.get("equipment_b", "Нет описания")[:60]

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📦 Вариант А: {equipment_a}...", callback_data="equip_A")],
        [InlineKeyboardButton(text=f"🎒 Вариант Б: {equipment_b}...", callback_data="equip_B")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_background")]
    ])


def create_character_list_keyboard(user_id: int) -> Optional[InlineKeyboardMarkup]:
    """Создаёт клавиатуру со списком персонажей пользователя"""
    characters = get_user_characters(user_id)

    if not characters:
        return None

    buttons = []
    for char in characters:
        text = f"{char['name']} - {char['class_name']} ур.{char['level']}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"view_{char['id']}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_delete_keyboard(characters: list) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для удаления персонажей"""
    buttons = []
    for char in characters:
        text = f"🗑 {char['name']} ({char['class_name']})"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"delete_{char['id']}")])

    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ---------------- START ----------------
@dp.message(Command("start"))
async def start(m: Message, state: FSMContext):
    await state.clear()

    welcome_text = (
        "🎮 **Добро пожаловать в D&D Character Creator 5.5e (2024)!**\n\n"
        "Я помогу тебе создать персонажа для Dungeons & Dragons 5-й редакции (обновлённые правила 2024 года).\n\n"
        "**Что нового в версии 5.5e:**\n"
        "• Предыстория даёт бонусы к характеристикам (а не раса) ✨\n"
        "• Оружейные приёмы (Weapon Mastery) для воинов ⚔️\n"
        "• Новый порядок создания персонажа 📋\n\n"
        "**Как начать:**\n"
        "Нажми кнопку «🎲 Создать персонажа» и следуй инструкциям!"
    )

    await m.answer(welcome_text, reply_markup=main_menu(), parse_mode=ParseMode.MARKDOWN)


@dp.message(Command("menu"))
async def menu_command(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("🎮 Главное меню", reply_markup=main_menu())


@dp.message(F.text == "❌ Отмена")
async def cancel_creation(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(
        "❌ Создание персонажа отменено.\n\nЧтобы начать заново, нажмите «🎲 Создать персонажа»",
        reply_markup=main_menu()
    )


@dp.message(Command("help"))
async def help_command(m: Message):
    help_text = (
        "❓ **Помощь по использованию бота**\n\n"
        "**Как создать персонажа (D&D 5.5e):**\n"
        "1️⃣ Выберите **КЛАСС** (с описанием и картинкой)\n"
        "2️⃣ Выберите **ПРЕДЫСТОРИЮ** (она даёт бонусы к характеристикам!)\n"
        "3️⃣ Выберите **РАСУ** (с описанием и картинкой)\n"
        "4️⃣ Распределите **ХАРАКТЕРИСТИКИ**\n"
        "5️⃣ Введите **ИМЯ**\n"
        "6️⃣ Выберите **ЗАКЛИНАНИЯ** (если класс заклинатель)\n"
        "7️⃣ Выберите **ОРУЖЕЙНЫЕ ПРИЁМЫ** (если есть)\n"
        "8️⃣ Выберите **БОЕВОЙ СТИЛЬ** (если есть)\n"
        "9️⃣ Выберите **СНАРЯЖЕНИЕ** (вариант А или Б)\n"
        "🔟 Напишите **ИСТОРИЮ** персонажа\n"
        "1️⃣1️⃣ Загрузите **ИЗОБРАЖЕНИЕ** (или пропустите)\n\n"
        "**Другие команды:**\n"
        "• /start - Главное меню\n"
        "• /help - Эта справка\n"
        "• /skip - Пропустить загрузку картинки\n\n"
        "**Приятной игры!** 🎲"
    )
    await m.answer(help_text, parse_mode=ParseMode.MARKDOWN)


@dp.message(F.text == "❓ Помощь")
async def help_button(m: Message):
    await help_command(m)


@dp.message(F.text == "ℹ️ О боте")
async def info_button(m: Message):
    info_text = (
        "ℹ️ **D&D Character Creator**\n\n"
        "**Особенности:**\n"
        "• 16 рас с подрасами и картинками\n"
        "• 13 классов с подклассами и картинками\n"
        "• 16 предысторий с бонусами к характеристикам\n"
        "• Заклинания, оружейные приёмы, боевые стили\n"
        "• Таинственные возвания для колдуна\n"
        "• Генерация PDF листа персонажа\n\n"
        "**Разработчик:** @danilenkokoko007_official\n\n"
        "Приятной игры! 🎲"
    )
    await m.answer(info_text, parse_mode=ParseMode.MARKDOWN)


# ---------------- CREATE CHARACTER (НОВЫЙ ПОРЯДОК!) ----------------
@dp.message(F.text == "🎲 Создать персонажа")
async def create_char_start(m: Message, state: FSMContext):
    await state.set_state(CreateCharacter.class_select)
    await m.answer(
        "🏰 **Создание нового персонажа (D&D 5.5e 2024)**\n\n"
        "**Шаг 1/12: Выберите КЛАСС**\n\n"
        "Класс определяет вашу роль в приключении и основные способности.\n"
        "Нажмите на класс, чтобы увидеть подробное описание и картинку:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_class_keyboard()
    )


# ---------------- ШАГ 1: КЛАСС (с картинкой и описанием!) ----------------
@dp.callback_query(lambda c: c.data.startswith("class_"))
async def select_class(call: CallbackQuery, state: FSMContext):
    class_name = call.data.replace("class_", "")
    await state.update_data(class_name=class_name)

    # Получаем полную информацию о классе
    class_desc = get_class_description(class_name)
    class_info = get_class_info(class_name)
    class_data = get_class_by_name(class_name)

    # Получаем подклассы
    subclasses = get_subclasses_for_class(class_name)

    # Формируем красивое описание
    text = (
        f"⚔️ **{class_name}**\n\n"
        f"📖 {class_desc}\n\n"
        f"**📊 Характеристики класса:**\n"
        f"• ❤️ **Хитовый кубик:** d{class_info.get('hit_die', 6)}\n"
        f"• 🎯 **Основные характеристики:** {', '.join(class_info.get('primary_stats', []))}\n"
        f"• 🛡️ **Спасброски:** {', '.join(class_info.get('saving_throws', []))}\n"
        f"• 🔮 **Заклинания:** {'Да' if class_info.get('spellcasting', False) else 'Нет'}\n"
    )

    if subclasses:
        text += f"\n**📖 Доступные подклассы (с уровня {subclasses[0]['level_acquired']}):**\n"
        for sub in subclasses[:3]:
            desc_preview = sub['description'][:50] + "..." if len(sub.get('description', '')) > 50 else sub.get(
                'description', '')
            text += f"   • **{sub['name']}** — {desc_preview}\n"
        text += f"\nВы можете выбрать подкласс сейчас или позже."
        reply_markup = create_subclass_keyboard(class_name)
        next_state = CreateCharacter.subclass_select
    else:
        text += f"\n\n**Шаг 2/12: Выберите ПРЕДЫСТОРИЮ**\n(именно она даст бонусы к характеристикам!)"
        reply_markup = create_background_keyboard()
        next_state = CreateCharacter.background_select

    await state.set_state(next_state)

    # Отправляем картинку класса (если есть)
    img_path = get_class_image_path(class_name)
    try:
        await call.message.delete()
        if img_path and os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await call.message.answer_photo(
                photo=photo,
                caption=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await call.message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка отправки картинки класса {class_name}: {e}")
        await call.message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("subclass_") and c.data != "subclass_skip")
async def select_subclass(call: CallbackQuery, state: FSMContext):
    subclass_id = int(call.data.replace("subclass_", ""))
    await state.update_data(subclass_id=subclass_id)

    data = await state.get_data()
    class_name = data.get("class_name")

    await state.set_state(CreateCharacter.background_select)

    await call.message.delete()
    await call.message.answer(
        f"**Шаг 2/12: Выберите ПРЕДЫСТОРИЮ**\n"
        f"(Класс: {class_name})\n\n"
        f"📜 **Предыстория** определяет ваше прошлое и **ДАЁТ БОНУСЫ К ХАРАКТЕРИСТИКАМ!** ✨\n\n"
        f"Нажмите на предысторию, чтобы увидеть подробности:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_background_keyboard()
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "subclass_skip")
async def skip_subclass(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.background_select)

    data = await state.get_data()
    class_name = data.get("class_name")

    await call.message.delete()
    await call.message.answer(
        f"**Шаг 2/12: Выберите ПРЕДЫСТОРИЮ**\n"
        f"(Класс: {class_name})\n\n"
        f"📜 **Предыстория** определяет ваше прошлое и **ДАЁТ БОНУСЫ К ХАРАКТЕРИСТИКАМ!** ✨\n\n"
        f"Нажмите на предысторию, чтобы увидеть подробности:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_background_keyboard()
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_classes")
async def back_to_classes(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.class_select)
    await call.message.delete()
    await call.message.answer(
        "**Шаг 1/12: Выберите КЛАСС**\n\nНажмите на класс, чтобы увидеть описание и картинку:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_class_keyboard()
    )
    await call.answer()


# ---------------- ШАГ 2: ПРЕДЫСТОРИЯ (КЛЮЧЕВОЙ ШАГ 5.5e!) ----------------
@dp.callback_query(lambda c: c.data.startswith("bg_"))
async def select_background(call: CallbackQuery, state: FSMContext):
    background = call.data.replace("bg_", "")
    await state.update_data(background=background)
    await state.set_state(CreateCharacter.race_select)

    bg_info = get_background_data(background)
    characteristics = get_background_characteristics(background)
    bg_skills = get_background_skills(background)
    bg_trait = get_background_trait(background)
    bg_tools = get_background_tools(background)

    text = (
        f"📜 **Предыстория: {background}**\n\n"
        f"📖 {bg_info.get('description', 'Нет описания')[:400]}...\n\n"
        f"✨ **Бонусы к характеристикам (ВАЖНО!):**\n"
        f"   • **+2** к **{characteristics[0]}**\n"
        f"   • **+1** к **{characteristics[1]}**\n\n"
        f"**Черта:** {bg_trait if bg_trait else 'Нет'}\n"
        f"**Навыки:** {', '.join(bg_skills) if bg_skills else 'Нет'}\n"
        f"**Инструменты:** {bg_tools if bg_tools else 'Нет'}\n\n"
        f"**Шаг 3/12: Выберите РАСУ**\n"
        f"🧝 Раса даёт врождённые способности (без бонусов к характеристикам в 5.5e!)\n\n"
        f"Нажмите на расу, чтобы увидеть описание и картинку:"
    )

    await call.message.delete()
    await call.message.answer(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_race_keyboard()
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_background")
async def back_to_background(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.background_select)

    data = await state.get_data()
    class_name = data.get("class_name", "")

    await call.message.delete()
    await call.message.answer(
        f"**Шаг 2/12: Выберите ПРЕДЫСТОРИЮ**\n(Класс: {class_name})\n\n"
        f"📜 Предыстория определяет ваше прошлое и даёт бонусы к характеристикам!",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_background_keyboard()
    )
    await call.answer()


# ---------------- ШАГ 3: РАСА (с картинкой и описанием!) ----------------
@dp.callback_query(lambda c: c.data.startswith("race_"))
async def select_race(call: CallbackQuery, state: FSMContext):
    race = call.data.replace("race_", "")
    await state.update_data(race=race)

    # Получаем полную информацию о расе
    race_desc = get_race_description(race)
    race_speed = get_race_speed(race)
    race_size = get_race_size(race)
    has_sub = has_subraces(race)
    subraces_list = get_subraces(race) if has_sub else []

    # Формируем красивое описание
    text = f"🧝 **Раса: {race}**\n\n"
    text += f"📖 {race_desc}\n\n"
    text += f"**🏃 Скорость:** {race_speed} футов\n"
    text += f"**📏 Размер:** {race_size}\n"

    if has_sub and subraces_list:
        text += f"\n**🌟 Доступные подрасы:**\n"
        for sub in subraces_list:
            sub_trait = get_subrace_trait(race, sub)
            text += f"   • **{sub}** — {sub_trait[:50] + '...' if len(sub_trait) > 50 else sub_trait}\n"
        text += f"\n**Шаг 3a/12: Выберите ПОДРАСУ**"
        reply_markup = create_subrace_keyboard(race)
        next_state = CreateCharacter.subrace_select
    else:
        text += f"\n\n**Шаг 4/12: Распределите ХАРАКТЕРИСТИКИ**\n"
        data = await state.get_data()
        background = data.get("background")
        stats = get_initial_stats(background)
        await state.update_data(stats=stats)

        text += f"\n📊 **Базовый набор:** 15, 14, 13, 12, 10, 8\n"
        text += f"✨ **Бонусы от предыстории уже применены!**\n\n"
        text += f"**Текущие характеристики:**\n"
        text += f"💪 STR: {stats['STR']} ({modifier(stats['STR']):+d})\n"
        text += f"🤸 DEX: {stats['DEX']} ({modifier(stats['DEX']):+d})\n"
        text += f"🏋️ CON: {stats['CON']} ({modifier(stats['CON']):+d})\n"
        text += f"🧠 INT: {stats['INT']} ({modifier(stats['INT']):+d})\n"
        text += f"🧙 WIS: {stats['WIS']} ({modifier(stats['WIS']):+d})\n"
        text += f"✨ CHA: {stats['CHA']} ({modifier(stats['CHA']):+d})\n\n"
        text += f"Нажмите на характеристику, чтобы увеличить её (до 18)."

        reply_markup = create_stats_keyboard(stats)
        next_state = CreateCharacter.stats_assign

    await state.set_state(next_state)

    # Отправляем картинку расы (если есть)
    img_path = get_race_image_path(race)
    try:
        await call.message.delete()
        if img_path and os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await call.message.answer_photo(
                photo=photo,
                caption=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await call.message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка отправки картинки расы {race}: {e}")
        await call.message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    await call.answer()


# ---------------- ШАГ 3a: ПОДРАСА (с описанием!) ----------------
@dp.callback_query(lambda c: c.data.startswith("subrace_") and c.data != "subrace_skip")
async def select_subrace(call: CallbackQuery, state: FSMContext):
    subrace = call.data.replace("subrace_", "")
    await state.update_data(subrace=subrace)

    data = await state.get_data()
    race = data.get("race")
    background = data.get("background")

    # Получаем описание подрасы
    sub_desc = get_subrace_description(race, subrace)
    sub_trait = get_subrace_trait(race, subrace)

    # Получаем характеристики с бонусами от предыстории
    stats = get_initial_stats(background)
    await state.update_data(stats=stats)

    await state.set_state(CreateCharacter.stats_assign)

    text = (
        f"🧝 **{race} — {subrace}**\n\n"
        f"📖 {sub_desc}\n\n"
        f"✨ **Особенность:** {sub_trait}\n\n"
        f"**Шаг 4/12: Распределите ХАРАКТЕРИСТИКИ**\n\n"
        f"📊 **Базовый набор:** 15, 14, 13, 12, 10, 8\n"
        f"✨ **Бонусы от предыстории ({background}) уже применены!**\n\n"
        f"**Текущие характеристики:**\n"
        f"💪 STR: {stats['STR']} ({modifier(stats['STR']):+d})\n"
        f"🤸 DEX: {stats['DEX']} ({modifier(stats['DEX']):+d})\n"
        f"🏋️ CON: {stats['CON']} ({modifier(stats['CON']):+d})\n"
        f"🧠 INT: {stats['INT']} ({modifier(stats['INT']):+d})\n"
        f"🧙 WIS: {stats['WIS']} ({modifier(stats['WIS']):+d})\n"
        f"✨ CHA: {stats['CHA']} ({modifier(stats['CHA']):+d})\n\n"
        f"Нажмите на характеристику, чтобы увеличить её (до 18)."
    )

    await call.message.delete()
    await call.message.answer(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_stats_keyboard(stats)
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "subrace_skip")
async def skip_subrace(call: CallbackQuery, state: FSMContext):
    await state.update_data(subrace=None)

    data = await state.get_data()
    background = data.get("background")
    stats = get_initial_stats(background)
    await state.update_data(stats=stats)

    await state.set_state(CreateCharacter.stats_assign)

    text = (
        f"**Шаг 4/12: Распределите ХАРАКТЕРИСТИКИ**\n\n"
        f"📊 **Базовый набор:** 15, 14, 13, 12, 10, 8\n"
        f"✨ **Бонусы от предыстории ({background}) уже применены!**\n\n"
        f"**Текущие характеристики:**\n"
        f"💪 STR: {stats['STR']} ({modifier(stats['STR']):+d})\n"
        f"🤸 DEX: {stats['DEX']} ({modifier(stats['DEX']):+d})\n"
        f"🏋️ CON: {stats['CON']} ({modifier(stats['CON']):+d})\n"
        f"🧠 INT: {stats['INT']} ({modifier(stats['INT']):+d})\n"
        f"🧙 WIS: {stats['WIS']} ({modifier(stats['WIS']):+d})\n"
        f"✨ CHA: {stats['CHA']} ({modifier(stats['CHA']):+d})\n\n"
        f"Нажмите на характеристику, чтобы увеличить её (до 18)."
    )

    await call.message.delete()
    await call.message.answer(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_stats_keyboard(stats)
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_races")
async def back_to_races(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.race_select)
    await call.message.delete()
    await call.message.answer(
        "**Шаг 3/12: Выберите РАСУ**\n\nНажмите на расу, чтобы увидеть описание и картинку:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_race_keyboard()
    )
    await call.answer()


# ---------------- ШАГ 4: ХАРАКТЕРИСТИКИ ----------------
@dp.callback_query(lambda c: c.data.startswith("stat_") and c.data != "stats_confirm")
async def adjust_stat(call: CallbackQuery, state: FSMContext):
    stat = call.data.replace("stat_", "")

    data = await state.get_data()
    stats = data.get("stats", {}).copy()

    # Увеличиваем характеристику (до 18)
    if stats.get(stat, 10) < 18:
        stats[stat] = stats.get(stat, 10) + 1
        await state.update_data(stats=stats)

        text = (
            f"**Шаг 4/12: Распределите ХАРАКТЕРИСТИКИ**\n\n"
            f"**Текущие характеристики:**\n"
            f"💪 STR: {stats.get('STR', 10)} ({modifier(stats.get('STR', 10)):+d})\n"
            f"🤸 DEX: {stats.get('DEX', 10)} ({modifier(stats.get('DEX', 10)):+d})\n"
            f"🏋️ CON: {stats.get('CON', 10)} ({modifier(stats.get('CON', 10)):+d})\n"
            f"🧠 INT: {stats.get('INT', 10)} ({modifier(stats.get('INT', 10)):+d})\n"
            f"🧙 WIS: {stats.get('WIS', 10)} ({modifier(stats.get('WIS', 10)):+d})\n"
            f"✨ CHA: {stats.get('CHA', 10)} ({modifier(stats.get('CHA', 10)):+d})\n\n"
            f"Нажмите на характеристику, чтобы увеличить её (до 18).\n"
            f"Когда закончите, нажмите «Подтвердить характеристики»."
        )

        try:
            await call.message.edit_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=create_stats_keyboard(stats)
            )
        except Exception as e:
            logger.error(f"Ошибка обновления характеристик: {e}")

    await call.answer()


@dp.callback_query(lambda c: c.data == "stats_confirm")
async def confirm_stats(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.name_input)

    data = await state.get_data()
    stats = data.get("stats", {})

    # Сохраняем финальные статы
    await state.update_data(final_stats=stats)

    await call.message.delete()
    await call.message.answer(
        f"**Шаг 5/12: Введите ИМЯ персонажа**\n\n"
        f"✅ Характеристики подтверждены!\n\n"
        f"📊 **Финальные характеристики:**\n"
        f"💪 STR: {stats.get('STR', 10)} ({modifier(stats.get('STR', 10)):+d})\n"
        f"🤸 DEX: {stats.get('DEX', 10)} ({modifier(stats.get('DEX', 10)):+d})\n"
        f"🏋️ CON: {stats.get('CON', 10)} ({modifier(stats.get('CON', 10)):+d})\n"
        f"🧠 INT: {stats.get('INT', 10)} ({modifier(stats.get('INT', 10)):+d})\n"
        f"🧙 WIS: {stats.get('WIS', 10)} ({modifier(stats.get('WIS', 10)):+d})\n"
        f"✨ CHA: {stats.get('CHA', 10)} ({modifier(stats.get('CHA', 10)):+d})\n\n"
        f"Отправьте имя вашего персонажа:",
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()


# ---------------- ШАГ 5: ИМЯ ----------------
@dp.message(CreateCharacter.name_input)
async def set_name(m: Message, state: FSMContext):
    if m.text == "❌ Отмена":
        await cancel_creation(m, state)
        return

    valid, msg = validate_name(m.text)
    if not valid:
        await m.answer(f"{msg}\nПожалуйста, введите другое имя:")
        return

    await state.update_data(name=m.text.strip())
    await m.answer(f"✅ Имя: {m.text.strip()}")

    # Определяем, нужно ли выбирать заклинания
    data = await state.get_data()
    class_name = data.get("class_name")
    class_info = get_class_info(class_name)
    is_spellcaster = class_info.get("spellcasting", False)

    if is_spellcaster:
        await state.set_state(CreateCharacter.spells_cantrips_select)
        await m.answer(
            f"**Шаг 6/12: Выбор ЗАКЛИНАНИЙ**\n\n"
            f"Класс {class_name} умеет использовать магию.\n\n"
            f"🔮 **Заговоры (кантрипы)** — заклинания, которые можно использовать без ограничений.\n\n"
            f"(В разработке: полноценный выбор заклинаний будет добавлен в следующем обновлении)\n\n"
            f"Пока что нажмите «Продолжить» для перехода к следующему шагу.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="▶️ Продолжить")]],
                resize_keyboard=True
            )
        )
    else:
        await go_to_masteries(m, state)


@dp.message(F.text == "▶️ Продолжить")
async def continue_after_spells(m: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == CreateCharacter.spells_cantrips_select.state:
        await go_to_masteries(m, state)
    elif current_state == CreateCharacter.masteries_select.state:
        await go_to_fighting_style(m, state)
    elif current_state == CreateCharacter.fighting_style_select.state:
        await go_to_invocations(m, state)
    elif current_state == CreateCharacter.invocations_select.state:
        await go_to_equipment(m, state)


async def go_to_masteries(m: Message, state: FSMContext):
    """Переход к выбору оружейных приёмов"""
    data = await state.get_data()
    class_name = data.get("class_name")

    # Список воинских классов, которые получают оружейные приёмы
    martial_classes = ["Воин", "Паладин", "Следопыт", "Варвар", "Плут"]

    if class_name in martial_classes:
        await state.set_state(CreateCharacter.masteries_select)

        masteries = get_all_weapon_masteries()

        text = (
            f"**Шаг 7/12: Выберите ОРУЖЕЙНЫЕ ПРИЁМЫ**\n\n"
            f"⚔️ Класс {class_name} получает оружейные приёмы (Weapon Mastery).\n\n"
            f"**Доступные приёмы:**\n"
        )
        for mst in masteries[:8]:
            text += f"• **{mst['name']}**: {mst['effect'][:60]}...\n"

        text += f"\n(В разработке: выбор приёмов будет добавлен в следующем обновлении)\n\n"
        text += f"Пока что нажмите «Продолжить» для перехода к боевым стилям."

        await m.answer(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="▶️ Продолжить")]],
                resize_keyboard=True
            )
        )
    else:
        await go_to_fighting_style(m, state)


async def go_to_fighting_style(m: Message, state: FSMContext):
    """Переход к выбору боевого стиля"""
    data = await state.get_data()
    class_name = data.get("class_name")

    # Классы, которые получают боевой стиль
    fighting_style_classes = ["Воин", "Паладин", "Следопыт"]

    if class_name in fighting_style_classes:
        await state.set_state(CreateCharacter.fighting_style_select)

        styles = get_all_fighting_styles()

        text = (
            f"**Шаг 8/12: Выберите БОЕВОЙ СТИЛЬ**\n\n"
            f"⚔️ Класс {class_name} может выбрать один боевой стиль.\n\n"
            f"**Доступные стили:**\n"
        )
        for style in styles:
            text += f"• **{style['name']}**\n"

        text += f"\n(В разработке: выбор стиля будет добавлен в следующем обновлении)\n\n"
        text += f"Пока что нажмите «Продолжить» для перехода к возваниям."

        await m.answer(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="▶️ Продолжить")]],
                resize_keyboard=True
            )
        )
    else:
        await go_to_invocations(m, state)


async def go_to_invocations(m: Message, state: FSMContext):
    """Переход к выбору таинственных возваний (только для колдуна)"""
    data = await state.get_data()
    class_name = data.get("class_name")

    if class_name == "Колдун":
        await state.set_state(CreateCharacter.invocations_select)

        invocations = get_all_invocations(level=1)

        text = (
            f"**Шаг 9/12: Выберите ТАИНСТВЕННЫЕ ВОЗВАНИЯ**\n\n"
            f"🔮 Колдун может выбрать таинственные возвания — особые силы.\n\n"
            f"**Доступные возвания (1-2 уровень):**\n"
        )
        for inv in invocations[:10]:
            text += f"• **{inv['name']}**: {inv['effect'][:50]}...\n"

        text += f"\n(В разработке: выбор возваний будет добавлен в следующем обновлении)\n\n"
        text += f"Пока что нажмите «Продолжить» для перехода к снаряжению."

        await m.answer(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="▶️ Продолжить")]],
                resize_keyboard=True
            )
        )
    else:
        await go_to_equipment(m, state)


async def go_to_equipment(m: Message, state: FSMContext):
    """Переход к выбору снаряжения"""
    await state.set_state(CreateCharacter.equipment_select)

    data = await state.get_data()
    background = data.get("background")

    await m.answer(
        f"**Шаг 10/12: Выберите СНАРЯЖЕНИЕ**\n\n"
        f"🎒 Предыстория **{background}** предоставляет два варианта стартового снаряжения.\n\n"
        f"Выберите вариант А или Б:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_equipment_keyboard(background)
    )


# ---------------- ШАГ 10: СНАРЯЖЕНИЕ ----------------
@dp.callback_query(lambda c: c.data.startswith("equip_"))
async def select_equipment(call: CallbackQuery, state: FSMContext):
    equipment_choice = call.data.replace("equip_", "")
    await state.update_data(equipment_choice=equipment_choice)
    await state.set_state(CreateCharacter.backstory_input)

    data = await state.get_data()
    background = data.get("background")
    bg_info = get_background_data(background)

    chosen_equipment = bg_info.get(f"equipment_{equipment_choice.lower()}", "Нет описания")

    await call.message.delete()
    await call.message.answer(
        f"🎒 **Выбран вариант снаряжения: {equipment_choice}**\n\n"
        f"**Снаряжение:**\n{chosen_equipment}\n\n"
        f"**Шаг 11/12: История персонажа**\n\n"
        f"📖 Расскажите историю вашего персонажа:\n"
        f"• Откуда он родом?\n"
        f"• Что с ним случилось?\n"
        f"• Какие у него цели?\n\n"
        f"Отправьте текст истории (можно коротко, до 2000 символов):",
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()


# ---------------- ШАГ 11: ИСТОРИЯ ----------------
@dp.message(CreateCharacter.backstory_input)
async def set_backstory(m: Message, state: FSMContext):
    if m.text == "❌ Отмена":
        await cancel_creation(m, state)
        return

    backstory = m.text.strip()
    if len(backstory) > 2000:
        await m.answer("❌ История слишком длинная (максимум 2000 символов). Пожалуйста, сократите:")
        return

    await state.update_data(backstory=backstory)
    await state.set_state(CreateCharacter.image_input)

    await m.answer(
        f"📖 **История сохранена!**\n\n"
        f"**Шаг 12/12: Изображение персонажа**\n\n"
        f"🖼️ Загрузите картинку вашего персонажа (можно портрет или арт).\n\n"
        f"Отправьте изображение, или нажмите «⏩ Пропустить» чтобы пропустить этот шаг.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⏩ Пропустить")]],
            resize_keyboard=True
        )
    )


# ---------------- ШАГ 12: ИЗОБРАЖЕНИЕ И ФИНАЛ ----------------
@dp.message(F.text == "⏩ Пропустить")
async def skip_image(m: Message, state: FSMContext):
    await finalize_character(m, state, image_file_id=None)


@dp.message(CreateCharacter.image_input, F.photo)
async def set_image(m: Message, state: FSMContext):
    photo = m.photo[-1]
    file_id = photo.file_id
    await finalize_character(m, state, image_file_id=file_id)


# ---------------- ФИНАЛЬНОЕ СОХРАНЕНИЕ (ИСПРАВЛЕННАЯ ВЕРСИЯ) ----------------
async def finalize_character(m: Message, state: FSMContext, image_file_id: Optional[str] = None):
    """Финальное сохранение персонажа и генерация PDF (исправленная версия)"""
    temp_pdf_file = None

    try:
        await m.answer("⏳ Создаю персонажа и генерирую PDF...")

        data = await state.get_data()

        # Получаем данные из состояния
        class_name = data.get("class_name")
        background = data.get("background")
        race = data.get("race")
        subrace = data.get("subrace")
        name = data.get("name")
        backstory = data.get("backstory", "Нет истории")
        equipment_choice = data.get("equipment_choice", "A")
        stats = data.get("final_stats", {})

        # Если final_stats нет, берём stats
        if not stats:
            stats = data.get("stats", {})

        # Получаем ID из БД по названиям
        race_id = None
        subrace_id = None
        class_id = None
        background_id = None

        with get_connection() as conn:
            with conn.cursor() as cur:
                # Получаем ID расы
                if race:
                    cur.execute("SELECT id FROM races WHERE name = %s", (race,))
                    result = cur.fetchone()
                    race_id = result[0] if result else None
                    logger.info(f"Race ID for {race}: {race_id}")

                # Получаем ID подрасы
                if subrace and race_id:
                    cur.execute("SELECT id FROM subraces WHERE name = %s AND race_id = %s", (subrace, race_id))
                    result = cur.fetchone()
                    subrace_id = result[0] if result else None
                    logger.info(f"Subrace ID for {subrace}: {subrace_id}")

                # Получаем ID класса
                if class_name:
                    cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                    result = cur.fetchone()
                    class_id = result[0] if result else None
                    logger.info(f"Class ID for {class_name}: {class_id}")

                # Получаем ID предыстории
                if background:
                    cur.execute("SELECT id FROM backgrounds WHERE name = %s", (background,))
                    result = cur.fetchone()
                    background_id = result[0] if result else None
                    logger.info(f"Background ID for {background}: {background_id}")

        # Расчёт HP и AC
        hp = calc_hp(class_id, stats.get("CON", 10), 1) if class_id else 10
        ac = calc_ac(stats.get("DEX", 10))

        # Особенности
        race_traits = get_race_traits_list(race, subrace)
        class_features = get_class_features(class_name, 1)
        bg_info = get_background_data(background)
        bg_skills = get_background_skills(background)
        bg_trait = get_background_trait(background)
        bg_tools = get_background_tools(background)

        # Снаряжение
        equipment_text = bg_info.get(f"equipment_{equipment_choice.lower()}", "")
        equipment_list = [item.strip() for item in equipment_text.split(",") if item.strip()]

        # Валидация
        valid, msg = validate_character(name, class_name, race, background, stats)
        if not valid:
            await m.answer(f"❌ Ошибка валидации: {msg}")
            await state.clear()
            return

        # Сохранение в БД (новая версия с ID)
        char_id = save_character(
            user_id=m.from_user.id,
            name=name,
            race_id=race_id,
            subrace_id=subrace_id,
            class_id=class_id,
            subclass_id=None,  # Пока не реализован выбор подкласса
            background_id=background_id,
            level=1,
            experience=0,
            stats=stats,
            hp=hp,
            ac=ac,
            speed=30,
            selected_skills=bg_skills,
            selected_masteries=[],
            selected_fighting_style=None,
            selected_invocations=[],
            selected_spells=[],
            selected_equipment_choice=equipment_choice,
            backstory=backstory,
            image_file_id=image_file_id,
            alignment="Нейтральное"
        )

        logger.info(f"✅ Персонаж сохранён с ID: {char_id}")

        # Генерация PDF
        pdf_data = {
            "name": name,
            "class_name": class_name,
            "race": f"{race} ({subrace})" if subrace else race,
            "level": 1,
            "stats": stats,
            "hp": hp,
            "ac": ac,
            "skills": bg_skills,
            "equipment": equipment_list,
            "spells": [],
            "proficiency_bonus": calculate_proficiency_bonus(1),
            "background": background,
            "background_trait": bg_trait,
            "background_description": bg_info.get("description", ""),
            "race_traits": race_traits,
            "class_features": class_features,
            "backstory": backstory
        }

        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{safe_name}.pdf")
        temp_pdf_file = tmp.name
        tmp.close()

        pdf_file = generate_pdf(pdf_data, temp_pdf_file)

        caption = (
            f"✅ **Персонаж создан!**\n\n"
            f"📛 **Имя:** {name}\n"
            f"⚔️ **Класс:** {class_name}\n"
            f"📜 **Предыстория:** {background}\n"
            f"🧝 **Раса:** {race}{f' ({subrace})' if subrace else ''}\n"
            f"❤️ **HP:** {hp} | 🛡️ **AC:** {ac}\n"
            f"📊 **Уровень:** 1\n\n"
            f"🎯 **Характеристики:**\n"
            f"💪 STR: {stats.get('STR', 10)} | 🤸 DEX: {stats.get('DEX', 10)}\n"
            f"🏋️ CON: {stats.get('CON', 10)} | 🧠 INT: {stats.get('INT', 10)}\n"
            f"🧙 WIS: {stats.get('WIS', 10)} | ✨ CHA: {stats.get('CHA', 10)}"
        )

        if image_file_id:
            await m.answer_photo(photo=image_file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
        else:
            await m.answer(caption, parse_mode=ParseMode.MARKDOWN)

        if pdf_file and os.path.exists(pdf_file):
            await m.answer_document(
                FSInputFile(pdf_file, filename=f"{safe_name}_character_sheet.pdf"),
                caption="📄 Лист персонажа в формате PDF (D&D 5.5e 2024)"
            )
            await asyncio.sleep(1)

        await m.answer("🎮 Главное меню", reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при создании персонажа: {e}", exc_info=True)
        await m.answer("❌ Произошла ошибка при создании персонажа. Попробуйте позже.")
        await state.clear()

    finally:
        if temp_pdf_file and os.path.exists(temp_pdf_file):
            try:
                os.remove(temp_pdf_file)
            except:
                pass


# ---------------- ПРОСМОТР И УДАЛЕНИЕ ПЕРСОНАЖЕЙ ----------------
@dp.message(F.text == "📋 Мои персонажи")
async def list_characters(m: Message):
    characters = get_user_characters(m.from_user.id)

    if not characters:
        await m.answer("📭 У вас пока нет созданных персонажей. Используйте кнопку '🎲 Создать персонажа'")
        return

    await m.answer(
        f"📋 **Ваши персонажи ({len(characters)}):**\n\nНажмите на персонажа для просмотра.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_character_list_keyboard(m.from_user.id)
    )


@dp.callback_query(lambda c: c.data.startswith("view_"))
async def view_character(call: CallbackQuery):
    char_id = int(call.data.replace("view_", ""))
    character = get_character_by_id(char_id)

    if not character:
        await call.answer("❌ Персонаж не найден")
        return

    info = (
        f"📛 **{character['name']}**\n\n"
        f"🧝 **Раса:** {character.get('race_name', 'Неизвестно')}\n"
        f"⚔️ **Класс:** {character.get('class_name', 'Неизвестно')}\n"
        f"📜 **Предыстория:** {character.get('background_name', 'Нет')}\n"
        f"📊 **Уровень:** {character['level']}\n"
        f"❤️ **HP:** {character['hp']} | 🛡️ **AC:** {character['ac']}\n\n"
        f"**Характеристики:**\n"
        f"💪 STR: {character['str']} | 🤸 DEX: {character['dex']}\n"
        f"🏋️ CON: {character['con']} | 🧠 INT: {character['int']}\n"
        f"🧙 WIS: {character['wis']} | ✨ CHA: {character['cha']}\n\n"
        f"**История:** {character.get('backstory', 'Нет истории')[:200]}..."
    )

    if character.get('image_file_id'):
        await call.message.answer_photo(photo=character['image_file_id'], caption=info, parse_mode=ParseMode.MARKDOWN)
    else:
        await call.message.answer(info, parse_mode=ParseMode.MARKDOWN)

    await call.answer()


@dp.message(F.text == "🗑 Удалить персонажа")
async def delete_character_menu(m: Message):
    characters = get_user_characters(m.from_user.id)

    if not characters:
        await m.answer("📭 У вас нет персонажей для удаления.")
        return

    await m.answer(
        "🗑 **Выберите персонажа для удаления:**\n\n⚠️ Внимание! Удаление необратимо.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_delete_keyboard(characters)
    )


@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def confirm_delete(call: CallbackQuery):
    char_id = int(call.data.replace("delete_", ""))
    character = get_character_by_id(char_id)

    if not character:
        await call.answer("❌ Персонаж не найден")
        return

    if delete_character(char_id, call.from_user.id):
        await call.message.edit_text(f"✅ Персонаж **{character['name']}** успешно удалён!",
                                     parse_mode=ParseMode.MARKDOWN)
    else:
        await call.message.edit_text("❌ Не удалось удалить персонажа.")

    await call.answer()


@dp.callback_query(lambda c: c.data == "cancel_delete")
async def cancel_delete(call: CallbackQuery):
    await call.message.edit_text("❌ Удаление отменено")
    await call.answer()


@dp.callback_query(lambda c: c.data == "cancel_creation")
async def cancel_creation_callback(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Создание персонажа отменено")
    await call.answer()


@dp.message(Command("skip"))
async def skip_command(m: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == CreateCharacter.image_input.state:
        await finalize_character(m, state, image_file_id=None)
    else:
        await m.answer("❌ Команда /skip доступна только на шаге загрузки изображения")


# ---------------- ОБРАБОТЧИК НЕИЗВЕСТНЫХ КОМАНД ----------------
@dp.message()
async def unknown_command(m: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state:
        await m.answer(
            "⏳ Вы находитесь в процессе создания персонажа.\n\n"
            "Пожалуйста, следуйте инструкциям или нажмите «❌ Отмена» чтобы начать заново.",
            reply_markup=cancel_kb()
        )
    else:
        await m.answer(
            "❓ Я не понимаю эту команду.\n\nИспользуйте кнопки меню или команду /help для получения справки.",
            reply_markup=main_menu()
        )


# ---------------- ЗАПУСК ----------------
async def main():
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК БОТА D&D CHARACTER CREATOR 5.5e (2024)")
    logger.info("=" * 50)

    try:
        from db import init_database, migrate_database
        init_database()
        migrate_database()
        logger.info("✅ База данных готова")

        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook удалён")

        bot_info = await bot.get_me()
        logger.info(f"✅ Бот: @{bot_info.username}")
        logger.info(f"   Ссылка: https://t.me/{bot_info.username}")

        logger.info("=" * 50)
        logger.info("🎲 БОТ ГОТОВ К РАБОТЕ!")
        logger.info("📨 Ожидание сообщений...")
        logger.info("=" * 50)

        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
    finally:
        logger.info("🛑 Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())