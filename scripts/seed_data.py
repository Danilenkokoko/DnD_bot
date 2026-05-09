#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_data.py - Наполнение базы данных D&D 5.5e (2024) данными
Запуск: python seed_data.py
Скрипт не зависит от внешних файлов — все данные встроены в код.
Включает: расы, классы, предыстории, заклинания, оружие, броню,
снаряжение классов, оружейные приёмы, боевые стили.
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
        "subraces": {
            "Облачный великан": {"trait": "Телепортация", "description": "Может телепортироваться на короткое расстояние"},
            "Огненный великан": {"trait": "Огненный урон", "description": "Добавляет огненный урон к атакам"},
            "Ледяной великан": {"trait": "Холод + замедление", "description": "Наносит холод и замедляет цель"},
            "Холмовой великан": {"trait": "Опрокидывание", "description": "Может опрокинуть врага"},
            "Каменный великан": {"trait": "Снижение урона", "description": "Получает сопротивление к урону"},
            "Штормовой великан": {"trait": "Ответный урон", "description": "При попадании возвращает урон молнией/громом"}
        }
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
        # PHB 2024: у Драконорожденного нет подрас. Цвет дракона выбирается
        # отдельным шагом Draconic Ancestry (см. proceed_after_race в
        # handlers/character_handlers.py). Раньше здесь были «псевдо-подрасы»
        # — они приводили к двойному запросу цвета дракона.
        "subraces": {}
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
        "subraces": {
            "Инфернальный": {"trait": "Огонь + атаки", "description": "Усиливает огненные атаки"},
            "Бездны": {"trait": "Яд + контроль", "description": "Добавляет ядовитый урон и контроль"},
            "Хтонический": {"trait": "Некротика + ослабление", "description": "Наносит некротический урон и ослабляет"}
        }
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
        "hit_die": 12, "primary_stats": ["STR"], "saving_throws": ["STR", "CON"],
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

    # PHB 2024 — количество заклинаний на L1 для каждого класса.
    # cantrips_count: сколько заговоров игрок выбирает при создании.
    # spells_count_level1: сколько заклинаний 1 уровня (известных/в книге).
    SPELL_COUNTS_L1 = {
        "Артефактор": (2, 2),
        "Бард":       (2, 4),
        "Жрец":       (3, 2),
        "Друид":      (2, 2),
        "Колдун":     (2, 2),
        "Паладин":    (0, 2),
        "Следопыт":   (0, 2),
        "Чародей":    (4, 2),
        "Волшебник":  (3, 6),
        # Не-кастеры: 0/0
        "Варвар": (0, 0), "Воин": (0, 0), "Монах": (0, 0), "Плут": (0, 0),
    }

    with conn.cursor() as cur:
        for class_name, class_data in CLASSES_DATA.items():
            cantrips_l1, level1_l1 = SPELL_COUNTS_L1.get(class_name, (0, 0))
            cur.execute("""
                INSERT INTO classes (name, hit_die, primary_stats, saving_throws,
                                     skill_choices, description, is_spellcaster,
                                     spellcasting_ability, cantrips_count, spells_count_level1)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    hit_die = EXCLUDED.hit_die,
                    primary_stats = EXCLUDED.primary_stats,
                    saving_throws = EXCLUDED.saving_throws,
                    skill_choices = EXCLUDED.skill_choices,
                    description = EXCLUDED.description,
                    cantrips_count = EXCLUDED.cantrips_count,
                    spells_count_level1 = EXCLUDED.spells_count_level1
                RETURNING id
            """, (
                class_name,
                class_data["hit_die"],
                json.dumps(class_data["primary_stats"]),
                json.dumps(class_data["saving_throws"]),
                class_data["skill_choices"],
                class_data["description"],
                class_data["is_spellcaster"],
                class_data["spellcasting_ability"],
                cantrips_l1,
                level1_l1,
            ))
            class_id = cur.fetchone()[0]
            logger.info(f"  ✅ Класс '{class_name}' (ID: {class_id})  [cantrips={cantrips_l1}, lvl1={level1_l1}]")

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
    {"name": "Рассечение", "trigger": "Попадание по цели", "effect": "Нанести урон ещё одной цели рядом", "weapons": "глефа, двуручный топор, алебарда, двуручный молот, двуручный меч"},
    {"name": "Задевание", "trigger": "Промах атакой", "effect": "Нанести частичный урон", "weapons": "двуручный меч, двуручный топор, алебарда, двуручный молот, глефа"},
    {"name": "Быстрый удар", "trigger": "Атака лёгким оружием", "effect": "Дополнительная атака", "weapons": "кинжал, короткий меч, серп, ручной топор, лёгкий молот, ятаган"},
    {"name": "Отталкивание", "trigger": "Попадание", "effect": "Оттолкнуть цель на 10 футов", "weapons": "боевой молот, моргенштерн, копьё, пика"},
    {"name": "Ослабление", "trigger": "Попадание", "effect": "Помеха на следующую атаку цели", "weapons": "булава, боевой посох, цеп, моргенштерн, дубинка"},
    {"name": "Замедление", "trigger": "Попадание", "effect": "Снизить скорость цели на 10 футов", "weapons": "арбалеты, длинный лук, копьё, рапира, боевой молот"},
    {"name": "Сбивание", "trigger": "Попадание", "effect": "Сбить цель с ног", "weapons": "копьё, пика, алебарда, боевой молот, боевой топор, длинный меч"},
    {"name": "Преимущество", "trigger": "Попадание", "effect": "Преимущество на следующую атаку", "weapons": "рапира, короткий меч, длинный лук, ручной арбалет, кинжал, ятаган"},
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
# 7. ДАННЫЕ ОРУЖИЯ И СВЯЗЕЙ (С ДЕТАЛЬНЫМИ ПРИЁМАМИ)
# =========================================================

