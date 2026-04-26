#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot.py - D&D Character Creator Bot for D&D 5.5e (2024)
Полностью переработанная версия с автоматическим:
- распределением характеристик (умные бонусы от предыстории)
- выдачей снаряжения от класса (с выбором А/Б для Воина)
- выдачей оружейных приёмов (автоматически, без участия игрока)
- правильным порядком шагов (снаряжение → характеристики → имя)
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
    modifier, calculate_proficiency_bonus, calc_hp, calc_ac_with_armor,

    # Расы
    get_race_list, get_race_info, get_race_description,
    get_race_speed, get_race_size, has_subraces, get_subraces,
    get_subrace_description, get_subrace_trait, get_race_traits_list,
    get_race_image_path,

    # Классы
    get_class_list, get_class_info, get_class_description,
    get_subclasses_for_class, get_class_image_path,

    # Предыстории
    get_background_list, get_background_data, get_background_by_name,
    get_background_characteristics, get_background_trait,
    get_background_skills, get_background_tools,
    get_background_description, get_equipment_choice,

    # Характеристики (АВТОМАТИЧЕСКИЕ)
    get_initial_stats_intelligent,

    # Заклинания
    get_recommended_spells, get_spells_for_class,
    get_cantrips_for_class_with_details, get_level1_spells_for_class_with_details,

    # Снаряжение и броня
    get_class_equipment, get_armor_by_name,

    # Оружие и приёмы
    auto_assign_masteries, get_weapon_by_name,

    # Боевые стили
    get_all_fighting_styles, get_fighting_styles_for_class,

    # Возвания
    get_all_invocations,

    # Валидация
    validate_character, validate_name,

    # Вспомогательные
    get_class_features, get_class_by_name,
)
from pdf_generator import generate_pdf

# ---------------- CONFIG ----------------
load_dotenv()

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


# ---------------- FSM STATES (ПРАВИЛЬНЫЙ ПОРЯДОК) ----------------
class CreateCharacter(StatesGroup):
    # Шаг 1: КЛАСС
    class_select = State()
    subclass_select = State()  # 1a. Подкласс (для жреца/друида/колдуна)

    # Шаг 2: ПРЕДЫСТОРИЯ
    background_select = State()

    # Шаг 3: РАСА
    race_select = State()
    subrace_select = State()

    # Шаг 4: СНАРЯЖЕНИЕ ОТ КЛАССА
    equipment_choice_select = State()

    # Шаг 5: ХАРАКТЕРИСТИКИ (АВТО)
    stats_auto = State()

    # Шаг 6: ИМЯ
    name_input = State()

    # Шаг 7: ЗАКЛИНАНИЯ
    spells_method_select = State()
    spells_cantrips_select = State()
    spells_level1_select = State()

    # Шаг 8: БОЕВОЙ СТИЛЬ
    fighting_style_select = State()

    # Шаг 9: ВОЗВАНИЯ (только для колдуна)
    invocations_select = State()

    # Шаг 10: СНАРЯЖЕНИЕ ОТ ПРЕДЫСТОРИИ
    background_equipment_select = State()

    # Шаг 11: ИСТОРИЯ
    backstory_input = State()

    # Шаг 12: ИЗОБРАЖЕНИЕ
    image_input = State()


