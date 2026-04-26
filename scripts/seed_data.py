#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_data.py - Наполнение базы данных D&D 5.5e (2024) данными
Запуск: python seed_data.py
Скрипт не зависит от внешних файлов — все данные встроены в код.
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
        "class_spells", "spells", "subclasses", "classes",
        "subraces", "races", "backgrounds", "weapon_masteries",
        "fighting_styles", "invocations"
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
        "description": "Мастера раскрытия магии в обычных вещах, изобретатели — величайшие выдумщики. Они видят магию как сложную систему, которую нужно расшифровывать и контролировать."
    },
    "Бард": {
        "hit_die": 8, "primary_stats": ["CHA"], "saving_throws": ["DEX", "CHA"],
        "skill_choices": 3, "is_spellcaster": True, "spellcasting_ability": "CHA",
        "description": "Бард плетёт магию из слов и музыки, вдохновляя союзников, деморализуя противников, манипулируя сознанием и даже исцеляя раны."
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
        "description": "Волшебники — адепты высшей магии, способные создавать заклинания взрывного огня, искрящихся молний и тонкого обмана."
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
        "description": "Колдуны — искатели знаний, через договор с таинственными существами открывающие магические эффекты."
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
# 4. ДАННЫЕ ОРУЖЕЙНЫХ ПРИЁМОВ
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
    """Перенос оружейных приёмов"""
    logger.info("\n" + "=" * 50)
    logger.info("4. ПЕРЕНОС ОРУЖЕЙНЫХ ПРИЁМОВ")
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
    "Дуэлянт", "Защита", "Оборона", "Перехват",
    "Сражение без оружия", "Сражение большим оружием",
    "Сражение вслепую", "Сражение двумя оружиями",
    "Сражение метательным оружием", "Стрельба"
]


