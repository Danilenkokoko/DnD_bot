# tests/integration/test_full_flow.py
"""
Интеграционные тесты для полного цикла создания персонажа
Проверяют взаимодействие всех компонентов системы
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

# Импорты из проекта
from engine.stats import BackgroundBonusDistributor, AbilityScores
from engine.hp import calculate_hp_at_level
from engine.ac import calculate_ac_with_armor
from engine.proficiency import calculate_proficiency_bonus
from services.character_service import CharacterStatsService, CharacterFinalizationService
from dnd_logic import (
    get_class_starting_stats,
    get_class_primary_stats,
    get_background_characteristics,
    get_class_info
)


# =========================================================
# ФИКСТУРЫ ДЛЯ ИНТЕГРАЦИОННЫХ ТЕСТОВ
# =========================================================

@pytest.fixture(scope="module")
def test_classes_data():
    """Данные о классах для тестирования"""
    return {
        "Воин": {
            "primary_stats": ["STR", "DEX"],
            "hit_die": 10,
            "is_spellcaster": False,
            "starting_stats": {"STR": 15, "DEX": 14, "CON": 13, "INT": 10, "WIS": 10, "CHA": 10}
        },
        "Волшебник": {
            "primary_stats": ["INT"],
            "hit_die": 6,
            "is_spellcaster": True,
            "starting_stats": {"STR": 8, "DEX": 12, "CON": 13, "INT": 15, "WIS": 14, "CHA": 10}
        },
        "Варвар": {
            "primary_stats": ["STR"],
            "hit_die": 12,
            "is_spellcaster": False,
            "starting_stats": {"STR": 15, "DEX": 13, "CON": 14, "INT": 10, "WIS": 10, "CHA": 8}
        }
    }


@pytest.fixture(scope="module")
def test_backgrounds_data():
    """Данные о предысториях для тестирования"""
    return {
        "Солдат": {
            "characteristics": ["STR", "DEX", "CON"],
            "skills": ["Атлетика", "Запугивание"],
            "trait": "Бдительный"
        },
        "Мудрец": {
            "characteristics": ["INT", "WIS", "CHA"],
            "skills": ["Аркана", "История"],
            "trait": "Посвящённый в магию"
        },
        "Преступник": {
            "characteristics": ["DEX", "INT", "CHA"],
            "skills": ["Ловкость рук", "Скрытность"],
            "trait": "Бдительный"
        }
    }


# =========================================================
# ТЕСТ 1: ПОЛНЫЙ ЦИКЛ РАСЧЁТА ХАРАКТЕРИСТИК
# =========================================================

class TestFullStatsCalculation:
    """Тесты полного расчёта характеристик"""

    def test_warrior_with_soldier_background(self, test_classes_data, test_backgrounds_data):
        """Тест: Воин + предыстория Солдат"""
        # Подготовка данных
        class_name = "Воин"
        background = "Солдат"

        class_data = test_classes_data[class_name]
        bg_data = test_backgrounds_data[background]

        primary_stats = class_data["primary_stats"]
        background_stats = bg_data["characteristics"]
        starting_stats = class_data["starting_stats"]

        # Расчёт через engine
        base_scores = AbilityScores.from_dict(starting_stats)
        distributor = BackgroundBonusDistributor(seed=42)
        bonuses = distributor.distribute(primary_stats, background_stats)
        final_scores = bonuses.apply_to(base_scores)

        # Проверки
        final_dict = final_scores.to_str_dict()

        # STR и DEX - основные характеристики
        assert final_dict["STR"] >= starting_stats["STR"] + 1
        assert final_dict["DEX"] >= starting_stats["DEX"] + 1

        # Сумма бонусов = 3
        total_bonus = sum(bonuses.to_dict().values())
        assert total_bonus == 3

        # Бонусы применены только к 3 характеристикам предыстории
        for stat in bonuses.to_dict().keys():
            assert stat in background_stats

    def test_wizard_with_sage_background(self, test_classes_data, test_backgrounds_data):
        """Тест: Волшебник + предыстория Мудрец"""
        class_name = "Волшебник"
        background = "Мудрец"

        class_data = test_classes_data[class_name]
        bg_data = test_backgrounds_data[background]

        primary_stats = class_data["primary_stats"]  # ["INT"]
        background_stats = bg_data["characteristics"]  # ["INT", "WIS", "CHA"]
        starting_stats = class_data["starting_stats"]

        base_scores = AbilityScores.from_dict(starting_stats)
        distributor = BackgroundBonusDistributor(seed=42)
        bonuses = distributor.distribute(primary_stats, background_stats)
        final_scores = bonuses.apply_to(base_scores)

        final_dict = final_scores.to_str_dict()
        bonuses_dict = bonuses.to_dict()

        # INT должна получить +2 (основная характеристика)
        assert bonuses_dict.get("INT", 0) == 2

        # Сумма бонусов = 3
        assert sum(bonuses_dict.values()) == 3

    def test_barbarian_with_criminal_background(self, test_classes_data, test_backgrounds_data):
        """Тест: Варвар + предыстория Преступник (основная характеристика не входит)"""
        class_name = "Варвар"
        background = "Преступник"

        class_data = test_classes_data[class_name]
        bg_data = test_backgrounds_data[background]

        primary_stats = class_data["primary_stats"]  # ["STR"]
        background_stats = bg_data["characteristics"]  # ["DEX", "INT", "CHA"]
        starting_stats = class_data["starting_stats"]

        base_scores = AbilityScores.from_dict(starting_stats)
        distributor = BackgroundBonusDistributor(seed=42)
        bonuses = distributor.distribute(primary_stats, background_stats)
        final_scores = bonuses.apply_to(base_scores)

        bonuses_dict = bonuses.to_dict()

        # STR не входит в background, значит все три характеристики background получают +1
        assert "STR" not in bonuses_dict
        assert bonuses_dict.get("DEX", 0) == 1
        assert bonuses_dict.get("INT", 0) == 1
        assert bonuses_dict.get("CHA", 0) == 1
        assert sum(bonuses_dict.values()) == 3


# =========================================================
# ТЕСТ 2: ПОЛНЫЙ ЦИКЛ РАСЧЁТА HP И AC
# =========================================================

class TestFullCombatStats:
    """Тесты расчёта боевых характеристик"""

    def test_warrior_hp_ac_calculation(self, test_classes_data):
        """Тест: расчёт HP и AC для Воина"""
        class_name = "Воин"
        class_data = test_classes_data[class_name]

        hit_die = class_data["hit_die"]

        # HP для уровня 1
        hp = calculate_hp_at_level(hit_die, constitution=15, level=1)
        assert hp == 10 + 2  # 10 (hit_die) + 2 (CON mod)

        # HP для уровня 3
        hp_level3 = calculate_hp_at_level(hit_die, constitution=15, level=3)
        assert hp_level3 > hp

        # AC без брони
        ac_no_armor = calculate_ac_with_armor(dexterity=14, armor_name=None)
        assert ac_no_armor == 10 + 2  # 10 + DEX mod

        # AC с кожаной бронёй
        ac_leather = calculate_ac_with_armor(dexterity=14, armor_name="Кожаная броня")
        assert ac_leather == 11 + 2  # 11 (leather) + DEX mod

        # AC с латами
        ac_plate = calculate_ac_with_armor(dexterity=14, armor_name="Латы")
        assert ac_plate == 18  # Plate без DEX

    def test_wizard_hp_ac_calculation(self, test_classes_data):
        """Тест: расчёт HP и AC для Волшебника"""
        class_name = "Волшебник"
        class_data = test_classes_data[class_name]

        hit_die = class_data["hit_die"]

        # HP для уровня 1 с CON=12
        hp = calculate_hp_at_level(hit_die, constitution=12, level=1)
        assert hp == 6 + 1  # 6 (hit_die) + 1 (CON mod)

        # HP для уровня 5
        hp_level5 = calculate_hp_at_level(hit_die, constitution=12, level=5)
        assert hp_level5 == 6 + 1 + 4 * ((6 // 2) + 1 + 1)  # среднее значение

        # AC без брони (DEX=12)
        ac = calculate_ac_with_armor(dexterity=12, armor_name=None)
        assert ac == 10 + 1


# =========================================================
# ТЕСТ 3: ПОЛНЫЙ ЦИКЛ СЕРВИСА
# =========================================================

class TestCharacterServiceIntegration:
    """Тесты интеграции с CharacterStatsService"""

    def test_service_calculate_and_format_stats(self):
        """Тест: полный расчёт через сервис"""
        result = CharacterStatsService.calculate_and_format_stats(
            class_name="Воин",
            background="Солдат"
        )

        # Проверка структуры результата
        assert "stats" in result
        assert "stats_text" in result
        assert "hp" in result
        assert "ac" in result
        assert "bg_chars" in result
        assert "proficiency_bonus" in result

        # Проверка значений
        assert result["proficiency_bonus"] == 2  # уровень 1
        assert isinstance(result["hp"], int)
        assert result["hp"] > 0
        assert isinstance(result["ac"], int)
        assert result["ac"] > 0

        # Проверка форматирования
        assert "STR" in result["stats_text"]
        assert "DEX" in result["stats_text"]
        assert "CON" in result["stats_text"]

    def test_service_calculate_stats_with_different_classes(self, test_classes_data):
        """Тест: расчёт для разных классов"""
        classes = ["Воин", "Волшебник", "Варвар"]

        for class_name in classes:
            result = CharacterStatsService.calculate_stats(
                class_name=class_name,
                background_name="Солдат"
            )

            assert "stats" in result
            assert "bonuses" in result
            assert "class_primary" in result
            assert "background_stats" in result

            # Сумма бонусов должна быть 3
            bonus_sum = sum(result["bonuses"].values())
            assert bonus_sum == 3, f"Для класса {class_name} сумма бонусов = {bonus_sum}"

    def test_service_calculate_hp_ac(self):
        """Тест: расчёт HP и AC через сервис"""
        hp = CharacterStatsService.calculate_hp("Воин", 15, level=1)
        assert hp == 12

        hp_high_con = CharacterStatsService.calculate_hp("Воин", 20, level=1)
        assert hp_high_con > hp

        ac = CharacterStatsService.calculate_ac(14, "Кожаная броня")
        assert ac == 13

        ac_with_shield = CharacterStatsService.calculate_ac(14, "Кожаная броня", has_shield=True)
        assert ac_with_shield == 15

    def test_service_validate_character_stats(self):
        """Тест: валидация характеристик через сервис"""
        valid_stats = {"STR": 15, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 8}
        valid, errors = CharacterStatsService.validate_character_stats(valid_stats)
        assert valid is True
        assert len(errors) == 0

        invalid_stats = {"STR": 15, "DEX": 14, "CON": 13}
        valid, errors = CharacterStatsService.validate_character_stats(invalid_stats)
        assert valid is False
        assert len(errors) > 0


# =========================================================
# ТЕСТ 4: ПОДГОТОВКА ДАННЫХ ДЛЯ СОХРАНЕНИЯ
# =========================================================

class TestCharacterFinalization:
    """Тесты финализации персонажа"""

    def test_prepare_character_data(self):
        """Тест: подготовка данных для сохранения"""
        state_data = {
            'class_name': 'Воин',
            'background': 'Солдат',
            'race': 'Человек',
            'subrace': None,
            'name': 'Test Warrior',
            'backstory': 'Test backstory',
            'background_equipment_choice': 'A',
            'final_stats': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 10, 'WIS': 10, 'CHA': 10},
            'selected_masteries': [],
            'selected_fighting_style': 'Оборона',
            'selected_invocations': [],
            'selected_weapon': 'Длинный меч',
            'selected_armor': 'Кольчуга',
            'spell_selector': None
        }

        prepared = CharacterFinalizationService.prepare_character_data(
            state_data=state_data,
            user_id=123456
        )

        assert prepared['user_id'] == 123456
        assert prepared['name'] == 'Test Warrior'
        assert prepared['class_name'] == 'Воин'
        assert prepared['background'] == 'Солдат'
        assert prepared['race'] == 'Человек'
        assert prepared['selected_weapon'] == 'Длинный меч'
        assert prepared['selected_armor'] == 'Кольчуга'

    def test_prepare_character_data_with_spells(self):
        """Тест: подготовка данных с заклинаниями"""
        # Мок для SpellSelector
        mock_selector = MagicMock()
        mock_selector.get_all_selected_spells.return_value = ['Огненный снаряд', 'Магическая стрела']

        state_data = {
            'class_name': 'Волшебник',
            'background': 'Мудрец',
            'race': 'Эльф',
            'subrace': 'Высший эльф',
            'name': 'Test Wizard',
            'backstory': 'Wizard backstory',
            'background_equipment_choice': 'B',
            'final_stats': {'STR': 8, 'DEX': 14, 'CON': 14, 'INT': 16, 'WIS': 12, 'CHA': 10},
            'selected_masteries': [],
            'selected_fighting_style': None,
            'selected_invocations': [],
            'selected_weapon': 'Посох',
            'selected_armor': None,
            'spell_selector': {'class_name': 'Волшебник'}  # Будет восстановлен
        }

        prepared = CharacterFinalizationService.prepare_character_data(
            state_data=state_data,
            user_id=123456
        )

        assert prepared['name'] == 'Test Wizard'
        assert prepared['race'] == 'Эльф'
        assert prepared['subrace'] == 'Высший эльф'


# =========================================================
# ТЕСТ 5: СКВОЗНОЙ ТЕСТ СОЗДАНИЯ ПЕРСОНАЖА
# =========================================================

@pytest.mark.slow
class TestFullCharacterCreation:
    """Сквозной тест создания персонажа (без Telegram)"""

    def test_complete_warrior_creation_flow(self, test_classes_data, test_backgrounds_data):
        """Тест: полный цикл создания Воина"""

        # Шаг 1: Выбор класса
        class_name = "Воин"
        class_data = test_classes_data[class_name]

        # Шаг 2: Выбор предыстории
        background = "Солдат"
        bg_data = test_backgrounds_data[background]

        # Шаг 3: Расчёт характеристик
        primary_stats = class_data["primary_stats"]
        background_stats = bg_data["characteristics"]
        starting_stats = class_data["starting_stats"]

        base_scores = AbilityScores.from_dict(starting_stats)
        distributor = BackgroundBonusDistributor(seed=42)
        bonuses = distributor.distribute(primary_stats, background_stats)
        final_scores = bonuses.apply_to(base_scores)
        final_stats = final_scores.to_str_dict()

        # Проверка характеристик
        assert final_stats["STR"] >= 16  # +1 минимум
        assert final_stats["DEX"] >= 15  # +1 минимум
        assert final_stats["CON"] >= 14  # +1 минимум

        # Шаг 4: Расчёт HP
        hit_die = class_data["hit_die"]
        constitution = final_stats["CON"]
        hp = calculate_hp_at_level(hit_die, constitution, level=1)

        # Шаг 5: Расчёт AC
        dexterity = final_stats["DEX"]
        ac = calculate_ac_with_armor(dexterity, "Кольчуга")  # Средняя броня

        # Финальные проверки
        assert hp == 10 + 2  # d10 + CON mod (14 → +2)
        assert ac == 16  # Chain mail: 16

        print(f"\n✅ Воин создан: HP={hp}, AC={ac}")
        print(f"   Характеристики: {final_stats}")

    def test_complete_wizard_creation_flow(self, test_classes_data, test_backgrounds_data):
        """Тест: полный цикл создания Волшебника"""

        class_name = "Волшебник"
        background = "Мудрец"

        class_data = test_classes_data[class_name]
        bg_data = test_backgrounds_data[background]

        # Расчёт характеристик
        primary_stats = class_data["primary_stats"]  # ["INT"]
        background_stats = bg_data["characteristics"]  # ["INT", "WIS", "CHA"]
        starting_stats = class_data["starting_stats"]

        base_scores = AbilityScores.from_dict(starting_stats)
        distributor = BackgroundBonusDistributor(seed=42)
        bonuses = distributor.distribute(primary_stats, background_stats)
        final_scores = bonuses.apply_to(base_scores)
        final_stats = final_scores.to_str_dict()

        # INT должна получить +2
        assert final_stats["INT"] >= 17

        # Расчёт HP
        hit_die = class_data["hit_die"]
        constitution = final_stats["CON"]
        hp = calculate_hp_at_level(hit_die, constitution, level=1)

        # Расчёт AC
        dexterity = final_stats["DEX"]
        ac = calculate_ac_with_armor(dexterity, None)  # Без брони

        print(f"\n✅ Волшебник создан: HP={hp}, AC={ac}")
        print(f"   Характеристики: {final_stats}")
        print(f"   Бонусы: {bonuses.to_dict()}")


# =========================================================
# ЗАПУСК ТЕСТОВ
# =========================================================

if __name__ == "__main__":
    # Ручной запуск интеграционных тестов
    pytest.main([__file__, "-v", "--tb=short"])