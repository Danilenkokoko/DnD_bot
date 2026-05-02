# migrate_add_class_features.py
"""
Миграция для добавления новых полей в таблицу characters и вспомогательных таблиц.
Запускается однократно после обновления кода.
"""

import logging
from db import get_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Создать таблицу languages, если её нет
            cur.execute("""
                CREATE TABLE IF NOT EXISTS languages (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL
                )
            """)
            # Заполнить стандартными языками, если пусто
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
                logger.info("✅ Таблица languages заполнена стандартными языками")

            # 2. Создать таблицу warlock_pacts (опционально)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS warlock_pacts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    description TEXT
                )
            """)
            logger.info("✅ Таблица warlock_pacts создана (если не существовала)")

            # 3. Добавить новые колонки в таблицу characters
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'characters'
            """)
            existing = {row[0] for row in cur.fetchall()}

            columns_to_add = [
                ('druid_order', 'VARCHAR(20)'),
                ('cleric_order', 'VARCHAR(20)'),
                ('warlock_pact', 'VARCHAR(30)'),
                ('rogue_expertise', 'TEXT[]'),
                ('rogue_extra_language', 'VARCHAR(50)'),
                ('auto_spells', 'TEXT[]'),
                ('pact_tome_cantrips', 'TEXT[]'),
                ('pact_tome_rituals', 'TEXT[]'),
                ('pact_blade_weapon', 'VARCHAR(50)')
            ]

            for col_name, col_type in columns_to_add:
                if col_name not in existing:
                    cur.execute(f"ALTER TABLE characters ADD COLUMN {col_name} {col_type}")
                    logger.info(f"✅ Добавлена колонка {col_name}")

            # 4. Убедиться, что origin_feat и alignment есть
            if 'origin_feat' not in existing:
                cur.execute("ALTER TABLE characters ADD COLUMN origin_feat VARCHAR(100) DEFAULT ''")
                logger.info("✅ Добавлена колонка origin_feat")
            if 'alignment' not in existing:
                cur.execute("ALTER TABLE characters ADD COLUMN alignment VARCHAR(30) DEFAULT 'Нейтральный'")
                logger.info("✅ Добавлена колонка alignment")

            # 5. Удалить устаревшую колонку selected_equipment_choice
            if 'selected_equipment_choice' in existing:
                cur.execute("ALTER TABLE characters DROP COLUMN selected_equipment_choice")
                logger.info("✅ Удалена колонка selected_equipment_choice")

            conn.commit()
            logger.info("🎉 Миграция успешно завершена")

if __name__ == "__main__":
    run_migration()