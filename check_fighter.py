# test_fighting_styles.py
"""
Диагностический скрипт для проверки боевых стилей
Запуск: python test_fighting_styles.py
"""

import asyncio
import sys
import os
from typing import Dict, Any, List

# Добавляем текущую директорию в путь
sys.path.insert(0, os.getcwd())

from dotenv import load_dotenv

load_dotenv()

from db import get_connection
from dnd_logic import get_fighting_styles_for_class, get_class_list
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Цвета для вывода
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{'=' * 70}{Colors.END}")
    print(f"{Colors.HEADER}{text}{Colors.END}")
    print(f"{Colors.HEADER}{'=' * 70}{Colors.END}")


def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.END}")


def print_info(text: str):
    print(f"{Colors.BLUE}📌 {text}{Colors.END}")


# ============================================================
# ТЕСТ 1: ПРОВЕРКА ТАБЛИЦЫ fighting_styles
# ============================================================

def test_fighting_styles_table():
    """Проверяет наличие и содержимое таблицы fighting_styles"""
    print_header("ТЕСТ 1: Проверка таблицы fighting_styles")

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Проверяем количество записей
                cur.execute("SELECT COUNT(*) FROM fighting_styles")
                count = cur.fetchone()[0]
                print_info(f"Всего записей в fighting_styles: {count}")

                if count == 0:
                    print_error("Таблица fighting_styles пуста! Нужно добавить боевые стили.")
                    return False

                # Выводим все стили
                cur.execute("SELECT id, name, description FROM fighting_styles ORDER BY name")
                styles = cur.fetchall()
                print_info("\nСписок боевых стилей:")
                for s in styles:
                    print(f"   {s[0]}: {s[1]} - {s[2][:50]}...")

                return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False


# ============================================================
# ТЕСТ 2: ПРОВЕРКА СВЯЗЕЙ С КЛАССАМИ
# ============================================================

def test_class_fighting_styles():
    """Проверяет связи между классами и боевыми стилями"""
    print_header("ТЕСТ 2: Проверка связей классов с боевыми стилями")

    classes_to_check = ["Воин", "Варвар", "Паладин", "Следопыт"]

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                for class_name in classes_to_check:
                    cur.execute("""
                        SELECT c.id, c.name, COUNT(cfs.style_id) as style_count
                        FROM classes c
                        LEFT JOIN class_fighting_styles cfs ON c.id = cfs.class_id
                        WHERE c.name = %s
                        GROUP BY c.id, c.name
                    """, (class_name,))
                    result = cur.fetchone()

                    if not result:
                        print_error(f"Класс {class_name} не найден в БД!")
                        continue

                    class_id, name, style_count = result

                    if style_count == 0:
                        print_warning(f"{name} (ID: {class_id}) - НЕТ СВЯЗАННЫХ СТИЛЕЙ!")

                        # Показываем доступные стили для связывания
                        cur.execute("SELECT id, name FROM fighting_styles")
                        all_styles = cur.fetchall()
                        print_info(f"   Доступные стили для связывания: {[s[1] for s in all_styles]}")
                    else:
                        print_success(f"{name} (ID: {class_id}) - {style_count} стилей")

                        # Показываем какие стили связаны
                        cur.execute("""
                            SELECT fs.id, fs.name 
                            FROM class_fighting_styles cfs
                            JOIN fighting_styles fs ON cfs.style_id = fs.id
                            WHERE cfs.class_id = %s
                        """, (class_id,))
                        linked_styles = cur.fetchall()
                        for ls in linked_styles:
                            print(f"      - {ls[1]}")

                return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False


# ============================================================
# ТЕСТ 3: ПРОВЕРКА ФУНКЦИИ get_fighting_styles_for_class
# ============================================================

def test_get_fighting_styles_function():
    """Проверяет функцию get_fighting_styles_for_class"""
    print_header("ТЕСТ 3: Проверка функции get_fighting_styles_for_class")

    classes_to_check = ["Воин", "Варвар", "Паладин", "Следопыт", "Волшебник"]

    for class_name in classes_to_check:
        try:
            styles = get_fighting_styles_for_class(class_name)
            print_info(f"{class_name}: {len(styles)} стилей")

            if styles:
                for s in styles:
                    print(f"   - {s['name']}: {s['description'][:50]}...")
            else:
                if class_name in ["Воин", "Варвар", "Паладин", "Следопыт"]:
                    print_warning(f"  ⚠️ {class_name} должен иметь боевые стили, но функция вернула пустой список!")
                else:
                    print_info(f"  (Для {class_name} боевые стили не предусмотрены - это нормально)")

        except Exception as e:
            print_error(f"Ошибка для {class_name}: {e}")

    return True


