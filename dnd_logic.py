"""
D&D 5e Character Logic Module
Модуль с игровой логикой для создания персонажей D&D
"""

from typing import Dict, List, Any, Tuple

# ---------------- CLASS DATA ----------------
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

# ---------------- CORE LOGIC ----------------
def modifier(stat: int) -> int:
    """Модификатор характеристики"""
    return (stat - 10) // 2


def calc_hp(character_class: str, constitution: int, level: int = 1) -> int:
    """Расчет HP"""
    if character_class not in CLASS_DATA:
        raise ValueError(f"Unknown class: {character_class}")

    if level < 1:
        raise ValueError("Level must be >= 1")

    hit_die = CLASS_DATA[character_class]["hit_die"]
    con_mod = modifier(constitution)

    if level == 1:
        return hit_die + con_mod
    else:
        avg_roll = (hit_die // 2) + 1
        return hit_die + con_mod + (level - 1) * (avg_roll + con_mod)


def calc_ac(dexterity: int, armor_type: str = "none") -> int:
    """Расчет AC"""
    dex_mod = modifier(dexterity)

    if armor_type == "none":
        return 10 + dex_mod
    elif armor_type == "light":
        return 11 + dex_mod
    elif armor_type == "medium":
        return 14 + min(2, dex_mod)
    elif armor_type == "heavy":
        return 16
    elif armor_type == "shield":
        return 10 + dex_mod + 2
    else:
        return 10 + dex_mod


# ---------------- RACE ----------------
def get_racial_bonuses(race: str) -> Dict[str, int]:
    racial_bonuses = {
        "Человек": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1},
        "Эльф": {"DEX": 2, "INT": 1},
        "Дварф": {"CON": 2, "STR": 1},
        "Полурослик": {"DEX": 2, "CHA": 1}
    }

    default = {"STR": 0, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0}
    return dict(racial_bonuses.get(race, default))


# ---------------- CLASS HELPERS ----------------
def get_class_skills(character_class: str) -> List[str]:
    return list(CLASS_DATA.get(character_class, {}).get("skills", []))


def get_class_equipment(character_class: str) -> List[str]:
    return list(CLASS_DATA.get(character_class, {}).get("equipment", []))


def get_class_spells(character_class: str) -> List[str]:
    return list(CLASS_DATA.get(character_class, {}).get("spells", []))


def get_class_data(class_name: str) -> Dict[str, Any]:
    return dict(CLASS_DATA.get(class_name, {}))


# ---------------- VALIDATION ----------------
def validate_character(
    name: str,
    character_class: str,
    race: str,
    stats: Dict[str, int]
) -> Tuple[bool, str]:

    if not name or len(name.strip()) == 0:
        return False, "Имя не может быть пустым"

    if len(name) > 50:
        return False, "Имя слишком длинное"

    if character_class not in CLASS_DATA:
        return False, f"Класс '{character_class}' не существует"

    valid_races = ["Человек", "Эльф", "Дварф", "Полурослик"]
    if race not in valid_races:
        return False, f"Раса '{race}' не существует"

    required_stats = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

    for stat in required_stats:
        if stat not in stats:
            return False, f"{stat} отсутствует"
        if not isinstance(stats[stat], int):
            return False, f"{stat} должно быть числом"
        if not (1 <= stats[stat] <= 20):
            return False, f"{stat} должно быть от 1 до 20"

    if sum(stats.values()) > 80:
        return False, "Слишком высокие характеристики"

    return True, "OK"


# ---------------- PROFICIENCY ----------------
def calculate_proficiency_bonus(level: int) -> int:
    if level < 1:
        raise ValueError("Level must be >= 1")

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


# ---------------- TEST ----------------
if __name__ == "__main__":
    print("=== TEST DND LOGIC ===")

    # modifier
    assert modifier(15) == 2
    assert modifier(10) == 0
    assert modifier(8) == -1

    # hp
    print("HP:", calc_hp("Воин", 14))
    print("HP lvl3:", calc_hp("Воин", 14, 3))

    # ac
    print("AC:", calc_ac(14))
    print("AC light:", calc_ac(14, "light"))

    # validation
    stats = {"STR": 15, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 8}
    print(validate_character("Hero", "Воин", "Человек", stats))

    print("✅ OK")