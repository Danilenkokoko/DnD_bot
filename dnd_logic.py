#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dnd_logic.py - D&D 5.5e (2024) Character Logic Module
Модуль с игровой логикой для создания персонажей
Все данные берутся из PostgreSQL
"""

import psycopg2
import json
import os
import random
import logging
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация базы данных
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "DND_DB"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "").strip(),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}


def get_connection():
    """Создаёт подключение к базе данных"""
    return psycopg2.connect(**DB_CONFIG)


# =========================================================
# 1. БАЗОВЫЕ РАСЧЁТЫ
# =========================================================

def modifier(stat: int) -> int:
    """
    Расчёт модификатора характеристики

    Args:
        stat: значение характеристики (от 1 до 30)

    Returns:
        int: модификатор характеристики
    """
    return (stat - 10) // 2


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


def calc_hp(class_id: int, constitution: int, level: int = 1) -> int:
    """
    Расчёт HP персонажа

    Args:
        class_id: ID класса
        constitution: значение телосложения
        level: уровень персонажа

    Returns:
        int: максимальное HP
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT hit_die FROM classes WHERE id = %s", (class_id,))
            result = cur.fetchone()
            if not result:
                raise ValueError(f"Класс с ID {class_id} не найден")
            hit_die = result[0]

    con_mod = modifier(constitution)

    if level == 1:
        return hit_die + max(1, con_mod)
    else:
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


# =========================================================
# 2. ГЕНЕРАЦИЯ ХАРАКТЕРИСТИК
# =========================================================

def roll_4d6_drop_lowest() -> int:
    """
    Бросает 4 кубика d6, отбрасывает минимальный, возвращает сумму

    Returns:
        int: сумма трёх наибольших кубиков
    """
    rolls = [random.randint(1, 6) for _ in range(4)]
    rolls.remove(min(rolls))
    return sum(rolls)


def generate_random_stats() -> Dict[str, int]:
    """
    Генерирует случайные характеристики методом 4d6 (отбросить минимальный)

    Returns:
        Dict[str, int]: словарь со значениями STR, DEX, CON, INT, WIS, CHA
    """
    stats_list = [roll_4d6_drop_lowest() for _ in range(6)]
    stats_list.sort(reverse=True)

    return {
        "STR": stats_list[0],
        "DEX": stats_list[1],
        "CON": stats_list[2],
        "INT": stats_list[3],
        "WIS": stats_list[4],
        "CHA": stats_list[5]
    }


def get_standard_stats() -> Dict[str, int]:
    """
    Возвращает стандартный набор характеристик (15, 14, 13, 12, 10, 8)
    """
    return {
        "STR": 15,
        "DEX": 14,
        "CON": 13,
        "INT": 12,
        "WIS": 10,
        "CHA": 8
    }


def apply_background_bonuses(stats: Dict[str, int], background_name: str) -> Dict[str, int]:
    """
    Применяет бонусы к характеристикам от предыстории (D&D 5.5e!)

    В 5.5e бонусы даёт ПРЕДЫСТОРИЯ, а не раса!
    """
    result = stats.copy()

    bg = get_background_by_name(background_name)
    if not bg:
        return result

    stat_map = {
        "Сила": "STR", "Ловкость": "DEX", "Телосложение": "CON",
        "Интеллект": "INT", "Мудрость": "WIS", "Харизма": "CHA"
    }

    characteristics = bg['characteristics']

    stat1 = stat_map.get(characteristics[0], "DEX")
    result[stat1] += 2

    stat2 = stat_map.get(characteristics[1], "DEX")
    result[stat2] += 1

    for stat in result:
        result[stat] = min(20, result[stat])

    return result


def get_initial_stats_by_method(method: str, background_name: str) -> Dict[str, int]:
    """
    Получает начальные характеристики выбранным методом с учётом предыстории

    Args:
        method: "random" или "standard"
        background_name: название предыстории
    """
    if method == "random":
        base_stats = generate_random_stats()
    else:
        base_stats = get_standard_stats()

    return apply_background_bonuses(base_stats, background_name)


