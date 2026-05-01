# keyboards/character_keyboards.py
"""
Клавиатуры для создания персонажа
"""

from typing import Optional, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

from db import get_user_characters
from dnd_logic import (
    get_class_list, get_class_equipment, get_subclasses_for_class,
    get_background_list, get_race_list, get_subraces,
    get_fighting_styles_for_class, get_all_invocations
)


# =========================================================
# REPLY KEYBOARDS
# =========================================================

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


def continue_kb_for_spells() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Продолжить")]],
        resize_keyboard=True
    )


# =========================================================
# INLINE KEYBOARDS
# =========================================================

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
            callback_data=f"equip_{choice}"
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


def create_skills_keyboard(
    skills: List[str],
    max_choices: int,
    selected_skills: List[str]
) -> InlineKeyboardMarkup:
    buttons = []
    buttons.append([
        InlineKeyboardButton(
            text=f"📌 Выбрано: {len(selected_skills)}/{max_choices}",
            callback_data="class_skills_info"
        )
    ])
    for skill in skills:
        is_selected = skill in selected_skills
        icon = "✅" if is_selected else "🔘"
        buttons.append([
            InlineKeyboardButton(
                text=f"{icon} {skill}",
                callback_data=f"class_skill_toggle_{skill}"
            )
        ])
    if len(selected_skills) == max_choices:
        buttons.append([InlineKeyboardButton(text="✅ Готово", callback_data="class_skills_ready")])
    else:
        buttons.append([InlineKeyboardButton(text="📖 Готово", callback_data="class_skills_ready_disabled")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")])
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
    from dnd_logic import get_background_by_name
    bg_info = get_background_by_name(background)
    if not bg_info:
        return InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="❌ Ошибка", callback_data="cancel_creation")]]
        )
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


def create_fighting_style_keyboard(class_name: str) -> InlineKeyboardMarkup:
    styles = get_fighting_styles_for_class(class_name)
    if not styles:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Продолжить (нет стилей)", callback_data="style_skip")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_spells")]
        ])
    buttons = []
    for s in styles:
        buttons.append([InlineKeyboardButton(
            text=f"🛡️ {s['name']}: {s['description'][:50]}",
            callback_data=f"style_{s['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="➡️ Пропустить", callback_data="style_skip")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_spells")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_invocations_keyboard(level: int = 1, selected_count: int = 0) -> InlineKeyboardMarkup:
    invocations = get_all_invocations(level)
    if not invocations:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Пропустить", callback_data="inv_skip")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_fighting")]
        ])
    buttons = []
    for inv in invocations[:8]:
        emoji = "🔮" if inv['level_required'] == 1 else "🔷"
        buttons.append([InlineKeyboardButton(text=f"{emoji} {inv['name']} (ур. {inv['level_required']})",
                                             callback_data=f"inv_{inv['id']}")])
    buttons.append([InlineKeyboardButton(text="➡️ Пропустить", callback_data="inv_skip")])
    if selected_count > 0:
        buttons.append([InlineKeyboardButton(text="✅ Продолжить", callback_data="inv_continue")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_fighting")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_character_list_keyboard(user_id: int) -> Optional[InlineKeyboardMarkup]:
    """Старая клавиатура – только текстовый просмотр (для обратной совместимости)"""
    characters = get_user_characters(user_id)
    if not characters:
        return None
    buttons = []
    for char in characters:
        buttons.append([InlineKeyboardButton(text=f"{char['name']} - {char['class_name']} ур.{char['level']}",
                                             callback_data=f"view_{char['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_character_list_with_webapp_keyboard(user_id: int, webapp_base_url: str) -> Optional[InlineKeyboardMarkup]:
    """
    Новая клавиатура списка персонажей с двумя кнопками:
    - текстовый просмотр (сохраняет старый функционал)
    - Web App (открывает красивый лист)
    """
    characters = get_user_characters(user_id)
    if not characters:
        return None
    buttons = []
    for char in characters:
        # Кнопка текстового просмотра
        text_btn = InlineKeyboardButton(
            text=f"📄 {char['name']} - {char['class_name']} ур.{char['level']}",
            callback_data=f"view_{char['id']}"
        )
        # Кнопка Web App
        webapp_btn = InlineKeyboardButton(
            text="🌐 Открыть лист",
            web_app=WebAppInfo(url=f"{webapp_base_url}/character/{char['id']}")
        )
        buttons.append([text_btn, webapp_btn])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_delete_keyboard(characters: list) -> InlineKeyboardMarkup:
    buttons = []
    for char in characters:
        buttons.append([InlineKeyboardButton(text=f"🗑 {char['name']} ({char['class_name']})",
                                             callback_data=f"delete_{char['id']}")])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)