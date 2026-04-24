import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import Json
from contextlib import contextmanager

load_dotenv(encoding='utf-8')

DB_PASSWORD = os.getenv("DB_PASSWORD")
if DB_PASSWORD:
    DB_PASSWORD = DB_PASSWORD.strip()

# Параметры подключения
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': DB_PASSWORD,
    'host': os.getenv('DB_HOST'),
    'port': 5432
}

# Контекстный менеджер для управления соединениями
@contextmanager
def get_connection():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def save_character(user_id, data, stats, hp, ac, skills, equipment, spells):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO characters (
                    user_id, name, class_name, race,
                    str, dex, con, int, wis, cha,
                    hp, ac, skills, equipment, spells
                )
                VALUES (%s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s)
            """, (
                user_id,
                data.get("name"),
                data.get("class_name"),
                data.get("race"),
                stats.get("STR"), stats.get("DEX"), stats.get("CON"),
                stats.get("INT"), stats.get("WIS"), stats.get("CHA"),
                hp, ac,
                Json(skills), Json(equipment), Json(spells)
            ))


def get_user_characters(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, class_name, race, level FROM characters WHERE user_id = %s",
                (user_id,)
            )
            return cur.fetchall()


def get_character_by_id(char_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM characters WHERE id = %s", (char_id,))
            return cur.fetchone()


def delete_character(char_id, user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM characters WHERE id = %s AND user_id = %s",
                (char_id, user_id)
            )