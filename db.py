import psycopg2
import os
import logging
from dotenv import load_dotenv
from psycopg2.extras import Json, RealDictCursor
from contextlib import contextmanager

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
    """Создает таблицу если она не существует"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    class_name VARCHAR(50) NOT NULL,
                    race VARCHAR(50) NOT NULL,
                    str INTEGER DEFAULT 10,
                    dex INTEGER DEFAULT 10,
                    con INTEGER DEFAULT 10,
                    int INTEGER DEFAULT 10,
                    wis INTEGER DEFAULT 10,
                    cha INTEGER DEFAULT 10,
                    hp INTEGER DEFAULT 0,
                    ac INTEGER DEFAULT 10,
                    level INTEGER DEFAULT 1,
                    skills JSONB DEFAULT '[]',
                    equipment JSONB DEFAULT '[]',
                    spells JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_characters_user_id 
                ON characters(user_id)
            """)

            logger.info("✅ Таблица characters готова")

# ---------------- CREATE ----------------
def save_character(user_id, data, stats, hp, ac, skills, equipment, spells):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO characters (
                    user_id, name, class_name, race,
                    str, dex, con, int, wis, cha,
                    hp, ac, level, skills, equipment, spells
                )
                VALUES (%s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                data.get("name"),
                data.get("class_name"),
                data.get("race"),
                stats.get("STR", 10),
                stats.get("DEX", 10),
                stats.get("CON", 10),
                stats.get("INT", 10),
                stats.get("WIS", 10),
                stats.get("CHA", 10),
                hp,
                ac,
                1,
                Json(skills),
                Json(equipment),
                Json(spells)
            ))

# ---------------- READ ----------------
def get_user_characters(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, class_name, race, level
                FROM characters
                WHERE user_id = %s
                ORDER BY id DESC
            """, (user_id,))
            return cur.fetchall()

def get_character_by_id(char_id):
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM characters WHERE id = %s",
                (char_id,)
            )
            return cur.fetchone()

# ---------------- DELETE ----------------
def delete_character(char_id, user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM characters
                WHERE id = %s AND user_id = %s
            """, (char_id, user_id))

            return cur.rowcount > 0