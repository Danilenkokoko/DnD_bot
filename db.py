# db.py
"""
D&D 5.5e (2024) Database Module
Модуль для работы с PostgreSQL базой данных
Поддерживает все таблицы для D&D 5.5e, включая оружие, заклинания, броню и снаряжение классов
"""

import psycopg2
import os
import logging
import json
from dotenv import load_dotenv
from psycopg2.extras import Json, RealDictCursor
from contextlib import contextmanager
from typing import Dict, Any, List, Optional

# ---------------- CONFIG ----------------
load_dotenv(encoding="utf-8")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "DND_DB"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": (os.getenv("DB_PASSWORD") or "").strip(),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "connect_timeout": 5
}

# Проверка env
for key, value in DB_CONFIG.items():
    if key == "connect_timeout":
        continue
    if not value:
        raise ValueError(f"❌ Не задана переменная окружения: {key}")

logger.info(f"📊 Настройки БД: host={DB_CONFIG['host']}, dbname={DB_CONFIG['dbname']}, user={DB_CONFIG['user']}")


# ---------------- CONNECTION ----------------
@contextmanager
def get_connection():
    """Создаёт подключение к базе данных"""
    conn = None
    try:
        logger.debug("🔄 Попытка подключения к БД...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        logger.debug("✅ Подключение к БД установлено")
        yield conn
        conn.commit()
    except psycopg2.OperationalError as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Ошибка БД: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()
            logger.debug("🔌 Соединение с БД закрыто")


# ---------------- INIT DATABASE ----------------
def init_database():
    """Создаёт все таблицы если они не существуют (D&D 5.5e)"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # ===== 1. ТАБЛИЦА РАС =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS races (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) UNIQUE NOT NULL,
                        speed INTEGER DEFAULT 30,
                        size VARCHAR(20) DEFAULT 'Средний',
                        description TEXT,
                        image_path VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица races готова")

                # ===== 2. ТАБЛИЦА ПОДРАС =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS subraces (
                        id SERIAL PRIMARY KEY,
                        race_id INTEGER NOT NULL REFERENCES races(id) ON DELETE CASCADE,
                        name VARCHAR(50) NOT NULL,
                        trait VARCHAR(255),
                        description TEXT,
                        extra_speed INTEGER DEFAULT 0,
                        extra_traits JSONB DEFAULT '[]',
                        UNIQUE(race_id, name)
                    )
                """)
                logger.info("✅ Таблица subraces готова")

                # ===== 3. ТАБЛИЦА КЛАССОВ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS classes (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) UNIQUE NOT NULL,
                        hit_die INTEGER NOT NULL CHECK (hit_die IN (6, 8, 10, 12)),
                        primary_stats JSONB NOT NULL,
                        saving_throws JSONB NOT NULL,
                        skill_choices INTEGER DEFAULT 2,
                        description TEXT,
                        image_path VARCHAR(255),
                        is_spellcaster BOOLEAN DEFAULT FALSE,
                        spellcasting_ability VARCHAR(3),
                        cantrips_count INTEGER DEFAULT 0,
                        spells_count_level1 INTEGER DEFAULT 0,
                        masteries_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица classes готова")

                # ===== 4. ТАБЛИЦА ПОДКЛАССОВ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS subclasses (
                        id SERIAL PRIMARY KEY,
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        name VARCHAR(50) NOT NULL,
                        level_acquired INTEGER DEFAULT 1,
                        description TEXT,
                        features JSONB DEFAULT '[]',
                        UNIQUE(class_id, name)
                    )
                """)
                logger.info("✅ Таблица subclasses готова")

                # ===== 5. ТАБЛИЦА ПРЕДЫСТОРИЙ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS backgrounds (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) UNIQUE NOT NULL,
                        characteristic1 VARCHAR(3) NOT NULL,
                        characteristic2 VARCHAR(3) NOT NULL,
                        characteristic3 VARCHAR(3) NOT NULL,
                        trait VARCHAR(255) NOT NULL,
                        skills JSONB NOT NULL,
                        tools VARCHAR(255),
                        equipment_a TEXT NOT NULL,
                        equipment_b TEXT NOT NULL,
                        description TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица backgrounds готова")

                # ===== 6. ТАБЛИЦА ЗАКЛИНАНИЙ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS spells (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        level INTEGER DEFAULT 0,
                        school VARCHAR(50),
                        casting_time VARCHAR(50),
                        range VARCHAR(50),
                        components VARCHAR(50),
                        duration VARCHAR(100),
                        description TEXT,
                        is_cantrip BOOLEAN DEFAULT FALSE,
                        is_ritual BOOLEAN DEFAULT FALSE,
                        requires_concentration BOOLEAN DEFAULT FALSE,
                        category VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица spells готова")

                # ===== 7. СВЯЗЬ КЛАССОВ С ЗАКЛИНАНИЯМИ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS class_spells (
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        spell_id INTEGER NOT NULL REFERENCES spells(id) ON DELETE CASCADE,
                        is_available BOOLEAN DEFAULT TRUE,
                        PRIMARY KEY (class_id, spell_id)
                    )
                """)
                logger.info("✅ Таблица class_spells готова")

                # ===== 8. ТАБЛИЦА РЕКОМЕНДОВАННЫХ ЗАКЛИНАНИЙ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS recommended_spells (
                        id SERIAL PRIMARY KEY,
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        spell_id INTEGER NOT NULL REFERENCES spells(id) ON DELETE CASCADE,
                        is_cantrip BOOLEAN DEFAULT FALSE,
                        priority INTEGER DEFAULT 1,
                        UNIQUE(class_id, spell_id)
                    )
                """)
                logger.info("✅ Таблица recommended_spells готова")

                # ===== 9. ТАБЛИЦА ОРУЖИЯ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS weapons (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL UNIQUE,
                        category VARCHAR(20) NOT NULL,
                        damage_dice VARCHAR(10),
                        damage_type VARCHAR(20),
                        properties JSONB DEFAULT '[]',
                        suitable_masteries JSONB DEFAULT '[]',
                        detailed_masteries JSONB DEFAULT '[]',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица weapons готова")

                # ===== 10. ДОСТУПНОЕ ОРУЖИЕ ПО КЛАССАМ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS class_weapons (
                        id SERIAL PRIMARY KEY,
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        weapon_category VARCHAR(20),
                        weapon_id INTEGER REFERENCES weapons(id) ON DELETE CASCADE,
                        UNIQUE(class_id, weapon_id)
                    )
                """)
                logger.info("✅ Таблица class_weapons готова")

                # ===== 11. ТАБЛИЦА ОРУЖЕЙНЫХ ПРИЁМОВ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS weapon_masteries (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL UNIQUE,
                        trigger_condition TEXT NOT NULL,
                        effect TEXT NOT NULL,
                        weapons TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица weapon_masteries готова")

                # ===== 12. ТАБЛИЦА БРОНИ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS armor (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL UNIQUE,
                        ac_base INTEGER NOT NULL,
                        ac_modifier VARCHAR(10) DEFAULT 'dex',
                        has_shield BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица armor готова")

                # ===== 13. ТАБЛИЦА СНАРЯЖЕНИЯ ПО КЛАССАМ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS class_equipment (
                        id SERIAL PRIMARY KEY,
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        choice VARCHAR(1),
                        armor VARCHAR(50),
                        weapon VARCHAR(50),
                        secondary_weapon VARCHAR(50),
                        other_items TEXT,
                        coins INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(class_id, choice)
                    )
                """)
                logger.info("✅ Таблица class_equipment готова")

                # ===== 14. ТАБЛИЦА БОЕВЫХ СТИЛЕЙ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS fighting_styles (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL UNIQUE,
                        description TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица fighting_styles готова")

                # ===== 15. ДОСТУПНЫЕ БОЕВЫЕ СТИЛИ ПО КЛАССАМ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS class_fighting_styles (
                        id SERIAL PRIMARY KEY,
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        style_id INTEGER NOT NULL REFERENCES fighting_styles(id) ON DELETE CASCADE,
                        UNIQUE(class_id, style_id)
                    )
                """)
                logger.info("✅ Таблица class_fighting_styles готова")

                # ===== 16. ТАБЛИЦА ТАИНСТВЕННЫХ ВОЗВАНИЙ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS invocations (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        level_required INTEGER DEFAULT 1,
                        effect TEXT NOT NULL,
                        requires_pact_boon BOOLEAN DEFAULT FALSE,
                        pact_boon_type VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица invocations готова")

                # ===== 17. ТАБЛИЦА ПЕРСОНАЖЕЙ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS characters (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        race_id INTEGER REFERENCES races(id),
                        subrace_id INTEGER REFERENCES subraces(id),
                        class_id INTEGER REFERENCES classes(id),
                        subclass_id INTEGER REFERENCES subclasses(id),
                        background_id INTEGER REFERENCES backgrounds(id),
                        level INTEGER DEFAULT 1,
                        experience INTEGER DEFAULT 0,
                        str INTEGER DEFAULT 10,
                        dex INTEGER DEFAULT 10,
                        con INTEGER DEFAULT 10,
                        int INTEGER DEFAULT 10,
                        wis INTEGER DEFAULT 10,
                        cha INTEGER DEFAULT 10,
                        hp INTEGER DEFAULT 0,
                        ac INTEGER DEFAULT 10,
                        speed INTEGER DEFAULT 30,
                        selected_skills JSONB DEFAULT '[]',
                        selected_masteries JSONB DEFAULT '[]',
                        selected_fighting_style VARCHAR(50),
                        selected_invocations JSONB DEFAULT '[]',
                        selected_spells JSONB DEFAULT '[]',
                        selected_weapon VARCHAR(50),
                        selected_armor VARCHAR(50),
                        selected_equipment_choice VARCHAR(1),
                        backstory TEXT,
                        image_file_id VARCHAR(255),
                        alignment VARCHAR(20) DEFAULT 'Нейтральное',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица characters готова")

                # ===== ИНДЕКСЫ =====
                cur.execute("CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_characters_class_id ON characters(class_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_characters_race_id ON characters(race_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_characters_background_id ON characters(background_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_class_spells_class_id ON class_spells(class_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_class_spells_spell_id ON class_spells(spell_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_subraces_race_id ON subraces(race_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_subclasses_class_id ON subclasses(class_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_recommended_spells_class_id ON recommended_spells(class_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_weapons_name ON weapons(name)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_class_weapons_class_id ON class_weapons(class_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_class_fighting_styles_class_id ON class_fighting_styles(class_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_armor_name ON armor(name)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_class_equipment_class_id ON class_equipment(class_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_spells_category ON spells(category)")
                logger.info("✅ Все индексы созданы")

                conn.commit()

    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации таблиц: {e}")
        raise