# ---------------- MENU ----------------
def main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🎲 Создать персонажа")],
        [KeyboardButton(text="📋 Мои персонажи")],
        [KeyboardButton(text="🗑 Удалить персонажа")],
        [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


# ---------------- INLINE KEYBOARDS ----------------
def create_class_keyboard() -> InlineKeyboardMarkup:
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
    subclasses = get_subclasses_for_class(class_name, level=1)

    if not subclasses:
        return None

    buttons = []
    for sub in subclasses:
        buttons.append([InlineKeyboardButton(
            text=f"📖 {sub['name']} — {sub['description'][:40]}...",
            callback_data=f"subclass_{sub['id']}"
        )])

    buttons.append([InlineKeyboardButton(text="➡️ Пропустить (выбрать позже)", callback_data="subclass_skip")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к классам", callback_data="back_to_classes")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_background_keyboard() -> InlineKeyboardMarkup:
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
    subraces = get_subraces(race)

    if not subraces:
        return None

    buttons = []
    for subrace in subraces:
        buttons.append([InlineKeyboardButton(text=subrace, callback_data=f"subrace_{subrace}")])

    buttons.append([InlineKeyboardButton(text="➡️ Пропустить", callback_data="subrace_skip")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к расам", callback_data="back_to_races")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_equipment_choice_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора варианта снаряжения для Воина"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Вариант А (тяжёлая броня, двуручный меч)", callback_data="equipment_A")],
        [InlineKeyboardButton(text="🏹 Вариант Б (лёгкая броня, длинный лук)", callback_data="equipment_B")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_race")]
    ])


def create_spells_method_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 Рекомендованный набор (для новичков)", callback_data="spells_recommended")],
        [InlineKeyboardButton(text="📖 Выбрать самому", callback_data="spells_manual")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_name")]
    ])


def create_cantrips_keyboard(class_name: str, selected: List[str], max_count: int) -> InlineKeyboardMarkup:
    cantrips = get_cantrips_for_class_with_details(class_name)
    buttons = []

    buttons.append([InlineKeyboardButton(
        text=f"📖 Выберите {max_count} заговора(ов) | Выбрано: {len(selected)}/{max_count}",
        callback_data="cantrips_info"
    )])

    for spell in cantrips:
        is_selected = spell['name'] in selected
        emoji = "✅" if is_selected else "🔘"
        school_emoji = {
            "Очарование": "🎭", "Некромантия": "💀", "Превращение": "🔄",
            "Вызов": "🔮", "Воплощение": "⚡", "Иллюзия": "👻",
            "Прорицание": "👁️"
        }.get(spell.get('school', ''), "✨")

        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {school_emoji} {spell['name']}",
            callback_data=f"cantrip_{spell['id']}"
        )])
        buttons.append([InlineKeyboardButton(
            text=f"   📖 {spell.get('description', 'Нет описания')[:60]}...",
            callback_data="spell_info"
        )])

    buttons.append([InlineKeyboardButton(text="✅ Подтвердить выбор", callback_data="cantrips_confirm")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_spells_method")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_level1_spells_keyboard(class_name: str, selected: List[str], max_count: int) -> InlineKeyboardMarkup:
    spells = get_level1_spells_for_class_with_details(class_name)
    buttons = []

    buttons.append([InlineKeyboardButton(
        text=f"🔮 Выберите {max_count} заклинание(й) 1 ур. | Выбрано: {len(selected)}/{max_count}",
        callback_data="level1_info"
    )])

    for spell in spells:
        is_selected = spell['name'] in selected
        emoji = "✅" if is_selected else "🔘"
        school_emoji = {
            "Очарование": "🎭", "Некромантия": "💀", "Превращение": "🔄",
            "Вызов": "🔮", "Воплощение": "⚡", "Иллюзия": "👻",
            "Прорицание": "👁️"
        }.get(spell.get('school', ''), "✨")

        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {school_emoji} {spell['name']}",
            callback_data=f"level1_{spell['id']}"
        )])
        buttons.append([InlineKeyboardButton(
            text=f"   📖 {spell.get('description', 'Нет описания')[:60]}...",
            callback_data="spell_info"
        )])

    buttons.append([InlineKeyboardButton(text="✅ Подтвердить выбор", callback_data="level1_confirm")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к заговорам", callback_data="back_to_cantrips")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_fighting_style_keyboard(class_name: str) -> InlineKeyboardMarkup:
    styles = get_fighting_styles_for_class(class_name)
    buttons = []

    for s in styles:
        buttons.append([InlineKeyboardButton(
            text=f"🛡️ {s['name']}: {s['description'][:50]}",
            callback_data=f"style_{s['id']}"
        )])

    buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="style_confirm")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_equipment")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_invocations_keyboard(level: int = 1) -> InlineKeyboardMarkup:
    invocations = get_all_invocations(level)
    buttons = []

    for inv in invocations[:8]:
        emoji = "🔮" if inv['level_required'] == 1 else "🔷"
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {inv['name']} (ур. {inv['level_required']}): {inv['effect'][:50]}",
            callback_data=f"inv_{inv['id']}"
        )])

    buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="inv_confirm")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_style")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_background_equipment_keyboard(background: str) -> InlineKeyboardMarkup:
    bg_info = get_background_data(background)
    equipment_a = bg_info.get("equipment_a", "Нет описания")[:60]
    equipment_b = bg_info.get("equipment_b", "Нет описания")[:60]

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📦 Вариант А: {equipment_a}...", callback_data="bg_equip_A")],
        [InlineKeyboardButton(text=f"🎒 Вариант Б: {equipment_b}...", callback_data="bg_equip_B")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_invocations")]
    ])


def create_character_list_keyboard(user_id: int) -> Optional[InlineKeyboardMarkup]:
    characters = get_user_characters(user_id)
    if not characters:
        return None

    buttons = []
    for char in characters:
        text = f"{char['name']} - {char['class_name']} ур.{char['level']}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"view_{char['id']}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_delete_keyboard(characters: list) -> InlineKeyboardMarkup:
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
        "Я помогу тебе создать персонажа для Dungeons & Dragons 5-й редакции.\n\n"
        "**Как начать:**\n"
        "Нажми кнопку «🎲 Создать персонажа» и следуй инструкциям!\n\n"
        "**Что нового:**\n"
        "• Характеристики распределяются автоматически ✨\n"
        "• Снаряжение выдаётся по классу ⚔️\n"
        "• Оружейные приёмы подбираются автоматически 🎯"
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
        "**Как создать персонажа:**\n"
        "1️⃣ Выберите **КЛАСС**\n"
        "2️⃣ Выберите **ПРЕДЫСТОРИЮ**\n"
        "3️⃣ Выберите **РАСУ**\n"
        "4️⃣ Выберите **СНАРЯЖЕНИЕ** (для Воина есть выбор)\n"
        "5️⃣ **ХАРАКТЕРИСТИКИ** рассчитаются автоматически\n"
        "6️⃣ Введите **ИМЯ**\n"
        "7️⃣ Выберите **ЗАКЛИНАНИЯ**\n"
        "8️⃣ Выберите **БОЕВОЙ СТИЛЬ** (если есть)\n"
        "9️⃣ Выберите **ВОЗВАНИЯ** (только для колдуна)\n"
        "🔟 Выберите **СНАРЯЖЕНИЕ ОТ ПРЕДЫСТОРИИ**\n"
        "1️⃣1️⃣ Напишите **ИСТОРИЮ**\n"
        "1️⃣2️⃣ Загрузите **ИЗОБРАЖЕНИЕ**\n\n"
        "**Другие команды:**\n"
        "• /start - Главное меню\n"
        "• /help - Эта справка\n"
        "• /skip - Пропустить загрузку картинки"
    )
    await m.answer(help_text, parse_mode=ParseMode.MARKDOWN)


@dp.message(F.text == "❓ Помощь")
async def help_button(m: Message):
    await help_command(m)


@dp.message(F.text == "ℹ️ О боте")
async def info_button(m: Message):
    info_text = (
        "ℹ️ D&D Character Creator\n\n"
        "Особенности:\n"
        "• 16 рас с подрасами и картинками\n"
        "• 13 классов с подклассами и картинками\n"
        "• 16 предысторий с бонусами к характеристикам\n"
        "• Автоматическое распределение характеристик\n"
        "• Автоматическая выдача снаряжения и приёмов\n"
        "• Рекомендованные наборы заклинаний\n"
        "• Генерация PDF листа персонажа\n\n"
        "Есть идеи? Пишите: @danilenkokoko007_official\n\n"
        "Приятной игры! 🎲"
    )
    await m.answer(info_text, parse_mode=None)


