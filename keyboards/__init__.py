# keyboards/__init__.py
""" Клавиатуры для Telegram бота """

from keyboards.spell_keyboards import (
    create_category_keyboard,
    create_spell_list_keyboard,
    create_spell_detail_keyboard,
)
from keyboards.character_keyboards import (
    main_menu,
    cancel_kb,
    skip_kb,
    continue_kb_for_spells,
    create_class_keyboard,
    create_class_equipment_keyboard,
    create_background_keyboard,
    create_race_keyboard,
    create_subrace_keyboard,
    create_fighting_style_keyboard,
    create_character_list_with_webapp_keyboard,   # новое имя
    create_character_list_keyboard,               # алиас для старых импортов
    create_delete_keyboard,                       # новая функция
)

__all__ = [
    'main_menu',
    'cancel_kb',
    'skip_kb',
    'continue_kb_for_spells',
    'create_class_keyboard',
    'create_class_equipment_keyboard',
    'create_background_keyboard',
    'create_race_keyboard',
    'create_subrace_keyboard',
    'create_fighting_style_keyboard',
    'create_character_list_with_webapp_keyboard',
    'create_character_list_keyboard',
    'create_delete_keyboard',
    'create_category_keyboard',
    'create_spell_list_keyboard',
    'create_spell_detail_keyboard',
]