# =========================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ПЕРСОНАЖАМИ
# =========================================================

def save_character(
        user_id: int,
        name: str,
        race_id: Optional[int] = None,
        subrace_id: Optional[int] = None,
        class_id: Optional[int] = None,
        subclass_id: Optional[int] = None,
        background_id: Optional[int] = None,
        level: int = 1,
        experience: int = 0,
        stats: Optional[Dict[str, int]] = None,
        hp: int = 0,
        ac: int = 10,
        speed: int = 30,
        selected_skills: Optional[List[str]] = None,
        selected_masteries: Optional[List[str]] = None,
        selected_fighting_style: Optional[str] = None,
        selected_invocations: Optional[List[str]] = None,
        selected_spells: Optional[List[str]] = None,
        selected_weapon: Optional[str] = None,
        selected_armor: Optional[str] = None,
        selected_equipment_choice: str = "A",
        backstory: str = "",
        image_file_id: Optional[str] = None,
        alignment: str = "Нейтральное"
) -> int:
    """Сохраняет персонажа в базу данных"""
    if stats is None:
        stats = {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10}
    if selected_skills is None:
        selected_skills = []
    if selected_masteries is None:
        selected_masteries = []
    if selected_invocations is None:
        selected_invocations = []
    if selected_spells is None:
        selected_spells = []

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO characters (
                    user_id, name, race_id, subrace_id, class_id, subclass_id,
                    background_id, level, experience, str, dex, con, int, wis, cha,
                    hp, ac, speed, selected_skills, selected_masteries,
                    selected_fighting_style, selected_invocations, selected_spells,
                    selected_weapon, selected_armor, selected_equipment_choice, backstory, image_file_id, alignment
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id, name, race_id, subrace_id, class_id, subclass_id,
                background_id, level, experience,
                stats.get("STR", 10), stats.get("DEX", 10), stats.get("CON", 10),
                stats.get("INT", 10), stats.get("WIS", 10), stats.get("CHA", 10),
                hp, ac, speed,
                Json(selected_skills), Json(selected_masteries),
                selected_fighting_style, Json(selected_invocations), Json(selected_spells),
                selected_weapon, selected_armor, selected_equipment_choice, backstory, image_file_id, alignment
            ))

            char_id = cur.fetchone()[0]
            logger.info(f"✅ Персонаж сохранён: ID={char_id}, Name={name}")
            return char_id


