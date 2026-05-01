# keyboards/spell_keyboards.py
"""
Клавиатуры для выбора заклинаний
"""

from typing import List, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импорт строковых констант
from strings import (
    BTN_PROGRESS_INFO, BTN_CATEGORY, BTN_SPELL_LIST_ITEM,
    BTN_BACK_TO_CATEGORIES, BTN_REMOVE_SPELL, BTN_ADD_SPELL,
    BTN_BACK_TO_LIST, BTN_REMAINING_COUNT, BTN_CANCEL
)


def create_category_keyboard(categories: Dict[str, Dict], spell_type: str,
                             selected_count: int, required_count: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру с категориями заклинаний"""
    buttons = []
    if required_count > 0:
        text = BTN_PROGRESS_INFO.format(selected=selected_count, required=required_count)
        buttons.append([InlineKeyboardButton(text=text, callback_data="progress_info")])
    for cat_name, cat_data in categories.items():
        icon = cat_data.get('icon', '✨')
        count = len(cat_data.get('spells', []))
        text = BTN_CATEGORY.format(icon=icon, cat_name=cat_name, count=count)
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"{spell_type}_cat_{cat_name}")])
    buttons.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="cancel_creation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_spell_list_keyboard(spells: List[Dict], spell_type: str,
                               selected_spells: List[str], category: str) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру со списком заклинаний в категории"""
    buttons = []
    for spell in spells:
        spell_id = spell.get('id')
        spell_name = spell.get('name', 'Unknown')
        is_selected = spell_name in selected_spells
        emoji = "✅" if is_selected else "🔘"
        text = BTN_SPELL_LIST_ITEM.format(emoji=emoji, spell_name=spell_name)
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"{spell_type}_view_{spell_id}")])
    buttons.append([InlineKeyboardButton(text=BTN_BACK_TO_CATEGORIES, callback_data=f"{spell_type}_back_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_spell_detail_keyboard(spell_id: int, spell_name: str, spell_type: str,
                                 is_selected: bool, remaining: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для детального просмотра заклинания"""
    buttons = []
    if is_selected:
        buttons.append([InlineKeyboardButton(text=BTN_REMOVE_SPELL, callback_data=f"{spell_type}_remove_{spell_id}")])
    else:
        buttons.append([InlineKeyboardButton(text=BTN_ADD_SPELL, callback_data=f"{spell_type}_add_{spell_id}")])
    buttons.append([InlineKeyboardButton(text=BTN_BACK_TO_LIST, callback_data=f"{spell_type}_back_list")])
    if remaining > 0:
        text = BTN_REMAINING_COUNT.format(remaining=remaining)
        buttons.append([InlineKeyboardButton(text=text, callback_data="progress_info")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)