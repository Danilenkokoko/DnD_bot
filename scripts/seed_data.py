#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_data.py - Наполнение базы данных D&D 5.5e (2024) данными
Запуск: python seed_data.py
Скрипт не зависит от внешних файлов — все данные встроены в код.
Включает: расы, классы, предыстории, заклинания, оружие, броню,
снаряжение классов, оружейные приёмы.
"""

import psycopg2
import json
import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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


def clear_tables(conn):
    """Очищает таблицы перед заполнением"""
    tables = [
        "class_fighting_styles", "class_weapons", "recommended_spells",
        "class_spells", "spells", "subclasses", "classes",
        "subraces", "races", "backgrounds", "weapon_masteries",
        "fighting_styles", "weapons", "invocations", "armor", "class_equipment"
    ]

    with conn.cursor() as cur:
        for table in tables:
            try:
                cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
                logger.info(f"🗑️ Очищена таблица: {table}")
            except Exception as e:
                logger.warning(f"⚠️ Не удалось очистить {table}: {e}")
        conn.commit()


# =========================================================
# 1. ДАННЫЕ РАС
# =========================================================

RACES_DATA = {
    "Аасимар": {
        "speed": 30, "size": "Средний",
        "description": "Аасимары — это смертные, которые несут в своих душах искру Верхних Планов. Они могут раздуть эту искру, чтобы нести свет, исцеление и небесную ярость.",
        "subraces": {
            "Протектор": {"trait": "Сияющая душа",
                          "description": "Протекторы используют силу света для защиты своих союзников."},
            "Разоритель": {"trait": "Пожирающий свет",
                           "description": "Разорители черпают силу из разрушения и несут возмездие."},
            "Несущий скорбь": {"trait": "Некротический гнев",
                               "description": "Несущие скорбь связаны с некротической энергией и тайнами смерти."}
        }
    },
    "Гном": {
        "speed": 25, "size": "Маленький",
        "description": "Гномы — миниатюрный народец с большими глазами и заострёнными ушами. Многим гномам нравится ощущение крыши над головой.",
        "subraces": {
            "Лесной гном": {"trait": "Разговор с мелкими зверями",
                            "description": "Лесные гномы умеют общаться с животными и прятаться в природе."},
            "Скальный гном": {"trait": "Сведущий в механизмах",
                              "description": "Скальные гномы искусны в работе с механизмами и алхимией."}
        }
    },
    "Голиаф": {
        "speed": 30, "size": "Средний",
        "description": "Возвышающиеся над большинством народов голиафы — отдалённые потомки великанов.",
        "subraces": {}
    },
    "Дампир": {
        "speed": 35, "size": "Средний",
        "description": "Дампиры живы, но обладают как способностями вампиров, так и их ужасным голодом.",
        "subraces": {}
    },
    "Дварф": {
        "speed": 25, "size": "Средний",
        "description": "Дварфы устойчивы, как горы; они живут около 350 лет.",
        "subraces": {
            "Горный дварф": {"trait": "Мастерство в лёгких и средних доспехах",
                             "description": "Горные дварфы сильны и выносливы."},
            "Холмовой дварф": {"trait": "Дварфийская живучесть",
                               "description": "Холмовые дварфы мудры и жизнерадостны."}
        }
    },
    "Драконорожденный": {
        "speed": 30, "size": "Средний",
        "description": "Драконорождённые выглядят как бескрылые двуногие драконы — чешуйчатые, ширококостные, с рожками на головах.",
        "subraces": {
            "Чёрный": {"trait": "Кислотное дыхание", "description": "Чёрные драконорожденные дышат кислотой."},
            "Синий": {"trait": "Электрическое дыхание", "description": "Синие драконорожденные дышат молнией."},
            "Красный": {"trait": "Огненное дыхание", "description": "Красные драконорожденные дышат огнём."},
            "Зелёный": {"trait": "Ядовитое дыхание", "description": "Зелёные драконорожденные дышат ядом."},
            "Белый": {"trait": "Ледяное дыхание", "description": "Белые драконорожденные дышат холодом."},
            "Золотой": {"trait": "Огненное дыхание", "description": "Золотые драконорожденные дышат огнём."},
            "Серебряный": {"trait": "Ледяное дыхание", "description": "Серебряные драконорожденные дышат холодом."},
            "Латунный": {"trait": "Огненное дыхание", "description": "Латунные драконорожденные дышат огнём."},
            "Медный": {"trait": "Кислотное дыхание", "description": "Медные драконорожденные дышат кислотой."},
            "Бронзовый": {"trait": "Электрическое дыхание", "description": "Бронзовые драконорожденные дышат молнией."}
        }
    },
    "Калаштар": {
        "speed": 30, "size": "Средний",
        "description": "Калаштары происходят от союза человечества и мятежных духов с плана снов, называемых куори.",
        "subraces": {}
    },
    "Кованный": {
        "speed": 30, "size": "Средний",
        "description": "Кованые — механические существа, созданные из дерева и металла, способные испытывать боль и эмоции.",
        "subraces": {}
    },
    "Кхоравар": {
        "speed": 30, "size": "Средний",
        "description": "Кхоравары — потомки союзов людей и эльфов, создавшие в Кхорваире свои сообщества.",
        "subraces": {}
    },
    "Орк": {
        "speed": 30, "size": "Средний",
        "description": "Орки выносливы, решительны и способны видеть в темноте.",
        "subraces": {}
    },
    "Полурослик": {
        "speed": 25, "size": "Маленький",
        "description": "Общины полуросликов бывают самых разных видов.",
        "subraces": {
            "Легконогий": {"trait": "Природно-незаметный",
                           "description": "Легконогие полурослики умеют прятаться за другими существами."},
            "Крепкостоп": {"trait": "Стойкость крепкостопа", "description": "Крепкостопы выносливы и стойки к ядам."}
        }
    },
    "Тифлинг": {
        "speed": 30, "size": "Средний",
        "description": "Тифлинги связаны кровными узами с дьяволом, демоном или другим Исчадием.",
        "subraces": {}
    },
    "Человек": {
        "speed": 30, "size": "Средний",
        "description": "Люди столь же разнообразны, сколь и многочисленны, и они стремятся достичь как можно большего за отведенные им годы жизни.",
        "subraces": {}
    },
    "Ченжлинг": {
        "speed": 30, "size": "Средний",
        "description": "Ченжлинги могут сверхъестественным образом принять любой облик, который им нравится.",
        "subraces": {}
    },
    "Шифтер": {
        "speed": 30, "size": "Средний",
        "description": "Шифтеры — гуманоиды с явно заметными животными чертами.",
        "subraces": {
            "Медвежий": {"trait": "Медвежья выносливость",
                         "description": "Медвежьи шифтеры получают временные хиты при сдвиге."},
            "Кошачий": {"trait": "Кошачья ловкость",
                        "description": "Кошачьи шифтеры получают бонус к скорости и ловкости."},
            "Крысиный": {"trait": "Крысиная хитрость",
                         "description": "Крысиные шифтеры получают бонус к интеллектуальным проверкам."},
            "Волчий": {"trait": "Волчье чутьё",
                       "description": "Волчьи шифтеры получают бонус к восприятию и выслеживанию."}
        }
    },
    "Эльф": {
        "speed": 30, "size": "Средний",
        "description": "Созданные богом Кореллоном, первые эльфы могли неограниченно менять свой облик.",
        "subraces": {
            "Высший эльф": {"trait": "Дополнительный кантрип",
                            "description": "Высшие эльфы искусны в магии и получают дополнительное заклинание."},
            "Лесной эльф": {"trait": "Быстрые ноги",
                            "description": "Лесные эльфы быстры и скрытны, они чувствуют себя в лесу как дома."},
            "Тёмный эльф (Дроу)": {"trait": "Фейский огонёк",
                                   "description": "Дроу живут в подземельях, они чувствительны к свету, но могут использовать магию."}
        }
    }
}


def migrate_races(conn):
    """Перенос рас и подрас"""
    logger.info("=" * 50)
    logger.info("1. ПЕРЕНОС РАС И ПОДРАС")
    logger.info("=" * 50)

    with conn.cursor() as cur:
        for race_name, race_data in RACES_DATA.items():
            cur.execute("""
                INSERT INTO races (name, speed, size, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    speed = EXCLUDED.speed,
                    size = EXCLUDED.size,
                    description = EXCLUDED.description
                RETURNING id
            """, (
                race_name,
                race_data.get("speed", 30),
                race_data.get("size", "Средний"),
                race_data.get("description", "")
            ))
            race_id = cur.fetchone()[0]
            logger.info(f"  ✅ Раса '{race_name}' (ID: {race_id})")

            for subrace_name, subrace_data in race_data.get("subraces", {}).items():
                cur.execute("""
                    INSERT INTO subraces (race_id, name, trait, description)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (race_id, name) DO NOTHING
                """, (
                    race_id,
                    subrace_name,
                    subrace_data.get("trait", ""),
                    subrace_data.get("description", "")
                ))
                logger.info(f"    • Подраса '{subrace_name}'")

        conn.commit()
    logger.info("✅ Расы и подрасы перенесены")


# =========================================================
# 2. ДАННЫЕ КЛАССОВ
# =========================================================

CLASSES_DATA = {
    "Артефактор": {
        "hit_die": 8, "primary_stats": ["INT"], "saving_throws": ["CON", "INT"],
        "skill_choices": 2, "is_spellcaster": True, "spellcasting_ability": "INT",
        "description": "Мастера раскрытия магии в обычных вещах, изобретатели — величайшие выдумщики."
    },
    "Бард": {
        "hit_die": 8, "primary_stats": ["CHA"], "saving_throws": ["DEX", "CHA"],
        "skill_choices": 3, "is_spellcaster": True, "spellcasting_ability": "CHA",
        "description": "Бард плетёт магию из слов и музыки, вдохновляя союзников и деморализуя противников."
    },
    "Варвар": {
        "hit_die": 12, "primary_stats": ["STR", "CON"], "saving_throws": ["STR", "CON"],
        "skill_choices": 2, "is_spellcaster": False, "spellcasting_ability": None,
        "description": "Варваров объединяет их ярость — необузданный, неугасимый и бездумный гнев."
    },
    "Воин": {
        "hit_die": 10, "primary_stats": ["STR", "DEX"], "saving_throws": ["STR", "CON"],
        "skill_choices": 2, "is_spellcaster": False, "spellcasting_ability": None,
        "description": "Воины мастерски владеют оружием, доспехами и приёмами ведения боя."
    },
    "Волшебник": {
        "hit_die": 6, "primary_stats": ["INT"], "saving_throws": ["INT", "WIS"],
        "skill_choices": 2, "is_spellcaster": True, "spellcasting_ability": "INT",
        "description": "Волшебники — адепты высшей магии, способные создавать заклинания взрывного огня и тонкого обмана."
    },
    "Друид": {
        "hit_die": 8, "primary_stats": ["WIS"], "saving_throws": ["INT", "WIS"],
        "skill_choices": 2, "is_spellcaster": True, "spellcasting_ability": "WIS",
        "description": "Друиды воплощают незыблемость, приспособляемость и гнев природы."
    },
    "Жрец": {
        "hit_die": 8, "primary_stats": ["WIS"], "saving_throws": ["WIS", "CHA"],
        "skill_choices": 2, "is_spellcaster": True, "spellcasting_ability": "WIS",
        "description": "Жрецы являются посредниками между миром смертных и далёкими мирами богов."
    },
    "Колдун": {
        "hit_die": 8, "primary_stats": ["CHA"], "saving_throws": ["WIS", "CHA"],
        "skill_choices": 2, "is_spellcaster": True, "spellcasting_ability": "CHA",
        "description": "Колдуны — искатели знаний, через договор с таинственными существами открывающие магию."
    },
    "Монах": {
        "hit_die": 8, "primary_stats": ["DEX", "WIS"], "saving_throws": ["STR", "DEX"],
        "skill_choices": 2, "is_spellcaster": False, "spellcasting_ability": None,
        "description": "Монахи управляют энергией, текущей в их телах, проявляя выдающиеся боевые способности."
    },
    "Паладин": {
        "hit_die": 10, "primary_stats": ["STR", "CHA"], "saving_throws": ["WIS", "CHA"],
        "skill_choices": 2, "is_spellcaster": True, "spellcasting_ability": "CHA",
        "description": "Паладинов объединяет их клятва противостоять силам зла."
    },
    "Плут": {
        "hit_die": 8, "primary_stats": ["DEX"], "saving_throws": ["DEX", "INT"],
        "skill_choices": 4, "is_spellcaster": False, "spellcasting_ability": None,
        "description": "Плуты полагаются на мастерство, скрытность и уязвимые места врагов."
    },
    "Следопыт": {
        "hit_die": 10, "primary_stats": ["DEX", "WIS"], "saving_throws": ["STR", "DEX"],
        "skill_choices": 3, "is_spellcaster": True, "spellcasting_ability": "WIS",
        "description": "Следопыты несут свой бесконечный дозор вдали от суеты городов и посёлков."
    },
    "Чародей": {
        "hit_die": 6, "primary_stats": ["CHA"], "saving_throws": ["CON", "CHA"],
        "skill_choices": 2, "is_spellcaster": True, "spellcasting_ability": "CHA",
        "description": "Чародеи являются носителями магии, дарованной им при рождении их экзотической родословной."
    }
}


def migrate_classes(conn):
    """Перенос классов"""
    logger.info("\n" + "=" * 50)
    logger.info("2. ПЕРЕНОС КЛАССОВ")
    logger.info("=" * 50)

    with conn.cursor() as cur:
        for class_name, class_data in CLASSES_DATA.items():
            cur.execute("""
                INSERT INTO classes (name, hit_die, primary_stats, saving_throws, 
                                     skill_choices, description, is_spellcaster, spellcasting_ability)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    hit_die = EXCLUDED.hit_die,
                    primary_stats = EXCLUDED.primary_stats,
                    saving_throws = EXCLUDED.saving_throws,
                    skill_choices = EXCLUDED.skill_choices,
                    description = EXCLUDED.description
                RETURNING id
            """, (
                class_name,
                class_data["hit_die"],
                json.dumps(class_data["primary_stats"]),
                json.dumps(class_data["saving_throws"]),
                class_data["skill_choices"],
                class_data["description"],
                class_data["is_spellcaster"],
                class_data["spellcasting_ability"]
            ))
            class_id = cur.fetchone()[0]
            logger.info(f"  ✅ Класс '{class_name}' (ID: {class_id})")

        conn.commit()
    logger.info("✅ Классы перенесены")


# =========================================================
# 3. ДАННЫЕ ПРЕДЫСТОРИЙ
# =========================================================

BACKGROUNDS_DATA = [
    {"name": "Артист", "chars": ["CHA", "DEX", "STR"], "trait": "Музыкант",
     "skills": ["Акробатика", "Выступление"], "tools": "Музыкальный инструмент",
     "equipment_a": "Музыкальный инструмент, 2 Костюма, Зеркало, Духи, 11 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы провели большую часть своей юности, следуя за бродячими ярмарками..."},
    {"name": "Мудрец", "chars": ["CON", "INT", "WIS"], "trait": "Посвящённый в магию",
     "skills": ["История", "Тайная магия"], "tools": "Инструменты каллиграфа",
     "equipment_a": "Боевой посох, Инструменты каллиграфа, Книга, Пергамент, 8 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы провели свои юные годы, путешествуя между поместьями и монастырями..."},
    {"name": "Преступник", "chars": ["DEX", "CON", "INT"], "trait": "Бдительный",
     "skills": ["Ловкость рук", "Скрытность"], "tools": "Воровские инструменты",
     "equipment_a": "2 Кинжала, Воровские инструменты, Ломик, 2 Кошеля, 16 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы зарабатывали на жизнь в тёмных переулках, срезая кошельки..."},
    {"name": "Стражник", "chars": ["STR", "INT", "WIS"], "trait": "Бдительный",
     "skills": ["Атлетика", "Восприятие"], "tools": "Игровой набор",
     "equipment_a": "Копьё, Лёгкий арбалет, 20 Болтов, Игровой набор, Кандалы, 12 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы провели бесчисленные часы на посту в башне..."},
    {"name": "Бродяга", "chars": ["DEX", "WIS", "CHA"], "trait": "Везучий",
     "skills": ["Проницательность", "Скрытность"], "tools": "Воровские инструменты",
     "equipment_a": "2 Кинжала, Воровские инструменты, Игровой набор, Спальник, 16 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы выросли на улицах в окружении таких же злосчастных отбросов..."},
    {"name": "Отшельник", "chars": ["CON", "WIS", "CHA"], "trait": "Лекарь",
     "skills": ["Медицина", "Религия"], "tools": "Набор травника",
     "equipment_a": "Боевой посох, Набор травника, Спальник, Книга, Лампа, 16 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы провели ранние годы в одиночестве, в хижине или монастыре..."},
    {"name": "Проводник", "chars": ["DEX", "CON", "WIS"], "trait": "Посвящённый в магию",
     "skills": ["Выживание", "Скрытность"], "tools": "Инструменты картографа",
     "equipment_a": "Короткий лук, 20 Стрел, Инструменты картографа, Спальник, Палатка, 3 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы вошли в возраст под открытым небом, вдали от обжитых земель..."},
    {"name": "Торговец", "chars": ["CON", "INT", "CHA"], "trait": "Везучий",
     "skills": ["Убеждение", "Обращение с животными"], "tools": "Инструменты навигатора",
     "equipment_a": "Инструменты навигатора, 2 Кошеля, Дорожная одежда, 22 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы были учеником торговца, хозяина каравана или лавочника..."},
    {"name": "Дворянин", "chars": ["STR", "INT", "CHA"], "trait": "Одарённый",
     "skills": ["История", "Убеждение"], "tools": "Игровой набор",
     "equipment_a": "Игровой набор, Отличная одежда, Духи, 29 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы выросли в замке, окруженные богатством, властью и привилегиями..."},
    {"name": "Писарь", "chars": ["DEX", "INT", "WIS"], "trait": "Одарённый",
     "skills": ["Восприятие", "Расследование"], "tools": "Инструменты каллиграфа",
     "equipment_a": "Инструменты каллиграфа, Отличная одежда, Лампа, Пергамент, 23 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Годы вашего становления прошли в скриптории..."},
    {"name": "Ремесленник", "chars": ["STR", "DEX", "INT"], "trait": "Мастеровой",
     "skills": ["Расследование", "Убеждение"], "tools": "Инструменты кузнеца",
     "equipment_a": "Ремесленные инструменты, 2 Кошеля, Дорожная одежда, 32 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы начали подмастерьем в мастерской ремесленника..."},
    {"name": "Фермер", "chars": ["STR", "CON", "WIS"], "trait": "Крепкий",
     "skills": ["Природа", "Обращение с животными"], "tools": "Инструменты плотника",
     "equipment_a": "Серп, Инструменты плотника, Комплект целителя, Котел, Лопата, 30 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы выросли в близости с землёй, работая в поле и ухаживая за животными..."},
    {"name": "Моряк", "chars": ["STR", "DEX", "WIS"], "trait": "Дебошир",
     "skills": ["Акробатика", "Восприятие"], "tools": "Инструменты навигатора",
     "equipment_a": "Кинжал, Инструменты навигатора, Верёвка, Дорожная одежда, 20 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы жили на морских просторах, палуба покачивалась под ногами..."},
    {"name": "Послушник", "chars": ["INT", "WIS", "CHA"], "trait": "Посвящённый в магию",
     "skills": ["Проницательность", "Религия"], "tools": "Инструменты каллиграфа",
     "equipment_a": "Инструменты каллиграфа, Молитвенник, Священный символ, Пергамент, 8 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы посвятили себя служению в храме или священной роще..."},
    {"name": "Солдат", "chars": ["STR", "DEX", "CON"], "trait": "Неистово атакующий",
     "skills": ["Атлетика", "Запугивание"], "tools": "Игровой набор",
     "equipment_a": "Копьё, Короткий лук, 20 Стрел, Игровой набор, Комплект целителя, 14 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы начали готовиться к войне, как только достигли зрелости..."},
    {"name": "Шарлатан", "chars": ["DEX", "CON", "CHA"], "trait": "Одарённый",
     "skills": ["Ловкость рук", "Обман"], "tools": "Набор для фальсификации",
     "equipment_a": "Набор для фальсификации, Костюм, Отличная одежда, 15 ЗМ",
     "equipment_b": "50 ЗМ",
     "description": "Вы научились наживаться на несчастных, ищущих утешившую их ложь..."}
]


def migrate_backgrounds(conn):
    """Перенос предысторий"""
    logger.info("\n" + "=" * 50)
    logger.info("3. ПЕРЕНОС ПРЕДЫСТОРИЙ")
    logger.info("=" * 50)

    with conn.cursor() as cur:
        for bg in BACKGROUNDS_DATA:
            cur.execute("""
                INSERT INTO backgrounds (name, characteristic1, characteristic2, characteristic3,
                                         trait, skills, tools, equipment_a, equipment_b, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    trait = EXCLUDED.trait,
                    skills = EXCLUDED.skills,
                    tools = EXCLUDED.tools,
                    equipment_a = EXCLUDED.equipment_a,
                    equipment_b = EXCLUDED.equipment_b,
                    description = EXCLUDED.description
            """, (
                bg["name"],
                bg["chars"][0], bg["chars"][1], bg["chars"][2],
                bg["trait"],
                json.dumps(bg["skills"]),
                bg["tools"],
                bg["equipment_a"],
                bg["equipment_b"],
                bg["description"]
            ))
            logger.info(f"  ✅ Предыстория '{bg['name']}'")

        conn.commit()
    logger.info("✅ Предыстории перенесены")


# =========================================================
# 4. ДАННЫЕ ОРУЖЕЙНЫХ ПРИЁМОВ (БАЗОВЫЕ)
# =========================================================

WEAPON_MASTERIES = [
    {"name": "Выпад", "trigger": "Атака лёгким оружием", "effect": "Доп. атака становится частью Действия Атака",
     "weapons": "Кинжал, Серп, Скимитар, Лёгкий молот"},
    {"name": "Прорубание", "trigger": "Попадание по врагу",
     "effect": "Можно атаковать второго врага рядом (без бонуса к урону)", "weapons": "Двуручный топор, Алебарда"},
    {"name": "Задевание", "trigger": "Промах атакой", "effect": "Всё равно наносите урон = модификатору характеристики",
     "weapons": "Глефа, Двуручный меч"},
    {"name": "Толкание", "trigger": "Попадание", "effect": "Отодвинуть врага (до 10 футов)",
     "weapons": "Большая дубина, Пика, Военный молот"},
    {"name": "Изнурение", "trigger": "Попадание", "effect": "У врага помеха на следующую атаку",
     "weapons": "Булава, Копьё, Длинный меч"},
    {"name": "Замедление", "trigger": "Попадание+урон", "effect": "Скорость врага падает на 10 футов",
     "weapons": "Дубина, Кнут, Длинный лук"},
    {"name": "Опрокидывание", "trigger": "Попадание", "effect": "Враг падает ничком",
     "weapons": "Боевой топор, Ланс, Трезубец"},
    {"name": "Подавление", "trigger": "Попадание+урон", "effect": "Вы получаете преимущество на следующую атаку",
     "weapons": "Рапира, Короткий лук, Метательный топор"},
]


def migrate_weapon_masteries(conn):
    """Перенос базовых оружейных приёмов"""
    logger.info("\n" + "=" * 50)
    logger.info("4. ПЕРЕНОС ОРУЖЕЙНЫХ ПРИЁМОВ (БАЗОВЫЕ)")
    logger.info("=" * 50)

    with conn.cursor() as cur:
        for m in WEAPON_MASTERIES:
            cur.execute("""
                INSERT INTO weapon_masteries (name, trigger_condition, effect, weapons)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (m["name"], m["trigger"], m["effect"], m["weapons"]))
            logger.info(f"  ✅ Приём '{m['name']}'")

        conn.commit()
    logger.info(f"✅ Перенесено приёмов: {len(WEAPON_MASTERIES)}")


# =========================================================
# 5. ДАННЫЕ БОЕВЫХ СТИЛЕЙ
# =========================================================

FIGHTING_STYLES = [
    {"name": "Дуэлянт",
     "description": "Когда вы атакуете оружием в одной руке и не используете щит, вы добавляете +2 к урону."},
    {"name": "Защита",
     "description": "Когда существо, которое вы видите, атакует цель, отличную от вас, вы можете реакцией дать помеху на эту атаку."},
    {"name": "Оборона", "description": "Вы получаете +1 к Классу Брони, если носите броню."},
    {"name": "Перехват",
     "description": "Когда существо атакует цель в пределах 5 футов от вас, вы можете реакцией уменьшить урон на 1d10 + бонус мастерства."},
    {"name": "Сражение без оружия", "description": "Ваши безоружные удары наносят 1d6 + модификатор силы урона."},
    {"name": "Сражение большим оружием",
     "description": "При атаке двуручным оружием вы можете перебросить единицы и двойки на кубиках урона."},
    {"name": "Сражение вслепую", "description": "Вы получаете слепое зрение в радиусе 10 футов."},
    {"name": "Сражение двумя оружиями",
     "description": "При атаке лёгким оружием вы можете добавить модификатор характеристики к урону бонусной атаки."},
    {"name": "Сражение метательным оружием",
     "description": "Вы можете выхватить метательное оружие как часть атаки им."},
    {"name": "Стрельба", "description": "Вы получаете +2 к броскам атаки дальнобойным оружием."},
]

CLASS_FIGHTING_STYLES = {
    "Воин": ["Дуэлянт", "Защита", "Оборона", "Перехват", "Сражение без оружия",
             "Сражение большим оружием", "Сражение вслепую", "Сражение двумя оружиями",
             "Сражение метательным оружием", "Стрельба"],
    "Паладин": ["Дуэлянт", "Защита", "Оборона", "Перехват", "Сражение без оружия",
                "Сражение большим оружием", "Сражение вслепую"],
    "Следопыт": ["Дуэлянт", "Защита", "Оборона", "Сражение вслепую",
                 "Сражение двумя оружиями", "Сражение метательным оружием", "Стрельба"],
}


def migrate_fighting_styles(conn, class_id_map):
    """Перенос боевых стилей и связей с классами"""
    logger.info("\n" + "=" * 50)
    logger.info("5. ПЕРЕНОС БОЕВЫХ СТИЛЕЙ")
    logger.info("=" * 50)

    style_id_map = {}

    with conn.cursor() as cur:
        for style in FIGHTING_STYLES:
            cur.execute("""
                INSERT INTO fighting_styles (name, description)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            """, (style["name"], style["description"]))
            result = cur.fetchone()
            if result:
                style_id_map[style["name"]] = result[0]
                logger.info(f"  ✅ Стиль '{style['name']}'")

        for class_name, styles in CLASS_FIGHTING_STYLES.items():
            if class_name in class_id_map:
                for style_name in styles:
                    if style_name in style_id_map:
                        cur.execute("""
                            INSERT INTO class_fighting_styles (class_id, style_id)
                            VALUES (%s, %s)
                            ON CONFLICT (class_id, style_id) DO NOTHING
                        """, (class_id_map[class_name], style_id_map[style_name]))
                        logger.info(f"    • {class_name} → {style_name}")

        conn.commit()
    logger.info(f"✅ Перенесено стилей: {len(FIGHTING_STYLES)}")


# =========================================================
# 6. ДАННЫЕ ТАИНСТВЕННЫХ ВОЗВАНИЙ
# =========================================================

INVOCATIONS = [
    {"name": "Недоговорённость клинка", "level": 1,
     "effect": "Вы создаёте оружие или связываетесь с магическим оружием. Можете использовать Харизму для атак и урона.",
     "requires_pact_boon": True, "pact_boon_type": "Blade"},
    {"name": "Недоговорённость цепи", "level": 1, "effect": "Вы учите Поиск фамильяра с расширенными формами.",
     "requires_pact_boon": True, "pact_boon_type": "Chain"},
    {"name": "Недоговорённость гримуара", "level": 1,
     "effect": "Вы получаете 3 заговора из любых списков и 2 ритуала 1 уровня.", "requires_pact_boon": True,
     "pact_boon_type": "Tome"},
    {"name": "Броня теней", "level": 1,
     "effect": "Вы можете накладывать Магическую броню на себя без использования ячейки.", "requires_pact_boon": False,
     "pact_boon_type": None},
    {"name": "Разум бездны", "level": 1,
     "effect": "Вы получаете преимущество на спасброски Телосложения для концентрации.", "requires_pact_boon": False,
     "pact_boon_type": None},
    {"name": "Дьявольское могущество", "level": 2,
     "effect": "Вы накладываете Ложную жизнь на себя без ячейки, автоматически получая максимальные хиты.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Дьявольское зрение", "level": 2, "effect": "Вы видите в магической тьме на 120 футов.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Маска многих лиц", "level": 2, "effect": "Вы накладываете Смену облика без ячейки.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Туманные видения", "level": 2, "effect": "Вы накладываете Немой образ без ячейки.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Иной мир прыжок", "level": 2, "effect": "Вы накладываете Прыжок на себя без ячейки.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Умножающий залп", "level": 2, "effect": "Вы добавляете модификатор Харизмы к урону выбранного заговора.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Колдовское копьё", "level": 2,
     "effect": "Дистанция выбранного заговора увеличивается на 30 футов x ваш уровень Колдуна.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Отталкивающий залп", "level": 2,
     "effect": "При попадании заговором, требующим броска атаки, вы толкаете цель на 10 футов.",
     "requires_pact_boon": False, "pact_boon_type": None},
]


def migrate_invocations(conn):
    """Перенос таинственных возваний"""
    logger.info("\n" + "=" * 50)
    logger.info("6. ПЕРЕНОС ТАИНСТВЕННЫХ ВОЗВАНИЙ")
    logger.info("=" * 50)

    with conn.cursor() as cur:
        for inv in INVOCATIONS:
            cur.execute("""
                INSERT INTO invocations (name, level_required, effect, requires_pact_boon, pact_boon_type)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (
                inv["name"], inv["level"], inv["effect"],
                inv["requires_pact_boon"], inv["pact_boon_type"]
            ))
            logger.info(f"  ✅ Возвание '{inv['name']}'")

        conn.commit()
    logger.info(f"✅ Перенесено возваний: {len(INVOCATIONS)}")


# =========================================================
# 7. ДАННЫЕ ОРУЖИЯ И СВЯЗЕЙ
# =========================================================

WEAPONS_DATA = [
    # Простое оружие
    {"name": "Кинжал", "category": "simple", "damage_dice": "1d4", "damage_type": "piercing",
     "properties": ["легкое", "метательное"], "suitable_masteries": ["Выпад", "Подавление"]},
    {"name": "Серп", "category": "simple", "damage_dice": "1d4", "damage_type": "slashing",
     "properties": ["легкое"], "suitable_masteries": ["Выпад"]},
    {"name": "Дубина", "category": "simple", "damage_dice": "1d4", "damage_type": "bludgeoning",
     "properties": ["легкое"], "suitable_masteries": ["Замедление"]},
    {"name": "Копьё", "category": "simple", "damage_dice": "1d6", "damage_type": "piercing",
     "properties": ["метательное", "универсальное"], "suitable_masteries": ["Изнурение", "Толкание"]},
    {"name": "Булава", "category": "simple", "damage_dice": "1d6", "damage_type": "bludgeoning",
     "properties": [], "suitable_masteries": ["Изнурение"]},

    # Воинское оружие
    {"name": "Длинный меч", "category": "martial", "damage_dice": "1d8", "damage_type": "slashing",
     "properties": ["универсальное"], "suitable_masteries": ["Изнурение"]},
    {"name": "Рапира", "category": "martial", "damage_dice": "1d8", "damage_type": "piercing",
     "properties": ["изящное"], "suitable_masteries": ["Подавление"]},
    {"name": "Боевой топор", "category": "martial", "damage_dice": "1d8", "damage_type": "slashing",
     "properties": ["универсальное"], "suitable_masteries": ["Опрокидывание", "Изнурение"]},
    {"name": "Двуручный меч", "category": "martial", "damage_dice": "2d6", "damage_type": "slashing",
     "properties": ["двуручное", "тяжёлое"], "suitable_masteries": ["Задевание", "Прорубание"]},
    {"name": "Двуручный топор", "category": "martial", "damage_dice": "1d12", "damage_type": "slashing",
     "properties": ["двуручное", "тяжёлое"], "suitable_masteries": ["Прорубание", "Задевание"]},
    {"name": "Алебарда", "category": "martial", "damage_dice": "1d10", "damage_type": "slashing",
     "properties": ["двуручное", "тяжёлое", "досягаемость"], "suitable_masteries": ["Прорубание"]},
    {"name": "Глефа", "category": "martial", "damage_dice": "1d10", "damage_type": "slashing",
     "properties": ["двуручное", "тяжёлое", "досягаемость"], "suitable_masteries": ["Задевание"]},
    {"name": "Пика", "category": "martial", "damage_dice": "1d10", "damage_type": "piercing",
     "properties": ["двуручное", "тяжёлое", "досягаемость"], "suitable_masteries": ["Толкание"]},
    {"name": "Большая дубина", "category": "martial", "damage_dice": "1d8", "damage_type": "bludgeoning",
     "properties": ["двуручное"], "suitable_masteries": ["Толкание"]},
    {"name": "Военный молот", "category": "martial", "damage_dice": "1d8", "damage_type": "bludgeoning",
     "properties": ["универсальное"], "suitable_masteries": ["Толкание"]},
    {"name": "Ланс", "category": "martial", "damage_dice": "1d10", "damage_type": "piercing",
     "properties": ["досягаемость", "особое"], "suitable_masteries": ["Опрокидывание"]},
    {"name": "Трезубец", "category": "martial", "damage_dice": "1d6", "damage_type": "piercing",
     "properties": ["метательное", "универсальное"], "suitable_masteries": ["Опрокидывание", "Толкание"]},
    {"name": "Кнут", "category": "martial", "damage_dice": "1d4", "damage_type": "slashing",
     "properties": ["изящное", "досягаемость"], "suitable_masteries": ["Замедление"]},
    {"name": "Короткий лук", "category": "martial", "damage_dice": "1d6", "damage_type": "piercing",
     "properties": ["двуручное", "дальнобойное"], "suitable_masteries": ["Замедление", "Подавление"]},
    {"name": "Длинный лук", "category": "martial", "damage_dice": "1d8", "damage_type": "piercing",
     "properties": ["двуручное", "тяжёлое", "дальнобойное"], "suitable_masteries": ["Замедление"]},
    {"name": "Лёгкий молот", "category": "simple", "damage_dice": "1d4", "damage_type": "bludgeoning",
     "properties": ["легкое", "метательное"], "suitable_masteries": ["Выпад"]},
    {"name": "Метательный топор", "category": "simple", "damage_dice": "1d6", "damage_type": "slashing",
     "properties": ["легкое", "метательное"], "suitable_masteries": ["Подавление"]},
    {"name": "Скимитар", "category": "martial", "damage_dice": "1d6", "damage_type": "slashing",
     "properties": ["изящное"], "suitable_masteries": ["Выпад"]},
    {"name": "Короткий меч", "category": "martial", "damage_dice": "1d6", "damage_type": "piercing",
     "properties": ["изящное", "легкое"], "suitable_masteries": ["Подавление"]},
    {"name": "Цеп", "category": "martial", "damage_dice": "1d8", "damage_type": "bludgeoning",
     "properties": [], "suitable_masteries": ["Изнурение"]},
    {"name": "Боевой посох", "category": "simple", "damage_dice": "1d6", "damage_type": "bludgeoning",
     "properties": ["универсальное"], "suitable_masteries": ["Толкание"]},
    {"name": "Секира", "category": "martial", "damage_dice": "1d8", "damage_type": "slashing",
     "properties": ["универсальное"], "suitable_masteries": ["Опрокидывание"]},
]


def migrate_weapons(conn, class_id_map):
    """Перенос оружия и связей с классами"""
    logger.info("\n" + "=" * 50)
    logger.info("7. ПЕРЕНОС ОРУЖИЯ")
    logger.info("=" * 50)

    weapon_id_map = {}

    with conn.cursor() as cur:
        for weapon in WEAPONS_DATA:
            cur.execute("""
                INSERT INTO weapons (name, category, damage_dice, damage_type, properties, suitable_masteries)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            """, (
                weapon["name"], weapon["category"], weapon["damage_dice"],
                weapon["damage_type"], json.dumps(weapon["properties"]),
                json.dumps(weapon["suitable_masteries"])
            ))
            result = cur.fetchone()
            if result:
                weapon_id_map[weapon["name"]] = result[0]
                logger.info(f"  ✅ Оружие '{weapon['name']}'")

        # Связываем оружие с классами
        if "Воин" in class_id_map:
            for weapon_name, weapon_id in weapon_id_map.items():
                cur.execute("""
                    INSERT INTO class_weapons (class_id, weapon_id)
                    VALUES (%s, %s)
                    ON CONFLICT (class_id, weapon_id) DO NOTHING
                """, (class_id_map["Воин"], weapon_id))
            logger.info(f"    • Воин → всё оружие ({len(weapon_id_map)} шт.)")

        martial_weapons = [w["name"] for w in WEAPONS_DATA if w["category"] == "martial"]
        simple_weapons = [w["name"] for w in WEAPONS_DATA if w["category"] == "simple"]

        if "Паладин" in class_id_map:
            for w_name in martial_weapons + simple_weapons:
                if w_name in weapon_id_map:
                    cur.execute("""
                        INSERT INTO class_weapons (class_id, weapon_id)
                        VALUES (%s, %s)
                        ON CONFLICT (class_id, weapon_id) DO NOTHING
                    """, (class_id_map["Паладин"], weapon_id_map[w_name]))
            logger.info(f"    • Паладин → всё оружие")

        if "Следопыт" in class_id_map:
            light_weapons = ["Короткий меч", "Кинжал", "Лёгкий молот", "Метательный топор", "Короткий лук",
                             "Длинный лук"]
            for w_name in light_weapons + simple_weapons:
                if w_name in weapon_id_map:
                    cur.execute("""
                        INSERT INTO class_weapons (class_id, weapon_id)
                        VALUES (%s, %s)
                        ON CONFLICT (class_id, weapon_id) DO NOTHING
                    """, (class_id_map["Следопыт"], weapon_id_map[w_name]))
            logger.info(f"    • Следопыт → лёгкое и простое оружие")

        for class_name in ["Варвар", "Плут"]:
            if class_name in class_id_map:
                for w_name in simple_weapons + ["Рапира", "Короткий лук", "Длинный меч", "Короткий меч"]:
                    if w_name in weapon_id_map:
                        cur.execute("""
                            INSERT INTO class_weapons (class_id, weapon_id)
                            VALUES (%s, %s)
                            ON CONFLICT (class_id, weapon_id) DO NOTHING
                        """, (class_id_map[class_name], weapon_id_map[w_name]))
                logger.info(f"    • {class_name} → простое + избранное воинское")

        conn.commit()
    logger.info(f"✅ Перенесено оружия: {len(WEAPONS_DATA)}")


# =========================================================
# 8. ДАННЫЕ БРОНИ
# =========================================================

ARMOR_DATA = [
    {"name": "Проклёпанный кожаный доспех", "ac_base": 12, "ac_modifier": "dex", "has_shield": False},
    {"name": "Кожаный доспех", "ac_base": 11, "ac_modifier": "dex", "has_shield": False},
    {"name": "Кольчуга", "ac_base": 16, "ac_modifier": "none", "has_shield": False},
    {"name": "Кольчужная рубаха", "ac_base": 13, "ac_modifier": "dex_max2", "has_shield": False},
    {"name": "Щит", "ac_base": 2, "ac_modifier": "shield", "has_shield": True},
]


def migrate_armor(conn):
    """Перенос брони"""
    logger.info("\n" + "=" * 50)
    logger.info("8. ПЕРЕНОС БРОНИ")
    logger.info("=" * 50)

    with conn.cursor() as cur:
        for armor in ARMOR_DATA:
            cur.execute("""
                INSERT INTO armor (name, ac_base, ac_modifier, has_shield)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (armor["name"], armor["ac_base"], armor["ac_modifier"], armor["has_shield"]))
            logger.info(f"  ✅ Броня '{armor['name']}'")

        conn.commit()
    logger.info(f"✅ Перенесено брони: {len(ARMOR_DATA)}")


# =========================================================
# 9. ДАННЫЕ СНАРЯЖЕНИЯ ПО КЛАССАМ
# =========================================================

CLASS_EQUIPMENT_DATA = [
    {"class": "Артефактор", "choice": None, "armor": "Проклёпанный кожаный доспех",
     "weapon": "Кинжал", "secondary": None,
     "other": "Воровские инструменты, Инструменты ремонтника, Набор исследователя подземелий", "coins": 16},
    {"class": "Бард", "choice": None, "armor": "Кожаный доспех",
     "weapon": "Кинжал", "secondary": "Кинжал", "other": "Музыкальный инструмент (любой), Набор артиста", "coins": 19},
    {"class": "Варвар", "choice": None, "armor": None,
     "weapon": "Секира", "secondary": None, "other": "4 Одноручных топора, Набор путешественника", "coins": 15},
    {"class": "Воин", "choice": "A", "armor": "Кольчуга",
     "weapon": "Двуручный меч", "secondary": "Цеп", "other": "8 Метательных копий, Набор исследователя подземелий",
     "coins": 4},
    {"class": "Воин", "choice": "B", "armor": "Проклёпанный кожаный доспех",
     "weapon": "Скимитар", "secondary": "Короткий меч",
     "other": "Длинный лук, 20 Стрел, Колчан, Набор исследователя подземелий", "coins": 11},
    {"class": "Волшебник", "choice": None, "armor": None,
     "weapon": "Кинжал", "secondary": "Кинжал",
     "other": "Магическая фокусировка (Боевой посох), Мантия, Книга заклинаний, Набор учёного", "coins": 5},
    {"class": "Друид", "choice": None, "armor": "Кожаный доспех",
     "weapon": "Серп", "secondary": None,
     "other": "Щит, Друидическая фокусировка (Боевой посох), Набор путешественника, Набор травника", "coins": 9},
    {"class": "Жрец", "choice": None, "armor": "Кольчужная рубаха",
     "weapon": "Булава", "secondary": None, "other": "Щит, Священный символ, Набор священника", "coins": 7},
    {"class": "Колдун", "choice": None, "armor": "Кожаный доспех",
     "weapon": "Серп", "secondary": "Кинжал",
     "other": "Кинжал, Магическая фокусировка (сфера), Книга (оккультные знания), Набор учёного", "coins": 15},
    {"class": "Монах", "choice": None, "armor": None,
     "weapon": "Копьё", "secondary": None,
     "other": "5 Кинжалов, Ремесленные или Музыкальный инструмент, Набор путешественника", "coins": 11},
    {"class": "Паладин", "choice": None, "armor": "Кольчуга",
     "weapon": "Длинный меч", "secondary": None,
     "other": "Щит, 6 Метательных копий, Священный символ, Набор священника", "coins": 9},
    {"class": "Плут", "choice": None, "armor": "Кожаный доспех",
     "weapon": "Кинжал", "secondary": "Короткий меч",
     "other": "Кинжал, Короткий лук, 20 Стрел, Колчан, Воровские инструменты, Набор взломщика", "coins": 8},
    {"class": "Следопыт", "choice": None, "armor": "Проклёпанный кожаный доспех",
     "weapon": "Скимитар", "secondary": "Короткий меч",
     "other": "Длинный лук, 20 Стрел, Колчан, Друидическая фокусировка (веточка омелы), Набор путешественника",
     "coins": 7},
    {"class": "Чародей", "choice": None, "armor": None,
     "weapon": "Копьё", "secondary": "Кинжал",
     "other": "Кинжал, Магическая фокусировка (кристалл), Набор исследователя подземелий", "coins": 28},
]


def migrate_class_equipment(conn, class_id_map):
    """Перенос снаряжения по классам"""
    logger.info("\n" + "=" * 50)
    logger.info("9. ПЕРЕНОС СНАРЯЖЕНИЯ ПО КЛАССАМ")
    logger.info("=" * 50)

    with conn.cursor() as cur:
        for eq in CLASS_EQUIPMENT_DATA:
            if eq["class"] in class_id_map:
                cur.execute("""
                    INSERT INTO class_equipment (class_id, choice, armor, weapon, secondary_weapon, other_items, coins)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (class_id, choice) DO NOTHING
                """, (
                    class_id_map[eq["class"]],
                    eq["choice"],
                    eq["armor"],
                    eq["weapon"],
                    eq["secondary"],
                    eq["other"],
                    eq["coins"]
                ))
                logger.info(
                    f"  ✅ Снаряжение для '{eq['class']}' (вариант {eq['choice'] if eq['choice'] else 'стандарт'})")

        conn.commit()
    logger.info(f"✅ Перенесено снаряжения: {len(CLASS_EQUIPMENT_DATA)}")


# =========================================================
# 10. ДАННЫЕ ЗАКЛИНАНИЙ И РЕКОМЕНДАЦИЙ
# =========================================================

SPELLS_DATA = [
    # Заговоры (кантрипы)
    {"name": "Волшебная рука", "level": 0, "is_cantrip": True,
     "description": "Создаёте призрачную руку для взаимодействия с объектами."},
    {"name": "Вспышка света", "level": 0, "is_cantrip": True, "description": "Вспышка света ослепляет врага."},
    {"name": "Починка", "level": 0, "is_cantrip": True, "description": "Чините один сломанный предмет."},
    {"name": "Сообщение", "level": 0, "is_cantrip": True, "description": "Шёпотом передаёте сообщение на расстояние."},
    {"name": "Удар грома", "level": 0, "is_cantrip": True,
     "description": "Создаёте громовой звук, отталкивающий врага."},
    {"name": "Фокус-покус", "level": 0, "is_cantrip": True, "description": "Создаёте мелкий магический эффект."},
    {"name": "Руководство", "level": 0, "is_cantrip": True,
     "description": "Даёте цели +1к4 к проверке характеристики."},
    {"name": "Священное пламя", "level": 0, "is_cantrip": True, "description": "Луч божественного огня."},
    {"name": "Мистический залп", "level": 0, "is_cantrip": True, "description": "Луч энергии, наносящий 1к10 урона."},
    {"name": "Вдохновение насмешки", "level": 0, "is_cantrip": True,
     "description": "Оскорбляете врага, давая ему помеху."},

    # Заклинания 1 уровня
    {"name": "Лечение ран", "level": 1, "is_cantrip": False, "description": "Восстанавливает 1к8 + модификатор хитов."},
    {"name": "Громовая волна", "level": 1, "is_cantrip": False, "description": "Ударная волна отталкивает врагов."},
    {"name": "Благословение", "level": 1, "is_cantrip": False,
     "description": "Три цели получают +1к4 к броскам атаки и спасброскам."},
    {"name": "Маскировка", "level": 1, "is_cantrip": False, "description": "Меняете свою внешность на 1 час."},
    {"name": "Щит", "level": 1, "is_cantrip": False, "description": "Реакция: +5 к КД до следующего хода."},
    {"name": "Хроматическая сфера", "level": 1, "is_cantrip": False,
     "description": "Метаете сферу выбранного типа урона."},
    {"name": "Сон", "level": 1, "is_cantrip": False, "description": "Погружаете существ в магический сон."},
    {"name": "Обнаружение магии", "level": 1, "is_cantrip": False,
     "description": "Чувствуете присутствие магии в радиусе 30 футов."},
    {"name": "Прыжок", "level": 1, "is_cantrip": False, "description": "Удваиваете дистанцию прыжка цели."},
    {"name": "Разговор с животными", "level": 1, "is_cantrip": False, "description": "Можете общаться с животными."},
    {"name": "Опутывание", "level": 1, "is_cantrip": False, "description": "Опутываете существ магическими лозами."},
    {"name": "Гекс", "level": 1, "is_cantrip": False, "description": "Проклинаете цель, нанося дополнительный урон."},
    {"name": "Метка охотника", "level": 1, "is_cantrip": False,
     "description": "Отмечаете врага, нанося ему дополнительный урон."},
    {"name": "Божественная кара", "level": 1, "is_cantrip": False, "description": "Добавляете 2к8 урона к атаке."},
    {"name": "Доспехи Агатиса", "level": 1, "is_cantrip": False,
     "description": "Получаете временные хиты и ледяную защиту."},
]

RECOMMENDED_SPELLS = {
    "Волшебник": {"cantrips": ["Волшебная рука", "Вспышка света", "Починка"],
                  "level1": ["Щит", "Хроматическая сфера", "Сон", "Обнаружение магии"]},
    "Бард": {"cantrips": ["Вдохновение насмешки", "Удар грома", "Сообщение"],
             "level1": ["Лечение ран", "Сон", "Благословение", "Маскировка"]},
    "Жрец": {"cantrips": ["Руководство", "Священное пламя", "Вспышка света"],
             "level1": ["Лечение ран", "Благословение", "Обнаружение магии", "Громовая волна"]},
    "Друид": {"cantrips": ["Руководство", "Фокус-покус", "Удар грома"],
              "level1": ["Лечение ран", "Опутывание", "Разговор с животными", "Прыжок"]},
    "Колдун": {"cantrips": ["Мистический залп", "Волшебная рука", "Удар грома"],
               "level1": ["Гекс", "Доспехи Агатиса", "Щит", "Сон"]},
    "Чародей": {"cantrips": ["Волшебная рука", "Вспышка света", "Удар грома"],
                "level1": ["Щит", "Хроматическая сфера", "Сон", "Обнаружение магии"]},
    "Паладин": {"cantrips": [],
                "level1": ["Лечение ран", "Божественная кара", "Благословение"]},
    "Следопыт": {"cantrips": [],
                 "level1": ["Метка охотника", "Лечение ран", "Прыжок"]},
    "Артефактор": {"cantrips": ["Починка", "Вспышка света", "Волшебная рука"],
                   "level1": ["Щит", "Лечение ран", "Обнаружение магии"]},
}

CLASS_SPELLS = {
    "Волшебник": ["Волшебная рука", "Вспышка света", "Починка", "Сообщение", "Удар грома",
                  "Лечение ран", "Громовая волна", "Щит", "Хроматическая сфера", "Сон", "Обнаружение магии"],
    "Бард": ["Вдохновение насмешки", "Удар грома", "Сообщение", "Фокус-покус",
             "Лечение ран", "Сон", "Благословение", "Маскировка", "Громовая волна"],
    "Жрец": ["Руководство", "Священное пламя", "Вспышка света",
             "Лечение ран", "Благословение", "Обнаружение магии", "Громовая волна"],
    "Друид": ["Руководство", "Фокус-покус", "Удар грома",
              "Лечение ран", "Опутывание", "Разговор с животными", "Прыжок"],
    "Колдун": ["Мистический залп", "Волшебная рука", "Удар грома",
               "Гекс", "Доспехи Агатиса", "Щит", "Сон"],
    "Чародей": ["Волшебная рука", "Вспышка света", "Удар грома",
                "Щит", "Хроматическая сфера", "Сон", "Обнаружение магии"],
    "Паладин": ["Лечение ран", "Божественная кара", "Благословение"],
    "Следопыт": ["Метка охотника", "Лечение ран", "Прыжок"],
    "Артефактор": ["Починка", "Вспышка света", "Волшебная рука",
                   "Щит", "Лечение ран", "Обнаружение магии"],
}


def migrate_spells(conn, class_id_map):
    """Перенос заклинаний, связей с классами и рекомендаций"""
    logger.info("\n" + "=" * 50)
    logger.info("10. ПЕРЕНОС ЗАКЛИНАНИЙ")
    logger.info("=" * 50)

    spell_id_map = {}

    with conn.cursor() as cur:
        for spell in SPELLS_DATA:
            cur.execute("""
                INSERT INTO spells (name, level, is_cantrip, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """, (spell["name"], spell["level"], spell["is_cantrip"], spell["description"]))

            result = cur.fetchone()
            if result:
                spell_id_map[spell["name"]] = result[0]
                logger.info(f"  ✅ Заклинание '{spell['name']}'")

        for class_name, spell_names in CLASS_SPELLS.items():
            if class_name in class_id_map:
                for spell_name in spell_names:
                    if spell_name in spell_id_map:
                        cur.execute("""
                            INSERT INTO class_spells (class_id, spell_id, is_available)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (class_id, spell_id) DO NOTHING
                        """, (class_id_map[class_name], spell_id_map[spell_name], True))
                logger.info(f"    • {class_name} → {len(spell_names)} заклинаний")

        for class_name, spells in RECOMMENDED_SPELLS.items():
            if class_name in class_id_map:
                priority = 1
                for spell_name in spells.get("cantrips", []):
                    if spell_name in spell_id_map:
                        cur.execute("""
                            INSERT INTO recommended_spells (class_id, spell_id, is_cantrip, priority)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (class_id, spell_id) DO NOTHING
                        """, (class_id_map[class_name], spell_id_map[spell_name], True, priority))
                        priority += 1

                priority = 1
                for spell_name in spells.get("level1", []):
                    if spell_name in spell_id_map:
                        cur.execute("""
                            INSERT INTO recommended_spells (class_id, spell_id, is_cantrip, priority)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (class_id, spell_id) DO NOTHING
                        """, (class_id_map[class_name], spell_id_map[spell_name], False, priority))
                        priority += 1

                logger.info(
                    f"    • {class_name} → рекомендовано {len(spells.get('cantrips', [])) + len(spells.get('level1', []))} заклинаний")

        conn.commit()

    logger.info(f"✅ Перенесено заклинаний: {len(SPELLS_DATA)}")


# =========================================================
# ГЛАВНАЯ ФУНКЦИЯ
# =========================================================

def main():
    print("\n" + "=" * 60)
    print("🐉 D&D 5.5e (2024) - НАПОЛНЕНИЕ БАЗЫ ДАННЫХ")
    print("Автономный скрипт (без внешних файлов)")
    print("=" * 60 + "\n")

    conn = None
    try:
        conn = get_connection()
        logger.info(f"✅ Подключено к БД: {DB_CONFIG['dbname']}")

        response = input("Очистить таблицы перед заполнением? (yes/no): ").strip().lower()
        if response == 'yes':
            clear_tables(conn)

        # Последовательный перенос
        migrate_races(conn)
        migrate_classes(conn)
        migrate_backgrounds(conn)
        migrate_weapon_masteries(conn)

        # Получаем ID классов для связей
        class_id_map = {}
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM classes")
            for row in cur.fetchall():
                class_id_map[row[1]] = row[0]

        migrate_fighting_styles(conn, class_id_map)
        migrate_invocations(conn)
        migrate_weapons(conn, class_id_map)
        migrate_armor(conn)
        migrate_class_equipment(conn, class_id_map)
        migrate_spells(conn, class_id_map)

        print("\n" + "=" * 60)
        logger.info("🎉 БАЗА ДАННЫХ УСПЕШНО НАПОЛНЕНА!")
        print("=" * 60)

        with conn.cursor() as cur:
            stats = [
                ("races", "Рас"), ("subraces", "Подрас"), ("classes", "Классов"),
                ("backgrounds", "Предысторий"), ("spells", "Заклинаний"),
                ("weapon_masteries", "Оружейных приёмов"), ("fighting_styles", "Боевых стилей"),
                ("weapons", "Оружия"), ("invocations", "Возваний"),
                ("armor", "Брони"), ("class_equipment", "Снаряжения классов")
            ]
            print("\n📊 СТАТИСТИКА:")
            for table, name in stats:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"   • {name}: {count}")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
            logger.info("🔌 Соединение с БД закрыто")


if __name__ == "__main__":
    main()