# =========================================================
# 3. РАБОТА С РАСАМИ (из БД)
# =========================================================

def get_all_races() -> List[Dict[str, Any]]:
    """Возвращает список всех рас"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, speed, size, description, image_path FROM races ORDER BY name")
            columns = ['id', 'name', 'speed', 'size', 'description', 'image_path']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_race_list() -> List[str]:
    """Возвращает список названий рас"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM races ORDER BY name")
            return [row[0] for row in cur.fetchall()]


def get_race_by_name(race_name: str) -> Optional[Dict[str, Any]]:
    """Получает полную информацию о расе по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, speed, size, description, image_path
                FROM races WHERE name = %s
            """, (race_name,))
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'speed': row[2],
                    'size': row[3],
                    'description': row[4] if row[4] else _get_fallback_race_description(race_name),
                    'image_path': row[5]
                }
    return None


def _get_fallback_race_description(race_name: str) -> str:
    """Возвращает fallback описание для расы"""
    descriptions = {
        "Аасимар": "Аасимары — это смертные, которые несут в своих душах искру Верхних Планов.",
        "Гном": "Гномы — миниатюрный народец с большими глазами и заострёнными ушами.",
        "Голиаф": "Возвышающиеся над большинством народов голиафы — отдалённые потомки великанов.",
        "Дварф": "Дварфы устойчивы, как горы; они живут около 350 лет.",
        "Драконорожденный": "Драконорождённые выглядят как бескрылые двуногие драконы.",
        "Полурослик": "Общины полуросликов бывают самых разных видов.",
        "Тифлинг": "Тифлинги связаны кровными узами с дьяволом или демоном.",
        "Человек": "Люди столь же разнообразны, сколь и многочисленны.",
        "Эльф": "Созданные богом Кореллоном, первые эльфы могли неограниченно менять свой облик.",
        "Орк": "Орки выносливы, решительны и способны видеть в темноте.",
        "Калаштар": "Калаштары происходят от союза человечества и духов с плана снов.",
        "Кованный": "Кованые — механические существа, созданные из дерева и металла.",
        "Кхоравар": "Кхоравары — потомки союзов людей и эльфов.",
        "Ченжлинг": "Ченжлинги могут сверхъестественным образом принять любой облик.",
        "Шифтер": "Шифтеры — гуманоиды с явно заметными животными чертами.",
        "Дампир": "Дампиры живы, но обладают способностями вампиров."
    }
    return descriptions.get(race_name, "Нет описания для этой расы.")


def get_race_description(race_name: str) -> str:
    """Возвращает описание расы"""
    race = get_race_by_name(race_name)
    if race:
        return race.get('description', "Нет описания")
    return _get_fallback_race_description(race_name)


def get_race_speed(race_name: str) -> int:
    """Возвращает скорость расы"""
    race = get_race_by_name(race_name)
    return race['speed'] if race else 30


def get_race_size(race_name: str) -> str:
    """Возвращает размер расы"""
    race = get_race_by_name(race_name)
    return race['size'] if race else "Средний"


def get_race_image_path(race_name: str) -> Optional[str]:
    """Возвращает путь к картинке расы"""
    race = get_race_by_name(race_name)
    if race and race.get('image_path'):
        return race['image_path']

    images = {
        "Аасимар": "images/races/aasimar.jpg", "Гном": "images/races/gnom.jpg",
        "Голиаф": "images/races/goliaf.jpg", "Дварф": "images/races/dwarf.jpg",
        "Драконорожденный": "images/races/dragonborn.jpg", "Полурослик": "images/races/halfman.jpg",
        "Тифлинг": "images/races/tifling.jpg", "Человек": "images/races/man.jpg",
        "Эльф": "images/races/elf.jpg", "Орк": "images/races/ork.jpg",
        "Калаштар": "images/races/kalashtar.jpg", "Кованный": "images/races/kowanniy.jpg",
        "Кхоравар": "images/races/khorawar.jpg", "Ченжлинг": "images/races/changaling.jpg",
        "Шифтер": "images/races/shifter.jpg", "Дампир": "images/races/dampir.jpg",
    }
    return images.get(race_name)


