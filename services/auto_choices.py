# services/auto_choices.py
"""
Вспомогательные функции автоматического выбора оптимальных параметров персонажа.
Реализует D&D 5.5e (2024) рекомендации для навыков, боевых стилей,
языков предысторий и владения инструментами.
"""
 
from typing import List, Optional
 
# =========================================================
# ОПТИМАЛЬНЫЕ НАВЫКИ ПО КЛАССАМ
# Основано на D&D 5.5e 2024 + популярные руководства
# =========================================================
 
# Маппинг русских имён навыков из available_skills на английские ключи из classes_data
_SKILL_NAME_MAP = {
    "Акробатика": "Acrobatics",
    "Атлетика": "Athletics",
    "Восприятие": "Perception",
    "Выживание": "Survival",
    "Выступление": "Performance",
    "Запугивание": "Intimidation",
    "История": "History",
    "Ловкость рук": "Sleight of Hand",
    "Медицина": "Medicine",
    "Обман": "Deception",
    "Обращение с животными": "Animal Handling",
    "Природа": "Nature",
    "Проницательность": "Insight",
    "Расследование": "Investigation",
    "Религия": "Religion",
    "Скрытность": "Stealth",
    "Тайная магия": "Arcana",
    "Убеждение": "Persuasion",
}
 
# Приоритетные навыки для каждого класса (от наиболее важного к менее важному)
# Используются английские ключи из classes_data для совместимости
_CLASS_OPTIMAL_SKILLS = {
    "Артефактор":  ["Arcana", "Investigation", "Perception", "History"],
    "Бард":        ["Persuasion", "Perception", "Deception", "Insight"],
    "Варвар":      ["Athletics", "Perception", "Survival", "Intimidation"],
    "Воин":        ["Athletics", "Perception", "Intimidation", "Survival"],
    "Волшебник":   ["Arcana", "Investigation", "History", "Insight"],
    "Друид":       ["Perception", "Nature", "Survival", "Animal Handling"],
    "Жрец":        ["Insight", "Persuasion", "Religion", "Medicine"],
    "Колдун":      ["Arcana", "Deception", "Intimidation", "Investigation"],
    "Монах":       ["Acrobatics", "Stealth", "Perception", "Insight"],
    "Паладин":     ["Persuasion", "Athletics", "Insight", "Religion"],
    "Плут":        ["Stealth", "Perception", "Acrobatics", "Deception"],
    "Следопыт":    ["Perception", "Survival", "Stealth", "Nature"],
    "Чародей":     ["Arcana", "Persuasion", "Deception", "Insight"],
}
 
# Обратный маппинг: английский -> русский
_SKILL_NAME_MAP_REVERSE = {v: k for k, v in _SKILL_NAME_MAP.items()}
 
 
def get_optimal_skills_for_class(
    class_name: str,
    available_skills: List[str],
    skill_choices: int,
) -> List[str]:
    """
    Возвращает список из skill_choices рекомендуемых навыков для класса.
 
    Args:
        class_name: название класса персонажа (на русском)
        available_skills: список доступных навыков (на русском, из UI)
        skill_choices: количество навыков, которые нужно выбрать
 
    Returns:
        Список рекомендуемых навыков (на русском), не превышающий skill_choices.
        Выбираются только те, которые входят в available_skills.
    """
    priority = _CLASS_OPTIMAL_SKILLS.get(class_name, [])
    result: List[str] = []
 
    # Конвертируем available_skills в set английских для быстрой проверки
    available_en = {_SKILL_NAME_MAP.get(s, s) for s in available_skills}
 
    for en_skill in priority:
        if en_skill in available_en:
            ru_skill = _SKILL_NAME_MAP_REVERSE.get(en_skill, en_skill)
            if ru_skill in available_skills:
                result.append(ru_skill)
        if len(result) >= skill_choices:
            break
 
    return result
 
 
# =========================================================
# РЕКОМЕНДАЦИЯ БОЕВОГО СТИЛЯ ПО ОРУЖИЮ
# =========================================================
 
# Маппинг оружия -> рекомендуемый боевой стиль
_WEAPON_TO_STYLE = {
    # Двуручное оружие
    "Двуручный меч": "Великое оружие",
    "Алебарда": "Великое оружие",
    "Секира": "Великое оружие",
    "Боевой посох": "Великое оружие",
    "Косарь": "Великое оружие",
    "Пика": "Великое оружие",
    "Алебарда ": "Великое оружие",
 
    # Одноручное + щит
    "Длинный меч": "Дуэлянт",
    "Булава": "Дуэлянт",
    "Боевой топор": "Дуэлянт",
    "Короткий меч": "Дуэлянт",
    "Рапира": "Дуэлянт",
 
    # Дальнобойное
    "Длинный лук": "Стрелок",
    "Короткий лук": "Стрелок",
    "Лёгкий арбалет": "Стрелок",
    "Тяжёлый арбалет": "Стрелок",
    "Ручной арбалет": "Стрелок",
 
    # Два оружия
    "Два коротких меча": "Сражение двумя оружиями",
    "Кинжал": "Сражение двумя оружиями",
}
 
 
def recommend_fighting_style(weapon_name: Optional[str]) -> Optional[str]:
    """
    Рекомендует боевой стиль на основе выбранного оружия.
 
    Args:
        weapon_name: название выбранного оружия (может быть None)
 
    Returns:
        Название рекомендуемого боевого стиля или None, если нет рекомендации.
    """
    if not weapon_name:
        return None
    return _WEAPON_TO_STYLE.get(weapon_name)
 
 
