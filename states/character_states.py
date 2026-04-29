# states/character_states.py
"""
FSM состояния для создания персонажа
"""

from aiogram.fsm.state import State, StatesGroup


class CreateCharacter(StatesGroup):
    """Состояния создания персонажа"""
    # Шаг 1: Класс
    class_select = State()
    subclass_select = State()
    
    # НОВЫЙ ШАГ: Выбор навыков класса
    skills_select = State()
    skills_list = State()
    skills_complete = State()
    
    # Шаг 2: Снаряжение класса
    class_equipment_select = State()
    
    # Шаг 3-4: Заклинания
    spells_cantrips_category = State()
    spells_cantrips_list = State()
    spells_cantrips_detail = State()
    spells_cantrips_complete = State()
    spells_level1_category = State()
    spells_level1_list = State()
    spells_level1_detail = State()
    spells_level1_complete = State()
    
    # Шаг 5: Боевой стиль
    fighting_style_select = State()
    
    # Шаг 6: Возвания (колдун)
    invocations_select = State()
    
    # Шаг 7-8: Предыстория и её снаряжение
    background_select = State()
    background_equipment_select = State()
    
    # Шаг 9-10: Раса и подраса
    race_select = State()
    subrace_select = State()
    
    # Шаг 11-12: Имя, история, изображение
    name_input = State()
    backstory_input = State()
    image_input = State()