def has_subraces(race_name: str) -> bool:
    """Проверяет, есть ли у расы подрасы"""
    race = get_race_by_name(race_name)
    if not race:
        return False

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM subraces WHERE race_id = %s", (race['id'],))
            return cur.fetchone()[0] > 0


def get_subraces(race_name: str) -> List[str]:
    """Возвращает список подрас для указанной расы"""
    race = get_race_by_name(race_name)
    if not race:
        return []

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM subraces WHERE race_id = %s ORDER BY name", (race['id'],))
            return [row[0] for row in cur.fetchall()]


def get_subrace_info(race_name: str, subrace_name: str) -> Optional[Dict[str, Any]]:
    """Возвращает полную информацию о подрасе"""
    race = get_race_by_name(race_name)
    if not race:
        return None

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, trait, description, extra_speed, extra_traits
                FROM subraces 
                WHERE race_id = %s AND name = %s
            """, (race['id'], subrace_name))
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0], 'name': row[1], 'trait': row[2] if row[2] else "",
                    'description': row[3] if row[3] else _get_fallback_subrace_description(subrace_name),
                    'extra_speed': row[4] if row[4] else 0, 'extra_traits': row[5] if row[5] else []
                }
    return None


def _get_fallback_subrace_description(subrace_name: str) -> str:
    """Возвращает fallback описание для подрасы"""
    descriptions = {
        "Протектор": "Протекторы используют силу света для защиты союзников.",
        "Разоритель": "Разорители черпают силу из разрушения и несут возмездие.",
        "Несущий скорбь": "Несущие скорбь связаны с некротической энергией.",
        "Лесной гном": "Лесные гномы умеют общаться с животными.",
        "Скальный гном": "Скальные гномы искусны в работе с механизмами.",
        "Горный дварф": "Горные дварфы сильны и выносливы.",
        "Холмовой дварф": "Холмовые дварфы мудры и жизнерадостны.",
        "Высший эльф": "Высшие эльфы искусны в магии.",
        "Лесной эльф": "Лесные эльфы быстры и скрытны.",
        "Тёмный эльф (Дроу)": "Дроу живут в подземельях, чувствительны к свету.",
        "Легконогий": "Легконогие полурослики умеют прятаться.",
        "Крепкостоп": "Крепкостопы выносливы и стойки к ядам.",
        "Медвежий": "Медвежьи шифтеры получают временные хиты.",
        "Кошачий": "Кошачьи шифтеры получают бонус к скорости.",
        "Крысиный": "Крысиные шифтеры получают бонус к интеллекту.",
        "Волчий": "Волчьи шифтеры получают бонус к восприятию."
    }
    return descriptions.get(subrace_name, "Нет описания для этой подрасы.")


def get_subrace_description(race_name: str, subrace_name: str) -> str:
    """Возвращает описание подрасы"""
    subrace = get_subrace_info(race_name, subrace_name)
    if subrace:
        if subrace.get('description'):
            return subrace['description']
        elif subrace.get('trait'):
            return f"Особенность: {subrace['trait']}"
    return "Нет описания для этой подрасы."


def get_subrace_trait(race_name: str, subrace_name: str) -> str:
    """Возвращает особенность подрасы"""
    subrace = get_subrace_info(race_name, subrace_name)
    return subrace['trait'] if subrace else ""


def get_race_info(race_name: str) -> Dict[str, Any]:
    """Возвращает полную информацию о расе (для совместимости)"""
    race = get_race_by_name(race_name)
    if not race:
        return {}

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, trait, description FROM subraces WHERE race_id = %s", (race['id'],))
            subraces = {row[0]: {'trait': row[1], 'description': row[2]} for row in cur.fetchall()}

    return {'name': race_name, 'speed': race['speed'], 'size': race['size'],
            'description': race['description'], 'traits': [], 'subraces': subraces}


def get_race_traits_list(race: str, subrace: Optional[str] = None) -> List[str]:
    """Возвращает особенности расы"""
    traits = []
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


# =========================================================
# 4. РАБОТА С КЛАССАМИ (из БД)
# =========================================================

def get_all_classes() -> List[Dict[str, Any]]:
    """Возвращает список всех классов"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, hit_die, primary_stats, saving_throws, 
                       skill_choices, description, image_path, is_spellcaster, spellcasting_ability
                FROM classes ORDER BY name
            """)
            columns = ['id', 'name', 'hit_die', 'primary_stats', 'saving_throws',
                       'skill_choices', 'description', 'image_path', 'is_spellcaster', 'spellcasting_ability']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_class_list() -> List[str]:
    """Возвращает список названий классов"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM classes ORDER BY name")
            return [row[0] for row in cur.fetchall()]


