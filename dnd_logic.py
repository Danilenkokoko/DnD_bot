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
# 2. ГЕНЕРАЦИЯ ХАРАКТЕРИСТИК (НОВАЯ ЛОГИКА ДЛЯ 5.5e!)
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
    Выполняется 6 бросков, результаты сортируются по убыванию

    Returns:
        Dict[str, int]: словарь со значениями STR, DEX, CON, INT, WIS, CHA
    """
    stats_list = [roll_4d6_drop_lowest() for _ in range(6)]
    stats_list.sort(reverse=True)  # Сортируем по убыванию

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

    Returns:
        Dict[str, int]: стандартные характеристики
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

    Args:
        stats: базовые характеристики
        background_name: название предыстории

    Returns:
        Dict[str, int]: изменённые характеристики
    """
    result = stats.copy()

    bg = get_background_by_name(background_name)
    if not bg:
        return result

    # Карта перевода русских названий в коды статов
    stat_map = {
        "Сила": "STR", "Ловкость": "DEX", "Телосложение": "CON",
        "Интеллект": "INT", "Мудрость": "WIS", "Харизма": "CHA"
    }

    characteristics = bg['characteristics']

    # +2 к первой характеристике
    stat1 = stat_map.get(characteristics[0], "DEX")
    result[stat1] += 2

    # +1 ко второй характеристике
    stat2 = stat_map.get(characteristics[1], "DEX")
    result[stat2] += 1

    # Ограничиваем максимальное значение 20
    for stat in result:
        result[stat] = min(20, result[stat])

    return result


def get_initial_stats_by_method(method: str, background_name: str) -> Dict[str, int]:
    """
    Получает начальные характеристики выбранным методом с учётом предыстории

    Args:
        method: "random" или "standard"
        background_name: название предыстории

    Returns:
        Dict[str, int]: финальные характеристики
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
    """Возвращает список всех рас с полной информацией"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, speed, size, description, image_path 
                FROM races ORDER BY name
            """)
            columns = ['id', 'name', 'speed', 'size', 'description', 'image_path']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_race_list() -> List[str]:
    """Возвращает список названий рас"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM races ORDER BY name")
            return [row[0] for row in cur.fetchall()]