# =========================================================
# ЯЗЫКИ ПО УМОЛЧАНИЮ ДЛЯ ПРЕДЫСТОРИЙ
# D&D 5.5e 2024: персонаж знает Общий + 2 доп. языка от предыстории
# =========================================================
 
_BACKGROUND_LANGUAGES = {
    "Аколит":          ["Общий", "Небесный", "Инфернальный"],
    "Артизан":         ["Общий", "Гномий", "Дварфийский"],
    "Атлет":           ["Общий", "Орочий", "Гигантский"],
    "Беспризорник":    ["Общий", "Воровской жаргон", "Эльфийский"],
    "Дворянин":        ["Общий", "Эльфийский", "Драконий"],
    "Развлекатель":    ["Общий", "Эльфийский", "Гномий"],
    "Исследователь":   ["Общий", "Эльфийский", "Первичный"],
    "Мудрец":          ["Общий", "Эльфийский", "Орочий"],
    "Моряк":           ["Общий", "Акванское", "Орочий"],
    "Преступник":      ["Общий", "Воровской жаргон", "Орочий"],
    "Простолюдин":     ["Общий", "Гигантский", "Гномий"],
    "Скиталец":        ["Общий", "Эльфийский", "Гигантский"],
    "Солдат":          ["Общий", "Орочий", "Гигантский"],
    "Торговец":        ["Общий", "Гномий", "Эльфийский"],
    "Чиновник":        ["Общий", "Драконий", "Эльфийский"],
    "Ярмарочный люд":  ["Общий", "Гномий", "Воровской жаргон"],
}
 
_DEFAULT_LANGUAGES = ["Общий", "Эльфийский", "Орочий"]
 
 
def get_default_languages_for_background(background_name: str) -> List[str]:
    """
    Возвращает список языков по умолчанию для предыстории.
 
    Args:
        background_name: название предыстории (на русском)
 
    Returns:
        Список из 2-3 языков (Общий всегда первый).
    """
    return _BACKGROUND_LANGUAGES.get(background_name, _DEFAULT_LANGUAGES)[:]
 
 
# =========================================================
# ПАРСИНГ ИНСТРУМЕНТОВ ПРЕДЫСТОРИИ
# =========================================================
 
# Слова-разделители и стоп-слова, которые не являются названиями инструментов
_TOOL_STOP_WORDS = {
    "и", "или", "а", "с", "на", "в", "по", "из", "для",
    "один", "одна", "одно", "набор", "инструменты",
    "владение", "владеет",
}
 
 
def parse_background_tools(tools_str: str) -> List[str]:
    """
    Разбирает строку инструментов предыстории в список названий.
 
    Например: "Инструменты вора, Один музыкальный инструмент"
    -> ["Инструменты вора", "Один музыкальный инструмент"]
 
    Args:
        tools_str: строка из поля tools в данных предыстории
 
    Returns:
        Список названий инструментов. Пустой список если строка пуста или «Нет».
    """
    if not tools_str or tools_str.strip().lower() in ("нет", "—", "-", ""):
        return []
 
    # Разделяем по запятой и точке с запятой
    parts = [p.strip() for p in tools_str.replace(";", ",").split(",")]
    result = [p for p in parts if p and p.lower() not in _TOOL_STOP_WORDS]
    return result
 
 
# =========================================================
# ВЛАДЕНИЕ ОРУЖИЕМ (WEAPON MASTERY) — D&D 5.5e 2024
# =========================================================
 
# Классы, получающие Weapon Mastery на 1-м уровне
_WEAPON_MASTERY_CLASSES = {
    "Варвар", "Воин", "Паладин", "Следопыт", "Плут", "Монах", "Бард",
}
 
# Лимит количества вооружений с Mastery по RAW D&D 5.5e 2024
_WEAPON_MASTERY_LIMIT = {
    "Воин":    3,
    "Варвар":  2,
    "Паладин": 2,
    "Следопыт": 2,
    "Плут":    2,
    "Монах":   2,
    "Бард":    2,
}
 
 
def class_has_weapon_mastery(class_name: str) -> bool:
    """
    Проверяет, получает ли класс Weapon Mastery на 1-м уровне.
 
    Args:
        class_name: название класса (на русском)
 
    Returns:
        True если класс имеет Weapon Mastery.
    """
    return class_name in _WEAPON_MASTERY_CLASSES
 
 
def get_weapon_mastery_limit(class_name: str) -> Optional[int]:
    """
    Возвращает максимальное количество вооружений с Mastery для класса.
 
    Args:
        class_name: название класса (на русском)
 
    Returns:
        Число или None если класс не имеет Weapon Mastery.
    """
    return _WEAPON_MASTERY_LIMIT.get(class_name)
