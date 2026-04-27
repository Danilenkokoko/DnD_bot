# check_fighting_styles_data.py
"""
Проверка формата хранения боевых стилей и связей с классами
Запуск: python check_fighting_styles_data.py
"""

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


def print_header(text):
    print(f"\n{'=' * 70}")
    print(f" {text}")
    print(f"{'=' * 70}")


def check_database():
    print_header("ПРОВЕРКА БОЕВЫХ СТИЛЕЙ В БАЗЕ ДАННЫХ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. Проверяем таблицу fighting_styles
        print("\n1. ТАБЛИЦА fighting_styles:")
        cur.execute("SELECT id, name, description FROM fighting_styles ORDER BY id")
        styles = cur.fetchall()
        if styles:
            for s in styles:
                print(f"   ID={s[0]}, name={s[1]}, desc={s[2][:40]}...")
        else:
            print("   ❌ Таблица пуста! Нужно добавить боевые стили.")

        # 2. Проверяем структуру таблицы class_fighting_styles
        print("\n2. ТАБЛИЦА class_fighting_styles (связи):")
        cur.execute(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'class_fighting_styles'")
        columns = cur.fetchall()
        print("   Структура таблицы:")
        for col in columns:
            print(f"     - {col[0]}: {col[1]}")

        # 3. Проверяем связи
        print("\n3. СВЯЗИ КЛАССОВ СО СТИЛЯМИ:")
        cur.execute("""
            SELECT c.name, fs.name 
            FROM class_fighting_styles cfs
            JOIN classes c ON cfs.class_id = c.id
            JOIN fighting_styles fs ON cfs.style_id = fs.id
            ORDER BY c.name, fs.name
        """)
        links = cur.fetchall()
        if links:
            current_class = None
            for link in links:
                if link[0] != current_class:
                    print(f"\n   {link[0]}:")
                    current_class = link[0]
                print(f"     - {link[1]}")
        else:
            print("   ❌ Нет связей между классами и боевыми стилями!")

        # 4. Проверяем ID классов
        print("\n4. ID КЛАССОВ:")
        cur.execute("SELECT id, name FROM classes ORDER BY name")
        classes = cur.fetchall()
        for cls in classes:
            print(f"   {cls[1]}: ID={cls[0]}")

        # 5. Проверяем функцию получения стилей для класса
        print("\n5. ПРОВЕРКА get_fighting_styles_for_class:")

        from dnd_logic import get_fighting_styles_for_class

        for class_name in ["Воин", "Варвар", "Паладин", "Следопыт"]:
            styles = get_fighting_styles_for_class(class_name)
            print(f"   {class_name}: {len(styles)} стилей")
            if styles:
                for s in styles[:3]:
                    print(f"     - {s['name']}")

        conn.close()

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


def check_bot_handlers():
    """Проверяет, правильно ли обрабатываются callback_data"""
    print_header("ПРОВЕРКА ФОРМАТА CALLBACK_DATA")

    # Правильный формат для выбора снаряжения
    print("\n1. ФОРМАТ ДЛЯ ВЫБОРА СНАРЯЖЕНИЯ:")
    print("   ❌ Неправильно: callback_data=f'class_equip_{class_name}_{choice}'")
    print("   ✅ Правильно:   callback_data=f'class_equip_{choice}'")
    print("   Пример: 'class_equip_A' или 'class_equip_B'")

    # Правильный формат для выбора класса
    print("\n2. ФОРМАТ ДЛЯ ВЫБОРА КЛАССА:")
    print("   ✅ callback_data=f'class_{class_name}'")
    print("   Пример: 'class_Воин'")

    # Проверяем, что значение choice - это A или B
    print("\n3. ДОПУСТИМЫЕ ЗНАЧЕНИЯ CHOICE:")
    print("   Должно быть 'A' или 'B' (заглавные буквы)")


def check_class_equipment_format():
    """Проверяет, как хранится снаряжение в БД"""
    print_header("ПРОВЕРКА СНАРЯЖЕНИЯ КЛАССОВ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT c.name, ce.choice, ce.weapon, ce.armor
            FROM class_equipment ce
            JOIN classes c ON ce.class_id = c.id
            WHERE c.name = 'Воин'
            ORDER BY ce.choice
        """)
        equipment = cur.fetchall()

        print("\nСнаряжение для класса 'Воин':")
        for eq in equipment:
            print(f"   Вариант {eq[1]}: оружие='{eq[2]}', броня='{eq[3]}'")
            if eq[1] not in ['A', 'B', None]:
                print(f"   ⚠️ Нестандартное значение choice: '{eq[1]}'")

        conn.close()

    except Exception as e:
        print(f"❌ Ошибка: {e}")


def fix_missing_data():
    """Добавляет недостающие данные"""
    print_header("ДОБАВЛЕНИЕ НЕДОСТАЮЩИХ ДАННЫХ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 1. Добавляем боевые стили, если их нет
        cur.execute("SELECT COUNT(*) FROM fighting_styles")
        if cur.fetchone()[0] == 0:
            print("Добавление боевых стилей...")
            styles = [
                ("Дуэлянт", "Когда вы атакуете оружием в одной руке и не используете щит, вы добавляете +2 к урону."),
                ("Защита",
                 "Когда существо, которое вы видите, атакует цель, отличную от вас, вы можете реакцией дать помеху на эту атаку."),
                ("Оборона", "Вы получаете +1 к Классу Брони, если носите броню."),
                ("Перехват",
                 "Когда существо атакует цель в пределах 5 футов от вас, вы можете реакцией уменьшить урон на 1d10 + бонус мастерства."),
                ("Сражение без оружия", "Ваши безоружные удары наносят 1d6 + модификатор силы урона."),
                ("Сражение большим оружием",
                 "При атаке двуручным оружием вы можете перебросить единицы и двойки на кубиках урона."),
                ("Сражение вслепую", "Вы получаете слепое зрение в радиусе 10 футов."),
                ("Сражение двумя оружиями",
                 "При атаке лёгким оружием вы можете добавить модификатор характеристики к урону бонусной атаки."),
                ("Сражение метательным оружием", "Вы можете выхватить метательное оружие как часть атаки им."),
                ("Стрельба", "Вы получаете +2 к броскам атаки дальнобойным оружием.")
            ]
            for name, desc in styles:
                cur.execute("INSERT INTO fighting_styles (name, description) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (name, desc))
            print("   ✅ Боевые стили добавлены")

        # 2. Добавляем связи, если их нет
        cur.execute("SELECT COUNT(*) FROM class_fighting_styles")
        if cur.fetchone()[0] == 0:
            print("Добавление связей классов со стилями...")

            # Получаем ID классов
            cur.execute("SELECT id, name FROM classes")
            class_ids = {row[1]: row[0] for row in cur.fetchall()}

            # Получаем ID стилей
            cur.execute("SELECT id, name FROM fighting_styles")
            style_ids = {row[1]: row[0] for row in cur.fetchall()}

            # Связи для Воина
            warrior_styles = ["Дуэлянт", "Защита", "Оборона", "Перехват", "Сражение без оружия",
                              "Сражение большим оружием", "Сражение вслепую", "Сражение двумя оружиями",
                              "Сражение метательным оружием", "Стрельба"]

            if "Воин" in class_ids:
                for style in warrior_styles:
                    if style in style_ids:
                        cur.execute(
                            "INSERT INTO class_fighting_styles (class_id, style_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (class_ids["Воин"], style_ids[style]))
                print("   ✅ Связи для Воина добавлены")

            # Связи для Варвара
            barbarian_styles = ["Оборона", "Сражение без оружия", "Сражение большим оружием",
                                "Сражение вслепую", "Сражение двумя оружиями"]
            if "Варвар" in class_ids:
                for style in barbarian_styles:
                    if style in style_ids:
                        cur.execute(
                            "INSERT INTO class_fighting_styles (class_id, style_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (class_ids["Варвар"], style_ids[style]))
                print("   ✅ Связи для Варвара добавлены")

            # Связи для Паладина
            paladin_styles = ["Дуэлянт", "Защита", "Оборона", "Перехват", "Сражение без оружия",
                              "Сражение большим оружием", "Сражение вслепую"]
            if "Паладин" in class_ids:
                for style in paladin_styles:
                    if style in style_ids:
                        cur.execute(
                            "INSERT INTO class_fighting_styles (class_id, style_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (class_ids["Паладин"], style_ids[style]))
                print("   ✅ Связи для Паладина добавлены")

            # Связи для Следопыта
            ranger_styles = ["Дуэлянт", "Защита", "Оборона", "Сражение вслепую",
                             "Сражение двумя оружиями", "Сражение метательным оружием", "Стрельба"]
            if "Следопыт" in class_ids:
                for style in ranger_styles:
                    if style in style_ids:
                        cur.execute(
                            "INSERT INTO class_fighting_styles (class_id, style_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                            (class_ids["Следопыт"], style_ids[style]))
                print("   ✅ Связи для Следопыта добавлены")

        conn.commit()
        print("\n✅ Все недостающие данные добавлены!")

        conn.close()

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


def main():
    print_header("ДИАГНОСТИКА БОЕВЫХ СТИЛЕЙ И СВЯЗЕЙ")

    # Проверяем БД
    check_database()

    # Проверяем формат callback_data
    check_bot_handlers()

    # Проверяем снаряжение
    check_class_equipment_format()

    # Спрашиваем, нужно ли добавить данные
    print("\n" + "=" * 70)
    answer = input("Добавить недостающие данные? (y/n): ")
    if answer.lower() == 'y':
        fix_missing_data()

    print_header("РЕКОМЕНДАЦИИ")
    print("""
    1. Убедитесь, что в классе CreateCharacter есть состояние fighting_style_select
    2. Проверьте, что в go_to_spells для классов без заклинаний вызывается go_to_fighting_style
    3. Убедитесь, что в select_class_equipment НЕ перезаписывается class_name
    4. Проверьте, что callback_data для выбора снаряжения имеет формат 'class_equip_A' (только choice)
    5. Убедитесь, что в БД есть и стили, и связи
    """)


if __name__ == "__main__":
    main()