WEAPONS_DATA = [
    # ===== ПРОСТОЕ ОРУЖИЕ =====
    {
        "name": "Кинжал", "category": "simple", "damage_dice": "1d4", "damage_type": "piercing",
        "properties": ["легкое", "метательное"], "suitable_masteries": ["Быстрый удар", "Преимущество"],
        "detailed_masteries": [
            {"name": "Пригвоздить", "description": "При попадании кинжалом можете пригвоздить существо к стене", "optimal": True},
            {"name": "Скрытый клинок", "description": "Можете спрятать кинжал и совершить атаку с преимуществом", "optimal": False}
        ]
    },
    {
        "name": "Серп", "category": "simple", "damage_dice": "1d4", "damage_type": "slashing",
        "properties": ["легкое"], "suitable_masteries": ["Быстрый удар"],
        "detailed_masteries": []
    },
    {
        "name": "Дубина", "category": "simple", "damage_dice": "1d4", "damage_type": "bludgeoning",
        "properties": ["легкое"], "suitable_masteries": ["Ослабление"],
        "detailed_masteries": [
            {"name": "Оглушение", "description": "Действием можете оглушить гуманоида", "optimal": True}
        ]
    },
    {
        "name": "Копьё", "category": "simple", "damage_dice": "1d6", "damage_type": "piercing",
        "properties": ["метательное", "универсальное"], "suitable_masteries": ["Ослабление", "Отталкивание", "Замедление", "Сбивание"],
        "detailed_masteries": []
    },
    {
        "name": "Булава", "category": "simple", "damage_dice": "1d6", "damage_type": "bludgeoning",
        "properties": [], "suitable_masteries": ["Ослабление"],
        "detailed_masteries": [
            {"name": "Сильный удар", "description": "Цель не может добавлять Ловкость к КД", "optimal": True}
        ]
    },
    {
        "name": "Боевой посох", "category": "simple", "damage_dice": "1d6", "damage_type": "bludgeoning",
        "properties": ["универсальное"], "suitable_masteries": ["Ослабление"],
        "detailed_masteries": [
            {"name": "Прыжок", "description": "Можете использовать посох, чтобы прыгать дальше", "optimal": True}
        ]
    },
    {
        "name": "Лёгкий молот", "category": "simple", "damage_dice": "1d4", "damage_type": "bludgeoning",
        "properties": ["легкое", "метательное"], "suitable_masteries": ["Быстрый удар"],
        "detailed_masteries": [
            {"name": "Оглушающий удар", "description": "Цель становится недееспособной", "optimal": True}
        ]
    },
    {
        "name": "Метательное копьё", "category": "simple", "damage_dice": "1d6", "damage_type": "piercing",
        "properties": ["метательное"], "suitable_masteries": [],
        "detailed_masteries": [
            {"name": "Устрашающая точность", "description": "Цель становится испуганной", "optimal": True}
        ]
    },
    {
        "name": "Ручной топор", "category": "simple", "damage_dice": "1d6", "damage_type": "slashing",
        "properties": ["легкое", "метательное"], "suitable_masteries": ["Быстрый удар"],
        "detailed_masteries": [
            {"name": "Пригвоздить", "description": "Можете пригвоздить существо к стене", "optimal": True}
        ]
    },
    {
        "name": "Короткий лук", "category": "simple", "damage_dice": "1d6", "damage_type": "piercing",
        "properties": ["двуручное", "дальнобойное"], "suitable_masteries": ["Замедление", "Преимущество"],
        "detailed_masteries": [
            {"name": "Пригвоздить", "description": "Можете пригвоздить существо к стене", "optimal": True},
            {"name": "Отвлекающий выстрел", "description": "Даёте союзнику преимущество", "optimal": False}
        ]
    },

    # ===== ВОИНСКОЕ ОРУЖИЕ =====
    {
        "name": "Длинный меч", "category": "martial", "damage_dice": "1d8", "damage_type": "slashing",
        "properties": ["универсальное"], "suitable_masteries": ["Ослабление", "Сбивание", "Гибкость"],
        "detailed_masteries": [
            {"name": "Скрестить клинки", "description": "Реакцией можете парировать атаку", "optimal": True},
            {"name": "Внезапный удар", "description": "Можете ударить рукоятью, давая преимущество", "optimal": False}
        ]
    },
    {
        "name": "Рапира", "category": "martial", "damage_dice": "1d8", "damage_type": "piercing",
        "properties": ["изящное"], "suitable_masteries": ["Замедление", "Преимущество", "Гибкость"],
        "detailed_masteries": [
            {"name": "Удар левой рукой", "description": "С кинжалом даёт +1к4 к КД", "optimal": True},
            {"name": "Скрестить клинки", "description": "Реакцией можете парировать атаку", "optimal": True}
        ]
    },
    {
        "name": "Боевой топор", "category": "martial", "damage_dice": "1d8", "damage_type": "slashing",
        "properties": ["универсальное"], "suitable_masteries": ["Сбивание", "Гибкость"],
        "detailed_masteries": [
            {"name": "Сокрушительный удар", "description": "КД цели снижается на 1", "optimal": True}
        ]
    },
    {
        "name": "Двуручный меч", "category": "martial", "damage_dice": "2d6", "damage_type": "slashing",
        "properties": ["двуручное", "тяжёлое"], "suitable_masteries": ["Рассечение", "Задевание"],
        "detailed_masteries": [
            {"name": "Атака по дуге", "description": "Можете атаковать двух существ одновременно", "optimal": True},
            {"name": "Упор в землю", "description": "Бонус к спасброску от вынужденного перемещения", "optimal": True}
        ]
    },
    {
        "name": "Двуручный топор", "category": "martial", "damage_dice": "1d12", "damage_type": "slashing",
        "properties": ["двуручное", "тяжёлое"], "suitable_masteries": ["Рассечение", "Задевание"],
        "detailed_masteries": []
    },
    {
        "name": "Алебарда", "category": "martial", "damage_dice": "1d10", "damage_type": "slashing",
        "properties": ["двуручное", "тяжёлое", "досягаемость"], "suitable_masteries": ["Рассечение", "Задевание", "Сбивание"],
        "detailed_masteries": [
            {"name": "Натиск", "description": "Можете оттолкнуть до двух существ", "optimal": True},
            {"name": "Подсечка", "description": "Можете сбить противника с ног", "optimal": True}
        ]
    },
    {
        "name": "Глефа", "category": "martial", "damage_dice": "1d10", "damage_type": "slashing",
        "properties": ["двуручное", "тяжёлое", "досягаемость"], "suitable_masteries": ["Рассечение", "Задевание"],
        "detailed_masteries": [
            {"name": "Обезоруживающее парирование", "description": "Можете обезоружить противника", "optimal": True},
            {"name": "Подсечка", "description": "Можете сбить противника с ног", "optimal": True}
        ]
    },
    {
        "name": "Пика", "category": "martial", "damage_dice": "1d10", "damage_type": "piercing",
        "properties": ["двуручное", "тяжёлое", "досягаемость"], "suitable_masteries": ["Отталкивание", "Сбивание"],
        "detailed_masteries": [
            {"name": "Фаланга", "description": "Атаки с преимуществом рядом с другими обладателями пик", "optimal": True},
            {"name": "Упреждение", "description": "Можете атаковать движущегося к вам врага", "optimal": True}
        ]
    },
    {
        "name": "Большая дубина", "category": "martial", "damage_dice": "1d8", "damage_type": "bludgeoning",
        "properties": ["двуручное"], "suitable_masteries": ["Отталкивание"],
        "detailed_masteries": []
    },
    {
        "name": "Военный молот", "category": "martial", "damage_dice": "1d8", "damage_type": "bludgeoning",
        "properties": ["универсальное"], "suitable_masteries": ["Отталкивание", "Замедление", "Сбивание", "Гибкость"],
        "detailed_masteries": [
            {"name": "Сильный удар", "description": "Цель не может добавлять Ловкость к КД", "optimal": True}
        ]
    },
    {
        "name": "Короткий меч", "category": "martial", "damage_dice": "1d6", "damage_type": "piercing",
        "properties": ["изящное", "легкое"], "suitable_masteries": ["Быстрый удар", "Преимущество"],
        "detailed_masteries": [
            {"name": "Ближний бой", "description": "Можете атаковать после захвата", "optimal": True},
            {"name": "Внезапный удар", "description": "Можете ударить рукоятью, давая преимущество", "optimal": False}
        ]
    },
    {
        "name": "Моргенштерн", "category": "martial", "damage_dice": "1d8", "damage_type": "piercing",
        "properties": [], "suitable_masteries": ["Отталкивание", "Ослабление", "Гибкость"],
        "detailed_masteries": [
            {"name": "Ребролом", "description": "Ошеломляет гуманоида", "optimal": True}
        ]
    },
    {
        "name": "Цеп", "category": "martial", "damage_dice": "1d8", "damage_type": "bludgeoning",
        "properties": [], "suitable_masteries": ["Ослабление"],
        "detailed_masteries": [
            {"name": "Цепная удавка", "description": "Можете схватить существо", "optimal": True},
            {"name": "Обвить щит", "description": "Игнорирует бонус КД от щита", "optimal": True}
        ]
    },
    {
        "name": "Кнут", "category": "martial", "damage_dice": "1d4", "damage_type": "slashing",
        "properties": ["изящное", "досягаемость"], "suitable_masteries": ["Замедление"],
        "detailed_masteries": [
            {"name": "Щелчок", "description": "Можете испугать зверя", "optimal": True},
            {"name": "Петля", "description": "Можете опутать существо", "optimal": True}
        ]
    },
    {
        "name": "Длинный лук", "category": "martial", "damage_dice": "1d8", "damage_type": "piercing",
        "properties": ["двуручное", "тяжёлое", "дальнобойное"], "suitable_masteries": ["Замедление", "Преимущество"],
        "detailed_masteries": [
            {"name": "Пригвоздить", "description": "Можете пригвоздить существо к стене", "optimal": True},
            {"name": "Отвлекающий выстрел", "description": "Даёте союзнику преимущество", "optimal": False}
        ]
    },
    {
        "name": "Ятаган", "category": "martial", "damage_dice": "1d6", "damage_type": "slashing",
        "properties": ["изящное"], "suitable_masteries": ["Быстрый удар", "Преимущество"],
        "detailed_masteries": [
            {"name": "Кровавая рана", "description": "Цель получает 1к6 рубящего урона в начале каждого хода", "optimal": True}
        ]
    },
    {
        "name": "Ручной арбалет", "category": "martial", "damage_dice": "1d6", "damage_type": "piercing",
        "properties": ["лёгкое", "дальнобойное"], "suitable_masteries": ["Преимущество"],
        "detailed_masteries": [
            {"name": "Быстрый выстрел", "description": "Бонусным действием можно совершить атаку с помехой", "optimal": True}
        ]
    },
    {
        "name": "Тяжёлый арбалет", "category": "martial", "damage_dice": "1d10", "damage_type": "piercing",
        "properties": ["двуручное", "тяжёлое", "дальнобойное"], "suitable_masteries": ["Замедление"],
        "detailed_masteries": [
            {"name": "Терпеливый выстрел", "description": "Если не двигались, атака с преимуществом", "optimal": True}
        ]
    },
    {
        "name": "Лёгкий арбалет", "category": "simple", "damage_dice": "1d8", "damage_type": "piercing",
        "properties": ["двуручное", "дальнобойное"], "suitable_masteries": ["Замедление"],
        "detailed_masteries": []
    },
    {
        "name": "Праща", "category": "simple", "damage_dice": "1d4", "damage_type": "bludgeoning",
        "properties": ["дальнобойное"], "suitable_masteries": [],
        "detailed_masteries": [
            {"name": "Камнем по голове", "description": "Цель становится ошеломлённой", "optimal": True}
        ]
    },
    {
        "name": "Дротик", "category": "simple", "damage_dice": "1d4", "damage_type": "piercing",
        "properties": ["метательное", "дальнобойное"], "suitable_masteries": [],
        "detailed_masteries": []
    }
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
                INSERT INTO weapons (name, category, damage_dice, damage_type, properties, suitable_masteries, detailed_masteries)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            """, (
                weapon["name"], weapon["category"], weapon["damage_dice"],
                weapon["damage_type"], json.dumps(weapon["properties"]),
                json.dumps(weapon["suitable_masteries"]),
                json.dumps(weapon["detailed_masteries"])
            ))
            result = cur.fetchone()
            if result:
                weapon_id_map[weapon["name"]] = result[0]
                logger.info(f"  ✅ Оружие '{weapon['name']}'")

        # Связываем оружие с классами
        # Воин — всё оружие
        if "Воин" in class_id_map:
            for weapon_name, weapon_id in weapon_id_map.items():
                cur.execute("""
                    INSERT INTO class_weapons (class_id, weapon_id)
                    VALUES (%s, %s)
                    ON CONFLICT (class_id, weapon_id) DO NOTHING
                """, (class_id_map["Воин"], weapon_id))
            logger.info(f"    • Воин → всё оружие ({len(weapon_id_map)} шт.)")

        # Паладин — всё оружие
        if "Паладин" in class_id_map:
            for weapon_name, weapon_id in weapon_id_map.items():
                cur.execute("""
                    INSERT INTO class_weapons (class_id, weapon_id)
                    VALUES (%s, %s)
                    ON CONFLICT (class_id, weapon_id) DO NOTHING
                """, (class_id_map["Паладин"], weapon_id))
            logger.info(f"    • Паладин → всё оружие")

        # Варвар — всё оружие
        if "Варвар" in class_id_map:
            for weapon_name, weapon_id in weapon_id_map.items():
                cur.execute("""
                    INSERT INTO class_weapons (class_id, weapon_id)
                    VALUES (%s, %s)
                    ON CONFLICT (class_id, weapon_id) DO NOTHING
                """, (class_id_map["Варвар"], weapon_id))
            logger.info(f"    • Варвар → всё оружие")

        # Следопыт — простое + лёгкое воинское
        ranger_weapons = ["Короткий меч", "Кинжал", "Лёгкий молот", "Метательное копьё",
                          "Короткий лук", "Длинный лук", "Ятаган", "Ручной топор"]
        if "Следопыт" in class_id_map:
            for weapon in WEAPONS_DATA:
                if weapon["category"] == "simple" and weapon["name"] in weapon_id_map:
                    cur.execute("""
                        INSERT INTO class_weapons (class_id, weapon_id)
                        VALUES (%s, %s)
                        ON CONFLICT (class_id, weapon_id) DO NOTHING
                    """, (class_id_map["Следопыт"], weapon_id_map[weapon["name"]]))
            for weapon_name in ranger_weapons:
                if weapon_name in weapon_id_map:
                    cur.execute("""
                        INSERT INTO class_weapons (class_id, weapon_id)
                        VALUES (%s, %s)
                        ON CONFLICT (class_id, weapon_id) DO NOTHING
                    """, (class_id_map["Следопыт"], weapon_id_map[weapon_name]))
            logger.info(f"    • Следопыт → простое и лёгкое воинское оружие")

        # Плут — простое + избранное воинское
        rogue_weapons = ["Рапира", "Короткий лук", "Длинный меч", "Короткий меч", "Кинжал"]
        if "Плут" in class_id_map:
            for weapon in WEAPONS_DATA:
                if weapon["category"] == "simple" and weapon["name"] in weapon_id_map:
                    cur.execute("""
                        INSERT INTO class_weapons (class_id, weapon_id)
                        VALUES (%s, %s)
                        ON CONFLICT (class_id, weapon_id) DO NOTHING
                    """, (class_id_map["Плут"], weapon_id_map[weapon["name"]]))
            for weapon_name in rogue_weapons:
                if weapon_name in weapon_id_map:
                    cur.execute("""
                        INSERT INTO class_weapons (class_id, weapon_id)
                        VALUES (%s, %s)
                        ON CONFLICT (class_id, weapon_id) DO NOTHING
                    """, (class_id_map["Плут"], weapon_id_map[weapon_name]))
            logger.info(f"    • Плут → простое и избранное воинское оружие")

        conn.commit()
    logger.info(f"✅ Перенесено оружия: {len(WEAPONS_DATA)}")


# =========================================================
# 8. ДАННЫЕ БРОНИ
# =========================================================

ARMOR_DATA = [
    {"name": "Стёганый доспех", "ac_base": 11, "ac_modifier": "dex"},
    {"name": "Кожаный доспех", "ac_base": 11, "ac_modifier": "dex"},
    {"name": "Проклёпанный кожаный доспех", "ac_base": 12, "ac_modifier": "dex"},
    {"name": "Шкурный доспех", "ac_base": 12, "ac_modifier": "dex_max2"},
    {"name": "Кольчужная рубаха", "ac_base": 13, "ac_modifier": "dex_max2"},
    {"name": "Кираса", "ac_base": 14, "ac_modifier": "dex_max2"},
    {"name": "Чешуйчатый доспех", "ac_base": 14, "ac_modifier": "dex_max2"},
    {"name": "Полулаты", "ac_base": 15, "ac_modifier": "dex_max2"},
    {"name": "Кольчужный доспех", "ac_base": 14, "ac_modifier": "none"},
    {"name": "Колечный доспех", "ac_base": 14, "ac_modifier": "none"},
    {"name": "Пластинчатый доспех", "ac_base": 15, "ac_modifier": "none"},
    {"name": "Латный доспех", "ac_base": 18, "ac_modifier": "none"},
]


def migrate_armor(conn):
    """Перенос брони (без щита)"""
    logger.info("\n" + "=" * 50)
    logger.info("8. ПЕРЕНОС БРОНИ")
    logger.info("=" * 50)

    with conn.cursor() as cur:
        for armor in ARMOR_DATA:
            cur.execute("""
                INSERT INTO armor (name, ac_base, ac_modifier)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (armor["name"], armor["ac_base"], armor["ac_modifier"]))
            logger.info(f"  ✅ Броня '{armor['name']}'")

        conn.commit()
    logger.info(f"✅ Перенесено брони: {len(ARMOR_DATA)}")


