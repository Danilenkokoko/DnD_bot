# db.py
"""
Database initialization and connection management.
"""
import os
import logging
import psycopg2
from psycopg2 import pool, extras
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()  # <-- загружаем переменные окружения из .env

logger = logging.getLogger(__name__)

_db_pool = None

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "dnd_bot")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def _init_pool():
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = pool.SimpleConnectionPool(
                1, 20,
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise


@contextmanager
def get_connection():
    _init_pool()
    conn = _db_pool.getconn()
    conn.autocommit = True
    try:
        yield conn
    finally:
        _db_pool.putconn(conn)


def init_db():
    """Initialize database tables if they don't exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # --- existing tables (unchanged) ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS races (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    speed INTEGER DEFAULT 30,
                    size VARCHAR(20) DEFAULT 'Средний',
                    description TEXT,
                    image_path VARCHAR(200)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subraces (
                    id SERIAL PRIMARY KEY,
                    race_id INTEGER REFERENCES races(id) ON DELETE CASCADE,
                    name VARCHAR(50) NOT NULL,
                    trait TEXT,
                    description TEXT,
                    extra_speed INTEGER DEFAULT 0,
                    extra_traits TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    hit_die INTEGER NOT NULL,
                    primary_stats TEXT[],
                    saving_throws TEXT[],
                    skill_choices INTEGER DEFAULT 2,
                    description TEXT,
                    image_path VARCHAR(200),
                    is_spellcaster BOOLEAN DEFAULT FALSE,
                    spellcasting_ability VARCHAR(10),
                    cantrips_count INTEGER DEFAULT 0,
                    spells_count_level1 INTEGER DEFAULT 0,
                    masteries_count INTEGER DEFAULT 0,
                    skills TEXT[]
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subclasses (
                    id SERIAL PRIMARY KEY,
                    class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
                    name VARCHAR(50) NOT NULL,
                    level_acquired INTEGER DEFAULT 3,
                    description TEXT,
                    features TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS backgrounds (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    characteristic1 VARCHAR(3),
                    characteristic2 VARCHAR(3),
                    characteristic3 VARCHAR(3),
                    trait TEXT,
                    skills TEXT[],
                    tools VARCHAR(100),
                    equipment_a TEXT,
                    equipment_b TEXT,
                    description TEXT,
                    origin_feat VARCHAR(100)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS spells (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    level INTEGER NOT NULL,
                    school VARCHAR(50),
                    casting_time VARCHAR(50),
                    range VARCHAR(50),
                    components VARCHAR(50),
                    duration VARCHAR(50),
                    description TEXT,
                    higher_levels TEXT,
                    is_cantrip BOOLEAN DEFAULT FALSE,
                    category VARCHAR(50),
                    class_list TEXT[],
                    is_ritual BOOLEAN DEFAULT FALSE
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS equipment (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    type VARCHAR(50),
                    subtype VARCHAR(50),
                    cost INTEGER,
                    weight REAL,
                    properties TEXT[],
                    description TEXT,
                    armor_base_ac INTEGER,
                    armor_dex_bonus BOOLEAN,
                    armor_strength_requirement INTEGER,
                    weapon_damage VARCHAR(20),
                    weapon_damage_type VARCHAR(20),
                    weapon_range_normal INTEGER,
                    weapon_range_long INTEGER,
                    weapon_mastery VARCHAR(50)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS class_equipment (
                    id SERIAL PRIMARY KEY,
                    class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
                    choice VARCHAR(10),
                    weapon VARCHAR(100),
                    armor VARCHAR(100),
                    secondary_weapon VARCHAR(100),
                    other_items TEXT,
                    coins INTEGER DEFAULT 0
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fighting_styles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    description TEXT,
                    allowed_classes TEXT[]
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS invocations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    level_required INTEGER DEFAULT 1,
                    effect TEXT,
                    description TEXT
                )
            """)

            # --- new table for warlock pacts (if needed) ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS warlock_pacts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    description TEXT
                )
            """)

            # --- languages reference table for rogue extra language ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS languages (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL
                )
            """)
            # insert standard languages if empty
            cur.execute("SELECT COUNT(*) FROM languages")
            if cur.fetchone()[0] == 0:
                languages = [
                    'Общий', 'Эльфийский', 'Дварфийский', 'Гномий', 'Полуросликов',
                    'Драконий', 'Гоблинский', 'Оркский', 'Великаний', 'Терранский',
                    'Акванский', 'Ауранский', 'Игнианский', 'Абиссальный', 'Небесный',
                    'Инфернальный', 'Глубинная речь', 'Примордиальный', 'Сильвани'
                ]
                for lang in languages:
                    cur.execute("INSERT INTO languages (name) VALUES (%s)", (lang,))

            # --- characters table with new columns ---
            cur.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    race_id INTEGER REFERENCES races(id),
                    subrace_id INTEGER REFERENCES subraces(id),
                    class_id INTEGER REFERENCES classes(id),
                    background_id INTEGER REFERENCES backgrounds(id),
                    level INTEGER DEFAULT 1,
                    experience INTEGER DEFAULT 0,
                    str INTEGER DEFAULT 10,
                    dex INTEGER DEFAULT 10,
                    con INTEGER DEFAULT 10,
                    int INTEGER DEFAULT 10,
                    wis INTEGER DEFAULT 10,
                    cha INTEGER DEFAULT 10,
                    hp INTEGER,
                    ac INTEGER,
                    speed INTEGER DEFAULT 30,
                    selected_skills TEXT[],
                    selected_masteries TEXT[],
                    selected_fighting_style VARCHAR(50),
                    selected_invocations TEXT[],
                    selected_spells TEXT[],
                    selected_weapon VARCHAR(100),
                    selected_armor VARCHAR(100),
                    backstory TEXT,
                    image_file_id VARCHAR(200),
                    origin_feat VARCHAR(100),
                    alignment VARCHAR(30) DEFAULT 'Нейтральный',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    -- new columns for class-specific features
                    druid_order VARCHAR(20),
                    cleric_order VARCHAR(20),
                    warlock_pact VARCHAR(30),
                    rogue_expertise TEXT[],
                    rogue_extra_language VARCHAR(50),
                    auto_spells TEXT[],
                    pact_tome_cantrips TEXT[],
                    pact_tome_rituals TEXT[],
                    pact_blade_weapon VARCHAR(50)
                )
            """)

            # --- migrations for missing columns (idempotent) ---
            # check and add columns if they don't exist
            existing_columns = []
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'characters'
            """)
            for row in cur.fetchall():
                existing_columns.append(row[0])

            def add_column_if_missing(col_name, col_type):
                if col_name not in existing_columns:
                    cur.execute(f"ALTER TABLE characters ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added column {col_name} to characters")

            add_column_if_missing('druid_order', 'VARCHAR(20)')
            add_column_if_missing('cleric_order', 'VARCHAR(20)')
            add_column_if_missing('warlock_pact', 'VARCHAR(30)')
            add_column_if_missing('rogue_expertise', 'TEXT[]')
            add_column_if_missing('rogue_extra_language', 'VARCHAR(50)')
            add_column_if_missing('auto_spells', 'TEXT[]')
            add_column_if_missing('pact_tome_cantrips', 'TEXT[]')
            add_column_if_missing('pact_tome_rituals', 'TEXT[]')
            add_column_if_missing('pact_blade_weapon', 'VARCHAR(50)')
            add_column_if_missing('origin_feat', 'VARCHAR(100)')
            add_column_if_missing('alignment', 'VARCHAR(30) DEFAULT \'Нейтральный\'')
            # D&D 5.5e (2024): персонаж знает Общий + 2 языка от предыстории.
            # Также сохраняем владение инструментом от предыстории отдельным полем,
            # т.к. backgrounds.tools хранит только описание.
            add_column_if_missing('languages', 'JSONB DEFAULT \'[]\'::jsonb')
            add_column_if_missing('selected_tools', 'JSONB DEFAULT \'[]\'::jsonb')

            # Снаряжение: вторичное оружие, прочие предметы и стартовые монеты.
            # До этого они хранились только в FSM-state и терялись при сохранении.
            # `coins` — JSONB со структурой {cp, sp, ep, gp, pp} (2024 PHB).
            add_column_if_missing('selected_secondary_weapon', 'VARCHAR(100)')
            add_column_if_missing('selected_other_items', 'TEXT')
            add_column_if_missing(
                'coins',
                "JSONB DEFAULT '{\"cp\":0,\"sp\":0,\"ep\":0,\"gp\":0,\"pp\":0}'::jsonb"
            )

            # 2024 PHB-специфичные расовые/классовые шаги:
            # - draconic_ancestry: тип дракона у Драконорождённого (10 опций).
            # - warlock_invocation: 1 воззвание Колдуна на 1 уровне.
            # - favored_enemy: Избранный враг Следопыта.
            add_column_if_missing('draconic_ancestry', 'VARCHAR(30)')
            add_column_if_missing('warlock_invocation', 'VARCHAR(100)')
            add_column_if_missing('favored_enemy', 'VARCHAR(50)')

            # 4 нарративных поля «Черты личности» (D&D 5.5e 2024).
            # Генерируются автоматически из таблиц предыстории; игрок может
            # отредактировать в отдельном инструменте (вне рамок этой версии).
            add_column_if_missing('personality_trait', 'TEXT')
            add_column_if_missing('ideal', 'TEXT')
            add_column_if_missing('bond', 'TEXT')
            add_column_if_missing('flaw', 'TEXT')

            # Inspiration (2024 PHB) — флаг (true/false).
            add_column_if_missing('inspiration', 'BOOLEAN DEFAULT FALSE')

            # PHB 2024: расширенный трекинг HP/состояния персонажа.
            # • max_hp / current_hp / temp_hp — отдельные значения, чтобы прогресс-бар
            #   на листе показывал реальный процент.
            # • hit_dice_used — сколько HD потрачено (для коротких отдыхов).
            # • exhaustion — уровень истощения 0..6 (PHB 2024).
            # • conditions — список текущих состояний (Очарован, Отравлен и т.д.).
            add_column_if_missing('max_hp',         'INTEGER')
            add_column_if_missing('current_hp',     'INTEGER')
            add_column_if_missing('temp_hp',        'INTEGER DEFAULT 0')
            add_column_if_missing('hit_dice_used',  'INTEGER DEFAULT 0')
            add_column_if_missing('exhaustion',     'INTEGER DEFAULT 0')
            add_column_if_missing('conditions',     "TEXT[] DEFAULT '{}'")

            # Бэкфилл существующих записей: если max_hp/current_hp пустые —
            # подтянуть из hp. Идемпотентно: WHERE … IS NULL не тронет уже
            # заполненные значения.
            cur.execute("UPDATE characters SET max_hp = hp WHERE max_hp IS NULL AND hp IS NOT NULL")
            cur.execute("UPDATE characters SET current_hp = hp WHERE current_hp IS NULL AND hp IS NOT NULL")

            # PHB 2024 — backfill cantrips_count/spells_count_level1 для классов,
            # у которых в БД эти поля = 0 (старые установки до seed-фикса).
            # Идемпотентно: WHERE … = 0 не задеть уже заполненные.
            class_l1_counts = {
                "Артефактор": (2, 2), "Бард": (2, 4), "Жрец": (3, 2),
                "Друид": (2, 2), "Колдун": (2, 2), "Паладин": (0, 2),
                "Следопыт": (0, 2), "Чародей": (4, 2), "Волшебник": (3, 6),
            }
            for cname, (c_cnt, l1_cnt) in class_l1_counts.items():
                cur.execute("""
                    UPDATE classes
                    SET cantrips_count = %s, spells_count_level1 = %s
                    WHERE name = %s AND (cantrips_count = 0 OR spells_count_level1 = 0)
                """, (c_cnt, l1_cnt, cname))

            # PHB 2024 — backfill полных описаний заклинаний (оригинальный
            # текст бота). Если описание короче 100 символов — считаем
            # старым/коротким и обновляем. Полные тексты длиной ~250-500.
            try:
                from scripts.spell_descriptions_full import SPELL_DESCRIPTIONS_2024
            except ImportError:
                SPELL_DESCRIPTIONS_2024 = {}
            updated_spells = 0
            for spell_name, full_desc in SPELL_DESCRIPTIONS_2024.items():
                cur.execute("""
                    UPDATE spells
                    SET description = %s
                    WHERE name = %s
                      AND (description IS NULL OR LENGTH(description) < 100)
                """, (full_desc, spell_name))
                if cur.rowcount > 0:
                    updated_spells += cur.rowcount
            if updated_spells:
                logger.info(f"Обновлены описания заклинаний: {updated_spells}")

            # PHB 2024 — backfill категорий (Урон/Защита/Лечение/...). Старые
            # установки имели NULL/'Прочее' для всех заклинаний; теперь
            # присваиваем правильные категории по словарю.
            try:
                from scripts.spell_categories import SPELL_CATEGORIES_2024
            except ImportError:
                SPELL_CATEGORIES_2024 = {}
            updated_cats = 0
            for spell_name, cat in SPELL_CATEGORIES_2024.items():
                cur.execute("""
                    UPDATE spells
                    SET category = %s
                    WHERE name = %s
                      AND (category IS NULL OR category = 'Прочее' OR category = '')
                """, (cat, spell_name))
                if cur.rowcount > 0:
                    updated_cats += cur.rowcount
            if updated_cats:
                logger.info(f"Обновлены категории заклинаний: {updated_cats}")

            # Переименование старых имён воззваний колдуна (PHB 2024 — Pact Boon).
            # «Недоговорённость» → «Договор». Идемпотентно.
            invocation_renames = [
                ("Недоговорённость клинка",   "Договор клинка"),
                ("Недоговорённость цепи",     "Договор цепи"),
                ("Недоговорённость гримуара", "Договор гримуара"),
            ]
            for old, new in invocation_renames:
                cur.execute(
                    "UPDATE invocations SET name = %s WHERE name = %s",
                    (new, old),
                )
                if cur.rowcount > 0:
                    logger.info(f"Переименовано воззвание: '{old}' → '{new}'")

            conn.commit()
            logger.info("Database initialized and migrated successfully")


def init_database():
    init_db()


def migrate_database_v2():
    init_db()


def get_user_characters(user_id: int) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT c.id, c.name, c.level, cl.name as class_name
                FROM characters c
                LEFT JOIN classes cl ON c.class_id = cl.id
                WHERE c.user_id = %s
                ORDER BY c.id DESC
            """, (user_id,))
            return cur.fetchall()


def get_background_from_db(name: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, characteristic1, characteristic2, characteristic3,
                       trait, skills, tools, equipment_a, equipment_b, description, origin_feat
                FROM backgrounds
                WHERE name = %s
            """, (name,))
            return cur.fetchone()


def get_all_backgrounds_from_db() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("SELECT id, name FROM backgrounds ORDER BY name")
            return cur.fetchall()
