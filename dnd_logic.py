# dnd_logic.py
"""
dnd_logic.py - D&D 5.5e (2024) Character Logic Module (LEGACY FACADE)

ВНИМАНИЕ: Этот модуль устарел и сохранён только для обратной совместимости.
Вся новая логика должна использовать:
- engine/          — чистые игровые механики
- repositories/    — доступ к данным
- services/        — бизнес-логику

Все функции этого модуля перенаправляют вызовы в новые модули и выдают
предупреждение DeprecationWarning.
"""

import warnings
import logging
from typing import Dict, List, Any, Optional, Tuple

# Импорты новых модулей
from engine.hp import calculate_hp_at_level, calculate_modifier as engine_modifier
from engine.ac import calculate_ac_with_armor as engine_ac, calculate_base_ac
from engine.proficiency import calculate_proficiency_bonus as engine_prof_bonus
from engine.stats import BackgroundBonusDistributor, AbilityScores
from engine.validators import validate_name as engine_validate_name

# Репозитории
from repositories.race_repository import RaceRepository
from repositories.class_repository import ClassRepository
from repositories.background_repository import BackgroundRepository
from repositories.equipment_repository import EquipmentRepository, FightingStyleRepository, InvocationRepository
from repositories.spell_repository import SpellRepository
from repositories.character_repository import CharacterRepository

# Для стартовых статов (пока оставляем статику)
CLASS_STARTING_STATS = {
    "Артефактор": {"STR": 10, "DEX": 14, "CON": 13, "INT": 15, "WIS": 12, "CHA": 8},
    "Бард": {"STR": 8, "DEX": 14, "CON": 12, "INT": 13, "WIS": 10, "CHA": 15},
    "Варвар": {"STR": 15, "DEX": 13, "CON": 14, "INT": 10, "WIS": 12, "CHA": 8},
    "Воин": {"STR": 15, "DEX": 14, "CON": 13, "INT": 8, "WIS": 10, "CHA": 12},
    "Воин_B": {"STR": 12, "DEX": 15, "CON": 13, "INT": 8, "WIS": 10, "CHA": 14},
    "Волшебник": {"STR": 8, "DEX": 12, "CON": 13, "INT": 15, "WIS": 14, "CHA": 10},
    "Друид": {"STR": 8, "DEX": 12, "CON": 14, "INT": 13, "WIS": 15, "CHA": 10},
    "Жрец": {"STR": 14, "DEX": 8, "CON": 13, "INT": 10, "WIS": 15, "CHA": 12},
    "Колдун": {"STR": 8, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 15},
    "Монах": {"STR": 12, "DEX": 15, "CON": 13, "INT": 10, "WIS": 14, "CHA": 8},
    "Паладин": {"STR": 15, "DEX": 10, "CON": 13, "INT": 8, "WIS": 12, "CHA": 14},
    "Плут": {"STR": 12, "DEX": 15, "CON": 13, "INT": 14, "WIS": 10, "CHA": 8},
    "Следопыт": {"STR": 12, "DEX": 15, "CON": 13, "INT": 8, "WIS": 14, "CHA": 10},
    "Чародей": {"STR": 10, "DEX": 13, "CON": 14, "INT": 8, "WIS": 12, "CHA": 15},
}

# Инициализация репозиториев (синглтоны)
_race_repo = RaceRepository()
_class_repo = ClassRepository()
_bg_repo = BackgroundRepository()
_equip_repo = EquipmentRepository()
_fighting_repo = FightingStyleRepository()
_inv_repo = InvocationRepository()
_spell_repo = SpellRepository()
_char_repo = CharacterRepository()


