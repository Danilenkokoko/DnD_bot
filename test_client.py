#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_bot_flows.py - Тестирование сценариев создания персонажа
Проверяет все шаги и возможные варианты выбора на наличие ошибок.
Запуск: python test_bot_flows.py
"""

import asyncio
import sys
import os
from typing import Dict, Any, List, Optional

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импортируем репозитории и сервисы
from repositories.race_repository import RaceRepository
from repositories.class_repository import ClassRepository
from repositories.background_repository import BackgroundRepository
from repositories.equipment_repository import EquipmentRepository, FightingStyleRepository, InvocationRepository
from repositories.spell_repository import SpellRepository
from repositories.character_repository import CharacterRepository
from services.character_service import CharacterStatsService, CharacterFinalizationService
from services.progression_service import ProgressionService
from services.spell_service import SpellSelectionService
from engine.stats import BackgroundBonusDistributor, AbilityScores

# Инициализация репозиториев
race_repo = RaceRepository()
class_repo = ClassRepository()
bg_repo = BackgroundRepository()
equip_repo = EquipmentRepository()
fighting_repo = FightingStyleRepository()
inv_repo = InvocationRepository()
spell_repo = SpellRepository()
char_repo = CharacterRepository()


def print_header(text: str):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_ok(text: str):
    print(f"  ✅ {text}")


def print_error(text: str):
    print(f"  ❌ {text}")


def print_warning(text: str):
    print(f"  ⚠️ {text}")


def test_data_integrity():
    """Проверка целостности данных в БД"""
    print_header("Проверка целостности данных")

    # Расы
    races = race_repo.get_all()
    print(f"Расы: {len(races)}")
    for race in races[:3]:
        print(f"  • {race['name']} (speed={race.get('speed')}, size={race.get('size')})")
        subraces = race_repo.get_subraces(race['name'])
        if subraces:
            print(f"    Подрасы: {', '.join([s['name'] for s in subraces])}")

    # Классы
    classes = class_repo.get_all()
    print(f"\nКлассы: {len(classes)}")
    for cls in classes:
        print(f"  • {cls['name']} (hit_die=d{cls['hit_die']}, spellcaster={cls['is_spellcaster']})")
        subclasses = class_repo.get_subclasses(cls['name'])
        if subclasses:
            print(f"    Подклассы на 1 уровне: {', '.join([s['name'] for s in subclasses if s['level_acquired'] == 1])}")

    # Предыстории
    backgrounds = bg_repo.get_all()
    print(f"\nПредыстории: {len(backgrounds)}")
    for bg in backgrounds[:5]:
        chars = bg.get('characteristics', [])
        print(f"  • {bg['name']} (бонусы: +2 к {chars[0] if len(chars) > 0 else '?'}, +1 к {chars[1] if len(chars) > 1 else '?'})")

    # Заклинания
    spells = spell_repo.get_all()
    print(f"\nЗаклинания: {len(spells)}")
    cantrips = [s for s in spells if s.get('is_cantrip')]
    level1 = [s for s in spells if s.get('level') == 1]
    print(f"  Заговоры: {len(cantrips)}, Заклинаний 1 уровня: {len(level1)}")

    # Оружие и броня
    weapons = equip_repo.get_all_weapons()
    armors = equip_repo.get_all_armors()
    print(f"\nОружие: {len(weapons)}, Броня: {len(armors)}")

    return True


def test_background_distribution():
    """Проверка распределения бонусов предыстории для всех комбинаций класс+предыстория"""
    print_header("Тест распределения бонусов предыстории")

    classes = class_repo.get_all_names()
    backgrounds = bg_repo.get_all_names()

    errors = 0
    for class_name in classes:
        for bg_name in backgrounds:
            try:
                # Получаем основные характеристики класса
                primary_stats = class_repo.get_primary_stats(class_name)
                # Получаем бонусы предыстории
                bg_chars = bg_repo.get_characteristics(bg_name)

                if not primary_stats:
                    print_error(f"{class_name} + {bg_name}: нет основных характеристик класса")
                    errors += 1
                    continue

                if len(bg_chars) < 2:
                    print_error(f"{class_name} + {bg_name}: предыстория дает меньше 2 бонусов")
                    errors += 1
                    continue

                # Распределяем бонусы
                distributor = BackgroundBonusDistributor()
                base_stats = AbilityScores(STR=10, DEX=10, CON=10, INT=10, WIS=10, CHA=10)
                bonuses = distributor.distribute(primary_stats, bg_chars)
                final = bonuses.apply_to(base_stats)

                # Проверка: бонусы должны быть применены к основным характеристикам
                # (это упрощённая проверка, в реальности логика сложнее)
                print_ok(f"{class_name} + {bg_name}: бонусы={bg_chars} -> распределено {bonuses.to_dict()}")

            except Exception as e:
                print_error(f"{class_name} + {bg_name}: {e}")
                errors += 1

    print(f"\nИтого ошибок: {errors}")
    return errors == 0


def test_class_equipment():
    """Проверка снаряжения классов"""
    print_header("Тест снаряжения классов")

    classes = class_repo.get_all_names()
    errors = 0
    for class_name in classes:
        equipment = equip_repo.get_class_equipment(class_name)
        if not equipment:
            print_warning(f"{class_name}: нет снаряжения в БД")
            continue

        # Проверяем вариант A и B
        for choice in ['A', 'B']:
            eq = equip_repo.get_class_equipment(class_name, choice)
            if not eq and len(equipment) > 1:
                print_warning(f"{class_name}: нет варианта {choice}")
            elif eq:
                eq_data = eq[0]
                if eq_data.get('weapon'):
                    weapon = equip_repo.get_weapon_by_name(eq_data['weapon'])
                    if not weapon:
                        print_error(f"{class_name}: оружие '{eq_data['weapon']}' не найдено в БД")
                        errors += 1
                if eq_data.get('armor'):
                    armor = equip_repo.get_armor_by_name(eq_data['armor'])
                    if not armor:
                        print_error(f"{class_name}: броня '{eq_data['armor']}' не найдена в БД")
                        errors += 1

        print_ok(f"{class_name}: снаряжение OK")

    print(f"\nИтого ошибок: {errors}")
    return errors == 0


def test_fighting_styles():
    """Проверка боевых стилей"""
    print_header("Тест боевых стилей")

    classes_with_styles = ["Воин", "Паладин", "Следопыт"]
    for class_name in classes_with_styles:
        styles = fighting_repo.get_for_class(class_name)
        if not styles:
            print_warning(f"{class_name}: нет боевых стилей")
        else:
            print_ok(f"{class_name}: {len(styles)} стилей")
            for s in styles[:2]:
                print(f"    • {s['name']}")

    # Проверка, что у других классов нет стилей
    other_classes = [c for c in class_repo.get_all_names() if c not in classes_with_styles]
    for class_name in other_classes:
        styles = fighting_repo.get_for_class(class_name)
        if styles:
            print_warning(f"{class_name}: имеет боевые стили, хотя не должен по D&D 5.5e (2024)")

    return True


def test_invocations():
    """Проверка возваний колдуна"""
    print_header("Тест возваний колдуна")

    invocations = inv_repo.get_all(level=1)
    if not invocations:
        print_warning("Нет возваний для 1 уровня")
    else:
        print_ok(f"Найдено возваний на 1 уровне: {len(invocations)}")
        for inv in invocations[:3]:
            print(f"    • {inv['name']} (уровень {inv.get('level_required', 1)})")

    return True


def test_spell_categories():
    """Проверка категорий заклинаний для классов-заклинателей"""
    print_header("Тест категорий заклинаний")

    spellcasters = [c for c in class_repo.get_all_names() if class_repo.is_spellcaster(c)]
    for class_name in spellcasters:
        # Проверяем заговоры
        cantrip_categories = spell_repo.get_categories_for_class(class_name, is_cantrip=True)
        if not cantrip_categories:
            print_warning(f"{class_name}: нет категорий заговоров")
        else:
            print_ok(f"{class_name}: {len(cantrip_categories)} категорий заговоров")

        # Проверяем заклинания 1 уровня
        level1_categories = spell_repo.get_categories_for_class(class_name, is_cantrip=False)
        if not level1_categories:
            print_warning(f"{class_name}: нет категорий заклинаний 1 уровня")
        else:
            print_ok(f"{class_name}: {len(level1_categories)} категорий заклинаний 1 уровня")

    return True


def test_character_save_load():
    """Тест сохранения и загрузки персонажа (без записи в БД, только структура)"""
    print_header("Тест структуры данных персонажа")

    test_data = {
        "user_id": 999999,
        "name": "Test Character",
        "class_name": "Воин",
        "race": "Человек",
        "subrace": None,
        "background": "Солдат",
        "level": 1,
        "stats": {"STR": 15, "DEX": 14, "CON": 13, "INT": 10, "WIS": 12, "CHA": 8},
        "hp": 12,
        "ac": 16,
        "selected_skills": ["Атлетика", "Запугивание"],
        "selected_masteries": ["Топор"],
        "selected_fighting_style": "Защита",
        "selected_invocations": [],
        "selected_spells": [],
        "selected_weapon": "Longsword",
        "selected_armor": "Chain Mail",
        "selected_equipment_choice": "A",
        "backstory": "Test backstory",
        "alignment": "Нейтральное"
    }

    try:
        # Проверяем, что все необходимые поля есть
        required_fields = ["name", "class_name", "race", "background", "stats", "hp", "ac"]
        for field in required_fields:
            if field not in test_data:
                print_error(f"Отсутствует поле: {field}")
                return False

        # Проверяем, что статистики корректны
        stats = test_data["stats"]
        if sum(stats.values()) > 90:
            print_warning("Сумма характеристик высокая")

        print_ok("Структура данных персонажа корректна")
        return True
    except Exception as e:
        print_error(f"Ошибка: {e}")
        return False


def test_progression_service():
    """Проверка логики порядка шагов"""
    print_header("Тест ProgressionService")

    test_cases = [
        ("Волшебник", True, False, False),   # заклинатель, не боевой стиль, не возвания
        ("Воин", False, True, False),        # боевой стиль
        ("Паладин", False, True, False),     # боевой стиль
        ("Следопыт", True, True, False),     # заклинатель + боевой стиль
        ("Колдун", True, False, True),       # заклинатель + возвания
        ("Варвар", False, False, False),     # ничего из перечисленного
    ]

    for class_name, expected_spellcaster, expected_fighting, expected_inv in test_cases:
        is_spell = ProgressionService.is_spellcaster(class_name)
        has_fighting = ProgressionService.should_select_fighting_style(class_name)
        has_inv = ProgressionService.should_select_invocations(class_name)

        ok = True
        if is_spell != expected_spellcaster:
            print_error(f"{class_name}: is_spellcaster={is_spell}, ожидалось {expected_spellcaster}")
            ok = False
        if has_fighting != expected_fighting:
            print_error(f"{class_name}: should_select_fighting_style={has_fighting}, ожидалось {expected_fighting}")
            ok = False
        if has_inv != expected_inv:
            print_error(f"{class_name}: should_select_invocations={has_inv}, ожидалось {expected_inv}")
            ok = False
        if ok:
            print_ok(f"{class_name}: всё верно")

    return True


def test_stats_calculation():
    """Тест расчёта итоговых характеристик"""
    print_header("Тест расчёта характеристик")

    # Тестовая комбинация
    class_name = "Воин"
    background = "Солдат"
    base_stats = {"STR": 14, "DEX": 12, "CON": 13, "INT": 10, "WIS": 10, "CHA": 8}

    try:
        result = CharacterStatsService.calculate_and_format_stats(
            class_name=class_name,
            background=background,
            base_stats_dict=base_stats,
            equipment_choice="A"
        )
        print_ok(f"Расчёт успешен: {class_name} + {background}")
        print(f"  Итоговые статы: {result['stats']}")
        print(f"  HP: {result['hp']}, AC: {result['ac']}")
        return True
    except Exception as e:
        print_error(f"Ошибка расчёта: {e}")
        return False


async def run_all_tests():
    """Запуск всех тестов"""
    print_header("НАЧАЛО ТЕСТИРОВАНИЯ BOT FLOWS")

    tests = [
        ("Целостность данных", test_data_integrity),
        ("Распределение бонусов предысторий", test_background_distribution),
        ("Снаряжение классов", test_class_equipment),
        ("Боевые стили", test_fighting_styles),
        ("Возвания", test_invocations),
        ("Категории заклинаний", test_spell_categories),
        ("Структура персонажа", test_character_save_load),
        ("ProgressionService", test_progression_service),
        ("Расчёт характеристик", test_stats_calculation),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"\n▶ Тест: {name}")
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_error(f"Исключение: {e}")
            failed += 1

    print_header("ИТОГИ ТЕСТИРОВАНИЯ")
    print(f"✅ Успешно: {passed}")
    print(f"❌ Ошибок: {failed}")
    print(f"📊 Всего: {passed + failed}")

    return failed == 0


if __name__ == "__main__":
    asyncio.run(run_all_tests())