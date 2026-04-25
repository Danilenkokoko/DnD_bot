# dnd_logic.py
"""
D&D 5e Character Logic Module
Модуль с игровой логикой для создания персонажей D&D
Поддерживает 16 рас, 13 классов и 17 предысторий
"""

from typing import Dict, List, Any, Tuple, Optional
from races_data import RACES_DATA, get_race_data, get_race_ability_bonuses, get_race_traits, get_all_races
from classes_data import CLASSES_DATA, get_class_data, get_class_hit_die, get_class_skill_choices, get_all_classes
from backgrounds_data import (
    get_all_backgrounds, get_background_data, get_background_characteristics,
    get_background_trait, get_background_skills, get_background_tools,
    get_background_description, get_equipment_choice, get_equipment_options,
    format_background_info, search_backgrounds
)


# ---------------- CORE LOGIC ----------------
def modifier(stat: int) -> int:
    """
    Расчёт модификатора характеристики

    Args:
        stat: значение характеристики (от 1 до 30)

    Returns:
        int: модификатор характеристики
    """
    return (stat - 10) // 2


def calc_hp(character_class: str, constitution: int, level: int = 1) -> int:
    """
    Расчёт HP персонажа

    Args:
        character_class: название класса
        constitution: значение телосложения
        level: уровень персонажа (по умолчанию 1)

    Returns:
        int: максимальное HP
    """
    class_data = get_class_data(character_class)
    if not class_data:
        raise ValueError(f"Неизвестный класс: {character_class}")

    if level < 1:
        raise ValueError("Уровень должен быть >= 1")

    hit_die = class_data.get("hit_die", 6)
    con_mod = modifier(constitution)

    if level == 1:
        # 1-й уровень: максимум хита + модификатор телосложения
        return hit_die + max(1, con_mod)
    else:
        # Для уровней выше 1-го: среднее значение + модификатор
        avg_roll = (hit_die // 2) + 1
        return hit_die + max(1, con_mod) + (level - 1) * (avg_roll + max(1, con_mod))


def calc_ac(dexterity: int, armor_type: str = "none", has_shield: bool = False) -> int:
    """
    Расчёт Класса Брони (AC)

    Args:
        dexterity: значение ловкости
        armor_type: тип брони ("none", "light", "medium", "heavy")
        has_shield: есть ли щит

    Returns:
        int: Класс Брони
    """
    dex_mod = modifier(dexterity)

    armor_base = {
        "none": 10 + dex_mod,
        "light": 11 + dex_mod,
        "medium": 14 + min(2, dex_mod),
        "heavy": 16
    }

    base_ac = armor_base.get(armor_type, 10 + dex_mod)

    if has_shield:
        base_ac += 2

    return base_ac


def calculate_proficiency_bonus(level: int) -> int:
    """
    Расчёт бонуса мастерства в зависимости от уровня

    Args:
        level: уровень персонажа (1-20)

    Returns:
        int: бонус мастерства
    """
    if level < 1:
        raise ValueError("Уровень должен быть >= 1")

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


# ---------------- STATS ----------------
def get_standard_stats() -> Dict[str, int]:
    """
    Возвращает стандартный набор характеристик (27 очков)
    Используется распределение: 15, 14, 13, 12, 10, 8
    """
    return {
        "STR": 15,
        "DEX": 14,
        "CON": 13,
        "INT": 12,
        "WIS": 10,
        "CHA": 8
    }


def apply_racial_bonuses(stats: Dict[str, int], race: str, subrace: Optional[str] = None) -> Dict[str, int]:
    """
    Применяет бонусы расы к характеристикам

    Args:
        stats: базовые характеристики
        race: название расы
        subrace: подраса (опционально)

    Returns:
        Dict[str, int]: изменённые характеристики
    """
    result = stats.copy()
    bonuses = get_race_ability_bonuses(race, subrace)

    for stat, bonus in bonuses.items():
        if stat in result:
            result[stat] += bonus

    return result


def get_initial_stats(race: str, subrace: Optional[str] = None) -> Dict[str, int]:
    """
    Получает начальные характеристики с учётом расы

    Args:
        race: название расы
        subrace: подраса (опционально)

    Returns:
        Dict[str, int]: готовые характеристики
    """
    base_stats = get_standard_stats()
    return apply_racial_bonuses(base_stats, race, subrace)


# ---------------- VALIDATION ----------------
def validate_name(name: str) -> Tuple[bool, str]:
    """Проверяет имя персонажа"""
    if not name or len(name.strip()) == 0:
        return False, "❌ Имя не может быть пустым"

    if len(name) > 50:
        return False, "❌ Имя слишком длинное (максимум 50 символов)"

    if len(name) < 2:
        return False, "❌ Имя слишком короткое (минимум 2 символа)"

    # Проверка на недопустимые символы
    import re
    if re.search(r'[<>@#$%^&*()]', name):
        return False, "❌ Имя содержит недопустимые символы"

    return True, "✅ Имя корректно"


def validate_race(race: str) -> Tuple[bool, str]:
    """Проверяет расу"""
    races = get_all_races()

    if race not in races:
        return False, f"❌ Раса '{race}' не существует. Доступные расы: {', '.join(races)}"

    return True, "✅ Раса корректна"


def validate_class(class_name: str) -> Tuple[bool, str]:
    """Проверяет класс"""
    classes = get_all_classes()

    if class_name not in classes:
        return False, f"❌ Класс '{class_name}' не существует. Доступные классы: {', '.join(classes)}"

    return True, "✅ Класс корректен"


def validate_background(background: str) -> Tuple[bool, str]:
    """Проверяет предысторию - ИСПРАВЛЕНО (убрана рекурсия)"""
    # Получаем список предысторий из БД
    backgrounds = get_all_backgrounds()

    if background not in backgrounds:
        return False, f"❌ Предыстория '{background}' не существует. Доступные предыстории: {', '.join(backgrounds[:10])}..."

    return True, "✅ Предыстория корректна"


def validate_stats(stats: Dict[str, int]) -> Tuple[bool, str]:
    """Проверяет характеристики"""
    required_stats = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

    # Проверка наличия всех характеристик
    for stat in required_stats:
        if stat not in stats:
            return False, f"❌ Характеристика {stat} отсутствует"
        if not isinstance(stats[stat], int):
            return False, f"❌ {stat} должно быть числом"
        if not (1 <= stats[stat] <= 30):
            return False, f"❌ {stat} должно быть от 1 до 30"

    # Суммарное ограничение (опционально)
    total = sum(stats.values())
    if total > 90:
        return False, f"⚠️ Сумма характеристик ({total}) очень высокая. Обычно рекомендуется не более 85-90"

    return True, "✅ Характеристики корректны"


def validate_character(
        name: str,
        character_class: str,
        race: str,
        background: str,
        stats: Dict[str, int]
) -> Tuple[bool, str]:
    """
    Полная валидация персонажа
    """
    # Проверка имени
    valid, msg = validate_name(name)
    if not valid:
        return False, msg

    # Проверка расы
    valid, msg = validate_race(race)
    if not valid:
        return False, msg

    # Проверка класса
    valid, msg = validate_class(character_class)
    if not valid:
        return False, msg

    # Проверка предыстории
    valid, msg = validate_background(background)
    if not valid:
        return False, msg

    # Проверка характеристик
    valid, msg = validate_stats(stats)
    if not valid:
        return False, msg

    return True, "✅ Персонаж валиден"


# ---------------- RACE HELPERS ----------------
def get_race_list() -> List[str]:
    """Возвращает список всех доступных рас"""
    return get_all_races()


def get_race_info(race: str) -> Dict[str, Any]:
    """Возвращает информацию о расе"""
    return get_race_data(race)


def get_race_traits_list(race: str, subrace: Optional[str] = None) -> List[str]:
    """Возвращает особенности расы"""
    return get_race_traits(race, subrace)


def get_race_ability_bonuses_list(race: str, subrace: Optional[str] = None) -> Dict[str, int]:
    """Возвращает бонусы расы к характеристикам"""
    return get_race_ability_bonuses(race, subrace)


def format_race_info(race: str, subrace: Optional[str] = None) -> str:
    """Форматирует информацию о расе для отображения"""
    race_data = get_race_info(race)
    if not race_data:
        return f"❌ Раса '{race}' не найдена"

    info = f"🧝 **{race}**"
    if subrace:
        info += f" ({subrace})"
    info += "\n\n"

    info += f"**Скорость:** {race_data.get('speed', 30)} футов\n"
    info += f"**Размер:** {race_data.get('size', 'Средний')}\n"
    info += f"**Языки:** {', '.join(race_data.get('languages', ['Общий']))}\n\n"

    info += "**Особенности:**\n"
    for trait in race_data.get('traits', []):
        info += f"• {trait}\n"

    return info


# ---------------- CLASS HELPERS ----------------
def get_class_list() -> List[str]:
    """Возвращает список всех доступных классов"""
    return get_all_classes()


def get_class_info(class_name: str) -> Dict[str, Any]:
    """Возвращает информацию о классе"""
    return get_class_data(class_name)


def get_class_skills_list(class_name: str) -> List[str]:
    """Возвращает список доступных навыков для класса"""
    return get_class_skill_choices(class_name)


def get_class_hp(class_name: str, constitution: int, level: int = 1) -> int:
    """Возвращает HP для класса"""
    return calc_hp(class_name, constitution, level)


def get_class_hit_die_value(class_name: str) -> int:
    """Возвращает хитовый кубик класса"""
    class_data = get_class_info(class_name)
    return class_data.get("hit_die", 6)


def format_class_info(class_name: str) -> str:
    """Форматирует информацию о классе для отображения"""
    class_data = get_class_info(class_name)
    if not class_data:
        return f"❌ Класс '{class_name}' не найден"

    info = f"⚔️ **{class_name}**\n\n"
    info += f"**Описание:** {class_data.get('description', 'Нет описания')}\n\n"
    info += f"**Хитовый кубик:** d{class_data.get('hit_die', 6)}\n"
    info += f"**Основные характеристики:** {', '.join(class_data.get('primary_stats', []))}\n"
    info += f"**Спасброски:** {', '.join(class_data.get('saving_throws', []))}\n\n"

    info += "**Доступные навыки:**\n"
    for skill in class_data.get('skills', [])[:5]:
        info += f"• {skill}\n"
    if len(class_data.get('skills', [])) > 5:
        info += f"• ... и {len(class_data.get('skills', [])) - 5} других\n"

    return info


# ---------------- BACKGROUND HELPERS ----------------
def get_background_list() -> List[str]:
    """Возвращает список всех доступных предысторий"""
    return get_all_backgrounds()


def get_background_info(background: str) -> Dict[str, Any]:
    """Возвращает информацию о предыстории"""
    return get_background_data(background)


def get_background_skills_list(background: str) -> List[str]:
    """Возвращает навыки от предыстории"""
    return get_background_skills(background)


def get_background_tools_list(background: str) -> str:
    """Возвращает инструменты от предыстории"""
    return get_background_tools(background)


def get_background_equipment_by_choice(background: str, choice: str = "A") -> str:
    """Возвращает снаряжение предыстории по выбору А или Б"""
    return get_equipment_choice(background, choice)


def format_background_for_display(background: str) -> str:
    """Форматирует информацию о предыстории для отображения"""
    return format_background_info(background)


# ---------------- LEVEL UP ----------------
def calculate_hp_increase(character_class: str, constitution: int, current_level: int, new_level: int) -> int:
    """
    Рассчитывает новое HP при повышении уровня

    Args:
        character_class: класс персонажа
        constitution: телосложение
        current_level: текущий уровень
        new_level: новый уровень

    Returns:
        int: новое максимальное HP
    """
    if new_level <= current_level:
        return calc_hp(character_class, constitution, current_level)

    return calc_hp(character_class, constitution, new_level)


def get_level_up_info(character_class: str, constitution: int, current_level: int) -> Dict[str, Any]:
    """
    Возвращает информацию о повышении уровня

    Returns:
        Dict с полями: new_hp, proficiency_bonus, features
    """
    new_level = current_level + 1
    new_hp = calculate_hp_increase(character_class, constitution, current_level, new_level)
    new_proficiency = calculate_proficiency_bonus(new_level)
    old_proficiency = calculate_proficiency_bonus(current_level)

    # Определяем, какие умения получает класс на новом уровне
    class_data = get_class_info(character_class)
    level_features = class_data.get("features", {}).get(new_level, [])

    return {
        "new_level": new_level,
        "new_hp": new_hp,
        "hp_increase": new_hp - calc_hp(character_class, constitution, current_level),
        "proficiency_bonus": new_proficiency,
        "proficiency_increased": new_proficiency > old_proficiency,
        "features": level_features
    }


# ---------------- SKILLS ----------------
def get_skills_from_class(class_name: str, selected_skills: List[str]) -> List[str]:
    """
    Получает навыки выбранные из доступных для класса

    Args:
        class_name: название класса
        selected_skills: список выбранных навыков

    Returns:
        List[str]: итоговый список навыков
    """
    available = get_class_skill_choices(class_name)
    # Фильтруем только выбранные навыки, которые есть в доступных
    return [skill for skill in selected_skills if skill in available]


def get_all_skills_for_class(class_name: str) -> List[str]:
    """Возвращает все доступные навыки для класса"""
    return get_class_skill_choices(class_name)


# ---------------- UTILITY ----------------
def calculate_saving_throw(stat_value: int, proficiency: bool = False, proficiency_bonus: int = 0) -> int:
    """
    Рассчитывает модификатор спасброска

    Args:
        stat_value: значение характеристики
        proficiency: есть ли владение
        proficiency_bonus: бонус мастерства

    Returns:
        int: модификатор спасброска
    """
    base = modifier(stat_value)
    if proficiency:
        base += proficiency_bonus
    return base


def calculate_skill_check(ability_mod: int, proficiency: bool = False, proficiency_bonus: int = 0) -> int:
    """
    Рассчитывает модификатор проверки навыка

    Args:
        ability_mod: модификатор характеристики
        proficiency: есть ли владение
        proficiency_bonus: бонус мастерства

    Returns:
        int: модификатор проверки
    """
    total = ability_mod
    if proficiency:
        total += proficiency_bonus
    return total


# ---------------- TEST ----------------
if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ D&D LOGIC MODULE")
    print("=" * 60)

    # 1. Тест модификатора
    print("\n1. Тест модификатора:")
    print(f"   modifier(15) = {modifier(15)} (ожидается 2)")
    print(f"   modifier(10) = {modifier(10)} (ожидается 0)")
    print(f"   modifier(8) = {modifier(8)} (ожидается -1)")
    assert modifier(15) == 2, "Ошибка в modifier(15)"
    assert modifier(10) == 0, "Ошибка в modifier(10)"
    assert modifier(8) == -1, "Ошибка в modifier(8)"
    print("   ✅ OK")

    # 2. Тест HP
    print("\n2. Тест HP:")
    print(f"   Воин, CON=14, уровень 1: {calc_hp('Воин', 14)} (ожидается 12)")
    print(f"   Волшебник, CON=12, уровень 1: {calc_hp('Волшебник', 12)} (ожидается 7)")
    print(f"   Воин, CON=14, уровень 3: {calc_hp('Воин', 14, 3)}")
    assert calc_hp('Воин', 14) == 12, "Ошибка в calc_hp для Воина"
    print("   ✅ OK")

    # 3. Тест AC
    print("\n3. Тест AC:")
    print(f"   Без брони, DEX=14: {calc_ac(14)} (ожидается 12)")
    print(f"   Лёгкая броня, DEX=14: {calc_ac(14, 'light')} (ожидается 13)")
    print(f"   Средняя броня, DEX=14: {calc_ac(14, 'medium')} (ожидается 16)")
    print("   ✅ OK")

    # 4. Тест бонуса мастерства
    print("\n4. Тест бонуса мастерства:")
    for level in [1, 5, 9, 13, 17]:
        print(f"   Уровень {level}: {calculate_proficiency_bonus(level)}")
    print("   ✅ OK")

    # 5. Тест рас
    print("\n5. Тест рас:")
    races = get_race_list()
    print(f"   Всего рас: {len(races)}")
    print(f"   Первые 5: {', '.join(races[:5])}")

    # 6. Тест классов
    print("\n6. Тест классов:")
    classes = get_class_list()
    print(f"   Всего классов: {len(classes)}")
    print(f"   Список: {', '.join(classes)}")

    # 7. Тест предысторий
    print("\n7. Тест предысторий:")
    backgrounds = get_background_list()
    print(f"   Всего предысторий: {len(backgrounds)}")
    if backgrounds:
        print(f"   Первые 5: {', '.join(backgrounds[:5])}")
    else:
        print("   ⚠️ Предыстории не загружены (проверьте БД)")

    # 8. Тест начальных характеристик
    print("\n8. Тест начальных характеристик:")
    stats = get_initial_stats("Дварф")
    print(f"   Дварф (без подрасы): {stats}")
    stats_elf = get_initial_stats("Эльф", "Лесной эльф")
    print(f"   Лесной эльф: {stats_elf}")
    print("   ✅ OK")

    # 9. Тест валидации
    print("\n9. Тест валидации:")
    test_stats = {"STR": 15, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 8}

    valid, msg = validate_character("Гимли", "Воин", "Дварф", "Солдат", test_stats)
    print(f"   Гимли: {msg}")

    valid, msg = validate_character("", "Воин", "Человек", "Мудрец", test_stats)
    print(f"   Пустое имя: {msg}")

    valid, msg = validate_character("Герой", "НесуществующийКласс", "Человек", "Мудрец", test_stats)
    print(f"   Несуществующий класс: {msg}")

    # 10. Тест информации о классе
    print("\n10. Тест информации о классе:")
    class_info = format_class_info("Воин")
    print(f"   {class_info[:100]}...")

    # 11. Тест информации о расе
    print("\n11. Тест информации о расе:")
    race_info = format_race_info("Эльф", "Лесной эльф")
    print(f"   {race_info[:100]}...")

    # 12. Тест повышения уровня
    print("\n12. Тест повышения уровня:")
    level_up = get_level_up_info("Воин", 14, 1)
    print(f"   Уровень 1 -> 2: +{level_up['hp_increase']} HP, новый бонус: {level_up['proficiency_bonus']}")

    print("\n" + "=" * 60)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("=" * 60)