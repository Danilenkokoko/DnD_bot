# migrate_origin_feat.py
"""
Скрипт для миграции: добавление колонки origin_feat в таблицу backgrounds
и заполнение её данными из списка черт происхождения для D&D 5.5e 2024.

Запуск: python migrate_origin_feat.py
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "DND_DB"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "").strip(),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}

# Соответствие предыстория -> черта происхождения (из предоставленного файла)
ORIGIN_FEATS = {
    "Артист": "Музыкант",
    "Бродяга": "Везучий",
    "Дворянин": "Одарённый",
    "Моряк": "Дебошир",
    "Мудрец": "Посвящённый в магию (Волшебник)",
    "Отшельник": "Лекарь",
    "Писарь": "Одарённый",
    "Послушник": "Посвящённый в магию (Жрец)",
    "Преступник": "Бдительный",
    "Проводник": "Посвящённый в магию (Друид)",
    "Ремесленник": "Мастеровой",
    "Солдат": "Неистово атакующий",
    "Стражник": "Бдительный",
    "Торговец": "Везучий",
    "Фермер": "Крепкий",
    "Шарлатан": "Одарённый",
}

def add_origin_feat_column(conn):
    """Добавляет колонку origin_feat, если её нет"""
    with conn.cursor() as cur:
        # Проверяем существование колонки
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'backgrounds' AND column_name = 'origin_feat'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE backgrounds ADD COLUMN origin_feat TEXT")
            print("✅ Колонка origin_feat добавлена")
        else:
            print("ℹ️ Колонка origin_feat уже существует")

def update_origin_feat_values(conn):
    """Заполняет origin_feat для каждой предыстории"""
    with conn.cursor() as cur:
        for bg_name, feat_name in ORIGIN_FEATS.items():
            cur.execute(
                "UPDATE backgrounds SET origin_feat = %s WHERE name = %s",
                (feat_name, bg_name)
            )
            if cur.rowcount > 0:
                print(f"  Обновлено: {bg_name} -> {feat_name}")
            else:
                print(f"⚠️ Предыстория '{bg_name}' не найдена в БД")
        conn.commit()

def main():
    print("🚀 Запуск миграции origin_feat...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        add_origin_feat_column(conn)
        update_origin_feat_values(conn)
        conn.commit()
        print("✅ Миграция завершена успешно")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