def get_race_by_name(race_name: str) -> Optional[Dict[str, Any]]:
    """Получает полную информацию о расе по названию (с описанием и картинкой!)"""
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
    """Возвращает fallback описание для расы (если в БД пусто)"""
    descriptions = {
        "Аасимар": "Аасимары — это смертные, которые несут в своих душах искру Верхних Планов. Они могут раздуть эту искру, чтобы нести свет, исцеление и небесную ярость.",
        "Гном": "Гномы — миниатюрный народец с большими глазами и заострёнными ушами. Многим гномам нравится ощущение крыши над головой.",
        "Голиаф": "Возвышающиеся над большинством народов голиафы — отдалённые потомки великанов. Каждый голиаф обладает благоволением первых великанов.",
        "Дампир": "Дампиры живы, но обладают как способностями вампиров, так и их ужасным голодом.",
        "Дварф": "Дварфы устойчивы, как горы; они живут около 350 лет. В древние времена дварфы были подняты из земли божеством кузни.",
        "Драконорожденный": "Драконорождённые выглядят как бескрылые двуногие драконы — чешуйчатые, ширококостные, с рожками на головах.",
        "Калаштар": "Калаштары происходят от союза человечества и мятежных духов с плана снов, называемых куори.",
        "Кованный": "Кованые — механические существа, созданные из дерева и металла, способные испытывать боль и эмоции.",
        "Кхоравар": "Кхоравары — потомки союзов людей и эльфов, создавшие в Кхорваире свои сообщества.",
        "Орк": "Орки выносливы, решительны и способны видеть в темноте. Они ведут своё сотворение от Груумша, могущественного бога.",
        "Полурослик": "Общины полуросликов бывают самых разных видов. Они известны своей удачливостью и храбростью.",
        "Тифлинг": "Тифлинги связаны кровными узами с дьяволом, демоном или другим Исчадием. Эта связь с Нижними планами сулит могущество.",
        "Человек": "Люди столь же разнообразны, сколь и многочисленны, и они стремятся достичь как можно большего за отведенные им годы жизни.",
        "Ченжлинг": "Ченжлинги могут сверхъестественным образом принять любой облик, который им нравится.",
        "Шифтер": "Шифтеры — гуманоиды с явно заметными животными чертами. Они могут временно усилить свои животные черты.",
        "Эльф": "Созданные богом Кореллоном, первые эльфы могли неограниченно менять свой облик. Они живут около 750 лет."
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

    # fallback пути к картинкам
    images = {
        "Аасимар": "images/races/aasimar.jpg",
        "Гном": "images/races/gnom.jpg",
        "Голиаф": "images/races/goliaf.jpg",
        "Дварф": "images/races/dwarf.jpg",
        "Драконорожденный": "images/races/dragonborn.jpg",
        "Полурослик": "images/races/halfman.jpg",
        "Тифлинг": "images/races/tifling.jpg",
        "Человек": "images/races/man.jpg",
        "Эльф": "images/races/elf.jpg",
        "Орк": "images/races/ork.jpg",
        "Калаштар": "images/races/kalashtar.jpg",
        "Кованный": "images/races/kowanniy.jpg",
        "Кхоравар": "images/races/khorawar.jpg",
        "Ченжлинг": "images/races/changaling.jpg",
        "Шифтер": "images/races/shifter.jpg",
        "Дампир": "images/races/dampir.jpg",
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
                    'id': row[0],
                    'name': row[1],
                    'trait': row[2] if row[2] else "",
                    'description': row[3] if row[3] else _get_fallback_subrace_description(subrace_name),
                    'extra_speed': row[4] if row[4] else 0,
                    'extra_traits': row[5] if row[5] else []
                }
    return None


def _get_fallback_subrace_description(subrace_name: str) -> str:
    """Возвращает fallback описание для подрасы"""
    descriptions = {
        "Протектор": "Протекторы используют силу света для защиты своих союзников.",
        "Разоритель": "Разорители черпают силу из разрушения и несут возмездие.",
        "Несущий скорбь": "Несущие скорбь связаны с некротической энергией и тайнами смерти.",
        "Лесной гном": "Лесные гномы умеют общаться с животными и прятаться в природе.",
        "Скальный гном": "Скальные гномы искусны в работе с механизмами и алхимией.",
        "Горный дварф": "Горные дварфы сильны и выносливы, они искусны в бою.",
        "Холмовой дварф": "Холмовые дварфы мудры и жизнерадостны, обладают повышенной выносливостью.",
        "Высший эльф": "Высшие эльфы искусны в магии и получают дополнительное заклинание.",
        "Лесной эльф": "Лесные эльфы быстры и скрытны, они чувствуют себя в лесу как дома.",
        "Тёмный эльф (Дроу)": "Дроу живут в подземельях, они чувствительны к свету, но могут использовать магию.",
        "Легконогий": "Легконогие полурослики умеют прятаться за другими существами.",
        "Крепкостоп": "Крепкостопы выносливы и стойки к ядам.",
        "Медвежий": "Медвежьи шифтеры получают временные хиты при сдвиге.",
        "Кошачий": "Кошачьи шифтеры получают бонус к скорости и ловкости.",
        "Крысиный": "Крысиные шифтеры получают бонус к интеллектуальным проверкам.",
        "Волчий": "Волчьи шифтеры получают бонус к восприятию и выслеживанию.",
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
    """Возвращает полную информацию о расе (для совместимости со старым кодом)"""
    race = get_race_by_name(race_name)
    if not race:
        return {}

    # Получаем подрасы
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, trait, description FROM subraces 
                WHERE race_id = %s
            """, (race['id'],))
            subraces = {}
            for row in cur.fetchall():
                subraces[row[0]] = {'trait': row[1], 'description': row[2]}

    return {
        'name': race_name,
        'speed': race['speed'],
        'size': race['size'],
        'description': race['description'],
        'traits': [],
        'subraces': subraces
    }


def get_race_traits_list(race: str, subrace: Optional[str] = None) -> List[str]:
    """Возвращает особенности расы"""
    traits = []

    # Базовые особенности расы
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

    # Особенности подрасы
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
                       skill_choices, description, image_path, 
                       is_spellcaster, spellcasting_ability
                FROM classes ORDER BY name
            """)
            columns = ['id', 'name', 'hit_die', 'primary_stats', 'saving_throws',
                       'skill_choices', 'description', 'image_path',
                       'is_spellcaster', 'spellcasting_ability']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_class_list() -> List[str]:
    """Возвращает список названий классов"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM classes ORDER BY name")
            return [row[0] for row in cur.fetchall()]


def get_class_by_name(class_name: str) -> Optional[Dict[str, Any]]:
    """Получает полную информацию о классе по названию (с описанием и картинкой!)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, hit_die, primary_stats, saving_throws, 
                       skill_choices, description, image_path, 
                       is_spellcaster, spellcasting_ability
                FROM classes WHERE name = %s
            """, (class_name,))
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'hit_die': row[2],
                    'primary_stats': row[3] if isinstance(row[3], list) else json.loads(row[3]),
                    'saving_throws': row[4] if isinstance(row[4], list) else json.loads(row[4]),
                    'skill_choices': row[5],
                    'description': row[6] if row[6] else _get_fallback_class_description(class_name),
                    'image_path': row[7],
                    'is_spellcaster': row[8],
                    'spellcasting_ability': row[9]
                }
    return None


def _get_fallback_class_description(class_name: str) -> str:
    """Возвращает fallback описание для класса (если в БД пусто)"""
    descriptions = {
        "Артефактор": "Мастера раскрытия магии в обычных вещах, изобретатели — величайшие выдумщики. Они видят магию как сложную систему, которую нужно расшифровывать и контролировать.",
        "Бард": "Бард плетёт магию из слов и музыки, вдохновляя союзников, деморализуя противников, манипулируя сознанием и даже исцеляя раны.",
        "Варвар": "Варваров объединяет их ярость — необузданный, неугасимый и бездумный гнев. Не просто эмоция, их ярость как свирепость загнанного в угол хищника.",
        "Воин": "Воины мастерски владеют оружием, доспехами и приёмами ведения боя. Странствующие рыцари, военачальники, королевские чемпионы — все они воины.",
        "Волшебник": "Волшебники — адепты высшей магии, способные создавать заклинания взрывного огня, искрящихся молний и тонкого обмана. Их магия вызывает чудовищ с других планов.",
        "Друид": "Друиды воплощают незыблемость, приспособляемость и гнев природы. Они ни в коем случае не владыки природы — вместо этого друиды ощущают себя частью её неодолимой воли.",
        "Жрец": "Жрецы являются посредниками между миром смертных и далёкими мирами богов. Настолько же разные, насколько боги, которым они служат, жрецы воплощают работу своих божеств.",
        "Колдун": "Колдуны — искатели знаний, через договор с таинственными существами открывающие магические эффекты. Они подпитывают свои силы древними знаниями.",
        "Монах": "Монахи управляют энергией, текущей в их телах, проявляя выдающиеся боевые способности, чуть заметное усиление защиты и скорости.",
        "Паладин": "Паладинов объединяет их клятва противостоять силам зла. Принесённая перед алтарём бога или в момент отчаяния, клятва паладина — могущественный договор.",
        "Плут": "Плуты полагаются на мастерство, скрытность и уязвимые места врагов. У них достаточно сноровки для нахождения решения в любой ситуации.",
        "Следопыт": "Следопыты несут свой бесконечный дозор вдали от суеты городов и посёлков, среди плотно стоящих деревьев и на просторах необъятных равнин.",
        "Чародей": "Чародеи являются носителями магии, дарованной им при рождении их экзотической родословной. Сила сама выбирает носителя."
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

    # fallback пути к картинкам
    images = {
        "Артефактор": "images/classes/artifactor.jpg",
        "Бард": "images/classes/bard.jpg",
        "Варвар": "images/classes/barbarian.jpg",
        "Воин": "images/classes/fighter.jpg",
        "Волшебник": "images/classes/wizard.jpg",
        "Друид": "images/classes/druid.jpg",
        "Жрец": "images/classes/cleric.jpg",
        "Колдун": "images/classes/warlock.jpg",
        "Монах": "images/classes/monk.jpg",
        "Паладин": "images/classes/paladin.jpg",
        "Плут": "images/classes/rogue.jpg",
        "Следопыт": "images/classes/ranger.jpg",
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


def get_class_hit_die(class_name: str) -> int:
    """Возвращает хитовый кубик класса"""
    class_data = get_class_by_name(class_name)
    return class_data['hit_die'] if class_data else 6


def get_class_skill_choices(class_name: str) -> List[str]:
    """Возвращает список доступных навыков для класса"""
    skills_map = {
        "Бард": ["Акробатика", "Выступление", "Обман", "Убеждение", "Проницательность", "Скрытность", "История",
                 "Магия"],
        "Воин": ["Атлетика", "Запугивание", "Восприятие", "Выживание", "История", "Проницательность"],
        "Волшебник": ["Тайная магия", "История", "Религия", "Расследование", "Медицина", "Проницательность"],
        "Жрец": ["Религия", "Медицина", "Убеждение", "Проницательность", "История"],
        "Плут": ["Ловкость рук", "Скрытность", "Обман", "Восприятие", "Расследование", "Акробатика"],
        "Следопыт": ["Выживание", "Восприятие", "Скрытность", "Природа", "Обращение с животными"],
        "Друид": ["Природа", "Выживание", "Восприятие", "Обращение с животными", "Медицина"],
        "Паладин": ["Убеждение", "Проницательность", "Религия", "Атлетика", "Запугивание"],
        "Чародей": ["Обман", "Убеждение", "Проницательность", "Запугивание", "Магия"],
        "Колдун": ["Магия", "Обман", "История", "Запугивание", "Расследование"],
        "Монах": ["Акробатика", "Атлетика", "История", "Проницательность", "Религия", "Скрытность"],
        "Варвар": ["Атлетика", "Запугивание", "Восприятие", "Выживание", "Природа"],
        "Артефактор": ["Магия", "История", "Расследование", "Медицина", "Восприятие"]
    }
    return skills_map.get(class_name, ["Восприятие", "Скрытность"])


# =========================================================
# 5. РАБОТА С ПОДКЛАССАМИ
# =========================================================

def get_subclasses_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Возвращает подклассы для указанного класса"""
    class_data = get_class_by_name(class_name)
    if not class_data:
        return []

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, level_acquired, description, features
                FROM subclasses 
                WHERE class_id = %s
                ORDER BY level_acquired, name
            """, (class_data['id'],))
            columns = ['id', 'name', 'level_acquired', 'description', 'features']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


# =========================================================
# 6. РАБОТА С ПРЕДЫСТОРИЯМИ (из БД) - КЛЮЧЕВОЕ ДЛЯ 5.5e!
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
                # Обрабатываем skills (может быть строкой JSON или списком)
                skills = row[6]
                if isinstance(skills, str):
                    try:
                        skills = json.loads(skills)
                    except:
                        skills = []

                return {
                    'id': row[0],
                    'name': row[1],
                    'characteristics': [row[2], row[3], row[4]],
                    'trait': row[5],
                    'skills': skills,
                    'tools': row[7],
                    'equipment_a': row[8],
                    'equipment_b': row[9],
                    'description': row[10] if row[10] else f"Предыстория {background_name}"
                }
    return None


def get_background_data(background_name: str) -> Dict[str, Any]:
    """Возвращает данные предыстории (для совместимости)"""
    bg = get_background_by_name(background_name)
    if not bg:
        return {}

    return {
        'characteristics': bg['characteristics'],
        'trait': bg['trait'],
        'skills': bg['skills'],
        'tools': bg['tools'],
        'equipment_a': bg['equipment_a'],
        'equipment_b': bg['equipment_b'],
        'description': bg['description']
    }


def get_background_characteristics(background_name: str) -> List[str]:
    """Возвращает бонусы к характеристикам от предыстории (КЛЮЧЕВО ДЛЯ 5.5e!)"""
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


def format_background_for_display(background: str) -> str:
    """Форматирует информацию о предыстории для отображения"""
    bg = get_background_by_name(background)
    if not bg:
        return f"❌ Предыстория '{background}' не найдена"

    info = f"📜 **{bg['name']}**\n\n"
    info += f"**Описание:** {bg['description'][:200]}...\n\n"
    info += f"**Черта:** {bg['trait']}\n"
    info += f"**Характеристики:** +2 к {bg['characteristics'][0]}, +1 к {bg['characteristics'][1]}\n"
    info += f"**Навыки:** {', '.join(bg['skills'])}\n"
    info += f"**Инструменты:** {bg['tools']}\n\n"
    info += f"**Снаряжение А:** {bg['equipment_a'][:100]}...\n"
    info += f"**Снаряжение Б:** {bg['equipment_b'][:100]}..."
    return info


# =========================================================
# 7. РАБОТА С ОРУЖЕЙНЫМИ ПРИЁМАМИ
# =========================================================

def get_all_weapon_masteries() -> List[Dict[str, Any]]:
    """Возвращает список всех оружейных приёмов"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, trigger_condition, effect, weapons FROM weapon_masteries ORDER BY name")
            columns = ['id', 'name', 'trigger_condition', 'effect', 'weapons']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_weapon_mastery_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о приёме по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, trigger_condition, effect, weapons 
                FROM weapon_masteries WHERE name = %s
            """, (name,))
            row = cur.fetchone()
            if row:
                return {'id': row[0], 'name': row[1], 'trigger_condition': row[2], 'effect': row[3], 'weapons': row[4]}
    return None


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


def get_fighting_style_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о стиле по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM fighting_styles WHERE name = %s", (name,))
            row = cur.fetchone()
            if row:
                return {'id': row[0], 'name': row[1], 'description': row[2]}
    return None


# =========================================================
# 9. РАБОТА С ТАИНСТВЕННЫМИ ВОЗВАНИЯМИ
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


def get_invocation_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о возвании по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, level_required, effect, requires_pact_boon, pact_boon_type 
                FROM invocations WHERE name = %s
            """, (name,))
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0], 'name': row[1], 'level_required': row[2],
                    'effect': row[3], 'requires_pact_boon': row[4], 'pact_boon_type': row[5]
                }
    return None


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


