# db.py
import psycopg2
import os
import logging
from dotenv import load_dotenv
from psycopg2.extras import Json, RealDictCursor
from contextlib import contextmanager
from typing import Dict, Any, List, Optional

# ---------------- CONFIG ----------------
load_dotenv(encoding="utf-8")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": (os.getenv("DB_PASSWORD") or "").strip(),
    "host": os.getenv("DB_HOST"),
    "port": 5432
}

# Проверка env
for key, value in DB_CONFIG.items():
    if not value:
        raise ValueError(f"❌ Не задана переменная окружения: {key}")


# ---------------- CONNECTION ----------------
@contextmanager
def get_connection():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Ошибка БД: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()


# ---------------- INIT ----------------
def init_database():
    """Создаёт таблицы если они не существуют"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Таблица персонажей
            cur.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,

                    -- Основная информация
                    name VARCHAR(100) NOT NULL,
                    race VARCHAR(50) NOT NULL,
                    class_name VARCHAR(50) NOT NULL,
                    level INTEGER DEFAULT 1,
                    background VARCHAR(100),
                    backstory TEXT,
                    image_file_id VARCHAR(255),

                    -- Характеристики
                    str INTEGER DEFAULT 10,
                    dex INTEGER DEFAULT 10,
                    con INTEGER DEFAULT 10,
                    int INTEGER DEFAULT 10,
                    wis INTEGER DEFAULT 10,
                    cha INTEGER DEFAULT 10,

                    -- Боевые характеристики
                    hp INTEGER DEFAULT 0,
                    ac INTEGER DEFAULT 10,

                    -- Особенности
                    race_traits JSONB DEFAULT '[]',
                    class_features JSONB DEFAULT '[]',

                    -- Навыки и инструменты
                    skills JSONB DEFAULT '[]',
                    tools JSONB DEFAULT '[]',

                    -- Снаряжение и магия
                    equipment JSONB DEFAULT '[]',
                    spells JSONB DEFAULT '[]',

                    -- Данные предыстории
                    background_trait VARCHAR(255),
                    background_skills JSONB DEFAULT '[]',
                    background_tools VARCHAR(255),
                    background_equipment_choice VARCHAR(1),

                    -- Системные поля
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица предысторий
            cur.execute("""
                CREATE TABLE IF NOT EXISTS backgrounds (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    characteristics JSONB NOT NULL,
                    trait VARCHAR(255) NOT NULL,
                    skills JSONB NOT NULL,
                    tools VARCHAR(255),
                    equipment_a TEXT NOT NULL,
                    equipment_b TEXT NOT NULL,
                    description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Индексы
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_characters_user_id 
                ON characters(user_id)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_characters_name 
                ON characters(name)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_backgrounds_name 
                ON backgrounds(name)
            """)

            logger.info("✅ Таблицы characters и backgrounds готовы")

            # Заполняем таблицу предысторий начальными данными
            seed_backgrounds()


def seed_backgrounds():
    """Заполняет таблицу backgrounds начальными данными"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Проверяем, пуста ли таблица
            cur.execute("SELECT COUNT(*) FROM backgrounds")
            count = cur.fetchone()[0]

            if count == 0:
                backgrounds_data = get_default_backgrounds_for_db()

                for bg in backgrounds_data:
                    cur.execute("""
                        INSERT INTO backgrounds (name, characteristics, trait, skills, tools, equipment_a, equipment_b, description)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (name) DO NOTHING
                    """, (
                        bg["name"],
                        Json(bg["characteristics"]),
                        bg["trait"],
                        Json(bg["skills"]),
                        bg["tools"],
                        bg["equipment_a"],
                        bg["equipment_b"],
                        bg["description"]
                    ))

                logger.info(f"✅ Добавлено {len(backgrounds_data)} предысторий в базу данных")


def get_default_backgrounds_for_db() -> List[Dict[str, Any]]:
    """Возвращает список предысторий для заполнения БД"""
    return [
        {
            "name": "Артист",
            "characteristics": ["Сила", "Ловкость", "Харизма"],
            "trait": "Музыкант",
            "skills": ["Акробатика", "Выступление"],
            "tools": "Музыкальный инструмент",
            "equipment_a": "Музыкальный инструмент (выбранный выше), 2 Костюма, Зеркало, Духи, Дорожная одежда, 11 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы провели большую часть своей юности следуя за бродячими ярмарками и карнавалами, иногда работая на музыкантов и акробатов в обмен на уроки."
        },
        {
            "name": "Мудрец",
            "characteristics": ["Телосложение", "Интеллект", "Мудрость"],
            "trait": "Посвящённый в магию (Волшебник)",
            "skills": ["История", "Тайная магия"],
            "tools": "Инструменты каллиграфа",
            "equipment_a": "Боевой посох, Инструменты каллиграфа, Книга (история), Пергамент (8 листов), Мантия, 8 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы провели свои юные годы, путешествуя между поместьями и монастырями, выполняя для них работу и оказывая услуги в обмен на доступ к их библиотекам."
        },
        {
            "name": "Преступник",
            "characteristics": ["Ловкость", "Телосложение", "Интеллект"],
            "trait": "Бдительный",
            "skills": ["Ловкость рук", "Скрытность"],
            "tools": "Воровские инструменты",
            "equipment_a": "2 Кинжала, Воровские инструменты, Ломик, 2 Кошеля, Дорожная одежда, 16 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы зарабатывали на жизнь в тёмных переулках, срезая кошельки и проникая в лавки."
        },
        {
            "name": "Стражник",
            "characteristics": ["Сила", "Интеллект", "Мудрость"],
            "trait": "Бдительный",
            "skills": ["Атлетика", "Восприятие"],
            "tools": "Игровой набор",
            "equipment_a": "Копьё, Лёгкий арбалет, 20 Болтов, Игровой набор (выбранный выше), Закрытый фонарь, Кандалы, Колчан, Дорожная одежда, 12 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Когда вы только вспоминаете бесчисленные часы, проведённые на посту в башне, у вас начинают ныть ноги."
        },
        {
            "name": "Бродяга",
            "characteristics": ["Ловкость", "Мудрость", "Харизма"],
            "trait": "Везучий",
            "skills": ["Проницательность", "Скрытность"],
            "tools": "Воровские инструменты",
            "equipment_a": "2 Кинжала, Воровские инструменты, Игровой набор (любой), Спальник, 2 Кошеля, Дорожная одежда, 16 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы выросли на улицах в окружении таких же злосчастных отбросов общества; с кем-то из них вы дружили, с кем-то соперничали."
        },
        {
            "name": "Отшельник",
            "characteristics": ["Телосложение", "Мудрость", "Харизма"],
            "trait": "Лекарь",
            "skills": ["Медицина", "Религия"],
            "tools": "Набор травника",
            "equipment_a": "Боевой посох, Набор травника, Спальник, Книга (философия), Лампа, Масло (3 фляги), Дорожная одежда, 16 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы провели свои ранние годы в одиночестве, в хижине или монастыре, далеко за пределами ближайшего поселения."
        },
        {
            "name": "Проводник",
            "characteristics": ["Ловкость", "Телосложение", "Мудрость"],
            "trait": "Посвящённый в магию (Друид)",
            "skills": ["Выживание", "Скрытность"],
            "tools": "Инструменты картографа",
            "equipment_a": "Короткий лук, 20 Стрел, Инструменты картографа, Спальник, Колчан, Палатка, Дорожная одежда, 3 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы вошли в возраст под открытым небом, вдали от обжитых земель. Домом вам было то место, где вы решили расстелить свой спальник."
        },
        {
            "name": "Торговец",
            "characteristics": ["Телосложение", "Интеллект", "Харизма"],
            "trait": "Везучий",
            "skills": ["Убеждение", "Обращение с животными"],
            "tools": "Инструменты навигатора",
            "equipment_a": "Инструменты навигатора, 2 Кошеля, Дорожная одежда, 22 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы были учеником торговца, хозяина каравана или лавочника, и так изучили основы коммерции."
        },
        {
            "name": "Дворянин",
            "characteristics": ["Сила", "Интеллект", "Харизма"],
            "trait": "Одарённый",
            "skills": ["История", "Убеждение"],
            "tools": "Игровой набор",
            "equipment_a": "Игровой набор (выбранный выше), Отличная одежда, Духи, 29 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы выросли в замке, окруженные богатством, властью и привилегиями. Ваша семья, из мелких аристократов, позаботилась о том, чтобы вы получили первоклассное образование."
        },
        {
            "name": "Писарь",
            "characteristics": ["Ловкость", "Интеллект", "Мудрость"],
            "trait": "Одарённый",
            "skills": ["Восприятие", "Расследование"],
            "tools": "Инструменты каллиграфа",
            "equipment_a": "Инструменты каллиграфа, Отличная одежда, Лампа, Масло (3 фляги), Пергамент (12 листов), 23 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Годы вашего становления прошли в скриптории, в государственном учреждении или в монастыре, посвященном сохранению знаний."
        },
        {
            "name": "Ремесленник",
            "characteristics": ["Сила", "Ловкость", "Интеллект"],
            "trait": "Мастеровой",
            "skills": ["Расследование", "Убеждение"],
            "tools": "Инструменты кузнеца",
            "equipment_a": "Ремесленные инструменты (выбранные выше), 2 Кошеля, Дорожная одежда, 32 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы начали мыть полы и прилавки в мастерской ремесленника за несколько медяков в день, как только окрепли настолько, что могли носить ведро."
        },
        {
            "name": "Фермер",
            "characteristics": ["Сила", "Телосложение", "Мудрость"],
            "trait": "Крепкий",
            "skills": ["Природа", "Обращение с животными"],
            "tools": "Инструменты плотника",
            "equipment_a": "Серп, Инструменты плотника, Комплект целителя, Железный горшок, Лопата, Дорожная одежда, 30 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы выросли в близости с землёй. За годы ухода за животными и работы в поле вы выработали терпение и крепкое здоровье."
        },
        {
            "name": "Моряк",
            "characteristics": ["Сила", "Ловкость", "Мудрость"],
            "trait": "Дебошир",
            "skills": ["Акробатика", "Восприятие"],
            "tools": "Инструменты навигатора",
            "equipment_a": "Кинжал, Инструменты навигатора, Верёвка, Дорожная одежда, 20 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы жили на морских просторах, ветер дул вам в спину, и палуба покачивалась под вашими ногами."
        },
        {
            "name": "Послушник",
            "characteristics": ["Интеллект", "Мудрость", "Харизма"],
            "trait": "Посвящённый в магию (Жрец)",
            "skills": ["Проницательность", "Религия"],
            "tools": "Инструменты каллиграфа",
            "equipment_a": "Инструменты каллиграфа, Книга (молитвенник), Священный символ, Пергамент (10 листов), Мантия, 8 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы посвятили себя служению в храме, среди городских улиц или в уединении священной рощи."
        },
        {
            "name": "Солдат",
            "characteristics": ["Сила", "Ловкость", "Телосложение"],
            "trait": "Неистово атакующий",
            "skills": ["Атлетика", "Запугивание"],
            "tools": "Игровой набор",
            "equipment_a": "Копьё, Короткий лук, 20 Стрел, Игровой набор (выбранный выше), Комплект целителя, Колчан, Дорожная одежда, 14 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Вы начали готовиться к войне, как только достигли зрелости, и вы почти не помните свою жизнь до того, как взяли в руки оружие."
        },
        {
            "name": "Шарлатан",
            "characteristics": ["Ловкость", "Телосложение", "Харизма"],
            "trait": "Одарённый",
            "skills": ["Ловкость рук", "Обман"],
            "tools": "Набор для фальсификации",
            "equipment_a": "Набор для фальсификации, Костюм, Отличная одежда, 15 ЗМ",
            "equipment_b": "50 ЗМ",
            "description": "Совсем мало времени прошло после того, как вы стали достаточно взрослы, чтобы заказывать эль — а у вас уже появилось любимое место в каждой таверне."
        }
    ]


# ---------------- CREATE ----------------
def save_character(
        user_id: int,
        name: str,
        race: str,
        class_name: str,
        background: str,
        backstory: str,
        stats: Dict[str, int],
        hp: int,
        ac: int,
        race_traits: List[str],
        class_features: List[str],
        skills: List[str],
        tools: List[str],
        equipment: List[str],
        spells: List[str],
        background_trait: str = "",
        background_skills: List[str] = None,
        background_tools: str = "",
        background_equipment_choice: str = "A",
        image_file_id: str = None,
        level: int = 1
) -> int:
    """
    Сохраняет персонажа в базу данных

    Returns:
        int: ID созданного персонажа
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO characters (
                    user_id, name, race, class_name, level,
                    background, backstory, image_file_id,
                    str, dex, con, int, wis, cha,
                    hp, ac,
                    race_traits, class_features,
                    skills, tools, equipment, spells,
                    background_trait, background_skills, background_tools, background_equipment_choice
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id, name, race, class_name, level,
                background, backstory, image_file_id,
                stats.get("STR", 10), stats.get("DEX", 10), stats.get("CON", 10),
                stats.get("INT", 10), stats.get("WIS", 10), stats.get("CHA", 10),
                hp, ac,
                Json(race_traits), Json(class_features),
                Json(skills), Json(tools), Json(equipment), Json(spells),
                background_trait, Json(background_skills or []), background_tools, background_equipment_choice
            ))

            char_id = cur.fetchone()[0]
            logger.info(f"✅ Персонаж сохранён: ID={char_id}, Name={name}")
            return char_id


# ---------------- READ ----------------
def get_user_characters(user_id: int) -> List[Dict[str, Any]]:
    """Возвращает всех персонажей пользователя"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, race, class_name, level, background, hp, ac, created_at
                FROM characters
                WHERE user_id = %s
                ORDER BY id DESC
            """, (user_id,))
            return cur.fetchall()


def get_character_by_id(char_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает персонажа по ID"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM characters WHERE id = %s",
                (char_id,)
            )
            return cur.fetchone()


def get_character_by_id_and_user(char_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает персонажа по ID и ID пользователя (для проверки прав)"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM characters WHERE id = %s AND user_id = %s",
                (char_id, user_id)
            )
            return cur.fetchone()


# ---------------- BACKGROUNDS FROM DB ----------------
def get_all_backgrounds_from_db() -> List[Dict[str, Any]]:
    """Получает все предыстории из БД"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT name, description FROM backgrounds ORDER BY name")
            return cur.fetchall()


