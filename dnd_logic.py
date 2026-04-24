"""
D&D 5e Character Logic Module
Модуль с игровой логикой для создания персонажей D&D
"""

from typing import Dict, List, Any, Tuple

# Данные классов
CLASS_DATA: Dict[str, Dict[str, Any]] = {
    "Воин": {
        "hit_die": 10,
        "primary_stats": ["STR", "CON"],
        "saving_throws": ["STR", "CON"],
        "skills": ["Athletics", "Intimidation"],
        "equipment": ["Longsword", "Shield", "Chain Mail"],
        "spells": [],
        "description": "Мастер боя, владеющий всеми видами оружия и доспехов"
    },
    "Маг": {
        "hit_die": 6,
        "primary_stats": ["INT"],
        "saving_throws": ["INT", "WIS"],
        "skills": ["Arcana", "History"],
        "equipment": ["Quarterstaff", "Spellbook", "Component Pouch"],
        "spells": ["Fire Bolt", "Mage Armor", "Magic Missile"],
        "description": "Таинственный заклинатель, черпающий силу из магии"
    },
    "Плут": {
        "hit_die": 8,
        "primary_stats": ["DEX"],
        "saving_throws": ["DEX", "INT"],
        "skills": ["Stealth", "Acrobatics"],
        "equipment": ["Two Daggers", "Leather Armor", "Thieves' Tools"],
        "spells": [],
        "description": "Ловкий и скрытный искатель приключений"
    }
}


def modifier(stat: int) -> int:
    """
    Вычисляет модификатор характеристики

    Args:
        stat: значение характеристики (обычно от 1 до 20)

    Returns:
        int: модификатор характеристики
    """
    return (stat - 10) // 2


def calc_hp(character_class: str, constitution: int, level: int = 1) -> int:
    """
    Вычисляет максимальное здоровье персонажа

    Args:
        character_class: название класса
        constitution: значение телосложения
        level: уровень персонажа (по умолчанию 1)

    Returns:
        int: максимальное здоровье
    """
    if character_class not in CLASS_DATA:
        raise ValueError(f"Unknown class: {character_class}")

    hit_die = CLASS_DATA[character_class]["hit_die"]
    con_mod = modifier(constitution)

    if level == 1:
        # На 1 уровне берем максимальное значение кубика
        return hit_die + con_mod
    else:
        # На следующих уровнях: максимальное на 1-м + среднее на остальных
        # hit_die + con_mod + (level-1) * (hit_die//2 + 1 + con_mod)
        hp_per_level = (hit_die // 2) + 1  # Среднее значение кубика
        return hit_die + con_mod + (level - 1) * (hp_per_level + con_mod)


def calc_ac(dexterity: int, armor_type: str = "none") -> int:
    """
    Вычисляет класс брони (AC)

    Args:
        dexterity: значение ловкости
        armor_type: тип брони ("none", "light", "medium", "heavy", "shield")

    Returns:
        int: класс брони
    """
    dex_mod = modifier(dexterity)

    # Простая версия для совместимости со старым кодом
    if armor_type == "none":
        return 10 + dex_mod
    elif armor_type == "light":
        return 11 + dex_mod
    elif armor_type == "medium":
        return 14 + min(2, dex_mod)
    elif armor_type == "heavy":
        return 16
    elif armor_type == "shield":
        return 2
    else:
        return 10 + dex_mod


def get_racial_bonuses(race: str) -> Dict[str, int]:
    """
    Возвращает бонусы к характеристикам за расу

    Args:
        race: название расы

    Returns:
        dict: словарь с бонусами к характеристикам
    """
    racial_bonuses = {
        "Человек": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1},
        "Эльф": {"DEX": 2, "INT": 1},
        "Дварф": {"CON": 2, "STR": 1},
        "Полурослик": {"DEX": 2, "CHA": 1}
    }

    return racial_bonuses.get(race, {"STR": 0, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0})


def get_class_skills(character_class: str) -> List[str]:
    """
    Возвращает список навыков класса

    Args:
        character_class: название класса

    Returns:
        list: список навыков
    """
    return CLASS_DATA.get(character_class, {}).get("skills", [])


def get_class_equipment(character_class: str) -> List[str]:
    """
    Возвращает список стартового снаряжения класса

    Args:
        character_class: название класса

    Returns:
        list: список снаряжения
    """
    return CLASS_DATA.get(character_class, {}).get("equipment", [])


def get_class_spells(character_class: str) -> List[str]:
    """
    Возвращает список заклинаний класса

    Args:
        character_class: название класса

    Returns:
        list: список заклинаний
    """
    return CLASS_DATA.get(character_class, {}).get("spells", [])