def get_class_by_name(class_name: str) -> Optional[Dict[str, Any]]:
    """Получает полную информацию о классе по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, hit_die, primary_stats, saving_throws, 
                       skill_choices, description, image_path, is_spellcaster, spellcasting_ability
                FROM classes WHERE name = %s
            """, (class_name,))
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0], 'name': row[1], 'hit_die': row[2],
                    'primary_stats': row[3] if isinstance(row[3], list) else json.loads(row[3]),
                    'saving_throws': row[4] if isinstance(row[4], list) else json.loads(row[4]),
                    'skill_choices': row[5],
                    'description': row[6] if row[6] else _get_fallback_class_description(class_name),
                    'image_path': row[7], 'is_spellcaster': row[8], 'spellcasting_ability': row[9]
                }
    return None


def _get_fallback_class_description(class_name: str) -> str:
    """Возвращает fallback описание для класса"""
    descriptions = {
        "Артефактор": "Мастера раскрытия магии в обычных вещах, величайшие выдумщики.",
        "Бард": "Бард плетёт магию из слов и музыки, вдохновляя союзников.",
        "Варвар": "Варваров объединяет их ярость — необузданный и бездумный гнев.",
        "Воин": "Воины мастерски владеют оружием, доспехами и приёмами боя.",
        "Волшебник": "Волшебники — адепты высшей магии, способные создавать заклинания.",
        "Друид": "Друиды воплощают незыблемость, приспособляемость и гнев природы.",
        "Жрец": "Жрецы являются посредниками между миром смертных и богами.",
        "Колдун": "Колдуны — искатели знаний, через договор открывающие магию.",
        "Монах": "Монахи управляют энергией, текущей в их телах.",
        "Паладин": "Паладинов объединяет их клятва противостоять силам зла.",
        "Плут": "Плуты полагаются на мастерство, скрытность и уязвимые места врагов.",
        "Следопыт": "Следопыты несут свой бесконечный дозор вдали от городов.",
        "Чародей": "Чародеи являются носителями магии, дарованной им при рождении."
    }
    return descriptions.get(class_name, "Нет описания для этого класса.")


def get_class_description(class_name: str) -> str:
    """Возвращает описание класса"""
    class_data = get_class_by_name(class_name)
    if class_data:
        return class_data.get('description', "Нет описания")
    return _get_fallback_class_description(class_name)


def get_class_image_path(class_name: str) -> Optional[str]:
    """Возвращает путь к картинке класса"""
    class_data = get_class_by_name(class_name)
    if class_data and class_data.get('image_path'):
        return class_data['image_path']

    images = {
        "Артефактор": "images/classes/artifactor.jpg", "Бард": "images/classes/bard.jpg",
        "Варвар": "images/classes/barbarian.jpg", "Воин": "images/classes/fighter.jpg",
        "Волшебник": "images/classes/wizard.jpg", "Друид": "images/classes/druid.jpg",
        "Жрец": "images/classes/cleric.jpg", "Колдун": "images/classes/warlock.jpg",
        "Монах": "images/classes/monk.jpg", "Паладин": "images/classes/paladin.jpg",
        "Плут": "images/classes/rogue.jpg", "Следопыт": "images/classes/ranger.jpg",
        "Чародей": "images/classes/sorcerer.jpg",
    }
    return images.get(class_name)


