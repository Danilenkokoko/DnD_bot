# check_backgrounds_debug.py
import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "DND_DB"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "").strip(),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}

print("=" * 60)
print("ДИАГНОСТИКА БАЗЫ ДАННЫХ - ПРЕДЫСТОРИИ")
print("=" * 60)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # 1. Проверяем, есть ли таблица
    print("\n1. ПРОВЕРКА ТАБЛИЦЫ backgrounds:")
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'backgrounds'
        )
    """)
    table_exists = cur.fetchone()[0]
    print(f"   Таблица существует: {table_exists}")

    if not table_exists:
        print("   ❌ Таблица backgrounds не существует! Запустите seed_data.py")
        exit()

    # 2. Проверяем количество записей
    print("\n2. КОЛИЧЕСТВО ЗАПИСЕЙ:")
    cur.execute("SELECT COUNT(*) FROM backgrounds")
    count = cur.fetchone()[0]
    print(f"   Всего предысторий: {count}")

    if count == 0:
        print("   ❌ Таблица пуста! Запустите seed_data.py")
        exit()

    # 3. Проверяем структуру таблицы
    print("\n3. СТРУКТУРА ТАБЛИЦЫ:")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'backgrounds'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    for col in columns:
        print(f"   • {col[0]}: {col[1]}")

    # 4. Проверяем данные первой предыстории
    print("\n4. ПРОВЕРКА ДАННЫХ (первая предыстория):")
    cur.execute("SELECT * FROM backgrounds LIMIT 1")
    row = cur.fetchone()
    if row:
        col_names = [desc[0] for desc in cur.description]
        print(f"   Колонки: {col_names}")
        print(f"   Значения:")
        for i, col in enumerate(col_names):
            val = row[i]
            if isinstance(val, str) and len(str(val)) > 50:
                val = str(val)[:50] + "..."
            print(f"      {col}: {val}")

    # 5. Проверяем конкретную предысторию, которую вы выбрали
    print("\n5. ПРОВЕРКА КОНКРЕТНОЙ ПРЕДЫСТОРИИ:")
    # Получаем список всех предысторий
    cur.execute("SELECT name FROM backgrounds")
    bg_names = [row[0] for row in cur.fetchall()]
    print(f"   Доступные предыстории: {bg_names}")

    # Проверяем первую
    test_bg = bg_names[0] if bg_names else None
    if test_bg:
        print(f"\n   Проверяем: '{test_bg}'")
        cur.execute("""
            SELECT name, characteristic1, characteristic2, characteristic3, 
                   equipment_a, equipment_b, trait, skills, tools, description
            FROM backgrounds WHERE name = %s
        """, (test_bg,))
        row = cur.fetchone()
        if row:
            print(f"   name: {row[0]}")
            print(f"   characteristic1: {row[1]}")
            print(f"   characteristic2: {row[2]}")
            print(f"   characteristic3: {row[3]}")
            print(f"   equipment_a: {row[4][:80]}...")
            print(f"   equipment_b: {row[5][:80]}...")
            print(f"   trait: {row[6]}")
            print(f"   skills: {row[7]}")
            print(f"   tools: {row[8]}")
            print(f"   description: {row[9][:100]}...")

    # 6. Проверяем, как работает get_background_by_name через импорт
    print("\n6. ПРОВЕРКА ФУНКЦИИ get_background_by_name:")
    try:
        from dnd_logic import get_background_by_name

        if test_bg:
            result = get_background_by_name(test_bg)
            if result:
                print(f"   ✅ Функция вернула данные для '{test_bg}'")
                print(f"   characteristics: {result.get('characteristics')}")
                print(f"   equipment_a: {result.get('equipment_a')[:80]}...")
            else:
                print(f"   ❌ Функция вернула None для '{test_bg}'")
    except Exception as e:
        print(f"   ❌ Ошибка импорта: {e}")

    cur.close()
    conn.close()

    print("\n" + "=" * 60)
    print("Если данные есть, но функция возвращает None - проблема в коде.")
    print("Если данных нет - нужно перезаполнить БД: python seed_data.py")
    print("=" * 60)

except Exception as e:
    print(f"❌ Ошибка: {e}")