def get_background_from_db(background_name: str) -> Optional[Dict[str, Any]]:
    """Получает предысторию по имени из БД"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM backgrounds WHERE name = %s", (background_name,))
            return cur.fetchone()


def get_background_names() -> List[str]:
    """Возвращает список названий предысторий"""
    backgrounds = get_all_backgrounds_from_db()
    return [bg["name"] for bg in backgrounds]


# ---------------- UPDATE ----------------
def update_character_level(char_id: int, new_level: int) -> bool:
    """Обновляет уровень персонажа"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE characters 
                SET level = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_level, char_id))
            return cur.rowcount > 0


def update_character_hp(char_id: int, new_hp: int) -> bool:
    """Обновляет HP персонажа"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE characters 
                SET hp = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_hp, char_id))
            return cur.rowcount > 0


def update_character_stats(char_id: int, stats: Dict[str, int]) -> bool:
    """Обновляет характеристики персонажа"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE characters 
                SET str = %s, dex = %s, con = %s, int = %s, wis = %s, cha = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                stats.get("STR", 10), stats.get("DEX", 10), stats.get("CON", 10),
                stats.get("INT", 10), stats.get("WIS", 10), stats.get("CHA", 10),
                char_id
            ))
            return cur.rowcount > 0


def update_character_backstory(char_id: int, backstory: str) -> bool:
    """Обновляет историю персонажа"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE characters 
                SET backstory = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (backstory, char_id))
            return cur.rowcount > 0


def update_character_image(char_id: int, image_file_id: str) -> bool:
    """Обновляет картинку персонажа"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE characters 
                SET image_file_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (image_file_id, char_id))
            return cur.rowcount > 0