def get_class_info(class_name: str) -> Dict[str, Any]:
    """Возвращает информацию о классе (для совместимости)"""
    class_data = get_class_by_name(class_name)
    if not class_data:
        return {}

    return {
        'hit_die': class_data['hit_die'],
        'primary_stats': class_data['primary_stats'],
        'saving_throws': class_data['saving_throws'],
        'skill_choices': class_data['skill_choices'],
        'description': class_data['description'],
        'spellcasting': class_data['is_spellcaster'],
        'spellcasting_ability': class_data['spellcasting_ability']
    }


def get_class_features(class_name: str, level: int = 1) -> List[str]:
    """Возвращает особенности класса на уровне"""
    class_data = get_class_by_name(class_name)
    if not class_data:
        return []

    features = []
    if class_data['is_spellcaster']:
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

    return features + class_specific.get(class_name, [])


# =========================================================
# 5. РАБОТА С ПОДКЛАССАМИ
# =========================================================

def get_subclasses_for_class(class_name: str, level: int = 1) -> List[Dict[str, Any]]:
    """Возвращает подклассы для указанного класса, доступные на уровне"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
            result = cur.fetchone()
            if not result:
                return []
            class_id = result[0]

            cur.execute("""
                SELECT id, name, level_acquired, description, features
                FROM subclasses 
                WHERE class_id = %s AND level_acquired <= %s
                ORDER BY level_acquired, name
            """, (class_id, level))
            columns = ['id', 'name', 'level_acquired', 'description', 'features']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


# =========================================================
# 6. РАБОТА С ПРЕДЫСТОРИЯМИ
# =========================================================

def get_all_backgrounds() -> List[Dict[str, Any]]:
    """Возвращает список всех предысторий"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, characteristic1, characteristic2, characteristic3,
                       trait, skills, tools, equipment_a, equipment_b, description
                FROM backgrounds ORDER BY name
            """)
            columns = ['id', 'name', 'characteristic1', 'characteristic2', 'characteristic3',
                       'trait', 'skills', 'tools', 'equipment_a', 'equipment_b', 'description']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_background_list() -> List[str]:
    """Возвращает список названий предысторий"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM backgrounds ORDER BY name")
            return [row[0] for row in cur.fetchall()]


