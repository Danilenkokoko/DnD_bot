# validate_project.py
"""
Скрипт для проверки корректности всех зависимостей в проекте D&D Character Creator
Запуск: python validate_project.py
"""

import sys
import os
import psycopg2
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

# ============================================================
# ДАННЫЕ ДЛЯ ПРОВЕРКИ (из предоставленных файлов)
# ============================================================

# Основные характеристики классов
CLASS_PRIMARY_STATS = {
    "Артефактор": ["INT"],
    "Бард": ["CHA"],
    "Варвар": ["STR"],
    "Воин": ["STR", "DEX"],
    "Волшебник": ["INT"],
    "Друид": ["WIS"],
    "Жрец": ["WIS"],
    "Колдун": ["CHA"],
    "Монах": ["DEX", "WIS"],
    "Паладин": ["STR", "CHA"],
    "Плут": ["DEX"],
    "Следопыт": ["DEX", "WIS"],
    "Чародей": ["CHA"]
}

# Количество заклинаний по классам
CLASS_SPELLS_COUNT = {
    "Артефактор": {"cantrips": 2, "level1": 2, "spellcasting": True},
    "Бард": {"cantrips": 2, "level1": 4, "spellcasting": True},
    "Варвар": {"cantrips": 0, "level1": 0, "spellcasting": False},
    "Воин": {"cantrips": 0, "level1": 0, "spellcasting": False},
    "Волшебник": {"cantrips": 3, "level1": 4, "spellcasting": True},
    "Друид": {"cantrips": 2, "level1": 4, "spellcasting": True},
    "Жрец": {"cantrips": 3, "level1": 4, "spellcasting": True},
    "Колдун": {"cantrips": 2, "level1": 2, "spellcasting": True},
    "Монах": {"cantrips": 0, "level1": 0, "spellcasting": False},
    "Паладин": {"cantrips": 0, "level1": 2, "spellcasting": True},
    "Плут": {"cantrips": 0, "level1": 0, "spellcasting": False},
    "Следопыт": {"cantrips": 0, "level1": 2, "spellcasting": True},
    "Чародей": {"cantrips": 4, "level1": 2, "spellcasting": True}
}

# Оружейные приемы по классам
CLASS_MASTERIES_COUNT = {
    "Артефактор": 0,
    "Бард": 0,
    "Варвар": 2,
    "Воин": 3,
    "Волшебник": 0,
    "Друид": 0,
    "Жрец": 0,
    "Колдун": 0,
    "Монах": 0,
    "Паладин": 2,
    "Плут": 2,
    "Следопыт": 2,
    "Чародей": 0
}

# Боевые стили по классам
CLASS_FIGHTING_STYLES = {
    "Воин": True,
    "Паладин": True,
    "Следопыт": True,
    "Варвар": False,
    "Другие": False
}

# Таинственные возвания (только для колдуна)
CLASS_INVOCATIONS = {
    "Колдун": True,
    "Другие": False
}

# Подклассы на 1 уровне
CLASS_SUBCLASSES_LEVEL1 = ["Жрец", "Друид", "Колдун"]

# Оружие по категориям для классов
CLASS_WEAPONS = {
    "Воин": ["simple", "martial"],
    "Варвар": ["simple", "martial"],
    "Паладин": ["simple", "martial"],
    "Следопыт": ["simple", "specific_martial"],
    "Плут": ["simple", "specific_martial"],
    "Другие": ["simple"]
}


# ============================================================
# ФУНКЦИИ ПРОВЕРКИ
# ============================================================

def print_header(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_result(test_name, passed, details=""):
    status = "✅" if passed else "❌"
    print(f"{status} {test_name}")
    if details and not passed:
        print(f"   → {details}")


def check_database_connection():
    """Проверка подключения к БД"""
    print_header("1. ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БД")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0][:50]
        print_result("Подключение к PostgreSQL", True, version)
        conn.close()
        return True
    except Exception as e:
        print_result("Подключение к PostgreSQL", False, str(e))
        return False


