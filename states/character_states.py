# states/character_states.py
"""
FSM состояния для создания персонажа
"""

from aiogram.fsm.state import State, StatesGroup


class CreateCharacter(StatesGroup):
    """Состояния создания персонажа"""
    class_select = State()
    subclass_select = State()
    class_equipment_select = State()
    spells_cantrips_category = State()
    spells_cantrips_list = State()
    spells_cantrips_detail = State()
    spells_cantrips_complete = State()
    spells_level1_category = State()
    spells_level1_list = State()
    spells_level1_detail = State()
    spells_level1_complete = State()
    fighting_style_select = State()
    invocations_select = State()
    background_select = State()
    background_equipment_select = State()
    race_select = State()
    subrace_select = State()
    name_input = State()
    backstory_input = State()
    image_input = State()