# ---------------- DELETE ----------------
def delete_character(char_id: int, user_id: int) -> bool:
    """Удаляет персонажа (только если он принадлежит пользователю)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM characters
                WHERE id = %s AND user_id = %s
            """, (char_id, user_id))

            deleted = cur.rowcount > 0
            if deleted:
                logger.info(f"🗑️ Персонаж удалён: ID={char_id}, User={user_id}")
            return deleted


# ---------------- STATS ----------------
def get_user_characters_count(user_id: int) -> int:
    """Возвращает количество персонажей пользователя"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM characters WHERE user_id = %s",
                (user_id,)
            )
            return cur.fetchone()[0]


# ---------------- MIGRATION ----------------
def migrate_database():
    """Миграция существующей базы данных (добавление новых полей)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Проверяем и добавляем новые колонки, если их нет
            new_columns = [
                ("background", "VARCHAR(100)"),
                ("backstory", "TEXT"),
                ("image_file_id", "VARCHAR(255)"),
                ("race_traits", "JSONB DEFAULT '[]'"),
                ("class_features", "JSONB DEFAULT '[]'"),
                ("tools", "JSONB DEFAULT '[]'"),
                ("background_trait", "VARCHAR(255)"),
                ("background_skills", "JSONB DEFAULT '[]'"),
                ("background_tools", "VARCHAR(255)"),
                ("background_equipment_choice", "VARCHAR(1)"),
                ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ]

            for col_name, col_type in new_columns:
                try:
                    cur.execute(f"""
                        ALTER TABLE characters 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                    """)
                    logger.info(f"✅ Добавлена колонка: {col_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось добавить {col_name}: {e}")

            conn.commit()
            logger.info("✅ Миграция базы данных завершена")