def get_background_by_name(background_name: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о предыстории по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, characteristic1, characteristic2, characteristic3,
                       trait, skills, tools, equipment_a, equipment_b, description
                FROM backgrounds WHERE name = %s
            """, (background_name,))
            row = cur.fetchone()
            if row:
                skills = row[6]
                if isinstance(skills, str):
                    try:
                        skills = json.loads(skills)
                    except:
                        skills = []

                return {
                    'id': row[0], 'name': row[1],
                    'characteristics': [row[2], row[3], row[4]],
                    'trait': row[5], 'skills': skills, 'tools': row[7],
                    'equipment_a': row[8], 'equipment_b': row[9],
                    'description': row[10] if row[10] else f"Предыстория {background_name}"
                }
    return None


def get_background_data(background_name: str) -> Dict[str, Any]:
    """Возвращает данные предыстории (для совместимости)"""
    bg = get_background_by_name(background_name)
    if not bg:
        return {}

    return {
        'characteristics': bg['characteristics'], 'trait': bg['trait'],
        'skills': bg['skills'], 'tools': bg['tools'],
        'equipment_a': bg['equipment_a'], 'equipment_b': bg['equipment_b'],
        'description': bg['description']
    }


def get_background_characteristics(background_name: str) -> List[str]:
    """Возвращает бонусы к характеристикам от предыстории"""
    bg = get_background_by_name(background_name)
    return bg['characteristics'] if bg else ["Ловкость", "Ловкость", "Ловкость"]


def get_background_trait(background_name: str) -> str:
    """Возвращает черту предыстории"""
    bg = get_background_by_name(background_name)
    return bg['trait'] if bg else ""


def get_background_skills(background_name: str) -> List[str]:
    """Возвращает навыки от предыстории"""
    bg = get_background_by_name(background_name)
    return bg['skills'] if bg else []


def get_background_tools(background_name: str) -> str:
    """Возвращает инструменты от предыстории"""
    bg = get_background_by_name(background_name)
    return bg['tools'] if bg else ""


def get_background_description(background_name: str) -> str:
    """Возвращает описание предыстории"""
    bg = get_background_by_name(background_name)
    return bg['description'] if bg else ""


def get_equipment_choice(background_name: str, choice: str = "A") -> str:
    """Возвращает снаряжение предыстории по выбору А или Б"""
    bg = get_background_by_name(background_name)
    if not bg:
        return ""
    return bg['equipment_a'] if choice.upper() == "A" else bg['equipment_b']


# =========================================================
# 7. РАБОТА С ОРУЖИЕМ И ПРИЁМАМИ
# =========================================================

def get_all_weapon_masteries() -> List[Dict[str, Any]]:
    """Возвращает список всех оружейных приёмов"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, trigger_condition, effect, weapons FROM weapon_masteries ORDER BY name")
            columns = ['id', 'name', 'trigger_condition', 'effect', 'weapons']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_weapons_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Возвращает список оружия, доступного для класса"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return []
                class_id = class_result[0]

                cur.execute("""
                    SELECT w.id, w.name, w.category, w.damage_dice, w.damage_type, w.properties, w.suitable_masteries
                    FROM weapons w
                    JOIN class_weapons cw ON w.id = cw.weapon_id
                    WHERE cw.class_id = %s
                    ORDER BY w.category, w.name
                """, (class_id,))
                columns = ['id', 'name', 'category', 'damage_dice', 'damage_type', 'properties', 'suitable_masteries']
                return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        logger.warning(f"Не удалось загрузить оружие для класса {class_name}: {e}")
        return []


def get_masteries_for_weapon(weapon_name: str) -> List[str]:
    """Возвращает список подходящих оружейных приёмов для указанного оружия"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT suitable_masteries FROM weapons WHERE name = %s", (weapon_name,))
                result = cur.fetchone()
                if result and result[0]:
                    if isinstance(result[0], list):
                        return result[0]
                    try:
                        return json.loads(result[0])
                    except:
                        return []
                return []
    except Exception as e:
        logger.warning(f"Не удалось загрузить приёмы для оружия {weapon_name}: {e}")
        return []


def check_mastery_compatibility(weapon_name: str, mastery_name: str) -> Tuple[bool, str]:
    """
    Проверяет, подходит ли приём к выбранному оружию

    Returns:
        Tuple[bool, str]: (подходит ли, сообщение)
    """
    suitable = get_masteries_for_weapon(weapon_name)
    if mastery_name in suitable:
        return True, f"✅ Приём '{mastery_name}' подходит для оружия '{weapon_name}'"
    else:
        return False, f"⚠️ ВНИМАНИЕ: Приём '{mastery_name}' не предназначен для оружия '{weapon_name}'. Вы всё равно можете его выбрать, но эффект может быть неоптимальным."


# =========================================================
# 8. РАБОТА С БОЕВЫМИ СТИЛЯМИ
# =========================================================

def get_all_fighting_styles() -> List[Dict[str, Any]]:
    """Возвращает список всех боевых стилей"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM fighting_styles ORDER BY name")
            columns = ['id', 'name', 'description']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_fighting_styles_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Возвращает боевые стили, доступные для класса (с фильтрацией)"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return []
                class_id = class_result[0]

                cur.execute("""
                    SELECT fs.id, fs.name, fs.description
                    FROM fighting_styles fs
                    JOIN class_fighting_styles cfs ON fs.id = cfs.style_id
                    WHERE cfs.class_id = %s
                    ORDER BY fs.name
                """, (class_id,))
                columns = ['id', 'name', 'description']
                return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception as e:
        logger.warning(f"Не удалось загрузить боевые стили для класса {class_name}: {e}")
        return []