def get_user_characters(user_id: int) -> List[Dict[str, Any]]:
    """Возвращает всех персонажей пользователя"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT c.id, c.name, c.level, c.hp, c.ac, c.created_at,
                       cls.name as class_name, r.name as race_name, bg.name as background_name
                FROM characters c
                LEFT JOIN classes cls ON c.class_id = cls.id
                LEFT JOIN races r ON c.race_id = r.id
                LEFT JOIN backgrounds bg ON c.background_id = bg.id
                WHERE c.user_id = %s
                ORDER BY c.id DESC
            """, (user_id,))
            return cur.fetchall()


def get_character_by_id(char_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает полную информацию о персонаже по ID"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT c.*, 
                       cls.name as class_name, cls.hit_die, cls.primary_stats, cls.saving_throws,
                       r.name as race_name, r.speed as race_speed, r.size as race_size,
                       bg.name as background_name, bg.trait as background_trait
                FROM characters c
                LEFT JOIN classes cls ON c.class_id = cls.id
                LEFT JOIN races r ON c.race_id = r.id
                LEFT JOIN backgrounds bg ON c.background_id = bg.id
                WHERE c.id = %s
            """, (char_id,))
            return cur.fetchone()


def get_character_by_id_and_user(char_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает персонажа по ID и ID пользователя"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT c.*, 
                       cls.name as class_name,
                       r.name as race_name,
                       bg.name as background_name
                FROM characters c
                LEFT JOIN classes cls ON c.class_id = cls.id
                LEFT JOIN races r ON c.race_id = r.id
                LEFT JOIN backgrounds bg ON c.background_id = bg.id
                WHERE c.id = %s AND c.user_id = %s
            """, (char_id, user_id))
            return cur.fetchone()


