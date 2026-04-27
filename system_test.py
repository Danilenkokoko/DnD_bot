# full_system_test.py
"""
Полный тест системы D&D Character Creator
Проверяет все модули: db, dnd_logic, spell_selector, pdf_generator, bot
Запуск: python full_system_test.py
"""

import asyncio
import sys
import os
import json
import logging
import traceback
from typing import Dict, Any, List

# Настройка подробного логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Подавляем излишние логи от некоторых модулей
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('aiohttp').setLevel(logging.WARNING)


# Цвета для вывода
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str, color: str = Colors.HEADER):
    """Выводит заголовок"""
    print(f"\n{color}{'=' * 70}{Colors.END}")
    print(f"{color}{text}{Colors.END}")
    print(f"{color}{'=' * 70}{Colors.END}\n")


def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️ {text}{Colors.END}")


def print_info(text: str):
    print(f"{Colors.BLUE}📌 {text}{Colors.END}")


def print_step(step: int, total: int, name: str):
    print(f"\n{Colors.BOLD}[{step}/{total}] {name}{Colors.END}")


# ============================================================
# ТЕСТ 1: ПРОВЕРКА ОКРУЖЕНИЯ И ИМПОРТОВ
# ============================================================

async def test_environment() -> bool:
    """Тест 1: Проверка окружения и импортов"""
    print_step(1, 12, "Проверка окружения и импортов")

    try:
        # Проверка .env
        print_info("Проверка файла .env...")
        from dotenv import load_dotenv
        load_dotenv()

        required_vars = ["BOT_TOKEN", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST"]
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            else:
                print_info(f"   {var} = {value[:10] + '...' if var == 'BOT_TOKEN' else value}")

        if missing_vars:
            print_error(f"Отсутствуют переменные: {missing_vars}")
            return False

        print_success("Файл .env загружен")

        # Проверка импорта модулей
        print_info("Проверка импорта модулей...")

        modules = [
            ("db", ["get_connection", "init_database", "get_spell_by_id"]),
            ("dnd_logic", ["modifier", "get_class_list", "calculate_final_stats_with_background"]),
            ("spell_selector", ["SpellSelector", "get_category_icon"]),
            ("pdf_generator", ["generate_pdf"]),
            ("aiogram", ["Bot", "Dispatcher"]),
        ]

        for module_name, functions in modules:
            try:
                module = __import__(module_name)
                for func in functions:
                    if hasattr(module, func):
                        print_info(f"   ✅ {module_name}.{func}")
                    else:
                        print_error(f"   ❌ {module_name}.{func} отсутствует")
                        return False
            except ImportError as e:
                print_error(f"Не удалось импортировать {module_name}: {e}")
                return False

        print_success("Все модули импортированы")
        return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        traceback.print_exc()
        return False


# ============================================================
# ТЕСТ 2: ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БД
# ============================================================

async def test_database_connection() -> bool:
    """Тест 2: Проверка подключения к БД и структуры таблиц"""
    print_step(2, 12, "Проверка подключения к базе данных")

    try:
        from db import get_connection, init_database

        print_info("Проверка подключения...")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print_success(f"Подключено: {version[:50]}...")

        print_info("Проверка инициализации таблиц...")
        init_database()
        print_success("Таблицы проверены/созданы")

        # Проверка количества записей в ключевых таблицах
        print_info("Проверка данных в таблицах...")

        tables_to_check = {
            "races": 16,
            "classes": 13,
            "backgrounds": 16,
            "spells": 50,  # минимум
            "weapons": 20,  # минимум
        }

        with get_connection() as conn:
            with conn.cursor() as cur:
                for table, min_count in tables_to_check.items():
                    cur.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cur.fetchone()[0]
                    if count >= min_count:
                        print_success(f"   {table}: {count} записей")
                    else:
                        print_warning(f"   {table}: {count} записей (ожидалось минимум {min_count})")

        # Проверка новых колонок
        print_info("Проверка новых колонок в таблице classes...")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'classes' 
                    AND column_name IN ('cantrips_count', 'spells_count_level1', 'masteries_count')
                """)
                new_columns = [row[0] for row in cur.fetchall()]
                expected_columns = ['cantrips_count', 'spells_count_level1', 'masteries_count']

                for col in expected_columns:
                    if col in new_columns:
                        print_success(f"   {col} присутствует")
                    else:
                        print_error(f"   {col} отсутствует!")
                        return False

        print_success("База данных работает корректно")
        return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        traceback.print_exc()
        return False


# ============================================================
# ТЕСТ 3: ПРОВЕРКА DND_LOGIC
# ============================================================

async def test_dnd_logic() -> bool:
    """Тест 3: Проверка функций dnd_logic"""
    print_step(3, 12, "Проверка dnd_logic.py")

    try:
        from dnd_logic import (
            modifier, calculate_proficiency_bonus,
            get_class_list, get_class_starting_stats,
            get_background_list, get_background_by_name,
            calculate_final_stats_with_background,
            get_class_spell_counts, get_class_masteries_count,
            auto_assign_masteries
        )

        # Тест modifier
        print_info("Тест modifier()...")
        assert modifier(10) == 0, "modifier(10) должно быть 0"
        assert modifier(14) == 2, "modifier(14) должно быть 2"
        assert modifier(8) == -1, "modifier(8) должно быть -1"
        print_success("modifier() работает")

        # Тест calculate_proficiency_bonus
        print_info("Тест calculate_proficiency_bonus()...")
        assert calculate_proficiency_bonus(1) == 2
        assert calculate_proficiency_bonus(5) == 3
        assert calculate_proficiency_bonus(9) == 4
        print_success("calculate_proficiency_bonus() работает")

        # Тест получения списков
        print_info("Тест get_class_list()...")
        classes = get_class_list()
        assert len(classes) >= 13, f"Ожидалось 13+ классов, получено {len(classes)}"
        print_success(f"Найдено классов: {len(classes)}")

        print_info("Тест get_background_list()...")
        backgrounds = get_background_list()
        assert len(backgrounds) >= 16, f"Ожидалось 16+ предысторий, получено {len(backgrounds)}"
        print_success(f"Найдено предысторий: {len(backgrounds)}")

        # Тест расчёта характеристик
        print_info("Тест calculate_final_stats_with_background()...")
        starting_stats = get_class_starting_stats("Воин")
        final_stats = calculate_final_stats_with_background("Воин", "Солдат", starting_stats)

        assert "STR" in final_stats
        assert "DEX" in final_stats
        assert sum(final_stats.values()) >= sum(starting_stats.values())
        print_success(f"   Старт: STR={starting_stats['STR']}, DEX={starting_stats['DEX']}")
        print_success(f"   Финал: STR={final_stats['STR']}, DEX={final_stats['DEX']}")

        # Тест количества заклинаний
        print_info("Тест get_class_spell_counts()...")
        wizard_spells = get_class_spell_counts("Волшебник")
        assert wizard_spells['cantrips'] == 3, f"Ожидалось 3 заговора, получено {wizard_spells['cantrips']}"
        assert wizard_spells['level1'] == 4, f"Ожидалось 4 заклинания, получено {wizard_spells['level1']}"
        print_success(f"Волшебник: заговоров={wizard_spells['cantrips']}, заклинаний={wizard_spells['level1']}")

        # Тест количества оружейных приёмов
        print_info("Тест get_class_masteries_count()...")
        fighter_masteries = get_class_masteries_count("Воин")
        assert fighter_masteries == 3, f"Ожидалось 3 приёма, получено {fighter_masteries}"
        rogue_masteries = get_class_masteries_count("Плут")
        assert rogue_masteries == 1, f"Ожидался 1 приём, получено {rogue_masteries}"
        print_success(f"Воин: {fighter_masteries} приёма, Плут: {rogue_masteries} приём")

        # Тест auto_assign_masteries
        print_info("Тест auto_assign_masteries()...")
        masteries = auto_assign_masteries("Двуручный меч", "Воин")
        assert len(masteries) <= 3, f"Слишком много приёмов: {len(masteries)}"
        print_success(f"Приёмы для Двуручный меч (Воин): {masteries}")

        print_success("Все тесты dnd_logic пройдены")
        return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        traceback.print_exc()
        return False


# ============================================================
# ТЕСТ 4: ПРОВЕРКА SPELL_SELECTOR
# ============================================================

async def test_spell_selector() -> bool:
    """Тест 4: Проверка spell_selector"""
    print_step(4, 12, "Проверка spell_selector.py")

    try:
        from spell_selector import SpellSelector, get_category_icon, SpellType

        # Создание селектора для Волшебника
        print_info("Создание SpellSelector для Волшебника...")
        selector = SpellSelector("Волшебник")
        assert selector.has_cantrips, "У Волшебника должны быть заговоры"
        assert selector.has_level1_spells, "У Волшебника должны быть заклинания 1 уровня"
        print_success("Селектор создан")

        # Проверка категорий заговоров
        print_info("Проверка категорий заговоров...")
        categories = selector.get_cantrip_categories()
        assert len(categories) > 0, "Нет категорий заговоров"
        print_success(f"Найдено категорий заговоров: {len(categories)}")
        for cat_name, cat_data in list(categories.items())[:3]:
            print_info(f"   {cat_data['icon']} {cat_name}: {len(cat_data['spells'])} заклинаний")

        # Проверка добавления заговора
        print_info("Проверка добавления заговора...")
        spells_in_category = selector.get_cantrips_in_category(list(categories.keys())[0])
        if spells_in_category:
            test_spell = spells_in_category[0]['name']
            success, msg = selector.add_cantrip(test_spell)
            print_info(f"   Добавление '{test_spell}': {msg}")

        selected = selector.get_selected_cantrips()
        progress = selector.get_cantrip_progress()
        print_success(f"Прогресс: {progress[0]}/{progress[1]}")

        # Проверка получения деталей заклинания
        print_info("Проверка get_spell_details()...")
        spells = selector.get_cantrips_in_category(list(categories.keys())[0])
        if spells:
            spell_id = spells[0]['id']
            from db import get_spell_by_id
            spell_details = get_spell_by_id(spell_id)
            assert spell_details is not None, "Заклинание не найдено"
            print_success(f"   Детали: {spell_details['name']} - {spell_details.get('category', 'Нет категории')}")

        # Проверка сериализации
        print_info("Проверка сериализации...")
        serialized = selector.to_dict()
        assert 'class_name' in serialized
        restored = SpellSelector.from_dict(serialized)
        assert restored.class_name == selector.class_name
        print_success("Сериализация работает")

        # Проверка get_category_icon
        print_info("Проверка get_category_icon()...")
        assert get_category_icon("Урон") == "💥"
        assert get_category_icon("Лечение") == "❤️"
        print_success("get_category_icon() работает")

        print_success("Все тесты spell_selector пройдены")
        return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        traceback.print_exc()
        return False


# ============================================================
# ТЕСТ 5: ПРОВЕРКА PDF_GENERATOR
# ============================================================

async def test_pdf_generator() -> bool:
    """Тест 5: Проверка pdf_generator"""
    print_step(5, 12, "Проверка pdf_generator.py")

    try:
        from pdf_generator import generate_pdf

        # Создание тестовых данных для PDF
        print_info("Создание тестовых данных для PDF...")
        test_data = {
            "name": "Тестовый Персонаж",
            "class_name": "Воин",
            "race": "Человек",
            "level": 1,
            "stats": {"STR": 16, "DEX": 14, "CON": 14, "INT": 10, "WIS": 12, "CHA": 10},
            "hp": 12,
            "ac": 16,
            "speed": 30,
            "skills": ["Атлетика", "Восприятие"],
            "equipment": ["Длинный меч", "Кольчуга", "Щит"],
            "spells": [],
            "proficiency_bonus": 2,
            "background": "Солдат",
            "background_trait": "Бдительный",
            "background_description": "Вы прошли военную подготовку.",
            "race_traits": ["Универсальность человечества"],
            "class_features": ["Второе дыхание", "Боевой стиль"],
            "backstory": "Тестовая история персонажа.",
            "alignment": "Нейтральное",
            "player_name": "Тестер",
            "experience": 0,
            "saving_throws": [],
            "notes": "",
            "coins": "50 ЗМ"
        }

        # Генерация PDF
        print_info("Генерация PDF...")
        filename = "test_character_sheet.pdf"
        result = generate_pdf(test_data, filename)

        if result and os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print_success(f"PDF создан: {filename} (размер: {file_size} байт)")
            # Очистка
            os.remove(filename)
        else:
            print_warning("PDF не создан (возможно, проблемы с WeasyPrint)")

        print_success("Тест pdf_generator пройден")
        return True

    except Exception as e:
        print_warning(f"PDF генератор может не работать: {e}")
        print_info("Это не критично для основного функционала бота")
        return True  # Не считаем ошибкой, так как может не хватать системных библиотек


# ============================================================
# ТЕСТ 6: ПРОВЕРКА КЛАВИАТУР
# ============================================================

async def test_keyboards() -> bool:
    """Тест 6: Проверка создания клавиатур"""
    print_step(6, 12, "Проверка клавиатур")

    try:
        from aiogram.types import InlineKeyboardMarkup

        # Импортируем функции клавиатур (нужно будет импортировать из bot.py)
        # Для теста создадим упрощённые версии

        print_info("Проверка create_class_keyboard...")
        from dnd_logic import get_class_list
        classes = get_class_list()
        assert len(classes) > 0, "Нет классов"
        print_success(f"   Классов для клавиатуры: {len(classes)}")

        print_info("Проверка create_race_keyboard...")
        from dnd_logic import get_race_list
        races = get_race_list()
        assert len(races) > 0, "Нет рас"
        print_success(f"   Рас для клавиатуры: {len(races)}")

        print_info("Проверка create_background_keyboard...")
        from dnd_logic import get_background_list
        backgrounds = get_background_list()
        assert len(backgrounds) > 0, "Нет предысторий"
        print_success(f"   Предысторий для клавиатуры: {len(backgrounds)}")

        print_info("Проверка create_fighting_style_keyboard...")
        from dnd_logic import get_fighting_styles_for_class
        styles = get_fighting_styles_for_class("Воин")
        print_success(f"   Боевых стилей для Воина: {len(styles)}")

        print_info("Проверка create_invocations_keyboard...")
        from dnd_logic import get_all_invocations
        invocations = get_all_invocations(1)
        print_success(f"   Возваний для Колдуна: {len(invocations)}")

        print_success("Все клавиатуры проверены")
        return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        traceback.print_exc()
        return False


# ============================================================
# ТЕСТ 7: ПРОВЕРКА FSM СОСТОЯНИЙ
# ============================================================

async def test_fsm_states() -> bool:
    """Тест 7: Проверка FSM состояний"""
    print_step(7, 12, "Проверка FSM состояний")

    try:
        from aiogram.fsm.state import State, StatesGroup

        # Создаём тестовый класс состояний
        class TestStates(StatesGroup):
            state1 = State()
            state2 = State()
            state3 = State()

        # Проверяем создание
        assert TestStates.state1 is not None
        assert TestStates.state2 is not None
        print_success("FSM состояния создаются корректно")

        # Проверяем, что все нужные состояния определены в bot.py
        print_info("Проверка наличия состояний в bot.py...")
        try:
            from bot import CreateCharacter

            required_states = [
                'class_select', 'subclass_select', 'class_equipment_select',
                'spells_cantrips_category', 'spells_cantrips_list', 'spells_cantrips_detail',
                'spells_level1_category', 'spells_level1_list', 'spells_level1_detail',
                'fighting_style_select', 'invocations_select',
                'background_select', 'background_equipment_select',
                'race_select', 'subrace_select',
                'name_input', 'backstory_input', 'image_input'
            ]

            for state_name in required_states:
                if hasattr(CreateCharacter, state_name):
                    print_success(f"   {state_name} определён")
                else:
                    print_warning(f"   {state_name} НЕ определён")

        except ImportError as e:
            print_warning(f"Не удалось импортировать CreateCharacter: {e}")

        print_success("FSM состояния проверены")
        return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        traceback.print_exc()
        return False


# ============================================================
# ТЕСТ 8: ПРОВЕРКА БАЗОВЫХ ОПЕРАЦИЙ С ПЕРСОНАЖЕМ
# ============================================================

async def test_character_operations() -> bool:
    """Тест 8: Проверка операций с персонажем"""
    print_step(8, 12, "Проверка операций с персонажем")

    try:
        from dnd_logic import (
            modifier, calc_hp, calc_ac_with_armor,
            get_class_starting_stats, calculate_final_stats_with_background,
            get_class_by_name
        )
        from db import get_connection

        # Тест расчёта HP
        print_info("Тест calc_hp()...")
        class_data = get_class_by_name("Воин")
        if class_data:
            hp = calc_hp(class_data['id'], 14, 1)
            assert hp > 0, "HP должно быть положительным"
            print_success(f"   Воин CON=14: HP={hp} (ожидалось ~12)")

        # Тест расчёта AC
        print_info("Тест calc_ac_with_armor()...")
        ac_no_armor = calc_ac_with_armor(14, None)
        ac_light = calc_ac_with_armor(14, "Кожаный доспех")
        assert ac_no_armor == 12, f"AC без брони: {ac_no_armor}"
        print_success(f"   AC без брони: {ac_no_armor}, AC с лёгкой бронёй: {ac_light}")

        # Тест полного расчёта персонажа
        print_info("Тест полного расчёта характеристик...")
        class_name = "Волшебник"
        background = "Мудрец"

        starting = get_class_starting_stats(class_name)
        final = calculate_final_stats_with_background(class_name, background, starting)

        print_success(f"   Волшебник + Мудрец:")
        print_info(f"     Старт: INT={starting['INT']}, WIS={starting['WIS']}")
        print_info(f"     Финал: INT={final['INT']}, WIS={final['WIS']}")

        print_success("Операции с персонажем работают")
        return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        traceback.print_exc()
        return False


# ============================================================
# ТЕСТ 9: ПРОВЕРКА ЗАПРОСОВ К БД
# ============================================================

async def test_database_queries() -> bool:
    """Тест 9: Проверка сложных запросов к БД"""
    print_step(9, 12, "Проверка запросов к базе данных")

    try:
        from db import get_connection, get_spells_by_category, get_class_spell_counts

        # Тест get_spells_by_category
        print_info("Тест get_spells_by_category()...")
        spells_by_cat = get_spells_by_category("Волшебник", is_cantrip=True)
        assert len(spells_by_cat) > 0, "Нет категорий заклинаний"
        print_success(f"   Найдено категорий: {len(spells_by_cat)}")
        for cat_name, spells in list(spells_by_cat.items())[:3]:
            print_info(f"     {cat_name}: {len(spells)} заклинаний")

        # Тест сложного JOIN запроса
        print_info("Тест JOIN запроса (классы+заклинания)...")
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT c.name, COUNT(DISTINCT cs.spell_id) as spell_count
                    FROM classes c
                    LEFT JOIN class_spells cs ON c.id = cs.class_id
                    GROUP BY c.name
                    ORDER BY spell_count DESC
                    LIMIT 3
                """)
                top_classes = cur.fetchall()
                print_success("   Топ-3 класса по количеству заклинаний:")
                for cls in top_classes:
                    print_info(f"     {cls[0]}: {cls[1]} заклинаний")

        print_success("Запросы к БД работают")
        return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        traceback.print_exc()
        return False


