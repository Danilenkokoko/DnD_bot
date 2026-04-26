# debug_full_flow.py
"""
Полная диагностика процесса создания персонажа
Запуск: python debug_full_flow.py
"""

import sys
import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Конфигурация БД
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "DND_DB"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "").strip(),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}


def print_separator(char="=", length=60):
    print(char * length)


def test_direct_db_access():
    """Тест 1: Прямой доступ к БД"""
    print_separator()
    print("ТЕСТ 1: Прямой доступ к БД")
    print_separator()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Получаем первую предысторию
        cur.execute("""
            SELECT name, characteristic1, characteristic2, characteristic3,
                   equipment_a, equipment_b, trait, skills
            FROM backgrounds 
            LIMIT 1
        """)
        row = cur.fetchone()

        if row:
            print(f"✅ Прямой доступ к БД работает")
            print(f"   Предыстория: {row[0]}")
            print(f"   characteristic1: {row[1]}")
            print(f"   characteristic2: {row[2]}")
            print(f"   characteristic3: {row[3]}")
            print(f"   equipment_a: {row[4][:60]}...")
            print(f"   equipment_b: {row[5][:60]}...")
            print(f"   trait: {row[6]}")
            print(f"   skills: {row[7]}")
            return True
        else:
            print("❌ Нет данных в таблице backgrounds")
            return False

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def test_import_dnd_logic():
    """Тест 2: Импорт dnd_logic"""
    print_separator()
    print("ТЕСТ 2: Импорт dnd_logic")
    print_separator()

    try:
        # Добавляем текущую директорию в путь
        sys.path.insert(0, os.getcwd())
        from dnd_logic import get_background_by_name, get_background_data
        print("✅ Модуль dnd_logic импортирован успешно")

        # Проверяем функцию get_background_by_name
        test_bg = "Артист"
        result = get_background_by_name(test_bg)
        if result:
            print(f"✅ get_background_by_name('{test_bg}') работает")
            print(f"   characteristics: {result.get('characteristics')}")
            print(f"   equipment_a: {result.get('equipment_a', '')[:60]}...")
        else:
            print(f"❌ get_background_by_name('{test_bg}') вернул None")

        # Проверяем функцию get_background_data
        result2 = get_background_data(test_bg)
        if result2:
            print(f"✅ get_background_data('{test_bg}') работает")
            print(f"   characteristics: {result2.get('characteristics')}")
            print(f"   equipment_a: {result2.get('equipment_a', '')[:60]}...")
        else:
            print(f"❌ get_background_data('{test_bg}') вернул пустой словарь")

        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dnd_logic_functions():
    """Тест 3: Тестирование функций dnd_logic по отдельности"""
    print_separator()
    print("ТЕСТ 3: Тестирование каждой функции dnd_logic")
    print_separator()

    try:
        from dnd_logic import (
            get_connection as dnd_get_connection,
            get_background_list,
            get_all_backgrounds,
            get_background_characteristics,
            get_background_trait,
            get_background_skills,
            get_background_tools,
            get_background_description,
            get_equipment_choice
        )

        # Тест get_background_list
        bg_list = get_background_list()
        print(f"✅ get_background_list(): {len(bg_list)} предысторий")
        if bg_list:
            print(f"   Первые 5: {bg_list[:5]}")

        # Тест get_all_backgrounds
        all_bg = get_all_backgrounds()
        print(f"✅ get_all_backgrounds(): {len(all_bg)} записей")

        # Тест каждой функции на конкретной предыстории
        test_bg = "Артист"

        chars = get_background_characteristics(test_bg)
        print(f"✅ get_background_characteristics('{test_bg}'): {chars}")

        trait = get_background_trait(test_bg)
        print(f"✅ get_background_trait('{test_bg}'): {trait}")

        skills = get_background_skills(test_bg)
        print(f"✅ get_background_skills('{test_bg}'): {skills}")

        tools = get_background_tools(test_bg)
        print(f"✅ get_background_tools('{test_bg}'): {tools}")

        desc = get_background_description(test_bg)
        print(f"✅ get_background_description('{test_bg}'): {desc[:60]}...")

        equip_a = get_equipment_choice(test_bg, "A")
        print(f"✅ get_equipment_choice('{test_bg}', 'A'): {equip_a[:60]}...")

        equip_b = get_equipment_choice(test_bg, "B")
        print(f"✅ get_equipment_choice('{test_bg}', 'B'): {equip_b[:60]}...")

        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bot_functions():
    """Тест 4: Эмуляция работы бота"""
    print_separator()
    print("ТЕСТ 4: Эмуляция работы бота")
    print_separator()

    # Симулируем state данные
    test_state = {
        "background": "Артист",
        "class_name": "Воин",
        "race": "Человек"
    }

    print(f"Симулируем state: {test_state}")

    # Проверяем получение данных предыстории разными способами

    # Способ 1: через dnd_logic
    try:
        from dnd_logic import get_background_data
        bg_data_1 = get_background_data(test_state["background"])
        print(f"\n1. Через get_background_data():")
        if bg_data_1:
            print(f"   ✅ Данные получены")
            print(f"   equipment_a: {bg_data_1.get('equipment_a', 'НЕТ')[:50]}...")
            print(f"   equipment_b: {bg_data_1.get('equipment_b', 'НЕТ')[:50]}...")
        else:
            print(f"   ❌ get_background_data() вернул пустой словарь или None")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Способ 2: прямой SQL запрос
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT equipment_a, equipment_b FROM backgrounds 
            WHERE name = %s
        """, (test_state["background"],))
        row = cur.fetchone()
        conn.close()

        print(f"\n2. Через прямой SQL запрос:")
        if row:
            print(f"   ✅ Данные получены")
            print(f"   equipment_a: {row[0][:50]}...")
            print(f"   equipment_b: {row[1][:50]}...")
        else:
            print(f"   ❌ Запрос не вернул данных")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")

    # Способ 3: через db.get_background_from_db
    try:
        from db import get_background_from_db
        bg_data_3 = get_background_from_db(test_state["background"])
        print(f"\n3. Через db.get_background_from_db():")
        if bg_data_3:
            print(f"   ✅ Данные получены")
            print(f"   equipment_a: {bg_data_3.get('equipment_a', 'НЕТ')[:50]}...")
        else:
            print(f"   ❌ get_background_from_db() вернул None")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")


def test_bot_imports():
    """Тест 5: Проверка импортов в bot.py"""
    print_separator()
    print("ТЕСТ 5: Проверка импортов bot.py")
    print_separator()

    try:
        # Проверяем, что все функции импортируются из dnd_logic
        from dnd_logic import (
            get_background_list,
            get_background_data,
            get_background_by_name,
            get_background_characteristics,
            get_background_trait,
            get_background_skills,
            get_background_tools,
            get_background_description,
            get_equipment_choice
        )
        print("✅ Все функции предысторий импортируются из dnd_logic")

        # Проверяем, что get_background_data не возвращает пустой словарь для существующей предыстории
        test_bg = "Артист"
        result = get_background_data(test_bg)
        if result and result.get('equipment_a'):
            print(f"✅ get_background_data('{test_bg}') возвращает корректные данные")
        else:
            print(f"❌ ПРОБЛЕМА: get_background_data('{test_bg}') возвращает: {result}")

        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def check_database_content():
    """Тест 6: Детальная проверка содержимого БД"""
    print_separator()
    print("ТЕСТ 6: Детальная проверка БД")
    print_separator()

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Проверяем все предыстории
        cur.execute("""
            SELECT name, 
                   characteristic1, characteristic2, characteristic3,
                   equipment_a IS NOT NULL as has_equip_a,
                   equipment_b IS NOT NULL as has_equip_b
            FROM backgrounds 
            ORDER BY name
        """)
        rows = cur.fetchall()

        print("Предыстории в БД:")
        for row in rows:
            status = "✅" if row[5] and row[6] else "⚠️"
            print(f"   {status} {row[0]}: +2 {row[1]}, +1 {row[2]}, +1 {row[3]} | equip_a: {row[4]}, equip_b: {row[5]}")

        # Проверяем конкретную предысторию, которая вызывает ошибку
        print("\nДетальная проверка предыстории 'Артист':")
        cur.execute("""
            SELECT * FROM backgrounds WHERE name = 'Артист'
        """)
        row = cur.fetchone()
        if row:
            col_names = [desc[0] for desc in cur.description]
            for i, col in enumerate(col_names):
                val = row[i]
                if col in ['equipment_a', 'equipment_b', 'description'] and val:
                    val = val[:80] + "..."
                print(f"   {col}: {val}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def simulate_bot_step_10():
    """Тест 7: Симуляция шага 10 (выбор снаряжения от предыстории)"""
    print_separator()
    print("ТЕСТ 7: Симуляция шага 10 бота")
    print_separator()

    # Эмуляция данных, которые бот получает из state
    state_background = "Артист"

    print(f"State содержит background = '{state_background}'")

    # Попытка получить данные так, как это делает бот
    try:
        from dnd_logic import get_background_data
        bg_info = get_background_data(state_background)

        print(f"\nРезультат get_background_data('{state_background}'):")
        print(f"  Тип результата: {type(bg_info)}")
        print(f"  Содержимое: {bg_info}")

        if bg_info:
            equipment_a = bg_info.get("equipment_a", "Нет описания")
            equipment_b = bg_info.get("equipment_b", "Нет описания")
            print(f"\n  equipment_a: {equipment_a[:60]}...")
            print(f"  equipment_b: {equipment_b[:60]}...")

            if equipment_a == "Нет описания" and equipment_b == "Нет описания":
                print("\n❌ ПРОБЛЕМА: equipment_a и equipment_b имеют значения по умолчанию!")
                print("   Это означает, что данные не загрузились из БД")
            else:
                print("\n✅ Данные загружены корректно")
        else:
            print("\n❌ ПРОБЛЕМА: get_background_data вернул None или пустой словарь!")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


def main():
    print_separator("=", 70)
    print("ПОЛНАЯ ДИАГНОСТИКА ПРОЦЕССА СОЗДАНИЯ ПЕРСОНАЖА")
    print_separator("=", 70)

    tests = [
        ("Прямой доступ к БД", test_direct_db_access),
        ("Импорт dnd_logic", test_import_dnd_logic),
        ("Функции dnd_logic", test_dnd_logic_functions),
        ("Эмуляция работы бота", test_bot_functions),
        ("Импорты bot.py", test_bot_imports),
        ("Содержимое БД", check_database_content),
        ("Симуляция шага 10", simulate_bot_step_10),
    ]

    results = {}
    for name, test_func in tests:
        print()
        result = test_func()
        results[name] = result
        print()

    print_separator("=", 70)
    print("ИТОГИ ДИАГНОСТИКИ:")
    print_separator("=", 70)

    for name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{status}: {name}")

    print_separator("=", 70)

    # Вывод рекомендаций
    print("\n📋 РЕКОМЕНДАЦИИ:")
    if not results["Прямой доступ к БД"]:
        print("   1. ПРОВЕРЬТЕ подключение к PostgreSQL")
        print("   2. Убедитесь, что переменные в .env правильные")
    elif not results["Импорт dnd_logic"]:
        print("   1. ПРОВЕРЬТЕ файл dnd_logic.py на синтаксические ошибки")
        print("   2. Убедитесь, что все зависимости установлены (psycopg2, python-dotenv)")
    elif not results["Функции dnd_logic"]:
        print("   1. ИСПРАВЬТЕ функции в dnd_logic.py, работающие с предысториями")
        print("   2. Обратите внимание на функцию get_background_by_name")
    elif not results["Симуляция шага 10"]:
        print("   1. ОСНОВНАЯ ПРОБЛЕМА: get_background_data() не загружает данные")
        print("   2. ВРЕМЕННОЕ РЕШЕНИЕ: используйте прямой SQL запрос в bot.py")
        print("   3. ПОСТОЯННОЕ РЕШЕНИЕ: исправьте функцию get_background_by_name в dnd_logic.py")
    else:
        print("   ✅ Все тесты пройдены! Проблема должна быть в другом месте.")
        print("   Проверьте, что бот использует правильные функции и state не теряется между шагами.")

    print()


if __name__ == "__main__":
    main()