def delete_character(char_id: int, user_id: int) -> bool:
    """Удаляет персонажа"""
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


def get_user_characters_count(user_id: int) -> int:
    """Возвращает количество персонажей пользователя"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM characters WHERE user_id = %s", (user_id,))
            return cur.fetchone()[0]


def get_total_characters_count() -> int:
    """Возвращает общее количество персонажей в базе"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM characters")
            return cur.fetchone()[0]


# =========================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ПРЕДЫСТОРИЯМИ
# =========================================================

def get_all_backgrounds_from_db() -> List[Dict[str, Any]]:
    """Получает все предыстории из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name, description FROM backgrounds ORDER BY name")
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить предыстории: {e}")
        return []


def get_background_from_db(background_name: str) -> Optional[Dict[str, Any]]:
    """Получает предысторию по имени из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, characteristic1, characteristic2, characteristic3,
                           trait, skills, tools, equipment_a, equipment_b, description
                    FROM backgrounds WHERE name = %s
                """, (background_name,))
                return cur.fetchone()
    except Exception as e:
        logger.warning(f"Не удалось загрузить предысторию {background_name}: {e}")
        return None


def get_background_names() -> List[str]:
    """Возвращает список названий предысторий"""
    backgrounds = get_all_backgrounds_from_db()
    return [bg["name"] for bg in backgrounds]


# =========================================================
# ФУНКЦИИ ДЛЯ МИГРАЦИИ
# =========================================================

def migrate_database_v2():
    """Миграция существующей базы данных до версии 2"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Добавляем новые колонки в таблицу classes
                new_columns = [
                    ("cantrips_count", "INTEGER DEFAULT 0"),
                    ("spells_count_level1", "INTEGER DEFAULT 0"),
                    ("masteries_count", "INTEGER DEFAULT 0"),
                ]

                for col_name, col_type in new_columns:
                    try:
                        cur.execute("""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = 'classes' AND column_name = %s
                        """, (col_name,))
                        if not cur.fetchone():
                            cur.execute(f"ALTER TABLE classes ADD COLUMN {col_name} {col_type}")
                            logger.info(f"✅ Добавлена колонка: {col_name} в classes")
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось добавить {col_name}: {e}")

                # 2. Добавляем колонку category в таблицу spells
                try:
                    cur.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'spells' AND column_name = 'category'
                    """)
                    if not cur.fetchone():
                        cur.execute("ALTER TABLE spells ADD COLUMN category VARCHAR(50)")
                        logger.info("✅ Добавлена колонка: category в spells")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось добавить category: {e}")

                conn.commit()
                logger.info("✅ Миграция структуры таблиц завершена")

                # 4. Заполняем данные
                migrate_data_v2()

    except Exception as e:
        logger.error(f"❌ Ошибка миграции: {e}")
        raise


def migrate_data_v2():
    """Заполняет новые поля данными"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. Количество заклинаний по классам
                class_spell_counts = {
                    'Волшебник': (3, 4, 0),
                    'Жрец': (3, 4, 0),
                    'Друид': (2, 4, 0),
                    'Паладин': (0, 4, 0),
                    'Бард': (2, 4, 0),
                    'Чародей': (4, 2, 0),
                    'Колдун': (2, 2, 0),
                    'Следопыт': (2, 2, 0),
                    'Артефактор': (2, 2, 0),
                    'Варвар': (0, 0, 2),
                    'Воин': (0, 0, 3),
                    'Монах': (0, 0, 0),
                    'Плут': (0, 0, 1),
                }

                for class_name, (cantrips, spells, masteries) in class_spell_counts.items():
                    cur.execute("""
                        UPDATE classes 
                        SET cantrips_count = %s, spells_count_level1 = %s, masteries_count = %s
                        WHERE name = %s
                    """, (cantrips, spells, masteries, class_name))

                # 2. Категории заклинаний
                cantrip_categories = {
                    'Огненный снаряд': 'Урон',
                    'Кислотный плевок': 'Урон',
                    'Ледяной луч': 'Урон',
                    'Удар по руке': 'Урон',
                    'Жуткий взрыв': 'Урон',
                    'Священное пламя': 'Урон',
                    'Шиллела': 'Урон',
                    'Леденящее прикосновение': 'Урон',
                    'Пляшущие огоньки': 'Утилита',
                    'Рука мага': 'Утилита',
                    'Починка': 'Утилита',
                    'Свет': 'Утилита',
                    'Сообщение': 'Утилита',
                    'Фокусы': 'Утилита',
                    'Руководство': 'Утилита',
                    'Элементализм': 'Природа',
                    'Терновый кнут': 'Природа',
                    'Жестокая насмешка': 'Контроль',
                    'Малая иллюзия': 'Иллюзии',
                    'Доспехи мага': 'Защита',
                    'Щит': 'Защита',
                    'Сопротивление': 'Защита',
                    'Лечение ран': 'Лечение',
                    'Лечащее слово': 'Лечение',
                    'Отсрочить смерть': 'Лечение',
                    'Сон': 'Контроль',
                    'Опутывание': 'Контроль',
                }

                for spell_name, category in cantrip_categories.items():
                    cur.execute("UPDATE spells SET category = %s WHERE name = %s", (category, spell_name))

                conn.commit()
                logger.info("✅ Миграция данных завершена успешно")

    except Exception as e:
        logger.error(f"❌ Ошибка заполнения данных: {e}")
        raise