# =========================================================
# 9. ДАННЫЕ СНАРЯЖЕНИЯ ПО КЛАССАМ (БЕЗ ЩИТА)
# =========================================================

CLASS_EQUIPMENT_DATA = [
    {"class": "Артефактор", "choice": None, "armor": "Проклёпанный кожаный доспех",
     "weapon": "Кинжал", "secondary": None,
     "other": "Воровские инструменты, Инструменты ремонтника, Набор исследователя подземелий", "coins": 16},
    {"class": "Бард", "choice": None, "armor": "Кожаный доспех",
     "weapon": "Кинжал", "secondary": "Кинжал", "other": "Музыкальный инструмент, Набор артиста", "coins": 19},
    {"class": "Варвар", "choice": None, "armor": None,
     "weapon": "Секира", "secondary": None, "other": "4 Одноручных топора, Набор путешественника", "coins": 15},
    {"class": "Воин", "choice": "A", "armor": "Кольчужный доспех",
     "weapon": "Двуручный меч", "secondary": "Цеп", "other": "8 Метательных копий, Набор исследователя подземелий", "coins": 4},
    {"class": "Воин", "choice": "B", "armor": "Проклёпанный кожаный доспех",
     "weapon": "Ятаган", "secondary": "Короткий меч",
     "other": "Длинный лук, 20 Стрел, Колчан, Набор исследователя подземелий", "coins": 11},
    {"class": "Волшебник", "choice": None, "armor": None,
     "weapon": "Кинжал", "secondary": "Кинжал",
     "other": "Магическая фокусировка (Боевой посох), Мантия, Книга заклинаний, Набор учёного", "coins": 5},
    {"class": "Друид", "choice": None, "armor": "Кожаный доспех",
     "weapon": "Серп", "secondary": None,
     "other": "Друидическая фокусировка (Боевой посох), Набор путешественника, Набор травника", "coins": 9},
    {"class": "Жрец", "choice": None, "armor": "Кольчужная рубаха",
     "weapon": "Булава", "secondary": None, "other": "Священный символ, Набор священника", "coins": 7},
    {"class": "Колдун", "choice": None, "armor": "Кожаный доспех",
     "weapon": "Серп", "secondary": "Кинжал",
     "other": "Кинжал, Магическая фокусировка (сфера), Книга (оккультные знания), Набор учёного", "coins": 15},
    {"class": "Монах", "choice": None, "armor": None,
     "weapon": "Копьё", "secondary": None,
     "other": "5 Кинжалов, Ремесленные инструменты или Музыкальный инструмент, Набор путешественника", "coins": 11},
    {"class": "Паладин", "choice": None, "armor": "Кольчужный доспех",
     "weapon": "Длинный меч", "secondary": None,
     "other": "6 Метательных копий, Священный символ, Набор священника", "coins": 9},
    {"class": "Плут", "choice": None, "armor": "Кожаный доспех",
     "weapon": "Кинжал", "secondary": "Короткий меч",
     "other": "Кинжал, Короткий лук, 20 Стрел, Колчан, Воровские инструменты, Набор взломщика", "coins": 8},
    {"class": "Следопыт", "choice": None, "armor": "Проклёпанный кожаный доспех",
     "weapon": "Ятаган", "secondary": "Короткий меч",
     "other": "Длинный лук, 20 Стрел, Колчан, Друидическая фокусировка (веточка омелы), Набор путешественника", "coins": 7},
    {"class": "Чародей", "choice": None, "armor": None,
     "weapon": "Копьё", "secondary": "Кинжал",
     "other": "Кинжал, Магическая фокусировка (кристалл), Набор исследователя подземелий", "coins": 28},
]