# ---------------- ШАГ 1: КЛАСС ----------------
@dp.message(F.text == "🎲 Создать персонажа")
async def create_char_start(m: Message, state: FSMContext):
    await state.set_state(CreateCharacter.class_select)
    await m.answer(
        "🏰 **Создание нового персонажа**\n\n"
        "**Шаг 1/12: Выберите КЛАСС**\n\n"
        "Класс определяет вашу роль в приключении.\n"
        "Нажмите на класс, чтобы увидеть описание:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_class_keyboard()
    )


@dp.callback_query(lambda c: c.data.startswith("class_"))
async def select_class(call: CallbackQuery, state: FSMContext):
    class_name = call.data.replace("class_", "")
    await state.update_data(class_name=class_name)

    class_desc = get_class_description(class_name)
    class_info = get_class_info(class_name)

    subclasses = get_subclasses_for_class(class_name, level=1)

    text = (
        f"⚔️ **{class_name}**\n\n"
        f"📖 {class_desc}\n\n"
        f"**📊 Характеристики класса:**\n"
        f"• ❤️ **Хитовый кубик:** d{class_info.get('hit_die', 6)}\n"
        f"• 🎯 **Основные характеристики:** {', '.join(class_info.get('primary_stats', []))}\n"
        f"• 🛡️ **Спасброски:** {', '.join(class_info.get('saving_throws', []))}\n"
        f"• 🔮 **Заклинания:** {'Да' if class_info.get('spellcasting', False) else 'Нет'}\n"
    )

    if subclasses and class_name in ["Жрец", "Друид", "Колдун"]:
        text += f"\n**📖 На 1 уровне вы можете выбрать подкласс:**\n"
        for sub in subclasses:
            text += f"   • **{sub['name']}** — {sub['description'][:60]}...\n"
        text += f"\nВы можете выбрать подкласс сейчас или позже."
        reply_markup = create_subclass_keyboard(class_name)
        next_state = CreateCharacter.subclass_select
    else:
        text += f"\n\n**Шаг 2/12: Выберите ПРЕДЫСТОРИЮ**\n(она влияет на распределение характеристик!)"
        reply_markup = create_background_keyboard()
        next_state = CreateCharacter.background_select

    await state.set_state(next_state)

    img_path = get_class_image_path(class_name)
    try:
        await call.message.delete()
        if img_path and os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await call.message.answer_photo(photo=photo, caption=text, parse_mode=ParseMode.MARKDOWN,
                                            reply_markup=reply_markup)
        else:
            await call.message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка отправки картинки класса: {e}")
        await call.message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("subclass_") and c.data != "subclass_skip")
async def select_subclass(call: CallbackQuery, state: FSMContext):
    subclass_id = int(call.data.replace("subclass_", ""))
    await state.update_data(subclass_id=subclass_id)
    await state.set_state(CreateCharacter.background_select)

    data = await state.get_data()
    class_name = data.get("class_name")

    await call.message.delete()
    await call.message.answer(
        f"**Шаг 2/12: Выберите ПРЕДЫСТОРИЮ**\n(Класс: {class_name})\n\n"
        f"📜 Предыстория определяет ваше прошлое и **ВЛИЯЕТ НА ХАРАКТЕРИСТИКИ!** ✨",
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
        f"**Шаг 2/12: Выберите ПРЕДЫСТОРИЮ**\n(Класс: {class_name})\n\n"
        f"📜 Предыстория определяет ваше прошлое и **ВЛИЯЕТ НА ХАРАКТЕРИСТИКИ!** ✨",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_background_keyboard()
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_classes")
async def back_to_classes(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.class_select)
    await call.message.delete()
    await call.message.answer(
        "**Шаг 1/12: Выберите КЛАСС**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_class_keyboard()
    )
    await call.answer()


# ---------------- ШАГ 2: ПРЕДЫСТОРИЯ ----------------
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
        f"✨ **Бонусы к характеристикам:**\n"
        f"   • **+2** к **{characteristics[0]}**\n"
        f"   • **+1** к **{characteristics[1]}**\n\n"
        f"**Черта:** {bg_trait if bg_trait else 'Нет'}\n"
        f"**Навыки:** {', '.join(bg_skills) if bg_skills else 'Нет'}\n"
        f"**Инструменты:** {bg_tools if bg_tools else 'Нет'}\n\n"
        f"**Шаг 3/12: Выберите РАСУ**\n"
        f"🧝 Раса даёт врождённые способности (без бонусов к характеристикам!)"
    )

    await call.message.delete()
    await call.message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=create_race_keyboard())
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_background")
async def back_to_background(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.background_select)
    await call.message.delete()
    await call.message.answer(
        "**Шаг 2/12: Выберите ПРЕДЫСТОРИЮ**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_background_keyboard()
    )
    await call.answer()


