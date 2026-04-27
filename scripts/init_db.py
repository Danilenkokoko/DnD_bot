# migrate_to_v2.py
"""Миграция базы данных D&D бота до версии 2"""

import sys
import os
from datetime import datetime

# Добавляем текущую папку в пути
sys.path.insert(0, os.getcwd())


def backup_warning():
    """Показывает предупреждение о необходимости бэкапа"""
    print("\n" + "=" * 60)
    print("⚠️  ВАЖНОЕ ПРЕДУПРЕЖДЕНИЕ ⚠️")
    print("=" * 60)
    print("Перед миграцией рекомендуется сделать резервную копию БД!")
    print()
    print("Для PostgreSQL:")
    print("  pg_dump -U postgres DND_DB > backup_before_migration.sql")
    print()
    print("Или используйте pgAdmin: правой кнопкой на БД -> Backup")
    print("=" * 60)

    response = input("\nВы сделали резервную копию? (yes/no): ").strip().lower()
    if response != 'yes':
        print("\n❌ Миграция отменена. Сделайте бэкап и запустите скрипт снова.")
        sys.exit(0)


def main():
    """Основная функция миграции"""
    print("\n" + "=" * 60)
    print("🔧 МИГРАЦИЯ БАЗЫ ДАННЫХ D&D БОТА (версия 2)")
    print("=" * 60)
    print(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Предупреждение о бэкапе
    backup_warning()

    try:
        from db import init_database, migrate_database_v2

        print("\n📋 Шаг 1/3: Проверка/создание таблиц...")
        init_database()
        print("✅ Таблицы готовы")

        print("\n📋 Шаг 2/3: Добавление новых полей и индексов...")
        migrate_database_v2()
        print("✅ Новые поля добавлены")

        print("\n📋 Шаг 3/3: Проверка результатов...")
        from db import get_connection

        with get_connection() as conn:
            with conn.cursor() as cur:
                # Проверяем classes
                cur.execute("""
                    SELECT COUNT(*) FROM classes 
                    WHERE cantrips_count IS NOT NULL AND spells_count_level1 IS NOT NULL
                """)
                classes_updated = cur.fetchone()[0]
                print(f"   • Классов с обновлёнными полями: {classes_updated}")

                # Проверяем spells
                cur.execute("SELECT COUNT(*) FROM spells WHERE category IS NOT NULL")
                spells_categorized = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM spells")
                total_spells = cur.fetchone()[0]
                print(f"   • Заклинаний с категориями: {spells_categorized}/{total_spells}")

        print("\n" + "=" * 60)
        print("✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 60)
        print("\nТеперь можно запускать бота:")
        print("  python bot.py")

    except Exception as e:
        print(f"\n❌ ОШИБКА МИГРАЦИИ: {e}")
        print("\nПроверьте:")
        print("  1. Что PostgreSQL запущен")
        print("  2. Что переменные в .env файле правильные")
        print("  3. Что у вас есть права на изменение БД")

        sys.exit(1)


if __name__ == "__main__":
    main()