def migrate_class_equipment(conn, class_id_map):
    """Перенос снаряжения по классам (без щита)"""
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
                logger.info(f"  ✅ Снаряжение для '{eq['class']}' (вариант {eq['choice'] if eq['choice'] else 'стандарт'})")

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
    {"name": "Брызги кислоты", "level": 0, "is_cantrip": True, "description": "Кислотная струя, 1к6 урона."},
    {"name": "Луч холода", "level": 0, "is_cantrip": True, "description": "Луч холода, 1к8 урона."},
    {"name": "Огненный снаряд", "level": 0, "is_cantrip": True, "description": "Огненная стрела, 1к10 урона."},
    {"name": "Терновый кнут", "level": 0, "is_cantrip": True, "description": "Кнут из шипов, 1к6 урона."},
    {"name": "Погребальный звон", "level": 0, "is_cantrip": True, "description": "Некротический урон, 1к8."},
    {"name": "Злая насмешка", "level": 0, "is_cantrip": True, "description": "Психический урон, помеха атаке."},
    {"name": "Леденящее прикосновение", "level": 0, "is_cantrip": True, "description": "Некротический урон, цель не лечится."},
    {"name": "Малая иллюзия", "level": 0, "is_cantrip": True, "description": "Создаёте простую иллюзию."},
    {"name": "Электрошок", "level": 0, "is_cantrip": True, "description": "Электрический разряд, 1к6 урона."},
    {"name": "Чародейский выброс", "level": 0, "is_cantrip": True, "description": "Силовой снаряд, 1к6 урона."},
    {"name": "Дубинка", "level": 0, "is_cantrip": True, "description": "Оружие становится магическим, 1к8 урона."},
    {"name": "Слово сияния", "level": 0, "is_cantrip": True, "description": "Луч света, 1к6 урона."},
    {"name": "Расщепление разума", "level": 0, "is_cantrip": True, "description": "Психический урон, 1к6."},
    {"name": "Меткий удар", "level": 0, "is_cantrip": True, "description": "Атака заклинанием, 1к6 урона."},
    {"name": "Звёздный светлячок", "level": 0, "is_cantrip": True, "description": "Светящаяся сфера."},
    {"name": "Сопротивление", "level": 0, "is_cantrip": True, "description": "Даёт сопротивление урону."},
    {"name": "Уход за умирающим", "level": 0, "is_cantrip": True, "description": "Стабилизирует умирающего."},
    {"name": "Ядовитые брызги", "level": 0, "is_cantrip": True, "description": "Ядовитый спрей, 1к12 урона."},
    {"name": "Элементализм", "level": 0, "is_cantrip": True, "description": "Мелкий эффект стихии."},
    {"name": "Искусство друидов", "level": 0, "is_cantrip": True, "description": "Природный эффект."},
    {"name": "Чудотворство", "level": 0, "is_cantrip": True, "description": "Малый божественный знак."},
    {"name": "Наставление", "level": 0, "is_cantrip": True, "description": "+1к4 к проверке."},
    {"name": "Свет", "level": 0, "is_cantrip": True, "description": "Создаёте свет."},
    {"name": "Пляшущие огоньки", "level": 0, "is_cantrip": True, "description": "4 огонька света."},
    {"name": "Защита от оружия", "level": 0, "is_cantrip": True, "description": "Преимущество к КД."},
    {"name": "Дружба", "level": 0, "is_cantrip": True, "description": "Преимущество на Харизму."},
    {"name": "Сотворение пламени", "level": 0, "is_cantrip": True, "description": "Создаёте пламя в руке."},

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
    {"name": "Волшебная стрела", "level": 1, "is_cantrip": False, "description": "Три стрелы силы, 1к4+1 каждая."},
    {"name": "Огненные ладони", "level": 1, "is_cantrip": False, "description": "Конус огня, 3к6 урона."},
    {"name": "Ледяной кинжал", "level": 1, "is_cantrip": False, "description": "Ледяной кинжал, 2к6 урона."},
    {"name": "Луч болезни", "level": 1, "is_cantrip": False, "description": "Луч некротической энергии, 2к8 урона."},
    {"name": "Псевдожизнь", "level": 1, "is_cantrip": False, "description": "Получаете временные хиты."},
    {"name": "Доспехи мага", "level": 1, "is_cantrip": False, "description": "Базовый КД = 13 + DEX."},
    {"name": "Огонь фей", "level": 1, "is_cantrip": False, "description": "Цель светится, атаки по ней с преимуществом."},
    {"name": "Намасливание", "level": 1, "is_cantrip": False, "description": "Создаёте скользкое пятно."},
    {"name": "Падение пёрышком", "level": 1, "is_cantrip": False, "description": "Медленное падение."},
    {"name": "Поспешное отступление", "level": 1, "is_cantrip": False, "description": "Действие Рывок как бонусное."},
    {"name": "Скороход", "level": 1, "is_cantrip": False, "description": "Удваивает скорость цели."},
    {"name": "Убежище", "level": 1, "is_cantrip": False, "description": "Атаки по цели с помехой."},
    {"name": "Сигнал тревоги", "level": 1, "is_cantrip": False, "description": "Защищает область от вторжения."},
    {"name": "Очищение пищи и питья", "level": 1, "is_cantrip": False, "description": "Очищает еду и воду."},
    {"name": "Обнаружение добра и зла", "level": 1, "is_cantrip": False, "description": "Чувствуете присутствие существ."},
    {"name": "Обнаружение болезней и ядов", "level": 1, "is_cantrip": False, "description": "Обнаруживает болезни и яды."},
    {"name": "Лечащее слово", "level": 1, "is_cantrip": False, "description": "Лечит на 1к4 + модификатор на расстоянии."},
    {"name": "Нанесение ран", "level": 1, "is_cantrip": False, "description": "Касание, 3к10 некротического урона."},
    {"name": "Направляющий снаряд", "level": 1, "is_cantrip": False, "description": "Снаряд света, 4к6 урона."},
    {"name": "Щит веры", "level": 1, "is_cantrip": False, "description": "+2 к КД цели."},
    {"name": "Героизм", "level": 1, "is_cantrip": False, "description": "Цель невосприимчива к страху, получает временные хиты."},
    {"name": "Приказ", "level": 1, "is_cantrip": False, "description": "Однословный приказ."},
    {"name": "Порча", "level": 1, "is_cantrip": False, "description": "Проклинает цель."},
    {"name": "Жуткий смех Таши", "level": 1, "is_cantrip": False, "description": "Цель падает и смеётся."},
    {"name": "Диссонирующий шёпот", "level": 1, "is_cantrip": False, "description": "Психический урон, цель убегает."},
    {"name": "Невидимый слуга", "level": 1, "is_cantrip": False, "description": "Создаёте невидимого слугу."},
    {"name": "Безмолвный образ", "level": 1, "is_cantrip": False, "description": "Создаёте визуальную иллюзию."},
    {"name": "Иллюзорные письмена", "level": 1, "is_cantrip": False, "description": "Скрываете сообщение."},
    {"name": "Опознание", "level": 1, "is_cantrip": False, "description": "Узнаёте свойства магического предмета."},
    {"name": "Парящий диск Тензера", "level": 1, "is_cantrip": False, "description": "Создаёте парящий диск для груза."},
    {"name": "Обретение фамильяра", "level": 1, "is_cantrip": False, "description": "Призываете духа-помощника."},
    {"name": "Сотворение или уничтожение воды", "level": 1, "is_cantrip": False, "description": "Создаёте или уничтожаете воду."},
    {"name": "Туманное облако", "level": 1, "is_cantrip": False, "description": "Создаёте облако тумана."},
    {"name": "Добряника", "level": 1, "is_cantrip": False, "description": "Создаёте 4 магических ягоды."},
    {"name": "Очарование личности", "level": 1, "is_cantrip": False, "description": "Очаровываете гуманоида."},
    {"name": "Понимание языков", "level": 1, "is_cantrip": False, "description": "Понимаете все языки."},
    {"name": "Палящая кара", "level": 1, "is_cantrip": False, "description": "Огненный урон при атаке."},
    {"name": "Гневная кара", "level": 1, "is_cantrip": False, "description": "Урон силой при атаке."},
    {"name": "Громовая кара", "level": 1, "is_cantrip": False, "description": "Громовой урон при атаке."},
    {"name": "Вызов на дуэль", "level": 1, "is_cantrip": False, "description": "Принуждаете врага атаковать вас."},
    {"name": "Ведьмин снаряд", "level": 1, "is_cantrip": False, "description": "Луч силы, 1к10 урона."},
    {"name": "Вспышка чаропламени", "level": 1, "is_cantrip": False, "description": "Луч силы, 2к8 урона."},
    {"name": "Руки Хадара", "level": 1, "is_cantrip": False, "description": "Психический урон, цель не реагирует."},
    {"name": "Адское возмездие", "level": 1, "is_cantrip": False, "description": "Огненный урон при получении урона."},
    {"name": "Оберегающий разряд", "level": 1, "is_cantrip": False, "description": "Союзник получает сопротивление урону."},
    {"name": "Град шипов", "level": 1, "is_cantrip": False, "description": "Создаёте зону шипов."},
    {"name": "Опутывающий удар", "level": 1, "is_cantrip": False, "description": "Опутываете цель."},
    {"name": "Дружба с животными", "level": 1, "is_cantrip": False, "description": "Очаровываете животное."},
    {"name": "Сверкающие брызги", "level": 1, "is_cantrip": False, "description": "Ослепляете существ."},
    {"name": "Усыпление", "level": 1, "is_cantrip": False, "description": "Погружаете существ в сон."},
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
    "Волшебник": ["Волшебная рука", "Вспышка света", "Починка", "Сообщение", "Удар грома", "Фокус-покус",
                  "Руководство", "Священное пламя", "Мистический залп", "Вдохновение насмешки", "Брызги кислоты",
                  "Луч холода", "Огненный снаряд", "Терновый кнут", "Погребальный звон", "Леденящее прикосновение",
                  "Малая иллюзия", "Электрошок", "Лечение ран", "Громовая волна", "Благословение", "Маскировка",
                  "Щит", "Хроматическая сфера", "Сон", "Обнаружение магии", "Прыжок", "Разговор с животными",
                  "Опутывание", "Метка охотника", "Доспехи Агатиса", "Волшебная стрела", "Огненные ладони",
                  "Ледяной кинжал", "Луч болезни", "Псевдожизнь", "Доспехи мага", "Огонь фей", "Намасливание",
                  "Падение пёрышком", "Поспешное отступление", "Скороход", "Убежище", "Сигнал тревоги",
                  "Обнаружение добра и зла", "Обнаружение болезней и ядов", "Лечащее слово", "Нанесение ран",
                  "Направляющий снаряд", "Щит веры", "Приказ", "Порча", "Жуткий смех Таши", "Диссонирующий шёпот",
                  "Невидимый слуга", "Безмолвный образ", "Иллюзорные письмена", "Опознание", "Парящий диск Тензера",
                  "Обретение фамильяра", "Сотворение или уничтожение воды", "Туманное облако", "Добряника",
                  "Очарование личности", "Понимание языков", "Палящая кара", "Гневная кара"],
    "Бард": ["Вдохновение насмешки", "Удар грома", "Сообщение", "Фокус-покус", "Волшебная рука", "Вспышка света",
             "Починка", "Руководство", "Лечение ран", "Сон", "Благословение", "Маскировка", "Громовая волна",
             "Щит", "Хроматическая сфера", "Обнаружение магии", "Прыжок", "Лечащее слово", "Диссонирующий шёпот",
             "Жуткий смех Таши", "Невидимый слуга", "Очарование личности", "Понимание языков", "Порча", "Приказ"],
    "Жрец": ["Руководство", "Священное пламя", "Вспышка света", "Починка", "Свет", "Сопротивление",
             "Уход за умирающим", "Чудотворство", "Лечение ран", "Благословение", "Обнаружение магии",
             "Громовая волна", "Лечащее слово", "Нанесение ран", "Направляющий снаряд", "Щит веры", "Приказ",
             "Порча", "Убежище", "Обнаружение добра и зла", "Обнаружение болезней и ядов", "Сотворение или уничтожение воды"],
    "Друид": ["Руководство", "Фокус-покус", "Удар грома", "Терновый кнут", "Дубинка", "Сотворение пламени",
              "Искусство друидов", "Починка", "Сообщение", "Сопротивление", "Элементализм", "Лечение ран",
              "Опутывание", "Разговор с животными", "Прыжок", "Громовая волна", "Добряника", "Лечащее слово",
              "Огонь фей", "Туманное облако", "Сотворение или уничтожение воды", "Обнаружение магии",
              "Обнаружение болезней и ядов", "Очарование личности"],
    "Колдун": ["Мистический залп", "Волшебная рука", "Удар грома", "Леденящее прикосновение", "Погребальный звон",
               "Расщепление разума", "Гекс", "Доспехи Агатиса", "Щит", "Сон", "Ведьмин снаряд", "Адское возмездие",
               "Руки Хадара", "Понимание языков", "Порча", "Очарование личности", "Обнаружение магии"],
    "Чародей": ["Волшебная рука", "Вспышка света", "Удар грома", "Брызги кислоты", "Луч холода", "Огненный снаряд",
                "Починка", "Сообщение", "Фокус-покус", "Чародейский выброс", "Электрошок", "Лечение ран",
                "Щит", "Хроматическая сфера", "Сон", "Обнаружение магии", "Доспехи мага", "Огненные ладони",
                "Ледяной кинжал", "Волшебная стрела", "Лечащее слово", "Маскировка", "Падение пёрышком",
                "Прыжок", "Псевдожизнь", "Туманное облако", "Усыпление"],
    "Паладин": ["Лечение ран", "Божественная кара", "Благословение", "Гневная кара", "Громовая кара", "Палящая кара",
                "Приказ", "Вызов на дуэль", "Героизм", "Обнаружение магии", "Обнаружение добра и зла"],
    "Следопыт": ["Метка охотника", "Лечение ран", "Прыжок", "Добряника", "Опутывание", "Опутывающий удар",
                 "Разговор с животными", "Туманное облако", "Обнаружение магии", "Обнаружение болезней и ядов",
                 "Град шипов", "Скороход", "Сигнал тревоги"],
    "Артефактор": ["Починка", "Вспышка света", "Волшебная рука", "Лечение ран", "Щит", "Обнаружение магии",
                   "Маскировка", "Огонь фей", "Падение пёрышком", "Прыжок", "Псевдожизнь", "Скороход", "Убежище"],
}


# Полные описания (PHB 2024-механики, оригинальный текст бота).
# Если для заклинания нет ключа — используется короткое описание из SPELLS_DATA.
try:
    from scripts.spell_descriptions_full import SPELL_DESCRIPTIONS_2024
except ImportError:
    SPELL_DESCRIPTIONS_2024 = {}


def migrate_spells(conn, class_id_map):
    """Перенос заклинаний, связей с классами и рекомендаций"""
    logger.info("\n" + "=" * 50)
    logger.info("10. ПЕРЕНОС ЗАКЛИНАНИЙ")
    logger.info("=" * 50)

    spell_id_map = {}

    with conn.cursor() as cur:
        for spell in SPELLS_DATA:
            # Берём полное описание из spell_descriptions_full.py (PHB 2024).
            # Если ключа нет — fallback на короткое описание из SPELLS_DATA.
            full_desc = SPELL_DESCRIPTIONS_2024.get(spell["name"], spell["description"])
            cur.execute("""
                INSERT INTO spells (name, level, is_cantrip, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """, (spell["name"], spell["level"], spell["is_cantrip"], full_desc))

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

                logger.info(f"    • {class_name} → рекомендовано {len(spells.get('cantrips', [])) + len(spells.get('level1', []))} заклинаний")

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