# =========================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ЗАКЛИНАНИЯМИ (V2)
# =========================================================

def get_class_spell_counts(class_name: str) -> Dict[str, int]:
    """Возвращает количество заговоров и заклинаний для класса"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT cantrips_count, spells_count_level1 
                FROM classes WHERE name = %s
            """, (class_name,))
            result = cur.fetchone()
            if result:
                return {
                    'cantrips': result['cantrips_count'] or 0,
                    'level1': result['spells_count_level1'] or 0
                }
    return {'cantrips': 0, 'level1': 0}


def get_class_masteries_count(class_name: str) -> int:
    """Возвращает количество оружейных приёмов для класса"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT masteries_count FROM classes WHERE name = %s", (class_name,))
            result = cur.fetchone()
            return result[0] if result else 0


def get_spells_by_category(class_name: str, is_cantrip: bool = True) -> Dict[str, List[Dict[str, Any]]]:
    """Возвращает заклинания для класса, сгруппированные по категориям"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return {}
                class_id = class_result['id']

                cur.execute("""
                    SELECT s.id, s.name, s.description, COALESCE(s.category, 'Прочее') as category, s.level
                    FROM spells s
                    JOIN class_spells cs ON s.id = cs.spell_id
                    WHERE cs.class_id = %s AND cs.is_available = TRUE AND s.is_cantrip = %s
                    ORDER BY s.category, s.name
                """, (class_id, is_cantrip))

                spells = cur.fetchall()

                result = {}
                for spell in spells:
                    category = spell.get('category') or 'Прочее'
                    if category not in result:
                        result[category] = []
                    result[category].append({
                        'id': spell['id'],
                        'name': spell['name'],
                        'description': spell['description'] or 'Описание отсутствует'
                    })
                return result
    except Exception as e:
        logger.warning(f"Не удалось загрузить заклинания для {class_name}: {e}")
        return {}