# ============================================================
# ТЕСТ 4: ПРОВЕРКА СОЗДАНИЯ КЛАВИАТУРЫ
# ============================================================

def test_keyboard_creation():
    """Проверяет создание клавиатуры для выбора боевых стилей"""
    print_header("ТЕСТ 4: Проверка создания клавиатуры")

    def create_fighting_style_keyboard(class_name: str):
        styles = get_fighting_styles_for_class(class_name)

        if not styles:
            return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➡️ Продолжить (нет стилей)", callback_data="style_skip")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_spells")]
            ])

        buttons = []
        for s in styles:
            buttons.append([InlineKeyboardButton(
                text=f"🛡️ {s['name']}: {s['description'][:50]}",
                callback_data=f"style_{s['id']}"
            )])

        buttons.append([InlineKeyboardButton(text="➡️ Пропустить", callback_data="style_skip")])
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_spells")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    classes_to_check = ["Воин", "Варвар", "Паладин", "Следопыт"]

    for class_name in classes_to_check:
        try:
            keyboard = create_fighting_style_keyboard(class_name)
            print_success(f"Клавиатура для {class_name} создана")
            print_info(f"   Количество кнопок: {len(keyboard.inline_keyboard)}")
        except Exception as e:
            print_error(f"Ошибка создания клавиатуры для {class_name}: {e}")

    return True


# ============================================================
# ТЕСТ 5: ДОБАВЛЕНИЕ ОТСУТСТВУЮЩИХ ДАННЫХ
# ============================================================