def migrate_fighting_styles(conn):
    """Перенос боевых стилей"""
    logger.info("\n" + "=" * 50)
    logger.info("5. ПЕРЕНОС БОЕВЫХ СТИЛЕЙ")
    logger.info("=" * 50)

    with conn.cursor() as cur:
        for style in FIGHTING_STYLES:
            cur.execute("""
                INSERT INTO fighting_styles (name, description)
                VALUES (%s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (style, f"Боевой стиль: {style}"))
            logger.info(f"  ✅ Стиль '{style}'")

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
    {"name": "Умножающий залп", "level": 2, "effect": "Вы добавляете модификатор Харизмы к урону выбранного заговора.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Колдовское копьё", "level": 2,
     "effect": "Дистанция выбранного заговора увеличивается на 30 футов x ваш уровень Колдуна.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Отталкивающий залп", "level": 2,
     "effect": "При попадании заговором, требующим броска атаки, вы толкаете цель на 10 футов.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Броня теней", "level": 1,
     "effect": "Вы можете накладывать Магическую броню на себя без использования ячейки.", "requires_pact_boon": False,
     "pact_boon_type": None},
    {"name": "Дьявольское зрение", "level": 2, "effect": "Вы видите в магической тьме на 120 футов.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Разум бездны", "level": 1,
     "effect": "Вы получаете преимущество на спасброски Телосложения для концентрации.", "requires_pact_boon": False,
     "pact_boon_type": None},
    {"name": "Дьявольское могущество", "level": 2,
     "effect": "Вы накладываете Ложную жизнь на себя без ячейки, автоматически получая максимальные хиты.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Маска многих лиц", "level": 2, "effect": "Вы накладываете Смену облика без ячейки.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Туманные видения", "level": 2, "effect": "Вы накладываете Немой образ без ячейки.",
     "requires_pact_boon": False, "pact_boon_type": None},
    {"name": "Иной мир прыжок", "level": 2, "effect": "Вы накладываете Прыжок на себя без ячейки.",
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
# 7. ДАННЫЕ ЗАКЛИНАНИЙ (основные)
# =========================================================

SPELLS_DATA = [
    # Заговоры (кантрипы) для всех классов
    {"name": "Волшебная рука", "level": 0, "is_cantrip": True,
     "description": "Создаёте призрачную руку для взаимодействия с объектами."},
    {"name": "Вспышка света", "level": 0, "is_cantrip": True, "description": "Вспышка света ослепляет врага."},
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
    {"name": "Рвотный луч", "level": 1, "is_cantrip": False,
     "description": "Цель должна совершить спасбросок Телосложения или получить урон ядом."},
    {"name": "Падение пера", "level": 1, "is_cantrip": False, "description": "Замедляете падение цели."},
    {"name": "Разговор с животными", "level": 1, "is_cantrip": False, "description": "Можете общаться с животными."},
    {"name": "Фея-покровительница", "level": 1, "is_cantrip": False, "description": "Призываете фею для помощи."},
    {"name": "Опутывание", "level": 1, "is_cantrip": False, "description": "Опутываете существ магическими лозами."},
    {"name": "Туман облака", "level": 1, "is_cantrip": False, "description": "Создаёте облако тумана."},
    {"name": "Эльфийское пламя", "level": 1, "is_cantrip": False,
     "description": "Освещаете цель фейским огнём, давая преимущество на атаки по ней."},
]


def get_class_id_map(conn):
    """Получает словарь соответствия имени класса и ID"""
    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM classes")
        return {name: id for id, name in cur.fetchall()}


def migrate_spells(conn):
    """Перенос заклинаний и связей с классами"""
    logger.info("\n" + "=" * 50)
    logger.info("7. ПЕРЕНОС ЗАКЛИНАНИЙ")
    logger.info("=" * 50)

    class_map = get_class_id_map(conn)

    with conn.cursor() as cur:
        for spell in SPELLS_DATA:
            # Вставляем заклинание
            cur.execute("""
                INSERT INTO spells (name, level, is_cantrip, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """, (
                spell["name"], spell["level"],
                spell["is_cantrip"], spell["description"]
            ))

            result = cur.fetchone()
            if result:
                spell_id = result[0]
                logger.info(f"  ✅ Заклинание '{spell['name']}' (уровень {spell['level']})")

                # Связываем с подходящими классами
                for class_name, class_id in class_map.items():
                    # Примерные связи (можно расширить)
                    spellcaster_classes = ["Волшебник", "Бард", "Жрец", "Друид", "Колдун", "Чародей", "Артефактор"]
                    if class_name in spellcaster_classes:
                        cur.execute("""
                            INSERT INTO class_spells (class_id, spell_id, is_available)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (class_id, spell_id) DO NOTHING
                        """, (class_id, spell_id, True))
            else:
                logger.warning(f"  ⚠️ Не удалось добавить заклинание '{spell['name']}'")

        conn.commit()

    # Подсчёт
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM spells")
        count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM class_spells")
        links = cur.fetchone()[0]

    logger.info(f"✅ Перенесено заклинаний: {count}, связей: {links}")


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

        # Очистка таблиц
        response = input("Очистить таблицы перед заполнением? (yes/no): ").strip().lower()
        if response == 'yes':
            clear_tables(conn)

        # Последовательный перенос
        migrate_races(conn)
        migrate_classes(conn)
        migrate_backgrounds(conn)
        migrate_weapon_masteries(conn)
        migrate_fighting_styles(conn)
        migrate_invocations(conn)
        migrate_spells(conn)

        print("\n" + "=" * 60)
        logger.info("🎉 БАЗА ДАННЫХ УСПЕШНО НАПОЛНЕНА!")
        print("=" * 60)

        # Показываем статистику
        with conn.cursor() as cur:
            stats = [
                ("races", "Рас"), ("subraces", "Подрас"), ("classes", "Классов"),
                ("backgrounds", "Предысторий"), ("spells", "Заклинаний"),
                ("weapon_masteries", "Оружейных приёмов"), ("fighting_styles", "Боевых стилей"),
                ("invocations", "Возваний")
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