def _deprecated(msg: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            warnings.warn(msg, DeprecationWarning, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ------------------------------------------------------------
# 1. Базовые расчёты (перенаправление в engine)
# ------------------------------------------------------------
@_deprecated("modifier() устарела. Используйте engine.hp.calculate_modifier()")
def modifier(stat: int) -> int:
    return engine_modifier(stat)


@_deprecated("calculate_proficiency_bonus() устарела. Используйте engine.proficiency.calculate_proficiency_bonus()")
def calculate_proficiency_bonus(level: int) -> int:
    return engine_prof_bonus(level)


@_deprecated("calc_hp() устарела. Используйте engine.hp.calculate_hp_at_level()")
def calc_hp(class_id: int, constitution: int, level: int = 1) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT hit_die FROM classes WHERE id = %s", (class_id,))
            row = cur.fetchone()
            hit_die = row[0] if row else 8
    return calculate_hp_at_level(hit_die, constitution, level)


@_deprecated("calc_ac_with_armor() устарела. Используйте engine.ac.calculate_ac_with_armor()")
def calc_ac_with_armor(dexterity: int, armor_name: Optional[str]) -> int:
    return engine_ac(dexterity, armor_name)


@_deprecated("calc_ac() устарела. Используйте engine.ac.calculate_base_ac() или calculate_ac_with_armor()")
def calc_ac(dexterity: int, armor_type: str = "none") -> int:
    if armor_type == "none":
        return calculate_base_ac(dexterity)
    dex_mod = modifier(dexterity)
    armor_base = {
        "light": 11 + dex_mod,
        "medium": 14 + min(2, dex_mod),
        "heavy": 16
    }.get(armor_type, 10 + dex_mod)
    return armor_base


# ------------------------------------------------------------
# 2. Характеристики и бонусы предыстории
# ------------------------------------------------------------
@_deprecated(
    "get_class_starting_stats() устарела (Этап 2). В новом flow характеристики "
    "назначаются игроком вручную на шаге abilities_assign из стандартного "
    "массива [15,14,13,12,10,8]. Функция оставлена как fallback для старых "
    "сессий и обратной совместимости — удалить в Этапе 9 (cleanup)."
)
def get_class_starting_stats(class_name: str, variant: Optional[str] = None) -> Dict[str, int]:
    key = f"{class_name}_{variant}" if variant else class_name
    if key in CLASS_STARTING_STATS:
        return CLASS_STARTING_STATS[key].copy()
    if class_name in CLASS_STARTING_STATS:
        return CLASS_STARTING_STATS[class_name].copy()
    return {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10}


def get_class_primary_stats(class_name: str) -> List[str]:
    return _class_repo.get_primary_stats(class_name)


def get_background_characteristics(background_name: str) -> List[str]:
    return _bg_repo.get_characteristics(background_name)


@_deprecated("calculate_final_stats_with_background() устарела. Используйте engine.stats.BackgroundBonusDistributor")
def calculate_final_stats_with_background(
    class_name: str,
    background_name: str,
    class_starting_stats: Dict[str, int]
) -> Dict[str, int]:
    primary = get_class_primary_stats(class_name)
    bg_stats = get_background_characteristics(background_name)
    base = AbilityScores.from_dict(class_starting_stats)
    dist = BackgroundBonusDistributor()
    bonuses = dist.distribute(primary, bg_stats)
    final = bonuses.apply_to(base)
    return final.to_str_dict()


# ------------------------------------------------------------
# 3. Работа с расами (перенаправление в RaceRepository)
# ------------------------------------------------------------
def get_all_races() -> List[Dict[str, Any]]:
    return _race_repo.get_all()


def get_race_list() -> List[str]:
    return _race_repo.get_all_names()


def get_race_by_name(race_name: str) -> Optional[Dict[str, Any]]:
    return _race_repo.get_by_name(race_name)


def get_race_description(race_name: str) -> str:
    race = _race_repo.get_by_name(race_name)
    return race.get('description', '') if race else ''


def get_race_speed(race_name: str) -> int:
    race = _race_repo.get_by_name(race_name)
    return race.get('speed', 30) if race else 30


def get_race_size(race_name: str) -> str:
    race = _race_repo.get_by_name(race_name)
    return race.get('size', 'Средний') if race else 'Средний'


def get_race_image_path(race_name: str) -> Optional[str]:
    race = _race_repo.get_by_name(race_name)
    return race.get('image_path') if race else None


def get_race_image_exists(race_name: str) -> bool:
    path = get_race_image_path(race_name)
    return path is not None and os.path.exists(path)


def has_subraces(race_name: str) -> bool:
    return _race_repo.has_subraces(race_name)


def get_subraces(race_name: str) -> List[str]:
    return _race_repo.get_subrace_names(race_name)


def get_subrace_description(race_name: str, subrace_name: str) -> str:
    sub = _race_repo.get_subrace_by_name(race_name, subrace_name)
    return sub.get('description', '') if sub else ''


def get_subrace_trait(race_name: str, subrace_name: str) -> str:
    sub = _race_repo.get_subrace_by_name(race_name, subrace_name)
    return sub.get('trait', '') if sub else ''


def get_race_info(race_name: str) -> Dict[str, Any]:
    race = _race_repo.get_by_name(race_name)
    if not race:
        return {}
    subraces = _race_repo.get_subraces(race_name)
    return {
        'name': race_name,
        'speed': race.get('speed', 30),
        'size': race.get('size', 'Средний'),
        'description': race.get('description', ''),
        'traits': [],
        'subraces': {s['name']: {'trait': s.get('trait', ''), 'description': s.get('description', '')} for s in subraces}
    }


def get_race_traits_list(race: str, subrace: Optional[str] = None) -> List[str]:
    traits = []
    # fallback для совместимости
    race_traits_map = {
        "Аасимар": ["Тёмное зрение", "Небесное наследие", "Исцеляющие руки", "Светоносный"],
        "Гном": ["Тёмное зрение", "Гномья хитрость", "Искусный ремесленник"],
        "Голиаф": ["Природный атлет", "Каменное телосложение", "Рождённый для холода"],
        "Дварф": ["Тёмное зрение", "Дварфийская стойкость", "Боевое мастерство", "Знание камня"],
        "Драконорожденный": ["Оружие дыхания", "Сопротивление урону", "Драконья внешность"],
        "Полурослик": ["Везучий", "Храбрый", "Полуросливая ловкость"],
        "Тифлинг": ["Тёмное зрение", "Адское сопротивление", "Наследие ада"],
        "Эльф": ["Тёмное зрение", "Заточение фей", "Транс"],
        "Человек": ["Универсальность человечества"],
    }
    traits.extend(race_traits_map.get(race, []))
    if subrace:
        sub_trait = get_subrace_trait(race, subrace)
        if sub_trait:
            traits.append(sub_trait)
    return traits


# ------------------------------------------------------------
# 4. Работа с классами (перенаправление в ClassRepository)
# ------------------------------------------------------------
def get_all_classes() -> List[Dict[str, Any]]:
    return _class_repo.get_all()


def get_class_list() -> List[str]:
    return _class_repo.get_all_names()


def get_class_by_name(class_name: str) -> Optional[Dict[str, Any]]:
    return _class_repo.get_by_name(class_name)


def get_class_spell_counts(class_name: str) -> Dict[str, int]:
    return _class_repo.get_spell_counts(class_name)


def get_class_masteries_count(class_name: str) -> int:
    return _class_repo.get_masteries_count(class_name)


def get_class_description(class_name: str) -> str:
    data = _class_repo.get_by_name(class_name)
    return data.get('description', '') if data else ''


def get_class_image_path(class_name: str) -> Optional[str]:
    data = _class_repo.get_by_name(class_name)
    return data.get('image_path') if data else None


def get_class_image_exists(class_name: str) -> bool:
    path = get_class_image_path(class_name)
    return path is not None and os.path.exists(path)


def get_class_info(class_name: str) -> Dict[str, Any]:
    data = _class_repo.get_by_name(class_name)
    if not data:
        return {}
    return {
        'hit_die': data.get('hit_die', 8),
        'primary_stats': data.get('primary_stats', []),
        'saving_throws': data.get('saving_throws', []),
        'skill_choices': data.get('skill_choices', 2),
        'description': data.get('description', ''),
        'spellcasting': data.get('is_spellcaster', False),
        'spellcasting_ability': data.get('spellcasting_ability')
    }


def get_class_features(class_name: str, level: int = 1) -> List[str]:
    features = []
    data = _class_repo.get_by_name(class_name)
    if data and data.get('is_spellcaster'):
        features.append("Заклинания")
    class_specific = {
        "Бард": ["Вдохновение барда"], "Варвар": ["Ярость", "Бездоспешная защита"],
        "Воин": ["Второе дыхание", "Боевой стиль"], "Волшебник": ["Книга заклинаний", "Восстановление магии"],
        "Друид": ["Друидийский язык"], "Жрец": ["Божественное вдохновение"],
        "Колдун": ["Потусторонний покровитель", "Магия договора"],
        "Монах": ["Боевые искусства", "Бездоспешная защита"],
        "Паладин": ["Божественное чутьё", "Наложение рук"],
        "Плут": ["Скрытая атака", "Взломщик", "Воровской жаргон"],
        "Следопыт": ["Избранный враг", "Следопыт"],
        "Чародей": ["Магия крови"], "Артефактор": ["Магия артефактов", "Владение инструментами"]
    }
    features.extend(class_specific.get(class_name, []))
    return features


def get_subclasses_for_class(class_name: str, level: int = 1) -> List[Dict[str, Any]]:
    return _class_repo.get_subclasses(class_name, level)


# ------------------------------------------------------------
# 5. Работа с предысториями (перенаправление в BackgroundRepository)
# ------------------------------------------------------------
def get_all_backgrounds() -> List[Dict[str, Any]]:
    return _bg_repo.get_all()


def get_background_list() -> List[str]:
    return _bg_repo.get_all_names()


def get_background_by_name(background_name: str) -> Optional[Dict[str, Any]]:
    return _bg_repo.get_by_name(background_name)


def get_background_data(background_name: str) -> Dict[str, Any]:
    bg = _bg_repo.get_by_name(background_name)
    return bg if bg else {}


def get_background_trait(background_name: str) -> str:
    return _bg_repo.get_trait(background_name)


def get_background_skills(background_name: str) -> List[str]:
    return _bg_repo.get_skills(background_name)


def get_background_tools(background_name: str) -> str:
    return _bg_repo.get_tools(background_name)


def get_background_description(background_name: str) -> str:
    return _bg_repo.get_description(background_name)


def get_equipment_choice(background_name: str, choice: str = "A") -> str:
    return _bg_repo.get_equipment_choice(background_name, choice)


# ------------------------------------------------------------
# 6. Снаряжение, оружие, броня (перенаправление в EquipmentRepository)
# ------------------------------------------------------------
def get_class_equipment(class_name: str, choice: Optional[str] = None) -> List[Dict[str, Any]]:
    return _equip_repo.get_class_equipment(class_name, choice)


def get_armor_by_name(armor_name: str) -> Optional[Dict[str, Any]]:
    return _equip_repo.get_armor_by_name(armor_name)


def get_weapon_by_name(weapon_name: str) -> Optional[Dict[str, Any]]:
    return _equip_repo.get_weapon_by_name(weapon_name)


def get_detailed_masteries_for_weapon(weapon_name: str) -> List[Dict[str, Any]]:
    return _equip_repo.get_detailed_masteries_for_weapon(weapon_name)


def auto_assign_masteries(weapon_name: str, class_name: str) -> List[str]:
    return _equip_repo.auto_assign_masteries(weapon_name, class_name)


def get_all_weapon_masteries() -> List[Dict[str, Any]]:
    return _equip_repo.get_all_weapon_masteries()


# ------------------------------------------------------------
# 7. Боевые стили
# ------------------------------------------------------------
def get_all_fighting_styles() -> List[Dict[str, Any]]:
    return _fighting_repo.get_all()


def get_fighting_styles_for_class(class_name: str) -> List[Dict[str, Any]]:
    return _fighting_repo.get_for_class(class_name)


def get_available_fighting_styles(class_name: str, weapon_type: Optional[str] = None) -> List[Dict[str, Any]]:
    return _fighting_repo.get_available_for_class_with_weapon(class_name, weapon_type)


# ------------------------------------------------------------
# 8. Возвания
# ------------------------------------------------------------
def get_all_invocations(level: int = 1) -> List[Dict[str, Any]]:
    return _inv_repo.get_all(level)


# ------------------------------------------------------------
# 9. Заклинания
# ------------------------------------------------------------
def get_spells_for_class(class_name: str, level: int = 1, is_cantrip: bool = None) -> List[Dict[str, Any]]:
    return _spell_repo.get_for_class(class_name, level, is_cantrip)


def get_spells_grouped_by_category(class_name: str, is_cantrip: bool = True) -> Dict[str, List[Dict[str, Any]]]:
    return _spell_repo.get_categories_for_class(class_name, is_cantrip)


def get_cantrips_for_class(class_name: str) -> List[Dict[str, Any]]:
    return _spell_repo.get_cantrips_for_class(class_name)


def get_level1_spells_for_class(class_name: str) -> List[Dict[str, Any]]:
    return _spell_repo.get_level1_spells_for_class(class_name)


def get_cantrips_for_class_with_details(class_name: str) -> List[Dict[str, Any]]:
    return get_cantrips_for_class(class_name)


def get_level1_spells_for_class_with_details(class_name: str) -> List[Dict[str, Any]]:
    return get_level1_spells_for_class(class_name)


def get_recommended_spells(class_name: str) -> Dict[str, List[Dict[str, Any]]]:
    return _spell_repo.get_recommended_for_class(class_name)


# ------------------------------------------------------------
# 10. Валидация
# ------------------------------------------------------------
def validate_name(name: str) -> Tuple[bool, str]:
    return engine_validate_name(name)


def validate_race(race: str) -> Tuple[bool, str]:
    races = get_race_list()
    if race not in races:
        return False, f"❌ Раса '{race}' не существует"
    return True, "✅ Раса корректна"


def validate_class(class_name: str) -> Tuple[bool, str]:
    classes = get_class_list()
    if class_name not in classes:
        return False, f"❌ Класс '{class_name}' не существует"
    return True, "✅ Класс корректен"


def validate_background(background: str) -> Tuple[bool, str]:
    backgrounds = get_background_list()
    if background not in backgrounds:
        return False, f"❌ Предыстория '{background}' не существует"
    return True, "✅ Предыстория корректна"


def validate_stats(stats: Dict[str, int]) -> Tuple[bool, str]:
    required = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    for stat in required:
        if stat not in stats:
            return False, f"❌ Характеристика {stat} отсутствует"
        if not (1 <= stats[stat] <= 30):
            return False, f"❌ {stat} должно быть от 1 до 30"
    total = sum(stats.values())
    if total > 90:
        return False, f"⚠️ Сумма характеристик ({total}) очень высокая"
    return True, "✅ Характеристики корректны"


def validate_character(name: str, class_name: str, race: str, background: str, stats: Dict[str, int]) -> Tuple[bool, str]:
    valid, msg = validate_name(name)
    if not valid:
        return False, msg
    valid, msg = validate_race(race)
    if not valid:
        return False, msg
    valid, msg = validate_class(class_name)
    if not valid:
        return False, msg
    valid, msg = validate_background(background)
    if not valid:
        return False, msg
    valid, msg = validate_stats(stats)
    if not valid:
        return False, msg
    return True, "✅ Персонаж валиден"


# ------------------------------------------------------------
# 11. Подклассы (уже есть в ClassRepository, но оставим для API)
# ------------------------------------------------------------
# get_subclasses_for_class уже определена выше

# Вспомогательное для обратной совместимости (get_connection)
from db import get_connection  # noqa
import os  # noqa