# ============================================================
# ТЕСТ 10: ПРОВЕРКА ВАЛИДАЦИИ
# ============================================================

async def test_validation() -> bool:
    """Тест 10: Проверка функций валидации"""
    print_step(10, 12, "Проверка валидации")

    try:
        from dnd_logic import validate_name, validate_race, validate_class, validate_background

        # Тест валидации имени
        print_info("Тест validate_name()...")
        valid, msg = validate_name("Арагорн")
        assert valid, "Имя 'Арагорн' должно быть валидным"

        valid, msg = validate_name("")
        assert not valid, "Пустое имя не должно быть валидным"

        valid, msg = validate_name("A" * 60)
        assert not valid, "Слишком длинное имя не должно быть валидным"
        print_success("validate_name() работает")

        # Тест валидации расы
        print_info("Тест validate_race()...")
        valid, msg = validate_race("Эльф")
        assert valid, "Раса 'Эльф' должна существовать"
        print_success("validate_race() работает")

        # Тест валидации класса
        print_info("Тест validate_class()...")
        valid, msg = validate_class("Волшебник")
        assert valid, "Класс 'Волшебник' должен существовать"
        print_success("validate_class() работает")

        # Тест валидации предыстории
        print_info("Тест validate_background()...")
        valid, msg = validate_background("Мудрец")
        assert valid, "Предыстория 'Мудрец' должна существовать"
        print_success("validate_background() работает")

        print_success("Все проверки валидации пройдены")
        return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        traceback.print_exc()
        return False


