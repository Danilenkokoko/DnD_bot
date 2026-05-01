# db.py
"""
Database initialization and connection management.
"""
from dotenv import load_dotenv
load_dotenv()

import os
import logging
import psycopg2
from psycopg2 import pool, extras
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Connection pool
_db_pool = None

# Database configuration from environment
# load_dotenv already called at top of file
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "dnd_bot")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def _init_pool():
    """Initialize connection pool if not already created."""
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
    """Get a connection from the pool and automatically return it when done."""
    _init_pool()
    conn = _db_pool.getconn()
    try:
        yield conn
    finally:
        _db_pool.putconn(conn)


def init_db():
    """Initialize database tables if they don't exist."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Create races table
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

            # Create subraces table
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

            # Create classes table
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

            # Create subclasses table
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

            # Create backgrounds table
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

            # Create spells table
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
                    class_list TEXT[]
                )
            """)

            # Create equipment table
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

            # Create class_equipment table
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

            # Create fighting_styles table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS fighting_styles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    description TEXT,
                    allowed_classes TEXT[]
                )
            """)

            # Create invocations table (not used on level 1, kept for future)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS invocations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    level_required INTEGER DEFAULT 1,
                    effect TEXT,
                    description TEXT
                )
            """)

            # Create characters table with new fields
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Migrations: add missing columns if they don't exist
            # Add origin_feat if missing
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='characters' AND column_name='origin_feat'
            """)
            if not cur.fetchone():
                cur.execute("ALTER TABLE characters ADD COLUMN origin_feat VARCHAR(100) DEFAULT ''")
                logger.info("Added origin_feat column to characters")

            # Add alignment if missing
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='characters' AND column_name='alignment'
            """)
            if not cur.fetchone():
                cur.execute("ALTER TABLE characters ADD COLUMN alignment VARCHAR(30) DEFAULT 'Нейтральный'")
                logger.info("Added alignment column to characters")

            # Drop deprecated selected_equipment_choice if exists
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='characters' AND column_name='selected_equipment_choice'
            """)
            if cur.fetchone():
                cur.execute("ALTER TABLE characters DROP COLUMN selected_equipment_choice")
                logger.info("Dropped deprecated column selected_equipment_choice")

            conn.commit()
            logger.info("Database initialized and migrated successfully")


def init_database():
    """Legacy wrapper for init_db(), called by bot.py."""
    logger.info("Initializing database (legacy wrapper)")
    init_db()


def migrate_database_v2():
    """Explicit migration for new fields (kept for compatibility)."""
    logger.info("Running migration v2 (already handled in init_db, but calling anyway)")
    init_db()


def get_user_characters(user_id: int) -> List[Dict[str, Any]]:
    """Get all characters for a user (simplified version, used by keyboards)."""
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
    """Fetch background data by name."""
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
    """Fetch all backgrounds."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name
                FROM backgrounds
                ORDER BY name
            """)
            return cur.fetchall()