def get_cantrips_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Возвращает заговоры для указанного класса"""
    return get_spells_for_class(class_name, is_cantrip=True)


def get_level1_spells_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Возвращает заклинания 1 уровня для указанного класса"""
    return get_spells_for_class(class_name, level=1, is_cantrip=False)


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
# 12. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (для совместимости)
# =========================================================

def get_class_features(class_name: str, level: int = 1) -> List[str]:
    """Возвращает особенности класса на уровне"""
    class_data = get_class_by_name(class_name)
    if not class_data:
        return []

    # Базовые особенности для 1 уровня
    features = []
    if class_data['is_spellcaster']:
        features.append("Заклинания")

    # Специфические для класса
    class_specific = {
        "Бард": ["Вдохновение барда"],
        "Варвар": ["Ярость", "Бездоспешная защита"],
        "Воин": ["Второе дыхание", "Боевой стиль"],
        "Волшебник": ["Книга заклинаний", "Восстановление магии"],
        "Друид": ["Друидийский язык"],
        "Жрец": ["Божественное вдохновение"],
        "Колдун": ["Потусторонний покровитель", "Магия договора"],
        "Монах": ["Боевые искусства", "Бездоспешная защита"],
        "Паладин": ["Божественное чутьё", "Наложение рук"],
        "Плут": ["Скрытая атака", "Взломщик", "Воровской жаргон"],
        "Следопыт": ["Избранный враг", "Следопыт"],
        "Чародей": ["Магия крови"],
        "Артефактор": ["Магия артефактов", "Владение инструментами"]
    }

    return features + class_specific.get(class_name, [])