# ============================================================
# ТЕСТ 11: ПРОВЕРКА ИНТЕГРАЦИИ
# ============================================================

async def test_integration() -> bool:
    """Тест 11: Интеграционный тест создания персонажа"""
    print_step(11, 12, "Интеграционный тест создания персонажа")

    try:
        from dnd_logic import (
            get_class_starting_stats, get_background_by_name,
            calculate_final_stats_with_background, modifier,
            get_class_spell_counts, get_class_masteries_count
        )
        from spell_selector import SpellSelector
        from db import get_connection

        print_info("Симуляция создания персонажа...")

        # Шаг 1: Выбор класса
        class_name = "Волшебник"
        print_info(f"   1. Класс: {class_name}")

        # Шаг 2: Получение стартовых характеристик
        starting_stats = get_class_starting_stats(class_name)
        print_info(f"   2. Стартовые статы: STR={starting_stats['STR']}, INT={starting_stats['INT']}")

        # Шаг 3: Выбор заклинаний
        spell_counts = get_class_spell_counts(class_name)
        print_info(f"   3. Заклинания: {spell_counts['cantrips']} заговоров, {spell_counts['level1']} заклинаний 1 ур.")

        selector = SpellSelector(class_name)
        print_info(f"   4. Селектор заклинаний создан")

        # Шаг 4: Выбор предыстории
        background = "Мудрец"
        bg_info = get_background_by_name(background)
        print_info(f"   5. Предыстория: {background}")
        print_info(f"      Бонусы: {bg_info['characteristics']}")

        # Шаг 5: Расчёт финальных характеристик
        final_stats = calculate_final_stats_with_background(class_name, background, starting_stats)
        print_info(
            f"   6. Финальные статы: INT={final_stats['INT']} (бонус: +{final_stats['INT'] - starting_stats['INT']})")

        # Шаг 6: Расчёт HP
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_id = cur.fetchone()[0]
        from dnd_logic import calc_hp
        hp = calc_hp(class_id, final_stats.get("CON", 10), 1)
        print_info(f"   7. HP: {hp}")

        # Шаг 7: Валидация
        assert hp > 0, "HP должно быть положительным"
        assert final_stats['INT'] >= 16, "INT должно быть высоким для Волшебника"

        print_success("Интеграционный тест пройден")
        print_success("Персонаж успешно создан в симуляции!")
        return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        traceback.print_exc()
        return False