# ---------------- ШАГ 3: РАСА ----------------
@dp.callback_query(lambda c: c.data.startswith("race_"))
async def select_race(call: CallbackQuery, state: FSMContext):
    race = call.data.replace("race_", "")
    await state.update_data(race=race)

    race_desc = get_race_description(race)
    race_speed = get_race_speed(race)
    race_size = get_race_size(race)
    has_sub = has_subraces(race)
    subraces_list = get_subraces(race) if has_sub else []

    text = f"🧝 **Раса: {race}**\n\n📖 {race_desc}\n\n**🏃 Скорость:** {race_speed} футов\n**📏 Размер:** {race_size}\n"

    if has_sub and subraces_list:
        text += f"\n**🌟 Доступные подрасы:**\n"
        for sub in subraces_list:
            sub_trait = get_subrace_trait(race, sub)
            text += f"   • **{sub}** — {sub_trait[:50] + '...' if len(sub_trait) > 50 else sub_trait}\n"
        text += f"\n**Шаг 3a/12: Выберите ПОДРАСУ**"
        reply_markup = create_subrace_keyboard(race)
        next_state = CreateCharacter.subrace_select
    else:
        # Переходим к выбору снаряжения
        text += f"\n\n**Шаг 4/12: Выберите снаряжение для класса**"
        reply_markup = create_equipment_choice_keyboard()
        next_state = CreateCharacter.equipment_choice_select

    await state.set_state(next_state)

    img_path = get_race_image_path(race)
    try:
        await call.message.delete()
        if img_path and os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await call.message.answer_photo(photo=photo, caption=text, parse_mode=ParseMode.MARKDOWN,
                                            reply_markup=reply_markup)
        else:
            await call.message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка отправки картинки расы: {e}")
        await call.message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("subrace_") and c.data != "subrace_skip")
async def select_subrace(call: CallbackQuery, state: FSMContext):
    subrace = call.data.replace("subrace_", "")
    await state.update_data(subrace=subrace)

    data = await state.get_data()
    race = data.get("race")
    sub_desc = get_subrace_description(race, subrace)
    sub_trait = get_subrace_trait(race, subrace)

    text = (
        f"🧝 **{race} — {subrace}**\n\n📖 {sub_desc}\n\n✨ **Особенность:** {sub_trait}\n\n"
        f"**Шаг 4/12: Выберите снаряжение для класса**"
    )

    await state.set_state(CreateCharacter.equipment_choice_select)
    await call.message.delete()
    await call.message.answer(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_equipment_choice_keyboard()
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "subrace_skip")
async def skip_subrace(call: CallbackQuery, state: FSMContext):
    await state.update_data(subrace=None)
    await state.set_state(CreateCharacter.equipment_choice_select)

    data = await state.get_data()
    race = data.get("race")

    await call.message.delete()
    await call.message.answer(
        f"🧝 **Раса: {race}**\n\n**Шаг 4/12: Выберите снаряжение для класса**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_equipment_choice_keyboard()
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_races")
async def back_to_races(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.race_select)
    await call.message.delete()
    await call.message.answer(
        "**Шаг 3/12: Выберите РАСУ**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_race_keyboard()
    )
    await call.answer()


# ---------------- ШАГ 4: СНАРЯЖЕНИЕ ОТ КЛАССА ----------------
@dp.callback_query(lambda c: c.data.startswith("equipment_"))
async def select_equipment_choice(call: CallbackQuery, state: FSMContext):
    choice = call.data.replace("equipment_", "")
    await state.update_data(equipment_choice=choice)

    data = await state.get_data()
    class_name = data.get("class_name")

    # Получаем выбранный вариант снаряжения
    equipment_list = get_class_equipment(class_name, choice)
    if equipment_list:
        eq = equipment_list[0]
        await apply_equipment_and_masteries(call.message, state, eq, class_name)
    else:
        # Если нет снаряжения, переходим к характеристикам
        await auto_calculate_stats(call.message, state)

    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_race")
async def back_to_race(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.race_select)
    await call.message.delete()
    await call.message.answer(
        "**Шаг 3/12: Выберите РАСУ**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_race_keyboard()
    )
    await call.answer()


async def apply_equipment_and_masteries(m: Message, state: FSMContext, equipment: Dict[str, Any], class_name: str):
    """Применяет снаряжение и переходит к расчёту характеристик"""

    armor_name = equipment.get('armor')
    weapon_name = equipment.get('weapon')
    secondary_weapon = equipment.get('secondary_weapon')
    other_items = equipment.get('other_items', '')
    coins = equipment.get('coins', 0)

    await state.update_data(selected_armor=armor_name)
    await state.update_data(selected_weapon=weapon_name)
    await state.update_data(selected_secondary_weapon=secondary_weapon)
    await state.update_data(selected_other_items=other_items)
    await state.update_data(selected_coins=coins)

    # Автоматически назначаем оружейные приёмы
    masteries = auto_assign_masteries(weapon_name, class_name)
    await state.update_data(selected_masteries=masteries)

    # Формируем сообщение о выданном снаряжении
    text = f"**Шаг 4/12: Снаряжение выдано!**\n\n"
    text += f"⚔️ **Класс:** {class_name}\n"
    text += f"🛡️ **Броня:** {armor_name if armor_name else 'нет'}\n"
    text += f"🗡️ **Оружие:** {weapon_name}\n"
    if secondary_weapon:
        text += f"🔪 **Доп. оружие:** {secondary_weapon}\n"
    if other_items:
        text += f"🎒 **Прочее:** {other_items}\n"
    if coins > 0:
        text += f"💰 **Монеты:** {coins} зм\n"

    if masteries:
        text += f"\n🎯 **Оружейные приёмы (выданы автоматически):**\n"
        for mastery in masteries:
            text += f"   • {mastery}\n"

    text += f"\nНажмите «Продолжить» для расчёта характеристик."

    await state.set_state(CreateCharacter.stats_auto)
    await m.answer(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="▶️ Продолжить")]],
            resize_keyboard=True
        )
    )


