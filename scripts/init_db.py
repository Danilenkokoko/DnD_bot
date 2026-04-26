#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
init_db.py - Скрипт для инициализации базы данных D&D 5.5e (2024)
Запуск: python init_db.py
"""

import psycopg2
import os
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация базы данных
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD", "").strip(),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}


def get_connection():
    """Создаёт подключение к базе данных"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        logger.info(f"✅ Подключение к БД: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
        return conn
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        raise


def create_tables(conn):
    """Создаёт все таблицы в правильном порядке (с учётом внешних ключей)"""

    sql_statements = [
        # 1. РАСЫ (без бонусов к характеристикам в 5.5e!)
        """
        CREATE TABLE IF NOT EXISTS races (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL,
            speed INTEGER DEFAULT 30,
            size VARCHAR(20) DEFAULT 'Средний',
            description TEXT,
            image_path VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # 2. ПОДРАСЫ
        """
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
        """,

        # 3. КЛАССЫ
        """
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # 4. ПОДКЛАССЫ
        """
        CREATE TABLE IF NOT EXISTS subclasses (
            id SERIAL PRIMARY KEY,
            class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
            name VARCHAR(50) NOT NULL,
            level_acquired INTEGER DEFAULT 1,
            description TEXT,
            features JSONB DEFAULT '[]',
            UNIQUE(class_id, name)
        )
        """,

        # 5. ПРЕДЫСТОРИИ (В 5.5e ОНИ ДАЮТ БОНУСЫ К ХАРАКТЕРИСТИКАМ!)
        """
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
        """,

        # 6. ЗАКЛИНАНИЯ
        """
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # 7. СВЯЗЬ КЛАССОВ С ЗАКЛИНАНИЯМИ
        """
        CREATE TABLE IF NOT EXISTS class_spells (
            class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
            spell_id INTEGER NOT NULL REFERENCES spells(id) ON DELETE CASCADE,
            is_available BOOLEAN DEFAULT TRUE,
            PRIMARY KEY (class_id, spell_id)
        )
        """,

        # 8. ОРУЖЕЙНЫЕ ПРИЁМЫ (Weapon Mastery)
        """
        CREATE TABLE IF NOT EXISTS weapon_masteries (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            trigger_condition TEXT NOT NULL,
            effect TEXT NOT NULL,
            weapons TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # 9. БОЕВЫЕ СТИЛИ
        """
        CREATE TABLE IF NOT EXISTS fighting_styles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # 10. ТАИНСТВЕННЫЕ ВОЗВАНИЯ
        """
        CREATE TABLE IF NOT EXISTS invocations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            level_required INTEGER DEFAULT 1,
            effect TEXT NOT NULL,
            requires_pact_boon BOOLEAN DEFAULT FALSE,
            pact_boon_type VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,

        # 11. ПЕРСОНАЖИ (обновлённая структура)
        """
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
            selected_equipment_choice VARCHAR(1),
            backstory TEXT,
            image_file_id VARCHAR(255),
            alignment VARCHAR(20) DEFAULT 'Нейтральное',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
    ]

    with conn.cursor() as cur:
        for sql in sql_statements:
            try:
                cur.execute(sql)
                logger.info(f"✅ Создана таблица")
            except Exception as e:
                logger.error(f"❌ Ошибка: {e}")
                raise
        conn.commit()

    logger.info("✅ Все таблицы успешно созданы")


def create_indexes(conn):
    """Создаёт индексы для оптимизации запросов"""

    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_characters_class_id ON characters(class_id)",
        "CREATE INDEX IF NOT EXISTS idx_characters_race_id ON characters(race_id)",
        "CREATE INDEX IF NOT EXISTS idx_characters_background_id ON characters(background_id)",
        "CREATE INDEX IF NOT EXISTS idx_class_spells_class_id ON class_spells(class_id)",
        "CREATE INDEX IF NOT EXISTS idx_class_spells_spell_id ON class_spells(spell_id)",
        "CREATE INDEX IF NOT EXISTS idx_subraces_race_id ON subraces(race_id)",
        "CREATE INDEX IF NOT EXISTS idx_subclasses_class_id ON subclasses(class_id)",
    ]

    with conn.cursor() as cur:
        for sql in index_statements:
            try:
                cur.execute(sql)
                logger.info(f"✅ Создан индекс")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка создания индекса: {e}")
        conn.commit()

    logger.info("✅ Все индексы созданы")


def drop_all_tables(conn):
    """Удаляет все таблицы (для пересоздания)"""

    tables = [
        "characters",
        "class_spells",
        "spells",
        "subclasses",
        "classes",
        "subraces",
        "races",
        "backgrounds",
        "weapon_masteries",
        "fighting_styles",
        "invocations"
    ]

    with conn.cursor() as cur:
        for table in tables:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                logger.info(f"🗑️ Удалена таблица: {table}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка удаления {table}: {e}")
        conn.commit()

    logger.info("✅ Все таблицы удалены")


def table_exists(conn, table_name):
    """Проверяет, существует ли таблица"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table_name,))
        return cur.fetchone()[0]


def show_tables(conn):
    """Показывает список всех таблиц"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cur.fetchall()

        print("\n" + "=" * 50)
        print("📋 СУЩЕСТВУЮЩИЕ ТАБЛИЦЫ:")
        print("=" * 50)
        for table in tables:
            print(f"  • {table[0]}")
        print(f"  Всего: {len(tables)} таблиц")
        print("=" * 50 + "\n")


def main():
    """Главная функция"""
    print("\n" + "=" * 60)
    print("🐉 D&D 5.5e (2024) - Инициализация базы данных")
    print("=" * 60 + "\n")

    # Проверка конфигурации
    if not DB_CONFIG["dbname"] or not DB_CONFIG["user"]:
        logger.error("❌ Не заданы переменные окружения DB_NAME и DB_USER")
        logger.info("💡 Проверьте файл .env:")
        logger.info("   DB_NAME=your_database")
        logger.info("   DB_USER=your_user")
        logger.info("   DB_PASSWORD=your_password")
        logger.info("   DB_HOST=localhost")
        logger.info("   DB_PORT=5432")
        return

    conn = None
    try:
        # Подключение к БД
        conn = get_connection()

        # Выбор действия
        print("Выберите действие:")
        print("  1. Создать таблицы (если не существуют)")
        print("  2. Пересоздать все таблицы (удалить существующие)")
        print("  3. Показать существующие таблицы")
        print("  4. Выйти")

        choice = input("\nВаш выбор (1-4): ").strip()

        if choice == "1":
            create_tables(conn)
            create_indexes(conn)
            show_tables(conn)
            logger.info("🎉 База данных готова к работе!")

        elif choice == "2":
            confirm = input("⚠️ ВНИМАНИЕ! Это удалит все данные. Уверены? (yes/no): ")
            if confirm.lower() == "yes":
                drop_all_tables(conn)
                create_tables(conn)
                create_indexes(conn)
                show_tables(conn)
                logger.info("🎉 База данных пересоздана!")
            else:
                logger.info("❌ Операция отменена")

        elif choice == "3":
            show_tables(conn)

        else:
            logger.info("👋 До свидания!")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            logger.info("🔌 Соединение с БД закрыто")


if __name__ == "__main__":
    main()