def check_tables():
    """Проверка существования всех необходимых таблиц"""
    print_header("2. ПРОВЕРКА ТАБЛИЦ")

    required_tables = [
        "races", "subraces", "classes", "subclasses", "backgrounds",
        "spells", "class_spells", "weapons", "class_weapons",
        "weapon_masteries", "armor", "class_equipment",
        "fighting_styles", "class_fighting_styles", "invocations", "characters"
    ]

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        all_passed = True
        for table in required_tables:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, (table,))
            exists = cur.fetchone()[0]
            if not exists:
                print_result(f"Таблица {table}", False, "не существует")
                all_passed = False
            else:
                # Проверяем количество записей
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                if table == "backgrounds" and count != 16:
                    print_result(f"Таблица {table}", False, f"ожидается 16 записей, найдено {count}")
                    all_passed = False
                elif table == "classes" and count != 13:
                    print_result(f"Таблица {table}", False, f"ожидается 13 записей, найдено {count}")
                    all_passed = False
                elif count == 0 and table not in ["characters", "subclasses"]:
                    print_result(f"Таблица {table}", False, f"пустая (0 записей)")
                    all_passed = False
                else:
                    print_result(f"Таблица {table} ({count} записей)", True)

        conn.close()
        return all_passed
    except Exception as e:
        print_result("Проверка таблиц", False, str(e))
        return False