def validate_character(name: str, character_class: str, race: str, stats: Dict[str, int]) -> Tuple[bool, str]:
    """
    Валидирует данные персонажа

    Args:
        name: имя персонажа
        character_class: класс
        race: раса
        stats: характеристики

    Returns:
        tuple: (валидность, сообщение об ошибке)
    """
    # Проверка имени
    if not name or len(name.strip()) < 1:
        return False, "Имя не может быть пустым"

    if len(name) > 50:
        return False, "Имя слишком длинное (максимум 50 символов)"

    # Проверка класса
    if character_class not in CLASS_DATA:
        return False, f"Класс '{character_class}' не существует"

    # Проверка расы
    valid_races = ["Человек", "Эльф", "Дварф", "Полурослик"]
    if race not in valid_races:
        return False, f"Раса '{race}' не существует"

    # Проверка характеристик
    required_stats = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    for stat in required_stats:
        if stat not in stats:
            return False, f"Характеристика {stat} отсутствует"
        if not isinstance(stats[stat], int):
            return False, f"Характеристика {stat} должна быть числом"
        if stats[stat] < 1 or stats[stat] > 20:
            return False, f"Характеристика {stat} должна быть от 1 до 20"

    return True, "OK"


def calculate_proficiency_bonus(level: int) -> int:
    """
    Вычисляет бонус владения в зависимости от уровня

    Args:
        level: уровень персонажа (1-20)

    Returns:
        int: бонус владения
    """
    if level <= 4:
        return 2
    elif level <= 8:
        return 3
    elif level <= 12:
        return 4
    elif level <= 16:
        return 5
    else:
        return 6


# Функция для обратной совместимости со старым кодом
def get_class_data(class_name: str) -> Dict[str, Any]:
    """
    Возвращает данные класса (для обратной совместимости)

    Args:
        class_name: название класса

    Returns:
        dict: данные класса
    """
    return CLASS_DATA.get(class_name, {})


# Тестирование модуля
if __name__ == "__main__":
    print("=== Тестирование D&D Logic Module ===\n")

    # Тест 1: modifier
    print("✓ Тест modifier:")
    assert modifier(15) == 2, "modifier(15) должно быть 2"
    assert modifier(10) == 0, "modifier(10) должно быть 0"
    assert modifier(8) == -1, "modifier(8) должно быть -1"
    print("  Все тесты пройдены!\n")

    # Тест 2: calc_hp (обратная совместимость)
    print("✓ Тест calc_hp (без level):")
    warrior_hp = calc_hp("Воин", 15)
    print(f"  Воин (CON 15) HP: {warrior_hp}")

    mage_hp = calc_hp("Маг", 13)
    print(f"  Маг (CON 13) HP: {mage_hp}")

    rogue_hp = calc_hp("Плут", 14)
    print(f"  Плут (CON 14) HP: {rogue_hp}\n")

    # Тест 3: calc_hp с уровнем
    print("✓ Тест calc_hp (с уровнем):")
    warrior_lvl3 = calc_hp("Воин", 15, level=3)
    print(f"  Воин 3 уровня: {warrior_lvl3} HP\n")

    # Тест 4: calc_ac
    print("✓ Тест calc_ac:")
    ac_no_armor = calc_ac(14)
    print(f"  AC без брони (DEX 14): {ac_no_armor}")

    ac_light = calc_ac(14, "light")
    print(f"  AC с легкой броней: {ac_light}\n")

    # Тест 5: расовые бонусы
    print("✓ Тест расовых бонусов:")
    elf_bonus = get_racial_bonuses("Эльф")
    print(f"  Эльф: {elf_bonus}")

    human_bonus = get_racial_bonuses("Человек")
    print(f"  Человек: {human_bonus}\n")

    # Тест 6: проверка данных классов
    print("✓ Тест данных классов:")
    for class_name in CLASS_DATA:
        stats = calc_hp(class_name, 14)
        skills = get_class_skills(class_name)
        equip = get_class_equipment(class_name)
        print(f"  {class_name}: HP={stats}, Навыки={len(skills)}, Снаряжение={len(equip)}")
    print()

    # Тест 7: валидация
    print("✓ Тест валидации:")
    test_stats = {"STR": 15, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 8}
    is_valid, msg = validate_character("Aragorn", "Воин", "Человек", test_stats)
    print(f"  Валидный персонаж: {is_valid} - {msg}")

    is_valid, msg = validate_character("", "Воин", "Человек", test_stats)
    print(f"  Пустое имя: {is_valid} - {msg}")

    is_valid, msg = validate_character("Aragorn", "Несуществующий", "Человек", test_stats)
    print(f"  Несуществующий класс: {is_valid} - {msg}\n")

    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Модуль работает корректно.")