# =========================================================
# ТЕСТИРОВАНИЕ
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ D&D LOGIC MODULE (PostgreSQL версия)")
    print("=" * 60)

    # 1. Тест генерации характеристик
    print("\n1. ТЕСТ ГЕНЕРАЦИИ ХАРАКТЕРИСТИК:")
    print("\n   Случайный метод (4d6):")
    for i in range(3):
        stats = generate_random_stats()
        print(f"     Попытка {i + 1}: STR={stats['STR']}, DEX={stats['DEX']}, CON={stats['CON']}, "
              f"INT={stats['INT']}, WIS={stats['WIS']}, CHA={stats['CHA']} "
              f"(сумма: {sum(stats.values())})")

    print("\n   Стандартный набор:")
    stats = get_standard_stats()
    print(f"     STR=15, DEX=14, CON=13, INT=12, WIS=10, CHA=8 (сумма: {sum(stats.values())})")

    # 2. Тест бонусов от предыстории
    print("\n2. ТЕСТ БОНУСОВ ОТ ПРЕДЫСТОРИИ (5.5e):")
    backgrounds = get_background_list()
    for bg in backgrounds[:3]:
        stats = get_initial_stats_by_method("standard", bg)
        chars = get_background_characteristics(bg)
        print(f"   {bg}: +2 {chars[0]}, +1 {chars[1]} → STR={stats['STR']}, DEX={stats['DEX']}, "
              f"CON={stats['CON']}, INT={stats['INT']}, WIS={stats['WIS']}, CHA={stats['CHA']}")

    # 3. Тест рас
    print("\n3. ТЕСТ РАС:")
    races = get_race_list()
    print(f"   Всего рас: {len(races)}")
    for race in races[:5]:
        desc = get_race_description(race)
        print(f"   • {race}: {desc[:60]}...")

    # 4. Тест классов
    print("\n4. ТЕСТ КЛАССОВ:")
    classes = get_class_list()
    print(f"   Всего классов: {len(classes)}")
    for cls in classes[:5]:
        desc = get_class_description(cls)
        print(f"   • {cls}: {desc[:60]}...")

    # 5. Тест предысторий
    print("\n5. ТЕСТ ПРЕДЫСТОРИЙ:")
    backgrounds = get_background_list()
    print(f"   Всего предысторий: {len(backgrounds)}")
    for bg in backgrounds[:5]:
        chars = get_background_characteristics(bg)
        print(f"   • {bg}: бонусы +2 {chars[0]}, +1 {chars[1]}")

    print("\n" + "=" * 60)
    print("✅ МОДУЛЬ DND_LOGIC.PY ГОТОВ К РАБОТЕ!")
    print("=" * 60)