def add_missing_fighting_styles():
    """Добавляет боевые стили, если их нет"""
    print_header("ТЕСТ 5: Добавление отсутствующих данных")

    styles_to_add = [
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

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Проверяем, есть ли уже стили
                cur.execute("SELECT COUNT(*) FROM fighting_styles")
                existing = cur.fetchone()[0]

                if existing > 0:
                    print_info(f"В БД уже есть {existing} стилей. Пропускаем добавление.")
                    user_input = input("Хотите добавить недостающие стили? (y/n): ")
                    if user_input.lower() != 'y':
                        return True

                # Добавляем стили
                added = 0
                for name, desc in styles_to_add:
                    cur.execute("""
                        INSERT INTO fighting_styles (name, description)
                        VALUES (%s, %s)
                        ON CONFLICT (name) DO NOTHING
                    """, (name, desc))
                    if cur.rowcount > 0:
                        added += 1
                        print_success(f"  Добавлен стиль: {name}")

                conn.commit()
                print_info(f"Добавлено {added} новых стилей")

    except Exception as e:
        print_error(f"Ошибка добавления стилей: {e}")
        return False

    return True


def add_class_style_links():
    """Добавляет связи между классами и стилями"""
    print_header("ТЕСТ 5b: Добавление связей классов со стилями")

    # Стили для каждого класса
    class_styles = {
        "Воин": ["Дуэлянт", "Защита", "Оборона", "Перехват", "Сражение без оружия",
                 "Сражение большим оружием", "Сражение вслепую", "Сражение двумя оружиями",
                 "Сражение метательным оружием", "Стрельба"],
        "Варвар": ["Оборона", "Сражение без оружия", "Сражение большим оружием",
                   "Сражение вслепую", "Сражение двумя оружиями"],
        "Паладин": ["Дуэлянт", "Защита", "Оборона", "Перехват", "Сражение без оружия",
                    "Сражение большим оружием", "Сражение вслепую"],
        "Следопыт": ["Дуэлянт", "Защита", "Оборона", "Сражение вслепую",
                     "Сражение двумя оружиями", "Сражение метательным оружием", "Стрельба"]
    }

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Получаем ID классов
                class_ids = {}
                for class_name in class_styles.keys():
                    cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                    result = cur.fetchone()
                    if result:
                        class_ids[class_name] = result[0]
                        print_success(f"Класс {class_name}: ID={result[0]}")
                    else:
                        print_error(f"Класс {class_name} не найден в БД!")
                        return False

                # Получаем ID стилей
                style_ids = {}
                cur.execute("SELECT id, name FROM fighting_styles")
                for row in cur.fetchall():
                    style_ids[row[1]] = row[0]

                print_info(f"Найдено стилей: {len(style_ids)}")

                # Добавляем связи
                total_added = 0
                for class_name, styles_list in class_styles.items():
                    class_id = class_ids.get(class_name)
                    if not class_id:
                        continue

                    added = 0
                    for style_name in styles_list:
                        style_id = style_ids.get(style_name)
                        if style_id:
                            cur.execute("""
                                INSERT INTO class_fighting_styles (class_id, style_id)
                                VALUES (%s, %s)
                                ON CONFLICT (class_id, style_id) DO NOTHING
                            """, (class_id, style_id))
                            if cur.rowcount > 0:
                                added += 1
                                total_added += 1

                    print_success(f"  {class_name}: добавлено {added} связей")

                conn.commit()
                print_info(f"Всего добавлено {total_added} связей")

    except Exception as e:
        print_error(f"Ошибка добавления связей: {e}")
        return False

    return True


# ============================================================
# ТЕСТ 6: ПРОВЕРКА masteries_count
# ============================================================

def test_masteries_count():
    """Проверяет количество оружейных приёмов для классов"""
    print_header("ТЕСТ 6: Проверка masteries_count")

    expected_masteries = {
        "Воин": 3,
        "Варвар": 2,
        "Паладин": 2,
        "Следопыт": 2,
        "Плут": 1
    }

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                for class_name, expected in expected_masteries.items():
                    cur.execute("SELECT masteries_count FROM classes WHERE name = %s", (class_name,))
                    result = cur.fetchone()
                    if result:
                        actual = result[0]
                        if actual == expected:
                            print_success(f"{class_name}: {actual} приёмов (OK)")
                        else:
                            print_warning(f"{class_name}: {actual} приёмов (должно быть {expected})")

                            # Исправляем, если нужно
                            cur.execute("UPDATE classes SET masteries_count = %s WHERE name = %s",
                                        (expected, class_name))
                            print_info(f"   Исправлено на {expected}")
                    else:
                        print_error(f"Класс {class_name} не найден")

                conn.commit()

    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False

    return True


# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

async def main():
    print_header("🐉 ДИАГНОСТИКА БОЕВЫХ СТИЛЕЙ")

    # Тест 1: Проверка таблицы
    if not test_fighting_styles_table():
        print_info("\nХотите добавить боевые стили?")
        user_input = input("Нажмите Enter для добавления или Ctrl+C для выхода: ")
        if not add_missing_fighting_styles():
            print_error("Не удалось добавить стили")
            return

    # Тест 2: Проверка связей
    test_class_fighting_styles()

    # Тест 3: Проверка функции
    test_get_fighting_styles_function()

    # Тест 4: Проверка клавиатуры
    test_keyboard_creation()

    # Тест 5: Добавление связей (если нужно)
    print_info("\nПроверка связей классов со стилями...")
    user_input = input("Добавить недостающие связи? (y/n): ")
    if user_input.lower() == 'y':
        add_class_style_links()

    # Тест 6: Проверка masteries_count
    test_masteries_count()

    # Финальный отчёт
    print_header("РЕЗУЛЬТАТЫ ДИАГНОСТИКИ")

    # Проверяем финальное состояние
    with get_connection() as conn:
        with conn.cursor() as cur:
            for class_name in ["Воин", "Варвар", "Паладин", "Следопыт"]:
                cur.execute("""
                    SELECT COUNT(cfs.style_id) 
                    FROM class_fighting_styles cfs
                    JOIN classes c ON cfs.class_id = c.id
                    WHERE c.name = %s
                """, (class_name,))
                count = cur.fetchone()[0]

                if count > 0:
                    print_success(f"{class_name}: {count} боевых стилей")
                else:
                    print_error(f"{class_name}: НЕТ БОЕВЫХ СТИЛЕЙ!")

    print_header("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")


if __name__ == "__main__":
    asyncio.run(main())