#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot.py - D&D Character Creator Bot for D&D 5.5e (2024)
Обновлённая версия с правильной последовательностью шагов
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
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from dotenv import load_dotenv

from db import (
    save_character,
    get_user_characters,
    get_character_by_id,
    delete_character,
    get_connection,
    get_spell_by_id,
)
from dnd_logic import (
    modifier, calculate_proficiency_bonus, calc_hp, calc_ac_with_armor,
    get_race_list, get_race_description,
    get_race_speed, get_race_size, has_subraces, get_subraces,
    get_subrace_description, get_subrace_trait, get_race_traits_list,
    get_race_image_path, get_race_image_exists,
    get_class_list, get_class_info, get_class_description,
    get_subclasses_for_class, get_class_image_path, get_class_image_exists,
    get_background_list, get_background_by_name,
    get_background_characteristics, get_background_trait,
    get_background_skills, get_background_tools,
    get_background_description, get_equipment_choice,
    get_class_starting_stats, calculate_final_stats_with_background,
    get_class_equipment,
    auto_assign_masteries,
    get_fighting_styles_for_class,
    get_all_invocations,
    validate_name,
    get_class_features, get_class_by_name,
    get_class_spell_counts
)
from pdf_generator import generate_pdf
from spell_selector import SpellSelector, get_category_icon

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


# ---------------- FSM STATES ----------------
class CreateCharacter(StatesGroup):
    class_select = State()
    subclass_select = State()
    class_equipment_select = State()
    spells_cantrips_category = State()
    spells_cantrips_list = State()
    spells_cantrips_detail = State()
    spells_level1_category = State()
    spells_level1_list = State()
    spells_level1_detail = State()
    fighting_style_select = State()
    invocations_select = State()
    background_select = State()
    background_equipment_select = State()
    race_select = State()
    subrace_select = State()
    name_input = State()
    backstory_input = State()
    image_input = State()


# ---------------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------------

def format_stats_display(stats: Dict[str, int]) -> str:
    return (f"💪 STR: {stats['STR']} ({modifier(stats['STR']):+d})\n"
            f"🤸 DEX: {stats['DEX']} ({modifier(stats['DEX']):+d})\n"
            f"🏋️ CON: {stats['CON']} ({modifier(stats['CON']):+d})\n"
            f"🧠 INT: {stats['INT']} ({modifier(stats['INT']):+d})\n"
            f"🧙 WIS: {stats['WIS']} ({modifier(stats['WIS']):+d})\n"
            f"✨ CHA: {stats['CHA']} ({modifier(stats['CHA']):+d})")