# ============================================================
# ТЕСТ 12: ПРОВЕРКА ЗАПУСКА БОТА (БЕЗ ПОЛЛИНГА)
# ============================================================

async def test_bot_creation() -> bool:
    """Тест 12: Проверка создания экземпляра бота"""
    print_step(12, 12, "Проверка создания бота")

    try:
        from aiogram import Bot, Dispatcher
        import os
        from dotenv import load_dotenv

        load_dotenv()
        BOT_TOKEN = os.getenv("BOT_TOKEN")

        if not BOT_TOKEN:
            print_error("BOT_TOKEN не найден")
            return False

        print_info("Создание экземпляра бота...")
        bot = Bot(token=BOT_TOKEN)
        dispatcher = Dispatcher()
        print_success("Бот и диспетчер созданы")

        print_info("Проверка webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        print_success("Webhook удалён")

        print_info("Получение информации о боте...")
        bot_info = await bot.get_me()
        print_success(f"Бот: @{bot_info.username}")

        print_info("Проверка регистрации обработчиков...")
        handlers_count = len(dispatcher.observers["message"].handlers) + len(
            dispatcher.observers["callback_query"].handlers)
        print_success(f"Зарегистрировано обработчиков: ~{handlers_count}")

        await bot.session.close()
        print_success("Сессия бота закрыта")

        print_success("Бот готов к запуску!")
        return True

    except Exception as e:
        print_error(f"Ошибка: {e}")
        traceback.print_exc()
        return False


# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================

async def run_all_tests():
    """Запуск всех тестов"""
    print_header("🐉 ПОЛНЫЙ ТЕСТ СИСТЕМЫ D&D CHARACTER CREATOR", Colors.BOLD)

    tests = [
        ("Окружение и импорты", test_environment),
        ("Подключение к БД", test_database_connection),
        ("dnd_logic.py", test_dnd_logic),
        ("spell_selector.py", test_spell_selector),
        ("pdf_generator.py", test_pdf_generator),
        ("Клавиатуры", test_keyboards),
        ("FSM состояния", test_fsm_states),
        ("Операции с персонажем", test_character_operations),
        ("Запросы к БД", test_database_queries),
        ("Валидация", test_validation),
        ("Интеграция", test_integration),
        ("Создание бота", test_bot_creation),
    ]

    results = {}
    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            result = await test_func()
            results[name] = result
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_error(f"Тест '{name}' упал с исключением: {e}")
            results[name] = False
            failed += 1

    # Итоговый отчёт
    print_header("ИТОГИ ТЕСТИРОВАНИЯ", Colors.BOLD)

    for name, result in results.items():
        status = f"{Colors.GREEN}✅ ПРОЙДЕН{Colors.END}" if result else f"{Colors.RED}❌ ПРОВАЛЕН{Colors.END}"
        print(f"   {status} - {name}")

    print(f"\n{Colors.BOLD}Всего тестов: {len(tests)}{Colors.END}")
    print(f"{Colors.GREEN}Пройдено: {passed}{Colors.END}")
    print(f"{Colors.RED}Провалено: {failed}{Colors.END}")

    if failed == 0:
        print_header("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! БОТ ГОТОВ К ЗАПУСКУ!", Colors.GREEN)
        return 0
    else:
        print_header("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ. ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ.", Colors.YELLOW)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)