# keyboards/spell_keyboards.py
"""
Клавиатуры для выбора заклинаний
"""

from typing import List, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_category_keyboard(categories: Dict[str, Dict], spell_type: str,
                             selected_count: int, required_count: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру с категориями заклинаний"""
    buttons = []
    if required_count > 0:
        buttons.append(
            [InlineKeyboardButton(text=f"📖 Выбрано: {selected_count}/{required_count}", callback_data="progress_info")]
        )
    for cat_name, cat_data in categories.items():
        icon = cat_data.get('icon', '✨')
        count = len(cat_data.get('spells', []))
        buttons.append(
            [InlineKeyboardButton(text=f"{icon} {cat_name} ({count})", callback_data=f"{spell_type}_cat_{cat_name}")]
        )
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")])
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
        buttons.append(
            [InlineKeyboardButton(text=f"{emoji} {spell_name}", callback_data=f"{spell_type}_view_{spell_id}")]
        )
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к категориям", callback_data=f"{spell_type}_back_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_spell_detail_keyboard(spell_id: int, spell_name: str, spell_type: str,
                                 is_selected: bool, remaining: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для детального просмотра заклинания"""
    buttons = []
    if is_selected:
        buttons.append([InlineKeyboardButton(text="❌ Удалить", callback_data=f"{spell_type}_remove_{spell_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="✅ Выбрать", callback_data=f"{spell_type}_add_{spell_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data=f"{spell_type}_back_list")])
    if remaining > 0:
        buttons.append([InlineKeyboardButton(text=f"Осталось выбрать: {remaining}", callback_data="progress_info")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)