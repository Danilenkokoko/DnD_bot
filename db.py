import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import Json

load_dotenv(encoding='utf-8')

DB_PASSWORD = os.getenv("DB_PASSWORD")
if DB_PASSWORD:
    DB_PASSWORD = DB_PASSWORD.strip()  # удаляем лишние пробелы/символы

conn = psycopg2.connect(
    f"dbname={os.getenv('DB_NAME')} "
    f"user={os.getenv('DB_USER')} "
    f"password={DB_PASSWORD} "
    f"host={os.getenv('DB_HOST')} "
    f"port=5432"
)


def save_character(user_id, data, stats, hp, ac, skills, equipment, spells):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO characters (
                user_id, name, class_name, race,
                str, dex, con, int, wis, cha,
                hp, ac, skills, equipment, spells
            )
            VALUES (%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s)
        """, (
            user_id,
            data["name"],
            data["class_name"],
            data["race"],
            stats["STR"], stats["DEX"], stats["CON"],
            stats["INT"], stats["WIS"], stats["CHA"],
            hp, ac,
            Json(skills), Json(equipment), Json(spells)
        ))
        conn.commit()


def get_user_characters(user_id):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, class_name, race, level FROM characters WHERE user_id=%s",
            (user_id,)
        )
        return cur.fetchall()


def get_character_by_id(char_id):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM characters WHERE id=%s", (char_id,))
        return cur.fetchone()


def delete_character(char_id, user_id):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM characters WHERE id=%s AND user_id=%s",
            (char_id, user_id)
        )
        conn.commit()