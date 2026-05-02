# states/character_states.py
"""
FSM состояния для создания персонажа
"""

from aiogram.fsm.state import State, StatesGroup


class CreateCharacter(StatesGroup):
    """Состояния создания персонажа"""
    # Шаг 1: Класс
    class_select = State()
    # Подкласс удалён (выбирается на 3 уровне, не на 1-м)

    # Шаг 2: Выбор навыков класса
    skills_select = State()
    skills_list = State()
    skills_complete = State()

    # Шаг 3: Снаряжение класса
    class_equipment_select = State()

    # Шаг 4-5: Заклинания
    spells_cantrips_category = State()
    spells_cantrips_list = State()
    spells_cantrips_detail = State()
    spells_cantrips_complete = State()
    spells_level1_category = State()
    spells_level1_list = State()
    spells_level1_detail = State()
    spells_level1_complete = State()

    # Шаг 6: Боевой стиль
    fighting_style_select = State()

    # Предыстория (без отдельного выбора снаряжения)
    background_select = State()

    # Раса и подраса
    race_select = State()
    subrace_select = State()

    # Имя, история, мировоззрение, изображение
    name_input = State()
    backstory_input = State()
    alignment_select = State()
    image_input = State()

    # ========== НОВЫЕ СОСТОЯНИЯ ==========
    # Друид: выбор природного ордена
    druid_order_select = State()
    # Жрец: выбор ордена
    cleric_order_select = State()
    # Колдун: выбор возвания (договора)
    warlock_pact_select = State()
    # Для договора гримуара: выбор 3 кантрипов
    warlock_tome_cantrips_select = State()
    # Для договора гримуара: выбор 2 ритуалов 1 уровня
    warlock_tome_rituals_select = State()
    # Плут: выбор двух навыков для экспертности
    rogue_expertise_select = State()
    # Плут: выбор дополнительного языка
    rogue_language_select = State()