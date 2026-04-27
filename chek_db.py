# check_db_data.py
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


def check_database():
    print("=" * 60)
    print("ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("=" * 60)

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. Проверяем все таблицы
        tables = [
            "races", "subraces", "classes", "subclasses", "backgrounds",
            "spells", "class_spells", "weapons", "class_weapons",
            "weapon_masteries", "armor", "class_equipment",
            "fighting_styles", "class_fighting_styles", "invocations", "characters"
        ]

        print("\n1. СУЩЕСТВУЮЩИЕ ТАБЛИЦЫ И КОЛИЧЕСТВО ЗАПИСЕЙ:")
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"   ✅ {table}: {count} записей")
            except Exception as e:
                print(f"   ❌ {table}: ошибка - {e}")

        # 2. Проверяем структуру таблицы classes (новые колонки)
        print("\n2. ПРОВЕРКА КОЛОНОК В ТАБЛИЦЕ classes:")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'classes'
            ORDER BY ordinal_position
        """)
        columns = [row[0] for row in cur.fetchall()]
        print(f"   Колонки: {columns}")

        required_columns = ['cantrips_count', 'spells_count_level1', 'masteries_count']
        for col in required_columns:
            if col in columns:
                print(f"   ✅ {col} присутствует")
            else:
                print(f"   ❌ {col} ОТСУТСТВУЕТ!")

        # 3. Проверяем данные в таблице classes
        print("\n3. ПРОВЕРКА ДАННЫХ В ТАБЛИЦЕ classes:")
        cur.execute("""
            SELECT name, hit_die, cantrips_count, spells_count_level1, masteries_count 
            FROM classes 
            ORDER BY name
        """)
        classes = cur.fetchall()

        expected_classes = {
            "Волшебник": (3, 4, 0),
            "Жрец": (3, 4, 0),
            "Друид": (2, 4, 0),
            "Паладин": (0, 4, 0),
            "Бард": (2, 4, 0),
            "Чародей": (4, 2, 0),
            "Колдун": (2, 2, 0),
            "Следопыт": (2, 2, 0),
            "Артефактор": (2, 2, 0),
            "Варвар": (0, 0, 2),
            "Воин": (0, 0, 3),
            "Монах": (0, 0, 0),
            "Плут": (0, 0, 1)
        }

        for cls in classes:
            name, hit_die, cant, spells, master = cls
            expected = expected_classes.get(name)
            if expected:
                expected_cant, expected_spells, expected_master = expected
                if cant != expected_cant or spells != expected_spells or master != expected_master:
                    print(
                        f"   ⚠️ {name}: заговоров={cant}/{expected_cant}, заклинаний={spells}/{expected_spells}, приёмов={master}/{expected_master}")
                else:
                    print(f"   ✅ {name}: заговоров={cant}, заклинаний={spells}, приёмов={master}")
            else:
                print(f"   ? {name}: заговоров={cant}, заклинаний={spells}, приёмов={master}")

        # 4. Проверяем колонку category в таблице spells
        print("\n4. ПРОВЕРКА КАТЕГОРИЙ ЗАКЛИНАНИЙ:")
        cur.execute("SELECT COUNT(*) FROM spells WHERE category IS NOT NULL")
        categorized = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM spells")
        total = cur.fetchone()[0]
        print(f"   Заклинаний с категориями: {categorized}/{total}")

        if categorized == 0:
            print("   ⚠️ ВНИМАНИЕ: Нет категорий у заклинаний! Это может вызывать ошибки.")

        # 5. Проверяем наличие заклинаний для классов
        print("\n5. ПРОВЕРКА ЗАКЛИНАНИЙ ДЛЯ КЛАССОВ:")
        cur.execute("""
            SELECT c.name, COUNT(cs.spell_id) 
            FROM classes c
            LEFT JOIN class_spells cs ON c.id = cs.class_id
            GROUP BY c.name
            ORDER BY c.name
        """)
        class_spells = cur.fetchall()
        for cls in class_spells:
            print(f"   {cls[0]}: {cls[1]} заклинаний")

        # 6. Проверяем наличие оружия
        print("\n6. ПРОВЕРКА ОРУЖИЯ:")
        cur.execute("SELECT COUNT(*) FROM weapons")
        weapon_count = cur.fetchone()[0]
        print(f"   Всего оружия: {weapon_count}")

        # Проверяем оружие с приёмами
        cur.execute("SELECT COUNT(*) FROM weapons WHERE detailed_masteries != '[]'::jsonb")
        weapons_with_masteries = cur.fetchone()[0]
        print(f"   Оружие с приёмами: {weapons_with_masteries}")

        # 7. Проверяем наличие предысторий
        print("\n7. ПРОВЕРКА ПРЕДЫСТОРИЙ:")
        cur.execute("SELECT COUNT(*) FROM backgrounds")
        bg_count = cur.fetchone()[0]
        print(f"   Всего предысторий: {bg_count}")

        if bg_count == 0:
            print("   ⚠️ ВНИМАНИЕ: Нет предысторий! Нужно запустить seed_data.py")

        conn.close()

        print("\n" + "=" * 60)
        if categorized == 0 or bg_count == 0 or weapon_count == 0:
            print("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ! Рекомендуется запустить seed_data.py")
        else:
            print("✅ Структура БД в порядке!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_database()