# ---------------- ШАГ 5: ХАРАКТЕРИСТИКИ (АВТОМАТИЧЕСКИЕ) ----------------
async def auto_calculate_stats(m: Message, state: FSMContext):
    """Автоматический расчёт характеристик"""
    data = await state.get_data()
    class_name = data.get("class_name")
    background = data.get("background")
    race = data.get("race")
    subrace = data.get("subrace", "")

    # Рассчитываем характеристики автоматически
    stats = get_initial_stats_intelligent(background, class_name)
    await state.update_data(stats=stats)
    await state.update_data(final_stats=stats)

    race_text = f"{race} ({subrace})" if subrace else race
    class_primary = get_class_info(class_name).get('primary_stats', [])
    bg_chars = get_background_characteristics(background)

    text = (
        f"**Шаг 5/12: Характеристики рассчитаны!**\n\n"
        f"🧝 **Раса:** {race_text}\n"
        f"📜 **Предыстория:** {background}\n"
        f"⚔️ **Класс:** {class_name}\n\n"
        f"✨ **Бонусы распределены с учётом класса:**\n"
        f"   • Основные класса: {', '.join(class_primary)}\n"
        f"   • Бонусы предыстории: +2 к {bg_chars[0]}, +1 к {bg_chars[1]}\n\n"
        f"**📊 Ваши характеристики:**\n"
        f"💪 **Сила (STR):** {stats['STR']} ({modifier(stats['STR']):+d})\n"
        f"🤸 **Ловкость (DEX):** {stats['DEX']} ({modifier(stats['DEX']):+d})\n"
        f"🏋️ **Телосложение (CON):** {stats['CON']} ({modifier(stats['CON']):+d})\n"
        f"🧠 **Интеллект (INT):** {stats['INT']} ({modifier(stats['INT']):+d})\n"
        f"🧙 **Мудрость (WIS):** {stats['WIS']} ({modifier(stats['WIS']):+d})\n"
        f"✨ **Харизма (CHA):** {stats['CHA']} ({modifier(stats['CHA']):+d})\n\n"
        f"Нажмите «Продолжить», чтобы перейти к вводу имени."
    )

    await state.set_state(CreateCharacter.name_input)
    await m.answer(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="▶️ Продолжить")]],
            resize_keyboard=True
        )
    )