# ---------------- TEST ----------------
if __name__ == "__main__":
    print("=== Тест базы данных ===\n")

    # Инициализация
    init_database()

    # Миграция (для существующих баз)
    migrate_database()

    # Проверка предысторий
    backgrounds = get_all_backgrounds_from_db()
    print(f"📚 Загружено предысторий: {len(backgrounds)}")
    for bg in backgrounds[:5]:
        print(f"   - {bg['name']}")

    # Тестовые данные
    test_stats = {"STR": 15, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 8}

    # Сохранение тестового персонажа
    char_id = save_character(
        user_id=123456789,
        name="Тестовый Герой",
        race="Человек",
        class_name="Воин",
        background="Солдат",
        backstory="Был солдатом, участвовал в великой войне...",
        stats=test_stats,
        hp=12,
        ac=16,
        race_traits=["Универсальность человечества"],
        class_features=["Боевой стиль", "Второе дыхание"],
        skills=["Атлетика", "Запугивание"],
        tools=["Игровой набор"],
        equipment=["Longsword", "Shield", "Chain Mail"],
        spells=[],
        background_trait="Неистово атакующий",
        background_skills=["Атлетика", "Запугивание"],
        background_tools="Игровой набор",
        background_equipment_choice="A"
    )

    print(f"\n✅ Создан персонаж с ID: {char_id}")

    # Получение персонажа
    char = get_character_by_id(char_id)
    if char:
        print(f"📖 Имя: {char['name']}")
        print(f"🎭 Класс: {char['class_name']}")
        print(f"🧝 Раса: {char['race']}")
        print(f"📜 Предыстория: {char['background']}")
        print(f"❤️ HP: {char['hp']}, 🛡️ AC: {char['ac']}")

    # Очистка
    delete_character(char_id, 123456789)
    print("\n🗑️ Тестовый персонаж удалён")

    print("\n✅ Модуль db.py готов к использованию!")