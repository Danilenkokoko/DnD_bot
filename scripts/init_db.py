# migrate_to_v2.py
"""Миграция базы данных D&D бота до версии 2"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.getcwd())


def main():
    """Основная функция миграции"""
    print("\n" + "=" * 60)
    print("🔧 МИГРАЦИЯ БАЗЫ ДАННЫХ D&D БОТА (версия 2)")
    print("=" * 60)

    try:
        from db import init_database, migrate_database_v2

        print("\n📋 Шаг 1/2: Проверка/создание таблиц...")
        init_database()
        print("✅ Таблицы готовы")

        print("\n📋 Шаг 2/2: Добавление новых полей и данных...")
        migrate_database_v2()
        print("✅ Миграция завершена")

        # Проверка
        from db import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT name, cantrips_count, spells_count_level1, masteries_count 
                    FROM classes WHERE name = 'Волшебник'
                """)
                wizard = cur.fetchone()
                if wizard:
                    print(
                        f"\n✅ Проверка: Волшебник - заговоров={wizard[1]}, заклинаний={wizard[2]}, приёмов={wizard[3]}")

        print("\n" + "=" * 60)
        print("✅ МИГРАЦИЯ ЗАВЕРШЕНА!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()