# =========================================================
# 9. РАБОТА С ВОЗВАНИЯМИ
# =========================================================

def get_all_invocations(level: int = 1) -> List[Dict[str, Any]]:
    """Возвращает список доступных возваний для колдуна"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, level_required, effect, requires_pact_boon, pact_boon_type
                FROM invocations 
                WHERE level_required <= %s
                ORDER BY level_required, name
            """, (level,))
            columns = ['id', 'name', 'level_required', 'effect', 'requires_pact_boon', 'pact_boon_type']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


# =========================================================
# 10. РАБОТА С ЗАКЛИНАНИЯМИ
# =========================================================

def get_spells_for_class(class_name: str, level: int = 1, is_cantrip: bool = None) -> List[Dict[str, Any]]:
    """Возвращает заклинания для указанного класса"""
    class_data = get_class_by_name(class_name)
    if not class_data:
        return []

    with get_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT s.id, s.name, s.level, s.is_cantrip, s.description, s.school
                FROM spells s
                JOIN class_spells cs ON s.id = cs.spell_id
                WHERE cs.class_id = %s AND cs.is_available = TRUE
            """
            params = [class_data['id']]

            if is_cantrip is not None:
                query += " AND s.is_cantrip = %s"
                params.append(is_cantrip)

            if not is_cantrip:
                query += " AND s.level <= %s"
                params.append(level)

            query += " ORDER BY s.level, s.name"

            cur.execute(query, params)
            columns = ['id', 'name', 'level', 'is_cantrip', 'description', 'school']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_recommended_spells(class_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """Возвращает рекомендованные заклинания для класса"""
    result = {"cantrips": [], "level1": []}

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return result
                class_id = class_result[0]

                cur.execute("""
                    SELECT s.id, s.name, s.level, s.is_cantrip, s.description
                    FROM spells s
                    JOIN recommended_spells rs ON s.id = rs.spell_id
                    WHERE rs.class_id = %s
                    ORDER BY rs.priority, s.name
                """, (class_id,))

                spells = cur.fetchall()
                for spell in spells:
                    if spell[3]:  # is_cantrip
                        result["cantrips"].append({'id': spell[0], 'name': spell[1], 'level': spell[2],
                                                   'is_cantrip': spell[3], 'description': spell[4]})
                    else:
                        result["level1"].append({'id': spell[0], 'name': spell[1], 'level': spell[2],
                                                 'is_cantrip': spell[3], 'description': spell[4]})

                return result
    except Exception as e:
        logger.warning(f"Не удалось загрузить рекомендованные заклинания для {class_name}: {e}")
        return result


# =========================================================
# 11. ВАЛИДАЦИЯ
# =========================================================

def validate_name(name: str) -> Tuple[bool, str]:
    """Проверяет имя персонажа"""
    if not name or len(name.strip()) == 0:
        return False, "❌ Имя не может быть пустым"
    if len(name) > 50:
        return False, "❌ Имя слишком длинное (максимум 50 символов)"
    if len(name) < 2:
        return False, "❌ Имя слишком короткое (минимум 2 символа)"
    return True, "✅ Имя корректно"


def validate_race(race: str) -> Tuple[bool, str]:
    """Проверяет расу"""
    races = get_race_list()
    if race not in races:
        return False, f"❌ Раса '{race}' не существует"
    return True, "✅ Раса корректна"


def validate_class(class_name: str) -> Tuple[bool, str]:
    """Проверяет класс"""
    classes = get_class_list()
    if class_name not in classes:
        return False, f"❌ Класс '{class_name}' не существует"
    return True, "✅ Класс корректен"


def validate_background(background: str) -> Tuple[bool, str]:
    """Проверяет предысторию"""
    backgrounds = get_background_list()
    if background not in backgrounds:
        return False, f"❌ Предыстория '{background}' не существует"
    return True, "✅ Предыстория корректна"


def validate_stats(stats: Dict[str, int]) -> Tuple[bool, str]:
    """Проверяет характеристики"""
    required_stats = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

    for stat in required_stats:
        if stat not in stats:
            return False, f"❌ Характеристика {stat} отсутствует"
        if not (1 <= stats[stat] <= 30):
            return False, f"❌ {stat} должно быть от 1 до 30"

    total = sum(stats.values())
    if total > 90:
        return False, f"⚠️ Сумма характеристик ({total}) очень высокая"

    return True, "✅ Характеристики корректны"


def validate_character(name: str, class_name: str, race: str, background: str, stats: Dict[str, int]) -> Tuple[
    bool, str]:
    """Полная валидация персонажа"""
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


# =========================================================
# ТЕСТИРОВАНИЕ
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ D&D LOGIC MODULE (PostgreSQL версия)")
    print("=" * 60)

    # 1. Тест генерации характеристик
    print("\n1. ТЕСТ ГЕНЕРАЦИИ ХАРАКТЕРИСТИК:")
    for i in range(3):
        stats = generate_random_stats()
        print(f"   Попытка {i + 1}: STR={stats['STR']}, DEX={stats['DEX']}, CON={stats['CON']}, "
              f"INT={stats['INT']}, WIS={stats['WIS']}, CHA={stats['CHA']}")

    # 2. Тест бонусов от предыстории
    print("\n2. ТЕСТ БОНУСОВ ОТ ПРЕДЫСТОРИИ:")
    backgrounds = get_background_list()
    for bg in backgrounds[:3]:
        stats = get_initial_stats_by_method("standard", bg)
        chars = get_background_characteristics(bg)
        print(f"   {bg}: +2 {chars[0]}, +1 {chars[1]} → STR={stats['STR']}, DEX={stats['DEX']}")

    # 3. Тест рас
    print("\n3. ТЕСТ РАС:")
    for race in get_race_list()[:5]:
        desc = get_race_description(race)
        print(f"   • {race}: {desc[:60]}...")

    # 4. Тест классов
    print("\n4. ТЕСТ КЛАССОВ:")
    for cls in get_class_list()[:5]:
        desc = get_class_description(cls)
        print(f"   • {cls}: {desc[:60]}...")

    # 5. Тест оружия для воина
    print("\n5. ТЕСТ ОРУЖИЯ ДЛЯ ВОИНА:")
    weapons = get_weapons_for_class("Воин")
    print(f"   Доступно оружия: {len(weapons)}")
    for w in weapons[:5]:
        masteries = get_masteries_for_weapon(w['name'])
        print(f"   • {w['name']} ({w['damage_dice']}) → подходит: {', '.join(masteries)}")

    # 6. Тест боевых стилей для паладина
    print("\n6. ТЕСТ БОЕВЫХ СТИЛЕЙ ДЛЯ ПАЛАДИНА:")
    styles = get_fighting_styles_for_class("Паладин")
    for s in styles:
        print(f"   • {s['name']}")

    # 7. Тест заклинаний
    print("\n7. ТЕСТ РЕКОМЕНДОВАННЫХ ЗАКЛИНАНИЙ:")
    rec = get_recommended_spells("Волшебник")
    print(f"   Заговоры: {', '.join([s['name'] for s in rec['cantrips']])}")
    print(f"   Заклинания 1 ур.: {', '.join([s['name'] for s in rec['level1']])}")

    print("\n" + "=" * 60)
    print("✅ МОДУЛЬ DND_LOGIC.PY ГОТОВ К РАБОТЕ!")
    print("=" * 60)