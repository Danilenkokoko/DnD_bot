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

# Импорт строковых констант
from strings import (
    BTN_CREATE_CHAR, BTN_MY_CHARS, BTN_DELETE_CHAR, BTN_ABOUT, BTN_HELP,
    BTN_CANCEL, BTN_SKIP, BTN_CONTINUE,
    BTN_SELECTED_COUNT, BTN_EQUIP_OPTION, BTN_BACK_TO_CLASSES,
    BTN_SKILLS_READY, BTN_SKILLS_READY_DISABLED, BTN_BACK_TO_RACES,
    BTN_BACK_TO_SPELLS, BTN_STYLE_SKIP, BTN_ALIGNMENT_NAMES,
    BTN_VIEW_CHAR, BTN_WEBAPP_CHAR, BTN_DELETE_ITEM, BTN_CANCEL_DELETE,
    BTN_CATEGORY, BTN_SPELL_LIST_ITEM, BTN_BACK_TO_CATEGORIES,
    BTN_REMOVE_SPELL, BTN_ADD_SPELL, BTN_BACK_TO_LIST, BTN_REMAINING_COUNT
)


# =========================================================
# REPLY KEYBOARDS
# =========================================================

def main_menu() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=BTN_CREATE_CHAR)],
        [KeyboardButton(text=BTN_MY_CHARS)],
        [KeyboardButton(text=BTN_DELETE_CHAR)],
        [KeyboardButton(text=BTN_ABOUT), KeyboardButton(text=BTN_HELP)]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True
    )


def skip_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_SKIP), KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True
    )


def continue_kb_for_spells() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CONTINUE)]],
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
    buttons.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_creation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_class_equipment_keyboard(class_name: str) -> Optional[InlineKeyboardMarkup]:
    """Клавиатура выбора снаряжения класса (если несколько вариантов)"""
    equipment = get_class_equipment(class_name)
    if len(equipment) <= 1:
        return None
    buttons = []
    for eq in equipment:
        choice = eq.get('choice', 'A')
        weapon = eq.get('weapon', 'нет оружия')
        armor = eq.get('armor', 'нет брони')
        # Используем константу, но подставляем значения
        text = BTN_EQUIP_OPTION.format(choice=choice, weapon=weapon, armor=armor)
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"equip_{choice}")])
    buttons.append([InlineKeyboardButton(text=BTN_BACK_TO_CLASSES, callback_data="back_to_classes")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_skills_keyboard(
    skills: List[str],
    max_choices: int,
    selected_skills: List[str]
) -> InlineKeyboardMarkup:
    buttons = []
    # Кнопка счётчика выбранных навыков
    counter_text = BTN_SELECTED_COUNT.format(selected=len(selected_skills), max=max_choices)
    buttons.append([InlineKeyboardButton(text=counter_text, callback_data="class_skills_info")])
    for skill in skills:
        is_selected = skill in selected_skills
        icon = "✅" if is_selected else "🔘"
        buttons.append([InlineKeyboardButton(text=f"{icon} {skill}", callback_data=f"class_skill_toggle_{skill}")])
    if len(selected_skills) == max_choices:
        buttons.append([InlineKeyboardButton(text=BTN_SKILLS_READY, callback_data="class_skills_ready")])
    else:
        buttons.append([InlineKeyboardButton(text=BTN_SKILLS_READY_DISABLED, callback_data="class_skills_ready_disabled")])
    buttons.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_creation")])
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
    buttons.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_creation")])
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
    buttons.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_creation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_subrace_keyboard(race: str) -> Optional[InlineKeyboardMarkup]:
    subraces = get_subraces(race)
    if not subraces:
        return None
    buttons = []
    for subrace in subraces:
        buttons.append([InlineKeyboardButton(text=subrace, callback_data=f"subrace_{subrace}")])
    # Кнопка пропуска отсутствует, только назад к расам
    buttons.append([InlineKeyboardButton(text=BTN_BACK_TO_RACES, callback_data="back_to_races")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_fighting_style_keyboard(class_name: str) -> InlineKeyboardMarkup:
    styles = get_fighting_styles_for_class(class_name)
    if not styles:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=BTN_STYLE_SKIP, callback_data="style_skip")],
            [InlineKeyboardButton(text=BTN_BACK_TO_SPELLS, callback_data="back_to_spells")]
        ])
    buttons = []
    for s in styles:
        text = f"🛡️ {s['name']}: {s['description'][:50]}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"style_{s['id']}")])
    buttons.append([InlineKeyboardButton(text=BTN_BACK_TO_SPELLS, callback_data="back_to_spells")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_alignment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора мировоззрения (вертикальный список, каждая кнопка в отдельной строке)"""
    alignments = [
        (BTN_ALIGNMENT_NAMES["lawful_good"], "lawful_good"),
        (BTN_ALIGNMENT_NAMES["neutral_good"], "neutral_good"),
        (BTN_ALIGNMENT_NAMES["chaotic_good"], "chaotic_good"),
        (BTN_ALIGNMENT_NAMES["lawful_neutral"], "lawful_neutral"),
        (BTN_ALIGNMENT_NAMES["neutral"], "neutral"),
        (BTN_ALIGNMENT_NAMES["chaotic_neutral"], "chaotic_neutral"),
        (BTN_ALIGNMENT_NAMES["lawful_evil"], "lawful_evil"),
        (BTN_ALIGNMENT_NAMES["neutral_evil"], "neutral_evil"),
        (BTN_ALIGNMENT_NAMES["chaotic_evil"], "chaotic_evil")
    ]
    buttons = []
    for name, value in alignments:
        buttons.append([InlineKeyboardButton(text=name, callback_data=f"alignment_{value}")])
    buttons.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_creation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_character_list_keyboard(user_id: int) -> Optional[InlineKeyboardMarkup]:
    """Старая клавиатура – только текстовый просмотр (для обратной совместимости)"""
    characters = get_user_characters(user_id)
    if not characters:
        return None
    buttons = []
    for char in characters:
        text = BTN_VIEW_CHAR.format(name=char['name'], class_name=char['class_name'], level=char['level'])
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"view_{char['id']}")])
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
        text_btn_text = BTN_VIEW_CHAR.format(name=char['name'], class_name=char['class_name'], level=char['level'])
        text_btn = InlineKeyboardButton(text=text_btn_text, callback_data=f"view_{char['id']}")
        # Кнопка Web App
        webapp_btn = InlineKeyboardButton(text=BTN_WEBAPP_CHAR, web_app=WebAppInfo(url=f"{webapp_base_url}/character/{char['id']}"))
        buttons.append([text_btn, webapp_btn])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_delete_keyboard(characters: list) -> InlineKeyboardMarkup:
    buttons = []
    for char in characters:
        text = BTN_DELETE_ITEM.format(name=char['name'], class_name=char['class_name'])
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"delete_{char['id']}")])
    buttons.append([InlineKeyboardButton(text=BTN_CANCEL_DELETE, callback_data="cancel_delete")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)