def main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🎲 Создать персонажа")],
        [KeyboardButton(text="📋 Мои персонажи")],
        [KeyboardButton(text="🗑 Удалить персонажа")],
        [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


def skip_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏩ Пропустить"), KeyboardButton(text="❌ Отмена")]],
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


def create_class_equipment_keyboard(class_name: str) -> Optional[InlineKeyboardMarkup]:
    equipment = get_class_equipment(class_name)
    if len(equipment) <= 1:
        return None
    buttons = []
    for eq in equipment:
        choice = eq.get('choice', 'A')
        weapon = eq.get('weapon', 'нет оружия')
        armor = eq.get('armor', 'нет брони')
        buttons.append([InlineKeyboardButton(
            text=f"📦 Вариант {choice}: {weapon}, {armor}",
            callback_data=f"class_equip_{choice}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к классам", callback_data="back_to_classes")])
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
    buttons.append([InlineKeyboardButton(text="➡️ Пропустить", callback_data="subclass_skip")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к классам", callback_data="back_to_classes")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_category_keyboard(categories: Dict[str, Dict], spell_type: str,
                             selected_count: int, required_count: int) -> InlineKeyboardMarkup:
    buttons = []
    if required_count > 0:
        buttons.append([InlineKeyboardButton(text=f"📖 Выбрано: {selected_count}/{required_count}", callback_data="progress_info")])
    for cat_name, cat_data in categories.items():
        icon = cat_data.get('icon', '✨')
        count = len(cat_data.get('spells', []))
        buttons.append([InlineKeyboardButton(text=f"{icon} {cat_name} ({count})", callback_data=f"{spell_type}_cat_{cat_name}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_spell_list_keyboard(spells: List[Dict], spell_type: str,
                               selected_spells: List[str], category: str) -> InlineKeyboardMarkup:
    buttons = []
    for spell in spells:
        spell_id = spell.get('id')
        spell_name = spell.get('name', 'Unknown')
        is_selected = spell_name in selected_spells
        emoji = "✅" if is_selected else "🔘"
        buttons.append([InlineKeyboardButton(text=f"{emoji} {spell_name}", callback_data=f"{spell_type}_view_{spell_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data=f"{spell_type}_back_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_spell_detail_keyboard(spell_id: int, spell_name: str, spell_type: str,
                                 is_selected: bool, remaining: int) -> InlineKeyboardMarkup:
    buttons = []
    if is_selected:
        buttons.append([InlineKeyboardButton(text="❌ Удалить", callback_data=f"{spell_type}_remove_{spell_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="✅ Выбрать", callback_data=f"{spell_type}_add_{spell_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data=f"{spell_type}_back_list")])
    if remaining > 0:
        buttons.append([InlineKeyboardButton(text=f"Осталось выбрать: {remaining}", callback_data="progress_info")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_fighting_style_keyboard(class_name: str) -> InlineKeyboardMarkup:
    styles = get_fighting_styles_for_class(class_name)
    buttons = []
    for s in styles:
        buttons.append([InlineKeyboardButton(text=f"🛡️ {s['name']}: {s['description'][:50]}", callback_data=f"style_{s['id']}")])
    buttons.append([InlineKeyboardButton(text="➡️ Пропустить", callback_data="style_skip")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_spells")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_invocations_keyboard(level: int = 1) -> InlineKeyboardMarkup:
    invocations = get_all_invocations(level)
    if not invocations:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Пропустить", callback_data="inv_skip")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_fighting")]
        ])
    buttons = []
    for inv in invocations[:8]:
        emoji = "🔮" if inv['level_required'] == 1 else "🔷"
        buttons.append([InlineKeyboardButton(text=f"{emoji} {inv['name']} (ур. {inv['level_required']})", callback_data=f"inv_{inv['id']}")])
    buttons.append([InlineKeyboardButton(text="➡️ Пропустить", callback_data="inv_skip")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_fighting")])
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
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_background_equipment_keyboard(background: str) -> InlineKeyboardMarkup:
    bg_info = get_background_by_name(background)
    if not bg_info:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Ошибка", callback_data="cancel_creation")]])
    equip_a = bg_info.get('equipment_a', 'Нет описания')[:60]
    equip_b = bg_info.get('equipment_b', 'Нет описания')[:60]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📦 Вариант А: {equip_a}...", callback_data="bg_equip_A")],
        [InlineKeyboardButton(text=f"🎒 Вариант Б: {equip_b}...", callback_data="bg_equip_B")],
        [InlineKeyboardButton(text="⬅️ Назад к предыстории", callback_data="back_to_background")]
    ])


def create_race_keyboard() -> InlineKeyboardMarkup:
    races = get_race_list()
    buttons = []
    row = []
    for i, race in enumerate(races):
        row.append(InlineKeyboardButton(text=race, callback_data=f"race_{race}"))
        if len(row) == 2 or i == len(races) - 1:
            buttons.append(row)
            row = []
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")])
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


def create_character_list_keyboard(user_id: int) -> Optional[InlineKeyboardMarkup]:
    characters = get_user_characters(user_id)
    if not characters:
        return None
    buttons = []
    for char in characters:
        buttons.append([InlineKeyboardButton(text=f"{char['name']} - {char['class_name']} ур.{char['level']}", callback_data=f"view_{char['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_delete_keyboard(characters: list) -> InlineKeyboardMarkup:
    buttons = []
    for char in characters:
        buttons.append([InlineKeyboardButton(text=f"🗑 {char['name']} ({char['class_name']})", callback_data=f"delete_{char['id']}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============================================================
# ОСНОВНЫЕ ФУНКЦИИ ПОРЯДКА ШАГОВ
# ============================================================

async def start_cantrips_selection(m: Message, state: FSMContext):
    """Начало выбора заговоров"""
    data = await state.get_data()
    selector_data = data.get("spell_selector", {})
    selector = SpellSelector.from_dict(selector_data)

    if not selector.has_cantrips:
        await start_level1_selection(m, state)
        return

    categories = selector.get_cantrip_categories()
    selected_count, required = selector.get_cantrip_progress()

    if not categories:
        await m.answer("❌ Нет доступных заговоров для этого класса")
        await go_to_fighting_style(m, state)
        return

    await state.set_state(CreateCharacter.spells_cantrips_category)
    await m.answer(
        f"📖 **Шаг 3/12: Выбор ЗАГОВОРОВ**\n\n"
        f"Класс **{selector.class_name}** может выбрать {required} заговор(а).\n"
        f"Выберите категорию для просмотра заговоров:",
        parse_mode=None,
        reply_markup=create_category_keyboard(categories, "cantrip", selected_count, required)
    )


async def start_level1_selection(m: Message, state: FSMContext):
    """Начало выбора заклинаний 1 уровня"""
    data = await state.get_data()
    selector_data = data.get("spell_selector", {})
    selector = SpellSelector.from_dict(selector_data)

    if not selector.has_level1_spells:
        await go_to_fighting_style(m, state)
        return

    categories = selector.get_level1_categories()
    selected_count, required = selector.get_level1_progress()

    if not categories:
        await m.answer("❌ Нет доступных заклинаний 1 уровня для этого класса")
        await go_to_fighting_style(m, state)
        return

    await state.set_state(CreateCharacter.spells_level1_category)
    await m.answer(
        f"🔮 **Шаг 4/12: Выбор ЗАКЛИНАНИЙ 1 УРОВНЯ**\n\n"
        f"Класс **{selector.class_name}** может выбрать {required} заклинание(й).\n"
        f"Выберите категорию для просмотра заклинаний:",
        parse_mode=None,
        reply_markup=create_category_keyboard(categories, "level1", selected_count, required)
    )


async def go_to_spells(m: Message, state: FSMContext):
    """Переход к выбору заклинаний после класса и снаряжения"""
    data = await state.get_data()
    class_name = data.get("class_name")
    class_info = get_class_info(class_name)
    spell_counts = get_class_spell_counts(class_name)

    is_spellcaster = class_info.get("spellcasting", False) and spell_counts.get('cantrips', 0) > 0

    if is_spellcaster:
        selector = SpellSelector(class_name)
        await state.update_data(spell_selector=selector.to_dict())
        await start_cantrips_selection(m, state)
    else:
        await go_to_fighting_style(m, state)


async def go_to_fighting_style(m: Message, state: FSMContext):
    """Переход к выбору боевого стиля"""
    data = await state.get_data()
    class_name = data.get("class_name")
    fighting_style_classes = ["Воин", "Паладин", "Следопыт"]

    if class_name in fighting_style_classes:
        await state.set_state(CreateCharacter.fighting_style_select)
        await m.answer(
            f"⚔️ **Шаг 5/12: Выбор БОЕВОГО СТИЛЯ**\n\n"
            f"Класс **{class_name}** может выбрать один боевой стиль.\n\n"
            f"Боевой стиль даёт постоянный бонус в бою.",
            parse_mode=None,
            reply_markup=create_fighting_style_keyboard(class_name)
        )
    else:
        await go_to_invocations(m, state)


async def go_to_invocations(m: Message, state: FSMContext):
    """Переход к выбору возваний (только для колдуна)"""
    data = await state.get_data()
    class_name = data.get("class_name")

    if class_name == "Колдун":
        await state.set_state(CreateCharacter.invocations_select)
        invocations = get_all_invocations(level=1)
        if invocations:
            await m.answer(
                f"🔮 **Шаг 6/12: Выбор ТАИНСТВЕННЫХ ВОЗВАНИЙ**\n\n"
                f"Колдун может выбрать таинственные возвания.\n"
                f"Вы можете выбрать до 2 возваний на 1 уровне.",
                parse_mode=None,
                reply_markup=create_invocations_keyboard(level=1)
            )
        else:
            await m.answer("📖 Нет доступных возваний для вашего уровня.")
            await go_to_background(m, state)
    else:
        await go_to_background(m, state)


async def go_to_background(m: Message, state: FSMContext):
    """Переход к выбору предыстории"""
    await state.set_state(CreateCharacter.background_select)
    await m.answer(
        f"📜 **Шаг 7/12: Выбор ПРЕДЫСТОРИИ**\n\n"
        f"Предыстория определяет ваше прошлое и даёт бонусы к характеристикам.\n\n"
        f"Выберите предысторию:",
        parse_mode=None,
        reply_markup=create_background_keyboard()
    )


async def go_to_name(m: Message, state: FSMContext):
    """Переход к вводу имени"""
    await state.set_state(CreateCharacter.name_input)
    await m.answer(
        "📛 **Шаг 11/12: Введите ИМЯ персонажа**\n\n"
        "Имя может быть любым (от 2 до 50 символов).\n\n"
        "Введите имя:",
        parse_mode=None,
        reply_markup=cancel_kb()
    )


async def go_to_backstory(m: Message, state: FSMContext):
    """Переход к вводу истории"""
    await state.set_state(CreateCharacter.backstory_input)
    await m.answer(
        "📖 **Шаг 12/12: История персонажа**\n\n"
        "Расскажите историю вашего персонажа:\n"
        "- Откуда он родом?\n"
        "- Что привело его к приключениям?\n"
        "- Какие у него цели?\n\n"
        "Введите историю (максимум 2000 символов):",
        parse_mode=None,
        reply_markup=cancel_kb()
    )


async def calculate_and_show_stats(m: Message, state: FSMContext):
    """Рассчитывает и показывает финальные характеристики"""
    data = await state.get_data()
    class_name = data.get("class_name")
    background = data.get("background")
    equipment_choice = data.get("equipment_choice", "A")

    starting_stats = get_class_starting_stats(class_name, equipment_choice)
    final_stats = calculate_final_stats_with_background(class_name, background, starting_stats)

    await state.update_data(final_stats=final_stats)
    await state.update_data(stats=final_stats)

    class_info = get_class_info(class_name)
    class_id = None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
            result = cur.fetchone()
            class_id = result[0] if result else None

    hp = calc_hp(class_id, final_stats.get("CON", 10), 1) if class_id else 10
    selected_armor = data.get("selected_armor")
    ac = calc_ac_with_armor(final_stats.get("DEX", 10), selected_armor)

    await state.update_data(hp=hp, ac=ac)

    stats_text = format_stats_display(final_stats)
    bg_chars = get_background_characteristics(background)

    await m.answer(
        f"📊 **Шаг 9/12: ХАРАКТЕРИСТИКИ РАССЧИТАНЫ!**\n\n"
        f"⚔️ **Класс:** {class_name}\n"
        f"📜 **Предыстория:** {background}\n\n"
        f"✨ **Бонусы предыстории:** +2 к {bg_chars[0]}, +1 к {bg_chars[1]}\n\n"
        f"📊 **Итоговые характеристики:**\n"
        f"{stats_text}\n\n"
        f"❤️ **Хиты (HP):** {hp}\n"
        f"🛡️ **Класс брони (AC):** {ac}\n\n"
        f"Теперь выберите РАСУ:",
        parse_mode=None,
        reply_markup=create_race_keyboard()
    )

    await state.set_state(CreateCharacter.race_select)


async def finalize_character(m: Message, state: FSMContext, image_file_id: Optional[str] = None):
    """Финальная генерация персонажа и PDF"""
    temp_pdf_file = None
    try:
        await m.answer("⏳ Создаю персонажа и генерирую PDF...", reply_markup=ReplyKeyboardRemove())
        data = await state.get_data()
        class_name = data.get("class_name")
        background = data.get("background")
        race = data.get("race")
        subrace = data.get("subrace")
        name = data.get("name")
        backstory = data.get("backstory", "Нет истории")
        background_equipment_choice = data.get("background_equipment_choice", "A")
        stats = data.get("final_stats", {})
        if not stats:
            stats = data.get("stats", {})
        selector_data = data.get("spell_selector", {})
        selector = SpellSelector.from_dict(selector_data)
        selected_spells = selector.get_all_selected_spells()
        selected_masteries = data.get("selected_masteries", [])
        selected_fighting_style = data.get("selected_fighting_style")
        selected_invocations = data.get("selected_invocations", [])
        selected_weapon = data.get("selected_weapon")
        selected_armor = data.get("selected_armor")
        if not name:
            await m.answer("❌ Ошибка: имя не сохранено.", reply_markup=main_menu())
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
        ac = calc_ac_with_armor(stats.get("DEX", 10), selected_armor)
        hp = calc_hp(class_id, stats.get("CON", 10), 1) if class_id else 10
        race_traits = get_race_traits_list(race, subrace)
        class_features = get_class_features(class_name, 1) if class_name else []
        bg_info = get_background_by_name(background) if background else None
        bg_skills = bg_info.get('skills', []) if bg_info else []
        bg_trait = bg_info.get('trait', "Нет") if bg_info else "Нет"
        equipment_list = []
        if selected_weapon:
            equipment_list.append(selected_weapon)
        if selected_armor:
            equipment_list.append(selected_armor)
        if data.get("selected_other_items"):
            equipment_list.append(data.get("selected_other_items"))
        if bg_info:
            chosen_equipment_key = f"equipment_{background_equipment_choice.lower()}"
            equipment_text = bg_info.get(chosen_equipment_key, "")
            for item in equipment_text.split(","):
                item = item.strip()
                if item and item not in equipment_list:
                    equipment_list.append(item)
        save_character(
            user_id=m.from_user.id, name=name, race_id=race_id, subrace_id=subrace_id,
            class_id=class_id, subclass_id=None, background_id=background_id, level=1, experience=0,
            stats=stats, hp=hp, ac=ac, speed=30, selected_skills=bg_skills,
            selected_masteries=selected_masteries, selected_fighting_style=selected_fighting_style,
            selected_invocations=selected_invocations, selected_spells=selected_spells,
            selected_weapon=selected_weapon, selected_armor=selected_armor,
            selected_equipment_choice=background_equipment_choice, backstory=backstory,
            image_file_id=image_file_id, alignment="Нейтральное"
        )
        pdf_data = {
            "name": name, "class_name": class_name if class_name else "Без класса",
            "race": f"{race} ({subrace})" if subrace else (race if race else "Неизвестно"),
            "level": 1, "stats": stats, "hp": hp, "ac": ac, "speed": 30,
            "skills": bg_skills, "equipment": equipment_list, "spells": selected_spells,
            "proficiency_bonus": calculate_proficiency_bonus(1),
            "background": background if background else "Нет", "background_trait": bg_trait,
            "background_description": bg_info.get("description", "") if bg_info else "",
            "race_traits": race_traits, "class_features": class_features, "backstory": backstory,
            "alignment": "Нейтральное", "player_name": m.from_user.full_name,
            "experience": 0, "saving_throws": [], "notes": "", "coins": data.get("selected_coins", 0)
        }
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{safe_name}.pdf")
        temp_pdf_file = tmp.name
        tmp.close()
        pdf_file = generate_pdf(pdf_data, temp_pdf_file)
        spells_preview = ""
        if selected_spells:
            spells_preview = f"\n🔮 **Заклинания:** {', '.join(selected_spells[:5])}"
            if len(selected_spells) > 5:
                spells_preview += f" и ещё {len(selected_spells) - 5}"
        caption = (f"✅ **Персонаж создан!**\n\n📛 **{name}**\n⚔️ **Класс:** {class_name}\n"
                   f"📜 **Предыстория:** {background}\n🧝 **Раса:** {race}{f' ({subrace})' if subrace else ''}\n"
                   f"❤️ **HP:** {hp} | 🛡️ **AC:** {ac}\n\n🎯 **Характеристики:**\n{format_stats_display(stats)}{spells_preview}\n\n"
                   f"📄 Лист персонажа в формате PDF прикреплён ниже!")
        if image_file_id:
            await m.answer_photo(photo=image_file_id, caption=caption, parse_mode=None)
        else:
            await m.answer(caption, parse_mode=None)
        if pdf_file and os.path.exists(pdf_file):
            await m.answer_document(FSInputFile(pdf_file, filename=f"{safe_name}_character_sheet.pdf"),
                                    caption="📄 Лист персонажа в формате PDF")
        else:
            logger.error(f"PDF не создан: {pdf_file}")
            await m.answer("⚠️ Не удалось создать PDF файл, но персонаж сохранён!")
        await m.answer("🎮 Главное меню", reply_markup=main_menu())
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка при создании персонажа: {e}", exc_info=True)
        await m.answer(f"❌ Произошла ошибка: {str(e)[:200]}\n\nПерсонаж может быть сохранён, но PDF не создан.",
                       reply_markup=main_menu())
        await state.clear()
    finally:
        if temp_pdf_file and os.path.exists(temp_pdf_file):
            try:
                os.remove(temp_pdf_file)
            except:
                pass


# ============================================================
# START
# ============================================================

@dp.message(Command("start"))
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(
        "🎮 Добро пожаловать в D&D Character Creator 5.5e (2024)!\n\n"
        "Я помогу тебе создать персонажа для Dungeons & Dragons 5-й редакции.\n\n"
        "📋 **Порядок создания:**\n"
        "1️⃣ Выбор класса\n"
        "2️⃣ Выбор снаряжения\n"
        "3️⃣ Выбор заклинаний\n"
        "4️⃣ Выбор боевого стиля\n"
        "5️⃣ Выбор предыстории\n"
        "6️⃣ Выбор расы\n"
        "7️⃣ Ввод имени и истории\n"
        "8️⃣ Генерация PDF\n\n"
        "Нажми кнопку «🎲 Создать персонажа» и следуй инструкциям!",
        reply_markup=main_menu(), parse_mode=None
    )


@dp.message(Command("menu"))
async def menu_command(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("🎮 Главное меню", reply_markup=main_menu())


@dp.message(F.text == "❌ Отмена")
async def cancel_creation(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("❌ Создание персонажа отменено.\n\nЧтобы начать заново, нажмите «🎲 Создать персонажа»",
                   reply_markup=main_menu())


@dp.message(Command("help"))
async def help_command(m: Message):
    await m.answer(
        "❓ **Помощь по использованию бота**\n\n"
        "**Порядок создания персонажа:**\n"
        "1️⃣ Выберите КЛАСС\n"
        "2️⃣ Выберите СНАРЯЖЕНИЕ КЛАССА\n"
        "3️⃣ Выберите ЗАКЛИНАНИЯ (если есть)\n"
        "4️⃣ Выберите БОЕВОЙ СТИЛЬ (для Воина, Паладина, Следопыта)\n"
        "5️⃣ Выберите ПРЕДЫСТОРИЮ\n"
        "6️⃣ Выберите РАСУ\n"
        "7️⃣ Введите ИМЯ\n"
        "8️⃣ Введите ИСТОРИЮ\n"
        "9️⃣ Загрузите ИЗОБРАЖЕНИЕ\n"
        "🔟 Получите PDF лист персонажа\n\n"
        "**Команды:**\n"
        "/start - начать работу\n"
        "/menu - главное меню\n"
        "/help - эта справка",
        parse_mode=None
    )


@dp.message(F.text == "❓ Помощь")
async def help_button(m: Message):
    await help_command(m)


@dp.message(F.text == "ℹ️ О боте")
async def info_button(m: Message):
    await m.answer(
        "ℹ️ **D&D Character Creator 5.5e (2024)**\n\n"
        "📊 **Данные:**\n"
        "• 16 рас с подрасами\n"
        "• 13 классов\n"
        "• 16 предысторий\n"
        "• 50+ заклинаний\n"
        "• 30+ видов оружия\n"
        "• Автоматическое распределение характеристик\n"
        "• Генерация PDF листа персонажа\n\n"
        "🎲 **Особенности:**\n"
        "• Умное распределение бонусов предыстории\n"
        "• Группировка заклинаний по категориям\n"
        "• Оружейные приёмы (Weapon Mastery)\n"
        "• Боевые стили и возвания\n\n"
        "🐉 **Приятной игры!**",
        parse_mode=None
    )


# ============================================================
# ШАГ 1: КЛАСС
# ============================================================

@dp.message(F.text == "🎲 Создать персонажа")
async def create_char_start(m: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CreateCharacter.class_select)
    await m.answer(
        "🏰 **СОЗДАНИЕ ПЕРСОНАЖА**\n\nШаг 1/12: Выберите КЛАСС\n\nКаждый класс даёт уникальные способности, стиль игры и снаряжение.",
        parse_mode=None, reply_markup=ReplyKeyboardRemove()
    )
    await m.answer("Выберите класс:", reply_markup=create_class_keyboard())


@dp.callback_query(lambda c: c.data.startswith("class_"))
async def select_class(call: CallbackQuery, state: FSMContext):
    class_name = call.data.replace("class_", "")
    await state.update_data(class_name=class_name)
    logger.info(f"[FLOW] Выбран класс: {class_name}")

    class_desc = get_class_description(class_name)
    class_info = get_class_info(class_name)
    subclasses = get_subclasses_for_class(class_name, level=1)
    equipment = get_class_equipment(class_name)
    has_equipment_choice = len(equipment) > 1

    text = (f"⚔️ **{class_name}**\n\n📖 {class_desc}\n\n"
            f"📊 **Характеристики класса:**\n"
            f"• ❤️ Хитовый кубик: d{class_info.get('hit_die', 6)}\n"
            f"• 🎯 Основные характеристики: {', '.join(class_info.get('primary_stats', []))}\n"
            f"• 🛡️ Спасброски: {', '.join(class_info.get('saving_throws', []))}\n"
            f"• 🔮 Заклинания: {'Да' if class_info.get('spellcasting', False) else 'Нет'}\n")

    if subclasses and class_name in ["Жрец", "Друид", "Колдун"]:
        text += f"\n📖 **На 1 уровне вы можете выбрать подкласс:**\n"
        for sub in subclasses:
            text += f"   • {sub['name']} — {sub['description'][:60]}...\n"
        reply_markup = create_subclass_keyboard(class_name)
        next_state = CreateCharacter.subclass_select
    else:
        if has_equipment_choice:
            reply_markup = create_class_equipment_keyboard(class_name)
            next_state = CreateCharacter.class_equipment_select
            text += f"\n\nШаг 2/12: Выберите СНАРЯЖЕНИЕ класса"
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
            await go_to_spells(call.message, state)
            await call.answer()
            return

    await state.set_state(next_state)
    img_path = get_class_image_path(class_name)
    try:
        await call.message.delete()
        if img_path and os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await call.message.answer_photo(photo=photo, caption=text, parse_mode=None, reply_markup=reply_markup)
        else:
            await call.message.answer(text, parse_mode=None, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await call.message.answer(text, parse_mode=None, reply_markup=reply_markup)
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("class_equip_"))
async def select_class_equipment(call: CallbackQuery, state: FSMContext):
    choice = call.data.replace("class_equip_", "")
    await state.update_data(equipment_choice=choice)
    data = await state.get_data()
    class_name = data.get("class_name")
    equipment = get_class_equipment(class_name, choice)
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
            masteries = auto_assign_masteries(weapon_name, class_name)
            await state.update_data(selected_masteries=masteries)
    await call.message.delete()
    await call.message.answer(f"✅ Снаряжение выбрано (вариант {choice})")
    await go_to_spells(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_classes")
async def back_to_classes(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.class_select)
    await call.message.delete()
    await call.message.answer("Шаг 1/12: Выберите КЛАСС", parse_mode=None, reply_markup=create_class_keyboard())
    await call.answer()


# ============================================================
# ШАГ 2: ЗАКЛИНАНИЯ (ОБРАБОТЧИКИ)
# ============================================================

@dp.callback_query(lambda c: c.data.startswith("cantrip_cat_"))
async def show_cantrips_in_category(call: CallbackQuery, state: FSMContext):
    category = call.data.replace("cantrip_cat_", "")
    data = await state.get_data()
    selector_data = data.get("spell_selector", {})
    selector = SpellSelector.from_dict(selector_data)
    spells = selector.get_cantrips_in_category(category)
    selected_spells = selector.get_selected_cantrips()
    await state.update_data(current_category=category)
    await state.set_state(CreateCharacter.spells_cantrips_list)
    if not spells:
        await call.message.edit_text(f"📖 В категории **{category}** нет заговоров для этого класса.")
        return
    await call.message.edit_text(
        f"📖 **Категория: {category}**\n\nВыберите заговор для просмотра:",
        reply_markup=create_spell_list_keyboard(spells, "cantrip", selected_spells, category)
    )
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("cantrip_view_"))
async def view_cantrip_detail(call: CallbackQuery, state: FSMContext):
    spell_id = int(call.data.replace("cantrip_view_", ""))
    spell = get_spell_by_id(spell_id)
    if not spell:
        await call.answer("❌ Заклинание не найдено")
        return
    data = await state.get_data()
    selector_data = data.get("spell_selector", {})
    selector = SpellSelector.from_dict(selector_data)
    is_selected = spell['name'] in selector.get_selected_cantrips()
    remaining = 0
    if selector.cantrip_state:
        remaining = selector.cantrip_state.remaining_count
    await state.update_data(current_spell_id=spell_id, current_spell_name=spell['name'])
    await state.set_state(CreateCharacter.spells_cantrips_detail)
    description = spell.get('description', 'Описание отсутствует')
    category = spell.get('category', 'Прочее')
    icon = get_category_icon(category)
    await call.message.edit_text(
        f"{icon} **{spell['name']}**\n\n📖 **Описание:**\n{description}\n\n"
        f"🏷️ **Категория:** {category}\n"
        f"📊 **Уровень:** {'Заговор' if spell.get('is_cantrip') else f'{spell.get('level')} уровень'}\n\n"
        f"{'✅ Уже выбран' if is_selected else '❌ Не выбран'}",
        reply_markup=create_spell_detail_keyboard(spell_id, spell['name'], "cantrip", is_selected, remaining)
    )
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("cantrip_add_"))
async def add_cantrip(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selector_data = data.get("spell_selector", {})
    selector = SpellSelector.from_dict(selector_data)
    spell_name = data.get("current_spell_name")
    if not spell_name:
        await call.answer("❌ Ошибка: название заклинания не найдено")
        return
    success, msg = selector.add_cantrip(spell_name)
    await call.answer(msg, show_alert=not success)
    if success:
        await state.update_data(spell_selector=selector.to_dict())
        if selector.cantrip_state and selector.cantrip_state.is_completed:
            await call.message.answer("✅ Все заговоры выбраны! Переходим к заклинаниям 1 уровня...")
            await start_level1_selection(call.message, state)
        else:
            await start_cantrips_selection(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("cantrip_remove_"))
async def remove_cantrip(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selector_data = data.get("spell_selector", {})
    selector = SpellSelector.from_dict(selector_data)
    spell_name = data.get("current_spell_name")
    if not spell_name:
        await call.answer("❌ Ошибка: название заклинания не найдено")
        return
    success, msg = selector.remove_cantrip(spell_name)
    await call.answer(msg)
    if success:
        await state.update_data(spell_selector=selector.to_dict())
        await start_cantrips_selection(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "cantrip_back_categories")
async def back_to_cantrip_categories(call: CallbackQuery, state: FSMContext):
    await start_cantrips_selection(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("level1_cat_"))
async def show_level1_in_category(call: CallbackQuery, state: FSMContext):
    category = call.data.replace("level1_cat_", "")
    data = await state.get_data()
    selector_data = data.get("spell_selector", {})
    selector = SpellSelector.from_dict(selector_data)
    spells = selector.get_level1_spells_in_category(category)
    selected_spells = selector.get_selected_level1_spells()
    await state.update_data(current_category=category)
    await state.set_state(CreateCharacter.spells_level1_list)
    if not spells:
        await call.message.edit_text(f"🔮 В категории **{category}** нет заклинаний 1 уровня для этого класса.")
        return
    await call.message.edit_text(
        f"🔮 **Категория: {category}**\n\nВыберите заклинание для просмотра:",
        reply_markup=create_spell_list_keyboard(spells, "level1", selected_spells, category)
    )
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("level1_view_"))
async def view_level1_detail(call: CallbackQuery, state: FSMContext):
    spell_id = int(call.data.replace("level1_view_", ""))
    spell = get_spell_by_id(spell_id)
    if not spell:
        await call.answer("❌ Заклинание не найдено")
        return
    data = await state.get_data()
    selector_data = data.get("spell_selector", {})
    selector = SpellSelector.from_dict(selector_data)
    is_selected = spell['name'] in selector.get_selected_level1_spells()
    remaining = 0
    if selector.level1_state:
        remaining = selector.level1_state.remaining_count
    await state.update_data(current_spell_id=spell_id, current_spell_name=spell['name'])
    await state.set_state(CreateCharacter.spells_level1_detail)
    description = spell.get('description', 'Описание отсутствует')
    category = spell.get('category', 'Прочее')
    icon = get_category_icon(category)
    await call.message.edit_text(
        f"{icon} **{spell['name']}**\n\n📖 **Описание:**\n{description}\n\n"
        f"🏷️ **Категория:** {category}\n"
        f"📊 **Уровень:** {spell.get('level')}\n\n"
        f"{'✅ Уже выбран' if is_selected else '❌ Не выбран'}",
        reply_markup=create_spell_detail_keyboard(spell_id, spell['name'], "level1", is_selected, remaining)
    )
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("level1_add_"))
async def add_level1_spell(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selector_data = data.get("spell_selector", {})
    selector = SpellSelector.from_dict(selector_data)
    spell_name = data.get("current_spell_name")
    if not spell_name:
        await call.answer("❌ Ошибка: название заклинания не найдено")
        return
    success, msg = selector.add_level1_spell(spell_name)
    await call.answer(msg, show_alert=not success)
    if success:
        await state.update_data(spell_selector=selector.to_dict())
        if selector.level1_state and selector.level1_state.is_completed:
            await call.message.answer("✅ Все заклинания выбраны! Переходим к следующему шагу...")
            await go_to_fighting_style(call.message, state)
        else:
            await start_level1_selection(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("level1_remove_"))
async def remove_level1_spell(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selector_data = data.get("spell_selector", {})
    selector = SpellSelector.from_dict(selector_data)
    spell_name = data.get("current_spell_name")
    if not spell_name:
        await call.answer("❌ Ошибка: название заклинания не найдено")
        return
    success, msg = selector.remove_level1_spell(spell_name)
    await call.answer(msg)
    if success:
        await state.update_data(spell_selector=selector.to_dict())
        await start_level1_selection(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "level1_back_categories")
async def back_to_level1_categories(call: CallbackQuery, state: FSMContext):
    await start_level1_selection(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_spells")
async def back_to_spells(call: CallbackQuery, state: FSMContext):
    await go_to_spells(call.message, state)
    await call.answer()


# ============================================================
# ШАГ 3: БОЕВОЙ СТИЛЬ И ВОЗВАНИЯ
# ============================================================

@dp.callback_query(lambda c: c.data.startswith("style_"))
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
    await go_to_invocations(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "style_skip")
async def skip_fighting_style(call: CallbackQuery, state: FSMContext):
    await go_to_invocations(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("inv_"))
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
            await call.answer("⚠️ Можно выбрать не более 2 возваний!", show_alert=True)
            return
        selected.append(inv_name)
        await call.answer(f"✅ Возвание '{inv_name}' добавлено")
    await state.update_data(selected_invocations=selected)
    await call.message.edit_reply_markup(reply_markup=create_invocations_keyboard(level=1))
    await call.answer()


@dp.callback_query(lambda c: c.data == "inv_skip")
async def skip_invocations(call: CallbackQuery, state: FSMContext):
    await go_to_background(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_fighting")
async def back_to_fighting(call: CallbackQuery, state: FSMContext):
    await go_to_fighting_style(call.message, state)
    await call.answer()


# ============================================================
# ШАГ 4: ПРЕДЫСТОРИЯ (ОБРАБОТЧИКИ)
# ============================================================

@dp.callback_query(lambda c: c.data.startswith("bg_") and not c.data.startswith("bg_equip_"))
async def select_background(call: CallbackQuery, state: FSMContext):
    background = call.data.replace("bg_", "")
    await state.update_data(background=background)
    logger.info(f"[FLOW] Выбрана предыстория: {background}")
    bg_info = get_background_by_name(background)
    if not bg_info:
        await call.message.answer(f"❌ Ошибка: предыстория '{background}' не найдена.", reply_markup=main_menu())
        await state.clear()
        return
    await state.update_data(selected_skills=bg_info.get('skills', []), background_trait=bg_info.get('trait', 'Нет'))
    await state.set_state(CreateCharacter.background_equipment_select)
    equip_a = bg_info.get('equipment_a', 'Нет описания')[:60]
    equip_b = bg_info.get('equipment_b', 'Нет описания')[:60]
    await call.message.delete()
    await call.message.answer(
        f"📜 **Предыстория: {background}**\n\n📖 {bg_info.get('description', 'Нет описания')[:300]}...\n\n"
        f"✨ **Бонусы к характеристикам:**\n   • +2 к {bg_info['characteristics'][0]}\n   • +1 к {bg_info['characteristics'][1]}\n\n"
        f"🔧 **Черта:** {bg_info.get('trait', 'Нет')}\n📚 **Навыки:** {', '.join(bg_info.get('skills', []))}\n"
        f"🛠️ **Инструменты:** {bg_info.get('tools', 'Нет')}\n\n"
        f"**Шаг 8/12: Выберите СНАРЯЖЕНИЕ от предыстории**\n\n"
        f"📦 Вариант А: {equip_a}...\n🎒 Вариант Б: {equip_b}...",
        parse_mode=None, reply_markup=create_background_equipment_keyboard(background)
    )
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("bg_equip_"))
async def select_background_equipment(call: CallbackQuery, state: FSMContext):
    equipment_choice = call.data.replace("bg_equip_", "")
    data = await state.get_data()
    background = data.get("background")
    if not background or background in ["equip_A", "equip_B", "equip_", "A", "B", None]:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: background = '{background}'")
        await call.message.answer(
            "❌ Ошибка: данные о предыстории потеряны.\nПожалуйста, начните создание заново: /start",
            reply_markup=main_menu())
        await state.clear()
        return
    await state.update_data(background_equipment_choice=equipment_choice)
    bg_info = get_background_by_name(background)
    if bg_info:
        chosen_equipment = bg_info['equipment_a'] if equipment_choice == "A" else bg_info['equipment_b']
        await state.update_data(background_equipment=chosen_equipment)
    await calculate_and_show_stats(call.message, state)
    await call.message.delete()
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_background")
async def back_to_background_list(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.background_select)
    await call.message.delete()
    await call.message.answer("Шаг 7/12: Выберите ПРЕДЫСТОРИЮ", parse_mode=None,
                              reply_markup=create_background_keyboard())
    await call.answer()


# ============================================================
# ШАГ 5: РАСА (ОБРАБОТЧИКИ)
# ============================================================

@dp.callback_query(lambda c: c.data.startswith("race_"))
async def select_race(call: CallbackQuery, state: FSMContext):
    race = call.data.replace("race_", "")
    await state.update_data(race=race)
    logger.info(f"[FLOW] Выбрана раса: {race}")
    race_desc = get_race_description(race)
    race_speed = get_race_speed(race)
    race_size = get_race_size(race)
    has_sub = has_subraces(race)
    subraces_list = get_subraces(race) if has_sub else []
    text = f"🧝 **Раса: {race}**\n\n📖 {race_desc}\n\n🏃 **Скорость:** {race_speed} футов\n📏 **Размер:** {race_size}\n"
    if has_sub and subraces_list:
        text += f"\n🌟 **Доступные подрасы:**\n"
        for sub in subraces_list:
            sub_trait = get_subrace_trait(race, sub)
            text += f"   • **{sub}** — {sub_trait[:50] + '...' if len(sub_trait) > 50 else sub_trait}\n"
        text += f"\n**Шаг 10/12: Выберите ПОДРАСУ**"
        reply_markup = create_subrace_keyboard(race)
        next_state = CreateCharacter.subrace_select
        await state.set_state(next_state)
    else:
        await go_to_name(call.message, state)
        await call.answer()
        return
    img_path = get_race_image_path(race)
    try:
        await call.message.delete()
        if img_path and os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await call.message.answer_photo(photo=photo, caption=text, parse_mode=None, reply_markup=reply_markup)
        else:
            await call.message.answer(text, parse_mode=None, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await call.message.answer(text, parse_mode=None, reply_markup=reply_markup)
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("subrace_") and c.data != "subrace_skip")
async def select_subrace(call: CallbackQuery, state: FSMContext):
    subrace = call.data.replace("subrace_", "")
    await state.update_data(subrace=subrace)
    data = await state.get_data()
    race = data.get("race")
    sub_desc = get_subrace_description(race, subrace)
    sub_trait = get_subrace_trait(race, subrace)
    text = f"🧝 **{race} — {subrace}**\n\n📖 {sub_desc}\n\n✨ **Особенность:** {sub_trait}\n\nПереходим к вводу имени..."
    await call.message.delete()
    await call.message.answer(text, parse_mode=None)
    await go_to_name(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "subrace_skip")
async def skip_subrace(call: CallbackQuery, state: FSMContext):
    await state.update_data(subrace=None)
    await call.message.delete()
    await go_to_name(call.message, state)
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_races")
async def back_to_races(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.race_select)
    await call.message.delete()
    await call.message.answer("Шаг 9/12: Выберите РАСУ", parse_mode=None, reply_markup=create_race_keyboard())
    await call.answer()


# ============================================================
# ШАГ 6: ИМЯ И ИСТОРИЯ (ОБРАБОТЧИКИ)
# ============================================================

@dp.message(CreateCharacter.name_input)
async def set_name(m: Message, state: FSMContext):
    if m.text == "❌ Отмена":
        await cancel_creation(m, state)
        return
    valid, msg = validate_name(m.text)
    if not valid:
        await m.answer(f"{msg}\nПожалуйста, введите другое имя:", reply_markup=cancel_kb())
        return
    await state.update_data(name=m.text.strip())
    logger.info(f"✅ Имя сохранено: {m.text.strip()}")
    await m.answer(f"✅ Имя: {m.text.strip()}", reply_markup=ReplyKeyboardRemove())
    await go_to_backstory(m, state)


@dp.message(CreateCharacter.backstory_input)
async def set_backstory(m: Message, state: FSMContext):
    if m.text == "❌ Отмена":
        await cancel_creation(m, state)
        return
    backstory = m.text.strip()
    if len(backstory) > 2000:
        await m.answer("❌ История слишком длинная (максимум 2000 символов).", reply_markup=cancel_kb())
        return
    await state.update_data(backstory=backstory)
    await state.set_state(CreateCharacter.image_input)
    await m.answer(
        f"📖 История сохранена!\n\n🖼️ **Финальный шаг: Изображение персонажа**\n\nЗагрузите картинку или нажмите «⏩ Пропустить».",
        parse_mode=None, reply_markup=skip_kb()
    )


# ============================================================
# ШАГ 7: ИЗОБРАЖЕНИЕ И ФИНАЛ
# ============================================================

@dp.message(F.text == "⏩ Пропустить")
async def skip_image(m: Message, state: FSMContext):
    await finalize_character(m, state, image_file_id=None)


@dp.message(CreateCharacter.image_input, F.photo)
async def set_image(m: Message, state: FSMContext):
    photo = m.photo[-1]
    file_id = photo.file_id
    await finalize_character(m, state, image_file_id=file_id)


# ============================================================
# ПРОСМОТР И УДАЛЕНИЕ ПЕРСОНАЖЕЙ
# ============================================================

@dp.message(F.text == "📋 Мои персонажи")
async def list_characters(m: Message):
    characters = get_user_characters(m.from_user.id)
    if not characters:
        await m.answer("📭 У вас пока нет персонажей.")
        return
    await m.answer("📋 Ваши персонажи:", reply_markup=create_character_list_keyboard(m.from_user.id))


@dp.callback_query(lambda c: c.data.startswith("view_"))
async def view_character(call: CallbackQuery):
    char_id = int(call.data.replace("view_", ""))
    character = get_character_by_id(char_id)
    if not character:
        await call.answer("❌ Персонаж не найден")
        return
    info = (f"📛 **{character['name']}**\n\n🧝 **Раса:** {character.get('race_name', 'Неизвестно')}\n"
            f"⚔️ **Класс:** {character.get('class_name', 'Неизвестно')}\n📜 **Предыстория:** {character.get('background_name', 'Нет')}\n"
            f"📊 **Уровень:** {character['level']}\n❤️ **HP:** {character['hp']} | 🛡️ **AC:** {character['ac']}\n\n"
            f"**Характеристики:**\nSTR {character['str']} | DEX {character['dex']} | CON {character['con']} | "
            f"INT {character['int']} | WIS {character['wis']} | CHA {character['cha']}")
    if character.get('image_file_id'):
        await call.message.answer_photo(photo=character['image_file_id'], caption=info, parse_mode=None)
    else:
        await call.message.answer(info, parse_mode=None)
    await call.answer()


@dp.message(F.text == "🗑 Удалить персонажа")
async def delete_character_menu(m: Message):
    characters = get_user_characters(m.from_user.id)
    if not characters:
        await m.answer("📭 У вас нет персонажей для удаления.")
        return
    await m.answer("🗑 Выберите персонажа для удаления:\n\n⚠️ Удаление необратимо.",
                   reply_markup=create_delete_keyboard(characters))


@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def confirm_delete(call: CallbackQuery):
    char_id = int(call.data.replace("delete_", ""))
    character = get_character_by_id(char_id)
    if not character:
        await call.answer("❌ Персонаж не найден")
        return
    if delete_character(char_id, call.from_user.id):
        await call.message.edit_text(f"✅ Персонаж {character['name']} удалён!", parse_mode=None)
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


@dp.callback_query(lambda c: c.data == "progress_info")
async def progress_info(call: CallbackQuery):
    await call.answer("Это информационное сообщение", show_alert=False)


@dp.message()
async def unknown_command(m: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await m.answer("⏳ Вы в процессе создания персонажа.\n\nСледуйте инструкциям или нажмите «❌ Отмена».",
                       reply_markup=cancel_kb())
    else:
        await m.answer("❓ Я не понимаю эту команду.\n\nИспользуйте кнопки меню или /help.",
                       reply_markup=main_menu())


# ============================================================
# ЗАПУСК
# ============================================================

async def main():
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК БОТА D&D CHARACTER CREATOR 5.5e (ВЕРСИЯ 2)")
    logger.info("=" * 50)
    try:
        from db import init_database, migrate_database_v2
        init_database()
        migrate_database_v2()
        logger.info("✅ База данных готова (версия 2)")
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