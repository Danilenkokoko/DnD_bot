# add_spell_categories.py
"""
Быстрый скрипт для добавления таблицы категорий заклинаний
Запуск: python add_spell_categories.py
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


def main():
    print("📝 Создание таблицы spell_categories...")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Создаём таблицу категорий
        cur.execute("""
            CREATE TABLE IF NOT EXISTS spell_categories (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                icon VARCHAR(10),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Добавляем категории
        categories = [
            ("Урон", "💥", "Атакующие заклинания, наносящие урон"),
            ("Защита", "🛡️", "Защитные заклинания: щиты, броня, сопротивление"),
            ("Лечение", "❤️", "Заклинания восстановления здоровья"),
            ("Контроль", "🎭", "Заклинания контроля: страх, очарование, сон"),
            ("Утилита", "🧭", "Полезные заклинания: движение, свет, связь"),
            ("Иллюзии", "🧠", "Иллюзии и обман восприятия"),
            ("Природа", "🌿", "Природные заклинания: элементы, растения, погода"),
            ("Прочее", "⚙️", "Особые и ситуативные эффекты"),
        ]

        for name, icon, desc in categories:
            cur.execute("""
                INSERT INTO spell_categories (name, icon, description)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO NOTHING
            """, (name, icon, desc))

        # Добавляем колонку category_id в таблицу spells
        cur.execute("""
            ALTER TABLE spells 
            ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES spell_categories(id)
        """)

        conn.commit()
        print("✅ Таблица spell_categories успешно создана!")

        # Проверяем результат
        cur.execute("SELECT COUNT(*) FROM spell_categories")
        count = cur.fetchone()[0]
        print(f"📊 Добавлено категорий: {count}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()