def get_spell_by_id(spell_id: int) -> Optional[Dict[str, Any]]:
    """Получает заклинание по ID с полным описанием"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, description, level, is_cantrip, COALESCE(category, 'Прочее') as category, school
                    FROM spells WHERE id = %s
                """, (spell_id,))
                return cur.fetchone()
    except Exception as e:
        logger.warning(f"Не удалось загрузить заклинание {spell_id}: {e}")
        return None


# =========================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БРОНЁЙ
# =========================================================

def get_armor_by_name(armor_name: str) -> Optional[Dict[str, Any]]:
    """Получает броню по названию"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name, ac_base, ac_modifier, has_shield FROM armor WHERE name = %s",
                            (armor_name,))
                return cur.fetchone()
    except Exception as e:
        logger.warning(f"Не удалось загрузить броню {armor_name}: {e}")
        return None


# =========================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ СО СНАРЯЖЕНИЕМ КЛАССОВ
# =========================================================

def get_class_equipment_from_db(class_name: str, choice: Optional[str] = None) -> List[Dict[str, Any]]:
    """Получает снаряжение для класса"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return []
                class_id = class_result["id"]

                if choice:
                    cur.execute("""
                        SELECT class_id, choice, armor, weapon, secondary_weapon, other_items, coins
                        FROM class_equipment 
                        WHERE class_id = %s AND choice = %s
                    """, (class_id, choice))
                else:
                    cur.execute("""
                        SELECT class_id, choice, armor, weapon, secondary_weapon, other_items, coins
                        FROM class_equipment 
                        WHERE class_id = %s
                        ORDER BY choice
                    """, (class_id,))
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить снаряжение для класса {class_name}: {e}")
        return []


# =========================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БОЕВЫМИ СТИЛЯМИ
# =========================================================

def get_fighting_styles_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Возвращает боевые стили, доступные для класса"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return []
                class_id = class_result["id"]

                cur.execute("""
                    SELECT fs.id, fs.name, fs.description
                    FROM fighting_styles fs
                    JOIN class_fighting_styles cfs ON fs.id = cfs.style_id
                    WHERE cfs.class_id = %s
                    ORDER BY fs.name
                """, (class_id,))
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить боевые стили для класса {class_name}: {e}")
        return []


# =========================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ВОЗВАНИЯМИ
# =========================================================

def get_all_invocations_from_db(level: int = 1) -> List[Dict[str, Any]]:
    """Получает доступные возвания для колдуна из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, level_required, effect, requires_pact_boon, pact_boon_type
                    FROM invocations 
                    WHERE level_required <= %s
                    ORDER BY level_required, name
                """, (level,))
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить возвания: {e}")
        return []


# =========================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ПОДКЛАССАМИ
# =========================================================

def get_subclasses_for_class_from_db(class_name: str, level: int = 1) -> List[Dict[str, Any]]:
    """Возвращает подклассы для указанного класса"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return []
                class_id = class_result["id"]

                cur.execute("""
                    SELECT id, name, level_acquired, description, features
                    FROM subclasses 
                    WHERE class_id = %s AND level_acquired <= %s
                    ORDER BY level_acquired, name
                """, (class_id, level))
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить подклассы для класса {class_name}: {e}")
        return []


# =========================================================
# ТЕСТИРОВАНИЕ
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🐉 ТЕСТ МОДУЛЯ DB.PY (ВЕРСИЯ 2)")
    print("=" * 60)

    try:
        init_database()
        migrate_database_v2()

        with get_connection() as conn:
            with conn.cursor() as cur:
                # Проверяем новые колонки
                cur.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'classes' AND column_name IN 
                    ('cantrips_count', 'spells_count_level1', 'masteries_count')
                """)
                new_columns = cur.fetchall()
                print(f"\n✅ Новые колонки в classes: {[c[0] for c in new_columns]}")

                # Проверяем категории
                cur.execute("SELECT COUNT(*) FROM spells WHERE category IS NOT NULL")
                categorized = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM spells")
                total = cur.fetchone()[0]
                print(f"✅ Заклинаний с категориями: {categorized}/{total}")

                # Проверяем данные по классам
                cur.execute("""
                    SELECT name, cantrips_count, spells_count_level1, masteries_count 
                    FROM classes ORDER BY name
                """)
                print("\n📊 КЛАССЫ (новые поля):")
                for row in cur.fetchall():
                    print(f"   • {row[0]}: заговоров={row[1]}, заклинаний={row[2]}, приёмов={row[3]}")

        print("\n✅ Модуль db.py версии 2 готов к использованию!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")