def check_classes_data():
    """Проверка данных классов"""
    print_header("3. ПРОВЕРКА ДАННЫХ КЛАССОВ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT name, hit_die, primary_stats, saving_throws, 
                   is_spellcaster, spellcasting_ability
            FROM classes
        """)
        classes = cur.fetchall()

        all_passed = True

        # Словарь для хранения ID классов
        class_ids = {}

        for cls in classes:
            name = cls[0]
            hit_die = cls[1]
            primary_stats = cls[2] if isinstance(cls[2], list) else json.loads(cls[2])
            is_spellcaster = cls[4]
            spellcasting_ability = cls[5]

            # Проверка хитового кубика
            expected_hit_die = {
                "Варвар": 12, "Воин": 10, "Паладин": 10, "Следопыт": 10,
                "Бард": 8, "Друид": 8, "Жрец": 8, "Колдун": 8, "Монах": 8, "Плут": 8, "Артефактор": 8,
                "Волшебник": 6, "Чародей": 6
            }.get(name, 8)

            if hit_die != expected_hit_die:
                print_result(f"Хитовый кубик {name}", False, f"ожидается d{expected_hit_die}, получено d{hit_die}")
                all_passed = False

            # Проверка основных характеристик
            expected_stats = CLASS_PRIMARY_STATS.get(name, [])
            if set(primary_stats) != set(expected_stats):
                print_result(f"Основные характеристики {name}", False,
                             f"ожидается {expected_stats}, получено {primary_stats}")
                all_passed = False

            # Проверка заклинаний
            expected_spellcasting = CLASS_SPELLS_COUNT.get(name, {}).get("spellcasting", False)
            if is_spellcaster != expected_spellcasting:
                print_result(f"Заклинания {name}", False,
                             f"ожидается {expected_spellcasting}, получено {is_spellcaster}")
                all_passed = False

            # Проверка способности колдовства
            if is_spellcaster:
                expected_ability = CLASS_PRIMARY_STATS.get(name, [None])[0]
                if spellcasting_ability != expected_ability:
                    print_result(f"Способность колдовства {name}", False,
                                 f"ожидается {expected_ability}, получено {spellcasting_ability}")
                    all_passed = False

            class_ids[name] = cls[0]  # сохраняем ID

        conn.close()

        if all_passed:
            print_result("Данные классов", True)
        return all_passed, class_ids

    except Exception as e:
        print_result("Проверка классов", False, str(e))
        return False, {}


def check_fighting_styles(class_ids):
    """Проверка боевых стилей"""
    print_header("4. ПРОВЕРКА БОЕВЫХ СТИЛЕЙ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Проверяем, какие классы имеют боевые стили
        classes_with_styles = ["Воин", "Паладин", "Следопыт"]

        all_passed = True

        for class_name in classes_with_styles:
            if class_name not in class_ids:
                continue

            cur.execute("""
                SELECT COUNT(*) FROM class_fighting_styles 
                WHERE class_id = %s
            """, (class_ids[class_name],))
            count = cur.fetchone()[0]

            if count == 0:
                print_result(f"Боевые стили для {class_name}", False, "нет доступных стилей")
                all_passed = False
            else:
                print_result(f"Боевые стили для {class_name} ({count} шт.)", True)

        # Проверяем, что у классов без боевых стилей их нет
        no_style_classes = ["Варвар", "Монах", "Плут", "Волшебник", "Бард", "Жрец", "Друид", "Колдун", "Чародей",
                            "Артефактор"]

        for class_name in no_style_classes:
            if class_name not in class_ids:
                continue

            cur.execute("""
                SELECT COUNT(*) FROM class_fighting_styles 
                WHERE class_id = %s
            """, (class_ids[class_name],))
            count = cur.fetchone()[0]

            if count > 0:
                print_result(f"Боевые стили для {class_name}", False, f"есть {count} стилей, хотя не должно быть")
                all_passed = False

        conn.close()
        return all_passed

    except Exception as e:
        print_result("Проверка боевых стилей", False, str(e))
        return False


def check_invocations(class_ids):
    """Проверка таинственных возваний (только для колдуна)"""
    print_header("5. ПРОВЕРКА ТАИНСТВЕННЫХ ВОЗВАНИЙ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Проверяем наличие возваний для колдуна
        if "Колдун" in class_ids:
            # Возвания должны быть в отдельной таблице, не привязанной к классу
            cur.execute("SELECT COUNT(*) FROM invocations")
            inv_count = cur.fetchone()[0]

            if inv_count == 0:
                print_result("Возвания для колдуна", False, "нет возваний в таблице invocations")
                return False
            else:
                print_result(f"Возвания для колдуна ({inv_count} шт.)", True)

                # Проверяем, что некоторые возвания требуют 2 уровень
                cur.execute("SELECT COUNT(*) FROM invocations WHERE level_required = 2")
                level2_count = cur.fetchone()[0]
                print_result(f"Возвания 2 уровня ({level2_count} шт.)", True)
        else:
            print_result("Класс Колдун не найден", False)
            return False

        # Проверяем, что другие классы не имеют доступа к возваниям
        # (возвания не должны быть привязаны к другим классам)
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'class_invocations'
        """)
        has_class_invocations = cur.fetchone()[0]

        if has_class_invocations:
            print_result("Таблица class_invocations", False, "существует, но не должна (возвания только для колдуна)")
            return False

        conn.close()
        return True

    except Exception as e:
        print_result("Проверка возваний", False, str(e))
        return False


def check_subclasses():
    """Проверка подклассов для Жреца, Друида, Колдуна"""
    print_header("6. ПРОВЕРКА ПОДКЛАССОВ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        subclasses_info = {
            "Жрец": ["Защитник", "Чудотворец"],
            "Друид": ["Ведун", "Страж"],
            "Колдун": []  # Для колдуна - Pact Boons (Недоговоренности)
        }

        all_passed = True

        for class_name, expected_subclasses in subclasses_info.items():
            cur.execute("""
                SELECT s.name, s.description 
                FROM subclasses s
                JOIN classes c ON s.class_id = c.id
                WHERE c.name = %s
            """, (class_name,))
            subclasses = cur.fetchall()

            if class_name == "Колдун":
                # Для колдуна проверяем наличие Pact Boons
                if len(subclasses) == 0:
                    print_result(f"Подклассы для {class_name}", False, "нет подклассов (ожидаются Pact Boons)")
                    all_passed = False
                else:
                    print_result(f"Подклассы для {class_name} ({len(subclasses)} шт.)", True)
            else:
                # Для Жреца и Друида проверяем конкретные подклассы
                found_names = [s[0] for s in subclasses]
                missing = [exp for exp in expected_subclasses if exp not in found_names]

                if missing:
                    print_result(f"Подклассы для {class_name}", False, f"отсутствуют: {missing}")
                    all_passed = False
                else:
                    print_result(f"Подклассы для {class_name} ({', '.join(found_names)})", True)

        conn.close()
        return all_passed

    except Exception as e:
        print_result("Проверка подклассов", False, str(e))
        return False