# ---------------- ШАГ 6: ИМЯ ----------------
@dp.message(F.text == "▶️ Продолжить")
async def continue_after_stats(m: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state == CreateCharacter.stats_auto.state:
        await auto_calculate_stats(m, state)
    elif current_state == CreateCharacter.name_input.state:
        # Переходим к заклинаниям
        await go_to_spells(m, state)
    else:
        await m.answer("⏳ Следуйте инструкциям...")


async def go_to_spells(m: Message, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    class_info = get_class_info(class_name)
    is_spellcaster = class_info.get("spellcasting", False) and class_name not in ["Паладин", "Следопыт"]

    if is_spellcaster:
        await state.set_state(CreateCharacter.spells_method_select)
        await m.answer(
            f"**Шаг 7/12: Выбор ЗАКЛИНАНИЙ**\n\n"
            f"Класс {class_name} умеет использовать магию.\n\n"
            f"Выберите, как хотите получить заклинания:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_spells_method_keyboard()
        )
    else:
        await go_to_fighting_style(m, state)


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
    logger.info(f"✅ Имя сохранено: {m.text.strip()}")
    await m.answer(f"✅ Имя: {m.text.strip()}")

    await go_to_spells(m, state)


# ---------------- ШАГ 7: ЗАКЛИНАНИЯ ----------------
@dp.callback_query(lambda c: c.data == "back_to_name")
async def back_to_name(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.name_input)
    await call.message.delete()
    await call.message.answer(
        "**Шаг 6/12: Введите ИМЯ персонажа**\n\nОтправьте имя вашего персонажа:",
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "spells_recommended")
async def use_recommended_spells(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")

    recommended = get_recommended_spells(class_name)
    selected_spells = []

    for spell in recommended.get("cantrips", []):
        selected_spells.append(spell['name'])
    for spell in recommended.get("level1", []):
        selected_spells.append(spell['name'])

    await state.update_data(selected_spells=selected_spells)

    text = (
        f"**✅ Рекомендованные заклинания для {class_name} выбраны!**\n\n"
        f"📖 **Заговоры:** {', '.join([s['name'] for s in recommended.get('cantrips', [])])}\n\n"
        f"🔮 **Заклинания 1 уровня:** {', '.join([s['name'] for s in recommended.get('level1', [])])}\n\n"
        f"Нажмите «Продолжить» для перехода к боевому стилю."
    )

    await call.message.answer(text, parse_mode=ParseMode.MARKDOWN)
    await go_to_fighting_style(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "spells_manual")
async def manual_spells(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")

    cantrips_count_map = {
        "Волшебник": 3, "Бард": 2, "Жрец": 3, "Друид": 2,
        "Колдун": 2, "Чародей": 4, "Артефактор": 2
    }
    max_cantrips = cantrips_count_map.get(class_name, 2)

    await state.update_data(max_cantrips=max_cantrips)
    await state.update_data(selected_cantrips=[])
    await state.update_data(selected_level1_spells=[])
    await state.set_state(CreateCharacter.spells_cantrips_select)

    text = (
        f"**Шаг 7/12: Выбор ЗАГОВОРОВ (кантрипов)**\n\n"
        f"📖 Класс **{class_name}** может выбрать **{max_cantrips}** заговора(ов).\n\n"
        f"🔘 Нажмите на заклинание, чтобы выбрать/отменить.\n"
        f"✅ Зелёной галочкой отмечены выбранные.\n\n"
        f"**Доступные заговоры:**"
    )

    await call.message.delete()
    await call.message.answer(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_cantrips_keyboard(class_name, [], max_cantrips)
    )
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("cantrip_") and c.data != "cantrips_confirm")
async def select_cantrip(call: CallbackQuery, state: FSMContext):
    spell_id = int(call.data.replace("cantrip_", ""))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM spells WHERE id = %s", (spell_id,))
            result = cur.fetchone()
            spell_name = result[0] if result else None

    if not spell_name:
        await call.answer("❌ Заклинание не найдено")
        return

    data = await state.get_data()
    selected = data.get("selected_cantrips", [])
    max_cantrips = data.get("max_cantrips", 2)
    class_name = data.get("class_name")

    if spell_name in selected:
        selected.remove(spell_name)
        await call.answer(f"❌ Заговор '{spell_name}' удалён")
    else:
        if len(selected) >= max_cantrips:
            await call.answer(f"⚠️ Можно выбрать не более {max_cantrips} заговоров!", show_alert=True)
            return
        selected.append(spell_name)
        await call.answer(f"✅ Заговор '{spell_name}' добавлен")

    await state.update_data(selected_cantrips=selected)

    try:
        await call.message.edit_reply_markup(
            reply_markup=create_cantrips_keyboard(class_name, selected, max_cantrips)
        )
    except Exception as e:
        logger.error(f"Ошибка обновления клавиатуры: {e}")


@dp.callback_query(lambda c: c.data == "cantrips_confirm")
async def confirm_cantrips(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_cantrips", [])
    max_cantrips = data.get("max_cantrips", 2)
    class_name = data.get("class_name")

    if len(selected) < max_cantrips:
        await call.answer(f"⚠️ Нужно выбрать {max_cantrips} заговора(ов)!", show_alert=True)
        return

    await state.update_data(selected_spells=selected.copy())

    level1_count_map = {
        "Волшебник": 4, "Бард": 4, "Жрец": 4, "Друид": 4,
        "Колдун": 2, "Чародей": 2, "Артефактор": 2
    }
    max_level1 = level1_count_map.get(class_name, 2)
    await state.update_data(max_level1=max_level1)
    await state.update_data(selected_level1_spells=[])
    await state.set_state(CreateCharacter.spells_level1_select)

    text = (
        f"**Шаг 7/12: Выбор ЗАКЛИНАНИЙ 1 УРОВНЯ**\n\n"
        f"🔮 Класс **{class_name}** может выбрать **{max_level1}** заклинание(й).\n\n"
        f"✅ Вы выбрали заговоры: {', '.join(selected)}\n\n"
        f"**Доступные заклинания 1 уровня:**"
    )

    await call.message.delete()
    await call.message.answer(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_level1_spells_keyboard(class_name, [], max_level1)
    )
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("level1_") and c.data != "level1_confirm")
async def select_level1_spell(call: CallbackQuery, state: FSMContext):
    spell_id = int(call.data.replace("level1_", ""))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM spells WHERE id = %s", (spell_id,))
            result = cur.fetchone()
            spell_name = result[0] if result else None

    if not spell_name:
        await call.answer("❌ Заклинание не найдено")
        return

    data = await state.get_data()
    selected = data.get("selected_level1_spells", [])
    max_level1 = data.get("max_level1", 2)
    class_name = data.get("class_name")

    if spell_name in selected:
        selected.remove(spell_name)
        await call.answer(f"❌ Заклинание '{spell_name}' удалено")
    else:
        if len(selected) >= max_level1:
            await call.answer(f"⚠️ Можно выбрать не более {max_level1} заклинаний!", show_alert=True)
            return
        selected.append(spell_name)
        await call.answer(f"✅ Заклинание '{spell_name}' добавлено")

    await state.update_data(selected_level1_spells=selected)

    try:
        await call.message.edit_reply_markup(
            reply_markup=create_level1_spells_keyboard(class_name, selected, max_level1)
        )
    except Exception as e:
        logger.error(f"Ошибка обновления клавиатуры: {e}")


@dp.callback_query(lambda c: c.data == "level1_confirm")
async def confirm_level1_spells(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_level1_spells", [])
    max_level1 = data.get("max_level1", 2)
    selected_cantrips = data.get("selected_cantrips", [])

    if len(selected) < max_level1:
        await call.answer(f"⚠️ Нужно выбрать {max_level1} заклинание(й)!", show_alert=True)
        return

    all_selected = selected_cantrips + selected
    await state.update_data(selected_spells=all_selected)

    text = (
        f"**✅ Заклинания выбраны!**\n\n"
        f"📖 **Заговоры ({len(selected_cantrips)}):** {', '.join(selected_cantrips)}\n\n"
        f"🔮 **Заклинания 1 уровня ({len(selected)}):** {', '.join(selected)}\n\n"
        f"Нажмите «Продолжить» для перехода к боевому стилю."
    )

    await call.message.answer(text, parse_mode=ParseMode.MARKDOWN)
    await go_to_fighting_style(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_spells_method")
async def back_to_spells_method(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.spells_method_select)
    await call.message.delete()
    await call.message.answer(
        "**Шаг 7/12: Выбор ЗАКЛИНАНИЙ**\n\nВыберите, как хотите получить заклинания:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_spells_method_keyboard()
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_cantrips")
async def back_to_cantrips(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    selected_cantrips = data.get("selected_cantrips", [])
    max_cantrips = data.get("max_cantrips", 2)

    await state.set_state(CreateCharacter.spells_cantrips_select)
    await call.message.delete()
    await call.message.answer(
        f"**Шаг 7/12: Выбор ЗАГОВОРОВ (кантрипов)**\n\n"
        f"📖 Класс **{class_name}** может выбрать **{max_cantrips}** заговора(ов).\n\n"
        f"🔘 Нажмите на заклинание, чтобы выбрать/отменить.\n\n"
        f"**Доступные заговоры:**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_cantrips_keyboard(class_name, selected_cantrips, max_cantrips)
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "spell_info")
async def spell_info(call: CallbackQuery):
    await call.answer("Нажмите на название заклинания, чтобы выбрать/отменить", show_alert=False)


# ---------------- ШАГ 8: БОЕВОЙ СТИЛЬ ----------------
async def go_to_fighting_style(m: Message, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")

    fighting_style_classes = ["Воин", "Паладин", "Следопыт"]

    if class_name in fighting_style_classes:
        await state.set_state(CreateCharacter.fighting_style_select)
        text = (
            f"**Шаг 8/12: Выберите БОЕВОЙ СТИЛЬ**\n\n"
            f"⚔️ Класс {class_name} может выбрать один боевой стиль.\n\n"
            f"Доступные стили:"
        )
        await m.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=create_fighting_style_keyboard(class_name))
    else:
        await go_to_invocations(m, state)


@dp.callback_query(lambda c: c.data.startswith("style_") and c.data != "style_confirm")
async def select_fighting_style(call: CallbackQuery, state: FSMContext):
    style_id = int(call.data.replace("style_", ""))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM fighting_styles WHERE id = %s", (style_id,))
            result = cur.fetchone()
            style_name = result[0] if result else None

    if style_name:
        await state.update_data(selected_fighting_style=style_name)
        await call.answer(f"✅ Выбран стиль: {style_name}")


@dp.callback_query(lambda c: c.data == "style_confirm")
async def confirm_fighting_style(call: CallbackQuery, state: FSMContext):
    await go_to_invocations(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_equipment")
async def back_to_equipment(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.equipment_choice_select)
    await call.message.delete()
    await call.message.answer(
        "**Шаг 4/12: Выберите снаряжение для класса**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_equipment_choice_keyboard()
    )
    await call.answer()


# ---------------- ШАГ 9: ВОЗВАНИЯ (ДЛЯ КОЛДУНА) ----------------
async def go_to_invocations(m: Message, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")

    if class_name == "Колдун":
        await state.set_state(CreateCharacter.invocations_select)
        await m.answer(
            f"**Шаг 9/12: Выберите ТАИНСТВЕННЫЕ ВОЗВАНИЯ**\n\n"
            f"🔮 Колдун может выбрать таинственные возвания — особые силы.\n\n"
            f"Доступные возвания (1-2 уровень):",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_invocations_keyboard(level=1)
        )
    else:
        await go_to_background_equipment(m, state)


@dp.callback_query(lambda c: c.data.startswith("inv_") and c.data != "inv_confirm")
async def select_invocation(call: CallbackQuery, state: FSMContext):
    inv_id = int(call.data.replace("inv_", ""))

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM invocations WHERE id = %s", (inv_id,))
            result = cur.fetchone()
            inv_name = result[0] if result else None

    if not inv_name:
        await call.answer("❌ Возвание не найдено")
        return

    data = await state.get_data()
    selected = data.get("selected_invocations", [])

    if inv_name in selected:
        selected.remove(inv_name)
        await call.answer(f"❌ Возвание '{inv_name}' удалено")
    else:
        if len(selected) >= 2:
            await call.answer("⚠️ Можно выбрать не более 2 возваний на 1 уровне!", show_alert=True)
            return
        selected.append(inv_name)
        await call.answer(f"✅ Возвание '{inv_name}' добавлено")

    await state.update_data(selected_invocations=selected)


@dp.callback_query(lambda c: c.data == "inv_confirm")
async def confirm_invocations(call: CallbackQuery, state: FSMContext):
    await go_to_background_equipment(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_style")
async def back_to_style(call: CallbackQuery, state: FSMContext):
    await go_to_fighting_style(call.message, state)
    await call.answer()


# ---------------- ШАГ 10: СНАРЯЖЕНИЕ ОТ ПРЕДЫСТОРИИ ----------------
async def go_to_background_equipment(m: Message, state: FSMContext):
    await state.set_state(CreateCharacter.background_equipment_select)

    data = await state.get_data()
    background = data.get("background")

    await m.answer(
        f"**Шаг 10/12: Выберите СНАРЯЖЕНИЕ ОТ ПРЕДЫСТОРИИ**\n\n"
        f"🎒 Предыстория **{background}** предоставляет два варианта стартового снаряжения.\n\n"
        f"Выберите вариант А или Б:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_background_equipment_keyboard(background)
    )


@dp.callback_query(lambda c: c.data.startswith("bg_equip_"))
async def select_background_equipment(call: CallbackQuery, state: FSMContext):
    equipment_choice = call.data.replace("bg_equip_", "")
    await state.update_data(background_equipment_choice=equipment_choice)
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


@dp.callback_query(lambda c: c.data == "back_to_invocations")
async def back_to_invocations(call: CallbackQuery, state: FSMContext):
    await go_to_invocations(call.message, state)
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
        f"🖼️ Загрузите картинку вашего персонажа.\n\n"
        f"Отправьте изображение, или нажмите «⏩ Пропустить».",
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


# ---------------- ФИНАЛЬНОЕ СОХРАНЕНИЕ ----------------
async def finalize_character(m: Message, state: FSMContext, image_file_id: Optional[str] = None):
    temp_pdf_file = None

    try:
        await m.answer("⏳ Создаю персонажа и генерирую PDF...")

        data = await state.get_data()

        class_name = data.get("class_name")
        background = data.get("background")
        race = data.get("race")
        subrace = data.get("subrace")
        name = data.get("name")
        backstory = data.get("backstory", "Нет истории")
        background_equipment_choice = data.get("background_equipment_choice", "A")
        stats = data.get("final_stats", {})
        selected_masteries = data.get("selected_masteries", [])
        selected_fighting_style = data.get("selected_fighting_style")
        selected_invocations = data.get("selected_invocations", [])
        selected_spells = data.get("selected_spells", [])
        selected_weapon = data.get("selected_weapon")
        selected_armor = data.get("selected_armor")

        if not stats:
            stats = data.get("stats", {})

        if not name:
            logger.error("❌ Имя персонажа не найдено в state!")
            await m.answer("❌ Ошибка: имя персонажа не сохранено. Попробуйте ещё раз.")
            await state.clear()
            return

        logger.info(f"📛 Сохраняем персонажа: {name}")

        race_id = subrace_id = class_id = background_id = None

        with get_connection() as conn:
            with conn.cursor() as cur:
                if race:
                    cur.execute("SELECT id FROM races WHERE name = %s", (race,))
                    result = cur.fetchone()
                    race_id = result[0] if result else None

                if subrace and race_id:
                    cur.execute("SELECT id FROM subraces WHERE name = %s AND race_id = %s", (subrace, race_id))
                    result = cur.fetchone()
                    subrace_id = result[0] if result else None

                if class_name:
                    cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                    result = cur.fetchone()
                    class_id = result[0] if result else None

                if background:
                    cur.execute("SELECT id FROM backgrounds WHERE name = %s", (background,))
                    result = cur.fetchone()
                    background_id = result[0] if result else None

        # Расчёт HP и AC с учётом брони
        has_shield = selected_armor == "Щит" if selected_armor else False
        ac = calc_ac_with_armor(stats.get("DEX", 10), selected_armor, has_shield)
        hp = calc_hp(class_id, stats.get("CON", 10), 1) if class_id else 10

        race_traits = get_race_traits_list(race, subrace)
        class_features = get_class_features(class_name, 1)
        bg_info = get_background_data(background)
        bg_skills = get_background_skills(background)
        bg_trait = get_background_trait(background)
        bg_tools = get_background_tools(background)

        equipment_text = bg_info.get(f"equipment_{background_equipment_choice.lower()}", "")
        equipment_list = [item.strip() for item in equipment_text.split(",") if item.strip()]

        if selected_weapon:
            equipment_list.append(selected_weapon)
        if selected_armor:
            equipment_list.append(selected_armor)

        char_id = save_character(
            user_id=m.from_user.id,
            name=name,
            race_id=race_id,
            subrace_id=subrace_id,
            class_id=class_id,
            subclass_id=None,
            background_id=background_id,
            level=1,
            experience=0,
            stats=stats,
            hp=hp,
            ac=ac,
            speed=30,
            selected_skills=bg_skills,
            selected_masteries=selected_masteries,
            selected_fighting_style=selected_fighting_style,
            selected_invocations=selected_invocations,
            selected_spells=selected_spells,
            selected_weapon=selected_weapon,
            selected_armor=selected_armor,
            selected_equipment_choice=background_equipment_choice,
            backstory=backstory,
            image_file_id=image_file_id,
            alignment="Нейтральное"
        )

        pdf_data = {
            "name": name, "class_name": class_name, "race": f"{race} ({subrace})" if subrace else race,
            "level": 1, "stats": stats, "hp": hp, "ac": ac, "skills": bg_skills,
            "equipment": equipment_list, "spells": selected_spells,
            "proficiency_bonus": calculate_proficiency_bonus(1), "background": background,
            "background_trait": bg_trait, "background_description": bg_info.get("description", ""),
            "race_traits": race_traits, "class_features": class_features, "backstory": backstory
        }

        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{safe_name}.pdf")
        temp_pdf_file = tmp.name
        tmp.close()

        pdf_file = generate_pdf(pdf_data, temp_pdf_file)

        caption = (
            f"✅ **Персонаж создан!**\n\n"
            f"📛 **Имя:** {name}\n⚔️ **Класс:** {class_name}\n📜 **Предыстория:** {background}\n"
            f"🧝 **Раса:** {race}{f' ({subrace})' if subrace else ''}\n"
            f"❤️ **HP:** {hp} | 🛡️ **AC:** {ac}\n"
            f"🎯 **Характеристики:** STR {stats.get('STR', 10)} | DEX {stats.get('DEX', 10)} | CON {stats.get('CON', 10)} | "
            f"INT {stats.get('INT', 10)} | WIS {stats.get('WIS', 10)} | CHA {stats.get('CHA', 10)}"
        )

        if image_file_id:
            await m.answer_photo(photo=image_file_id, caption=caption, parse_mode=ParseMode.MARKDOWN)
        else:
            await m.answer(caption, parse_mode=ParseMode.MARKDOWN)

        if pdf_file and os.path.exists(pdf_file):
            await m.answer_document(FSInputFile(pdf_file, filename=f"{safe_name}_character_sheet.pdf"),
                                    caption="📄 Лист персонажа в формате PDF")

        await m.answer("🎮 Главное меню", reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при создании персонажа: {e}", exc_info=True)
        await m.answer("❌ Произошла ошибка. Попробуйте позже.")
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
        await m.answer("📭 У вас пока нет персонажей.")
        return

    await m.answer(
        f"📋 **Ваши персонажи ({len(characters)}):**",
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
        f"📛 **{character['name']}**\n\n🧝 **Раса:** {character.get('race_name', 'Неизвестно')}\n"
        f"⚔️ **Класс:** {character.get('class_name', 'Неизвестно')}\n"
        f"📜 **Предыстория:** {character.get('background_name', 'Нет')}\n"
        f"📊 **Уровень:** {character['level']}\n❤️ **HP:** {character['hp']} | 🛡️ **AC:** {character['ac']}\n\n"
        f"**Характеристики:** STR {character['str']} | DEX {character['dex']} | CON {character['con']} | "
        f"INT {character['int']} | WIS {character['wis']} | CHA {character['cha']}\n\n"
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
        "🗑 **Выберите персонажа для удаления:**\n\n⚠️ Удаление необратимо.",
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
        await call.message.edit_text(f"✅ Персонаж **{character['name']}** удалён!", parse_mode=ParseMode.MARKDOWN)
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
        await m.answer("❌ /skip доступен только на шаге загрузки изображения")


# ---------------- ОБРАБОТЧИК НЕИЗВЕСТНЫХ КОМАНД ----------------
@dp.message()
async def unknown_command(m: Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state:
        await m.answer(
            "⏳ Вы в процессе создания персонажа.\n\nСледуйте инструкциям или нажмите «❌ Отмена».",
            reply_markup=cancel_kb()
        )
    else:
        await m.answer(
            "❓ Я не понимаю эту команду.\n\nИспользуйте кнопки меню или /help.",
            reply_markup=main_menu()
        )


# ---------------- ЗАПУСК ----------------
async def main():
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК БОТА D&D CHARACTER CREATOR 5.5e")
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

        logger.info("🎲 БОТ ГОТОВ К РАБОТЕ!")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())