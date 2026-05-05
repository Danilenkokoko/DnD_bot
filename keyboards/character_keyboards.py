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
    get_fighting_styles_for_class, get_all_invocations,
)

# Импорт строковых констант
from strings import (
    BTN_CREATE_CHAR, BTN_MY_CHARS, BTN_DELETE_CHAR, BTN_ABOUT, BTN_HELP,
    BTN_CANCEL, BTN_SKIP, BTN_CONTINUE,
    BTN_SELECTED_COUNT, BTN_EQUIP_OPTION, BTN_BACK_TO_CLASSES,
    BTN_SKILLS_READY, BTN_SKILLS_READY_DISABLED, BTN_BACK_TO_RACES,
    BTN_BACK_TO_SPELLS, BTN_STYLE_SKIP, BTN_ALIGNMENT_NAMES,
    BTN_VIEW_CHAR, BTN_WEBAPP_CHAR, BTN_DELETE_ITEM, BTN_CANCEL_DELETE,
    BTN_DRUID_ORDER_GUIDE, BTN_DRUID_ORDER_GUARDIAN,
    BTN_CLERIC_ORDER_PROTECTOR, BTN_CLERIC_ORDER_MIRACLE,
    BTN_WARLOCK_PACT_TOME, BTN_WARLOCK_PACT_BLADE, BTN_WARLOCK_PACT_CHAIN,
    BTN_WARLOCK_PACT_SHADOW_ARMOR, BTN_WARLOCK_PACT_ARCANE_MIND
)


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
    equipment = get_class_equipment(class_name)
    if len(equipment) <= 1:
        return None
    buttons = []
    for eq in equipment:
        choice = eq.get('choice', 'A')
        weapon = eq.get('weapon', 'нет оружия')
        armor = eq.get('armor', 'нет брони')
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

def create_background_equipment_keyboard(background_name: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора снаряжения предыстории (вариант А или Б)."""
    from dnd_logic import get_background_by_name
    bg_info = get_background_by_name(background_name)
    if not bg_info:
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Ошибка", callback_data="cancel_creation")]])
    equip_a = bg_info.get('equipment_a', 'Нет описания')[:60]
    equip_b = bg_info.get('equipment_b', 'Нет описания')[:60]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📦 Вариант А: {equip_a}...", callback_data="bg_equip_A")],
        [InlineKeyboardButton(text=f"🎒 Вариант Б: {equip_b}...", callback_data="bg_equip_B")],
        [InlineKeyboardButton(text="⬅️ Назад к предыстории", callback_data="back_to_background")]
    ])


# =========================================================
# КЛАВИАТУРЫ ДЛЯ ОРДЕНОВ, ДОГОВОРОВ И Т.Д.
# =========================================================
def create_druid_order_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=BTN_DRUID_ORDER_GUIDE, callback_data="druid_order_guide")],
        [InlineKeyboardButton(text=BTN_DRUID_ORDER_GUARDIAN, callback_data="druid_order_guardian")],
        [InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_creation")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_cleric_order_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=BTN_CLERIC_ORDER_PROTECTOR, callback_data="cleric_order_protector")],
        [InlineKeyboardButton(text=BTN_CLERIC_ORDER_MIRACLE, callback_data="cleric_order_miracle")],
        [InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_creation")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_warlock_pact_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=BTN_WARLOCK_PACT_TOME, callback_data="warlock_pact_tome")],
        [InlineKeyboardButton(text=BTN_WARLOCK_PACT_BLADE, callback_data="warlock_pact_blade")],
        [InlineKeyboardButton(text=BTN_WARLOCK_PACT_CHAIN, callback_data="warlock_pact_chain")],
        [InlineKeyboardButton(text=BTN_WARLOCK_PACT_SHADOW_ARMOR, callback_data="warlock_pact_shadow_armor")],
        [InlineKeyboardButton(text=BTN_WARLOCK_PACT_ARCANE_MIND, callback_data="warlock_pact_arcane_mind")],
        [InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_creation")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# =========================================================
# КЛАВИАТУРЫ ДЛЯ ПЛУТА
# =========================================================
def create_rogue_expertise_keyboard(skills: List[str], selected: List[str] = None) -> InlineKeyboardMarkup:
    if selected is None:
        selected = []
    buttons = []
    for skill in skills:
        check = "✅ " if skill in selected else "🔘 "
        buttons.append([InlineKeyboardButton(text=f"{check}{skill}", callback_data=f"rogue_expertise_{skill}")])
    buttons.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_creation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_rogue_language_keyboard(languages: List[str]) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i, lang in enumerate(languages):
        row.append(InlineKeyboardButton(text=lang, callback_data=f"rogue_lang_{lang}"))
        if len(row) == 2 or i == len(languages) - 1:
            buttons.append(row)
            row = []
    buttons.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_creation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# =========================================================
# КЛАВИАТУРЫ ДЛЯ ПРОСМОТРА И УДАЛЕНИЯ ПЕРСОНАЖЕЙ
# =========================================================
def create_character_list_keyboard(user_id: int) -> Optional[InlineKeyboardMarkup]:
    characters = get_user_characters(user_id)
    if not characters:
        return None
    buttons = []
    for char in characters:
        text = BTN_VIEW_CHAR.format(name=char['name'], class_name=char['class_name'], level=char['level'])
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"view_{char['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_character_list_with_webapp_keyboard(user_id: int, webapp_base_url: str) -> Optional[InlineKeyboardMarkup]:
    characters = get_user_characters(user_id)
    if not characters:
        return None
    buttons = []
    for char in characters:
        text_btn_text = BTN_VIEW_CHAR.format(name=char['name'], class_name=char['class_name'], level=char['level'])
        text_btn = InlineKeyboardButton(text=text_btn_text, callback_data=f"view_{char['id']}")
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