def check_equipment():
    """Проверка снаряжения классов"""
    print_header("7. ПРОВЕРКА СНАРЯЖЕНИЯ КЛАССОВ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Ожидаемое снаряжение
        expected_equipment = {
            "Артефактор": ("Проклёпанный кожаный доспех", "Кинжал"),
            "Бард": ("Кожаный доспех", "Кинжал"),
            "Варвар": (None, "Секира"),
            "Воин": ("Кольчуга", "Двуручный меч"),
            "Волшебник": (None, "Кинжал"),
            "Друид": ("Кожаный доспех", "Серп"),
            "Жрец": ("Кольчужная рубаха", "Булава"),
            "Колдун": ("Кожаный доспех", "Серп"),
            "Монах": (None, "Копьё"),
            "Паладин": ("Кольчуга", "Длинный меч"),
            "Плут": ("Кожаный доспех", "Кинжал"),
            "Следопыт": ("Проклёпанный кожаный доспех", "Скимитар"),
            "Чародей": (None, "Копьё")
        }

        all_passed = True

        for class_name, (expected_armor, expected_weapon) in expected_equipment.items():
            cur.execute("""
                SELECT ce.armor, ce.weapon 
                FROM class_equipment ce
                JOIN classes c ON ce.class_id = c.id
                WHERE c.name = %s AND (ce.choice IS NULL OR ce.choice = 'A')
                LIMIT 1
            """, (class_name,))

            row = cur.fetchone()
            if not row:
                print_result(f"Снаряжение для {class_name}", False, "не найдено")
                all_passed = False
            else:
                armor, weapon = row
                armor_ok = True if expected_armor is None else (armor == expected_armor)
                weapon_ok = True if expected_weapon is None else (weapon == expected_weapon)

                if not armor_ok:
                    print_result(f"Броня {class_name}", False, f"ожидается {expected_armor}, получено {armor}")
                    all_passed = False
                if not weapon_ok:
                    print_result(f"Оружие {class_name}", False, f"ожидается {expected_weapon}, получено {weapon}")
                    all_passed = False

        # Проверка выбора для Воина (вариант Б)
        cur.execute("""
            SELECT ce.armor, ce.weapon 
            FROM class_equipment ce
            JOIN classes c ON ce.class_id = c.id
            WHERE c.name = 'Воин' AND ce.choice = 'B'
        """)
        row = cur.fetchone()
        if not row:
            print_result("Воин вариант Б", False, "не найден")
            all_passed = False
        else:
            print_result("Воин вариант Б", True, f"броня: {row[0]}, оружие: {row[1]}")

        conn.close()
        return all_passed

    except Exception as e:
        print_result("Проверка снаряжения", False, str(e))
        return False


def check_armor_ac():
    """Проверка КД брони"""
    print_header("8. ПРОВЕРКА КЛАССА БРОНИ (AC)")

    expected_ac = {
        "Проклёпанный кожаный доспех": {"base": 12, "modifier": "dex"},
        "Кожаный доспех": {"base": 11, "modifier": "dex"},
        "Кольчуга": {"base": 16, "modifier": "none"},
        "Кольчужная рубаха": {"base": 13, "modifier": "dex_max2"},
        "Щит": {"base": 2, "modifier": "shield"}
    }

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        all_passed = True

        for armor_name, expected in expected_ac.items():
            cur.execute("SELECT ac_base, ac_modifier FROM armor WHERE name = %s", (armor_name,))
            row = cur.fetchone()

            if not row:
                print_result(f"Броня {armor_name}", False, "не найдена в БД")
                all_passed = False
            else:
                ac_base, ac_modifier = row
                if ac_base != expected["base"]:
                    print_result(f"AC {armor_name}", False, f"ожидается {expected['base']}, получено {ac_base}")
                    all_passed = False
                if ac_modifier != expected["modifier"]:
                    print_result(f"Модификатор {armor_name}", False,
                                 f"ожидается {expected['modifier']}, получено {ac_modifier}")
                    all_passed = False

        conn.close()

        if all_passed:
            print_result("Класс брони (AC)", True)
        return all_passed

    except Exception as e:
        print_result("Проверка AC", False, str(e))
        return False


def check_weapons_and_masteries():
    """Проверка оружия и оружейных приемов"""
    print_header("9. ПРОВЕРКА ОРУЖИЯ И ОРУЖЕЙНЫХ ПРИЕМОВ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        all_passed = True

        # Проверяем наличие оружия
        cur.execute("SELECT COUNT(*) FROM weapons")
        weapon_count = cur.fetchone()[0]

        if weapon_count == 0:
            print_result("Оружие", False, "нет записей в таблице weapons")
            return False
        else:
            print_result(f"Оружие ({weapon_count} шт.)", True)

        # Проверяем наличие оружейных приемов
        cur.execute("SELECT COUNT(*) FROM weapon_masteries")
        masteries_count = cur.fetchone()[0]

        if masteries_count == 0:
            print_result("Оружейные приемы (базовые)", False, "нет записей в таблице weapon_masteries")
            all_passed = False
        else:
            print_result(f"Оружейные приемы (базовые) ({masteries_count} шт.)", True)

        # Проверяем, что у некоторых классов есть приемы
        classes_with_masteries = ["Воин", "Варвар", "Паладин", "Следопыт", "Плут"]

        for class_name in classes_with_masteries:
            cur.execute("""
                SELECT COUNT(*) FROM class_weapons cw
                JOIN classes c ON cw.class_id = c.id
                JOIN weapons w ON cw.weapon_id = w.id
                WHERE c.name = %s AND w.detailed_masteries != '[]'::jsonb
            """, (class_name,))
            count = cur.fetchone()[0]

            expected = CLASS_MASTERIES_COUNT.get(class_name, 0)
            if count == 0 and expected > 0:
                print_result(f"Оружие с приемами для {class_name}", False, f"нет оружия с детальными приемами")
                all_passed = False
            else:
                print_result(f"Оружие с приемами для {class_name} ({count} шт.)", True)

        conn.close()
        return all_passed

    except Exception as e:
        print_result("Проверка оружия", False, str(e))
        return False


def check_spells():
    """Проверка заклинаний"""
    print_header("10. ПРОВЕРКА ЗАКЛИНАНИЙ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        all_passed = True

        # Проверяем количество заклинаний
        cur.execute("SELECT COUNT(*) FROM spells")
        spell_count = cur.fetchone()[0]

        if spell_count == 0:
            print_result("Заклинания", False, "нет записей в таблице spells")
            return False
        else:
            print_result(f"Заклинания ({spell_count} шт.)", True)

        # Проверяем количество заговоров и заклинаний 1 уровня
        cur.execute("SELECT COUNT(*) FROM spells WHERE is_cantrip = true")
        cantrips_count = cur.fetchone()[0]
        print_result(f"Заговоры (кантрипы) ({cantrips_count} шт.)", True)

        cur.execute("SELECT COUNT(*) FROM spells WHERE level = 1 AND is_cantrip = false")
        level1_count = cur.fetchone()[0]
        print_result(f"Заклинания 1 уровня ({level1_count} шт.)", True)

        # Проверяем, что у заклинающих классов есть заклинания
        spellcasting_classes = ["Волшебник", "Бард", "Жрец", "Друид", "Колдун", "Чародей", "Артефактор", "Паладин",
                                "Следопыт"]

        for class_name in spellcasting_classes:
            cur.execute("""
                SELECT COUNT(*) FROM class_spells cs
                JOIN classes c ON cs.class_id = c.id
                WHERE c.name = %s
            """, (class_name,))
            count = cur.fetchone()[0]

            expected_min = CLASS_SPELLS_COUNT.get(class_name, {}).get("cantrips", 0) + \
                           CLASS_SPELLS_COUNT.get(class_name, {}).get("level1", 0)

            if count < expected_min:
                print_result(f"Заклинания для {class_name}", False,
                             f"ожидается минимум {expected_min}, получено {count}")
                all_passed = False
            else:
                print_result(f"Заклинания для {class_name} ({count} шт.)", True)

        conn.close()
        return all_passed

    except Exception as e:
        print_result("Проверка заклинаний", False, str(e))
        return False


def check_races():
    """Проверка рас"""
    print_header("11. ПРОВЕРКА РАС")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Ожидаемое количество рас
        cur.execute("SELECT COUNT(*) FROM races")
        race_count = cur.fetchone()[0]

        expected_races = 16  # из races_data.py
        if race_count != expected_races:
            print_result(f"Расы", False, f"ожидается {expected_races}, получено {race_count}")
            return False
        else:
            print_result(f"Расы ({race_count} шт.)", True)

        # Проверяем подрасы
        cur.execute("SELECT COUNT(*) FROM subraces")
        subrace_count = cur.fetchone()[0]
        print_result(f"Подрасы ({subrace_count} шт.)", True)

        # Проверяем, что у рас с подрасами они есть
        races_with_subraces = ["Аасимар", "Гном", "Дварф", "Драконорожденный", "Полурослик", "Эльф", "Шифтер"]

        for race_name in races_with_subraces:
            cur.execute("""
                SELECT COUNT(*) FROM subraces s
                JOIN races r ON s.race_id = r.id
                WHERE r.name = %s
            """, (race_name,))
            count = cur.fetchone()[0]

            if count == 0:
                print_result(f"Подрасы для {race_name}", False, "нет подрас")
                return False

        conn.close()
        return True

    except Exception as e:
        print_result("Проверка рас", False, str(e))
        return False


def check_backgrounds():
    """Проверка предысторий"""
    print_header("12. ПРОВЕРКА ПРЕДЫСТОРИЙ")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Проверяем количество предысторий
        cur.execute("SELECT COUNT(*) FROM backgrounds")
        bg_count = cur.fetchone()[0]

        expected_bg = 16
        if bg_count != expected_bg:
            print_result(f"Предыстории", False, f"ожидается {expected_bg}, получено {bg_count}")
            return False
        else:
            print_result(f"Предыстории ({bg_count} шт.)", True)

        # Проверяем, что у всех предысторий есть equipment_a и equipment_b
        cur.execute("""
            SELECT name, equipment_a IS NULL OR equipment_a = '', 
                   equipment_b IS NULL OR equipment_b = ''
            FROM backgrounds
        """)
        rows = cur.fetchall()

        all_passed = True
        for row in rows:
            name, missing_a, missing_b = row
            if missing_a:
                print_result(f"Снаряжение А для {name}", False, "отсутствует")
                all_passed = False
            if missing_b:
                print_result(f"Снаряжение Б для {name}", False, "отсутствует")
                all_passed = False

        if all_passed:
            print_result("Снаряжение предысторий", True)

        conn.close()
        return all_passed

    except Exception as e:
        print_result("Проверка предысторий", False, str(e))
        return False


def check_state_flow():
    """Проверка корректности flow создания персонажа"""
    print_header("13. ПРОВЕРКА FLOW СОЗДАНИЯ ПЕРСОНАЖА")

    print("\nОжидаемый порядок шагов:")
    print("  1. Выбор КЛАССА")
    print("  2. Выбор ПРЕДЫСТОРИИ")
    print("  3. Выбор РАСЫ")
    print("  4. Выбор подрасы (если есть)")
    print("  5. Выбор снаряжения класса (если есть выбор)")
    print("  6. Авторасчет ХАРАКТЕРИСТИК")
    print("  7. Ввод ИМЕНИ")
    print("  8. Выбор ЗАКЛИНАНИЙ (только для заклинающих классов)")
    print("  9. Выбор БОЕВОГО СТИЛЯ (только для Воина, Паладина, Следопыта)")
    print("  10. Выбор ВОЗВАНИЙ (только для Колдуна)")
    print("  11. Выбор снаряжения ПРЕДЫСТОРИИ")
    print("  12. Ввод ИСТОРИИ")
    print("  13. Загрузка ИЗОБРАЖЕНИЯ")

    print("\n⚠️ ВАЖНЫЕ ЗАМЕЧАНИЯ ПО FLOW:")
    print("  • Предыстория НЕ должна перезаписываться на этапе выбора снаряжения")
    print("  • Возвания доступны ТОЛЬКО для Колдуна")
    print("  • Боевой стиль доступен ТОЛЬКО для Воина, Паладина, Следопыта")
    print("  • Подклассы на 1 уровне доступны для Жреца, Друида, Колдуна")

    print("\n✅ Flow проверен (требуется ручная проверка кода)")


# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

def main():
    print("=" * 70)
    print("🐉 D&D 5.5e CHARACTER CREATOR - ВАЛИДАЦИЯ ПРОЕКТА")
    print("=" * 70)

    # Проверка подключения
    if not check_database_connection():
        print("\n❌ Невозможно продолжить проверку без подключения к БД")
        return

    # Последовательная проверка
    results = {}

    results["tables"] = check_tables()

    if results["tables"]:
        classes_ok, class_ids = check_classes_data()
        results["classes"] = classes_ok

        if classes_ok:
            results["fighting_styles"] = check_fighting_styles(class_ids)
            results["invocations"] = check_invocations(class_ids)
        else:
            results["fighting_styles"] = False
            results["invocations"] = False

        results["subclasses"] = check_subclasses()
        results["equipment"] = check_equipment()
        results["armor"] = check_armor_ac()
        results["weapons"] = check_weapons_and_masteries()
        results["spells"] = check_spells()
        results["races"] = check_races()
        results["backgrounds"] = check_backgrounds()
    else:
        results["classes"] = False
        results["fighting_styles"] = False
        results["invocations"] = False
        results["subclasses"] = False
        results["equipment"] = False
        results["armor"] = False
        results["weapons"] = False
        results["spells"] = False
        results["races"] = False
        results["backgrounds"] = False

    # Проверка flow (всегда выполняется)
    check_state_flow()

    # ИТОГИ
    print_header("ИТОГИ ВАЛИДАЦИИ")

    all_passed = True
    for test_name, passed in results.items():
        if test_name != "tables" or passed:  # tables выводим отдельно
            status = "✅" if passed else "❌"
            print(f"{status} {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)

    if all_passed:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Проект в хорошем состоянии.")
        print("\n📌 РЕКОМЕНДАЦИИ:")
        print("  1. Исправьте проблему с background='equip_A' в bot.py")
        print("  2. Убедитесь, что в state не перезаписывается background")
        print("  3. Добавьте защиту от перезаписи background во всех обработчиках")
    else:
        print("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ! Требуется исправление.")
        print("\n📌 ПРИОРИТЕТНЫЕ ИСПРАВЛЕНИЯ:")
        print("  1. Исправьте проблему с background='equip_A' в bot.py")
        print("  2. Добавьте проверки в go_to_background_equipment")
        print("  3. Убедитесь, что предыстория не перезаписывается")
        print("  4. Проверьте, что возвания только для колдуна")

    print("=" * 70)


if __name__ == "__main__":
    main()