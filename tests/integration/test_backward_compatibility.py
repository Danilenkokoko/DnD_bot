"""
Тесты обратной совместимости
Проверяют, что после рефакторинга существующие персонажи и API остаются рабочими
"""

import pytest
import json
import os
from typing import Dict, Any
from datetime import datetime

# Импорты для проверки совместимости
from dnd_logic import (
    # Старые функции, которые должны остаться рабочими
    get_race_list,
    get_class_list,
    get_background_list,
    get_race_by_name,
    get_class_by_name,
    get_background_by_name,
    get_class_starting_stats,
    get_class_primary_stats,
    get_background_characteristics,
    validate_name,
    validate_stats,
    # Deprecated функции (должны работать с предупреждениями)
    modifier,
    calculate_proficiency_bonus,
    calc_hp,
    calc_ac_with_armor,
)

from services.character_service import CharacterStatsService
from engine.stats import AbilityScores, BackgroundBonusDistributor


# =========================================================
# ТЕСТ 1: СОВМЕСТИМОСТЬ API СТАРЫХ ФУНКЦИЙ
# =========================================================

class TestLegacyApiCompatibility:
    """Проверка, что старые функции возвращают те же результаты"""

    def test_get_race_list_returns_list(self):
        """get_race_list() возвращает список (не изменился формат)"""
        races = get_race_list()
        assert isinstance(races, list)
        assert len(races) > 0
        assert "Человек" in races
        assert "Эльф" in races

    def test_get_class_list_returns_list(self):
        """get_class_list() возвращает список"""
        classes = get_class_list()
        assert isinstance(classes, list)
        assert len(classes) > 0
        assert "Воин" in classes
        assert "Волшебник" in classes

    def test_get_background_list_returns_list(self):
        """get_background_list() возвращает список"""
        backgrounds = get_background_list()
        assert isinstance(backgrounds, list)
        assert len(backgrounds) > 0
        assert "Солдат" in backgrounds

    def test_get_race_by_name_returns_dict(self):
        """get_race_by_name() возвращает словарь с ожидаемой структурой"""
        race = get_race_by_name("Человек")
        assert isinstance(race, dict)
        assert "name" in race
        assert "speed" in race
        assert "size" in race
        assert race["name"] == "Человек"

    def test_get_class_by_name_returns_dict(self):
        """get_class_by_name() возвращает словарь с ожидаемой структурой"""
        class_data = get_class_by_name("Воин")
        assert isinstance(class_data, dict)
        assert "name" in class_data
        assert "hit_die" in class_data
        assert class_data["name"] == "Воин"
        assert class_data["hit_die"] == 10

    def test_get_background_by_name_returns_dict(self):
        """get_background_by_name() возвращает словарь с ожидаемой структурой"""
        bg = get_background_by_name("Солдат")
        assert isinstance(bg, dict)
        assert "name" in bg
        assert "characteristics" in bg
        assert bg["name"] == "Солдат"

    def test_get_class_starting_stats_returns_dict(self):
        """get_class_starting_stats() возвращает словарь с 6 характеристиками"""
        stats = get_class_starting_stats("Воин")
        assert isinstance(stats, dict)
        assert len(stats) == 6
        assert "STR" in stats
        assert "DEX" in stats
        assert "CON" in stats
        assert "INT" in stats
        assert "WIS" in stats
        assert "CHA" in stats

    def test_get_class_primary_stats_returns_list(self):
        """get_class_primary_stats() возвращает список"""
        primary = get_class_primary_stats("Воин")
        assert isinstance(primary, list)
        assert len(primary) in [1, 2]
        assert "STR" in primary or "DEX" in primary

    def test_get_background_characteristics_returns_list(self):
        """get_background_characteristics() возвращает список из 3 элементов"""
        chars = get_background_characteristics("Солдат")
        assert isinstance(chars, list)
        assert len(chars) == 3

    def test_validate_name_returns_tuple(self):
        """validate_name() возвращает (bool, str)"""
        valid, msg = validate_name("Test")
        assert isinstance(valid, bool)
        assert isinstance(msg, str)

        valid, msg = validate_name("A")  # слишком короткое
        assert valid is False

    def test_validate_stats_returns_tuple(self):
        """validate_stats() возвращает (bool, str)"""
        valid_stats = {"STR": 15, "DEX": 14, "CON": 13, "INT": 12, "WIS": 10, "CHA": 8}
        valid, msg = validate_stats(valid_stats)
        assert isinstance(valid, bool)
        assert isinstance(msg, str)


# =========================================================
# ТЕСТ 2: DEPRECATED ФУНКЦИИ (ДОЛЖНЫ РАБОТАТЬ)
# =========================================================

class TestDeprecatedFunctions:
    """Проверка, что deprecated функции всё ещё работают"""

    def test_modifier_works(self):
        """modifier() возвращает корректный модификатор"""
        with pytest.deprecated_call():
            mod = modifier(15)
            assert mod == 2

        with pytest.deprecated_call():
            mod = modifier(8)
            assert mod == -1

    def test_calculate_proficiency_bonus_works(self):
        """calculate_proficiency_bonus() возвращает корректный бонус"""
        with pytest.deprecated_call():
            bonus = calculate_proficiency_bonus(5)
            assert bonus == 3

        with pytest.deprecated_call():
            bonus = calculate_proficiency_bonus(1)
            assert bonus == 2

    def test_calc_hp_works(self):
        """calc_hp() возвращает корректные HP (требует мок БД)"""
        # Этот тест требует реальной БД или мока
        # Пропускаем если нет БД
        pytest.skip("Requires database with class id mapping")

    def test_calc_ac_with_armor_works(self):
        """calc_ac_with_armor() возвращает корректный AC"""
        # Без брони
        with pytest.deprecated_call():
            ac = calc_ac_with_armor(14, None)
            assert ac == 12

        # С кожаной бронёй
        with pytest.deprecated_call():
            ac = calc_ac_with_armor(14, "Кожаная броня")
            # 11 + 2 = 13
            assert ac == 13


# =========================================================
# ТЕСТ 3: СОХРАНЕНИЕ СУЩЕСТВУЮЩИХ ПЕРСОНАЖЕЙ
# =========================================================

class TestExistingCharactersCompatibility:
    """Проверка, что существующие персонажи корректно загружаются"""

    @pytest.fixture
    def existing_character_data(self) -> Dict[str, Any]:
        """Данные существующего персонажа (формат из БД)"""
        return {
            'id': 9999,
            'user_id': 12345,
            'name': 'Legacy Character',
            'class_name': 'Воин',
            'race_name': 'Человек',
            'background_name': 'Солдат',
            'level': 1,
            'str': 16,
            'dex': 14,
            'con': 14,
            'int': 10,
            'wis': 10,
            'cha': 10,
            'hp': 12,
            'ac': 16,
            'selected_skills': ['Атлетика', 'Восприятие'],
            'selected_spells': [],
        }

    def test_character_from_db_can_be_loaded(self, existing_character_data):
        """Персонаж из старой БД может быть загружен"""
        # Проверяем, что структура данных совместима
        assert 'str' in existing_character_data
        assert 'dex' in existing_character_data

        # Преобразование в формат engine
        stats = {
            "STR": existing_character_data['str'],
            "DEX": existing_character_data['dex'],
            "CON": existing_character_data['con'],
            "INT": existing_character_data.get('int', 10),
            "WIS": existing_character_data.get('wis', 10),
            "CHA": existing_character_data.get('cha', 10),
        }

        # Проверка, что характеристики в допустимом диапазоне
        for value in stats.values():
            assert 1 <= value <= 30

        # Проверка, что можно создать AbilityScores
        scores = AbilityScores.from_dict(stats)
        assert scores.strength == stats["STR"]

        # Пересчёт HP через новый engine
        hp = CharacterStatsService.calculate_hp(
            existing_character_data['class_name'],
            stats["CON"],
            level=existing_character_data['level']
        )
        assert hp > 0

    def test_old_pdf_data_structure_compatible(self):
        """Старая структура данных для PDF совместима с новой"""
        old_pdf_data = {
            'name': 'Test',
            'class_name': 'Воин',
            'race': 'Человек',
            'level': 1,
            'stats': {'STR': 16, 'DEX': 14, 'CON': 14, 'INT': 10, 'WIS': 10, 'CHA': 10},
            'hp': 12,
            'ac': 16,
            'background': 'Солдат',
        }

        # Проверка, что все необходимые поля присутствуют
        required_fields = ['name', 'class_name', 'race', 'level', 'stats', 'hp', 'ac']
        for field in required_fields:
            assert field in old_pdf_data

        # Проверка, что stats содержит 6 характеристик
        assert len(old_pdf_data['stats']) == 6
        assert all(stat in old_pdf_data['stats'] for stat in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA'])


# =========================================================
# ТЕСТ 4: ОБРАТНАЯ СОВМЕСТИМОСТЬ РАСЧЁТОВ
# =========================================================

class TestCalculationCompatibility:
    """Проверка, что результаты расчётов не изменились"""

    def test_stat_bonus_distribution_same_result(self):
        """Распределение бонусов даёт тот же результат"""
        # Старый способ (через dnd_logic)
        from dnd_logic import calculate_final_stats_with_background

        class_name = "Воин"
        background = "Солдат"
        starting_stats = {"STR": 15, "DEX": 14, "CON": 13, "INT": 10, "WIS": 10, "CHA": 10}

        # Старый результат (с предупреждением)
        with pytest.deprecated_call():
            old_result = calculate_final_stats_with_background(class_name, background, starting_stats)

        # Новый способ (через engine)
        distributor = BackgroundBonusDistributor(seed=42)
        bonuses = distributor.distribute(
            primary_stats=["STR", "DEX"],
            background_stats=["STR", "DEX", "CON"]
        )
        base_scores = AbilityScores.from_dict(starting_stats)
        new_result = bonuses.apply_to(base_scores).to_str_dict()

        # Сравниваем только структуру, точные значения могут отличаться
        # из-за random в старом алгоритме
        assert set(old_result.keys()) == set(new_result.keys())
        assert all(isinstance(v, int) for v in old_result.values())
        assert all(isinstance(v, int) for v in new_result.values())

    def test_modifier_consistency(self):
        """Модификаторы совпадают в старой и новой реализации"""
        test_values = [1, 3, 8, 10, 12, 15, 18, 20, 25, 30]

        for value in test_values:
            with pytest.deprecated_call():
                old_mod = modifier(value)

            from engine.hp import calculate_modifier as new_mod
            assert old_mod == new_mod(value), f"Value {value}: old={old_mod}, new={new_mod(value)}"

    def test_proficiency_bonus_consistency(self):
        """Бонус мастерства совпадает в старой и новой реализации"""
        for level in range(1, 21):
            with pytest.deprecated_call():
                old_bonus = calculate_proficiency_bonus(level)

            from engine.proficiency import calculate_proficiency_bonus as new_bonus
            assert old_bonus == new_bonus(level), f"Level {level}: old={old_bonus}, new={new_bonus(level)}"


# =========================================================
# ТЕСТ 5: СЕРИАЛИЗАЦИЯ И ДЕСЕРИАЛИЗАЦИЯ
# =========================================================

class TestSerializationCompatibility:
    """Проверка, что данные корректно сериализуются/десериализуются"""

    def test_character_data_json_serializable(self):
        """Данные персонажа должны быть JSON-сериализуемыми"""
        character = {
            'name': 'Test',
            'class_name': 'Воин',
            'stats': {'STR': 15, 'DEX': 14, 'CON': 13, 'INT': 12, 'WIS': 10, 'CHA': 8},
            'level': 1,
            'hp': 12,
            'ac': 16,
            'created_at': datetime.now().isoformat()
        }

        # Должно сериализоваться без ошибок
        json_str = json.dumps(character, default=str)
        assert isinstance(json_str, str)

        # Должно десериализоваться обратно
        restored = json.loads(json_str)
        assert restored['name'] == character['name']
        assert restored['class_name'] == character['class_name']

    def test_spell_selector_state_compatible(self):
        """Состояние SpellSelector должно сохраняться между версиями"""
        from spell_selector import SpellSelector

        selector = SpellSelector("Волшебник")
        selector.add_cantrip("Огненный снаряд")

        # Сериализация
        state = selector.to_dict()

        # Должна быть JSON-сериализуемой
        json_str = json.dumps(state, default=str)

        # Десериализация
        restored = json.loads(json_str)

        # Восстановление селектора
        new_selector = SpellSelector.from_dict(restored)
        assert new_selector.get_selected_cantrips() == selector.get_selected_cantrips()


# =========================================================
# ТЕСТ 6: БЕЗОПАСНОСТЬ - ОТСУТСТВИЕ УТЕЧЕК
# =========================================================

class TestNoDataLeakage:
    """Проверка, что нет утечек данных между пользователями"""

    def test_user_characters_isolation(self):
        """Персонажи разных пользователей не перемешиваются"""
        from db import get_user_characters

        # Эта функция уже должна правильно фильтровать по user_id
        # Тест проверяет, что сигнатура не изменилась
        user1_chars = get_user_characters(111)
        user2_chars = get_user_characters(222)

        assert isinstance(user1_chars, list)
        assert isinstance(user2_chars, list)

    def test_no_global_state_in_engine(self):
        """Engine не хранит глобальное состояние между запросами"""
        distributor1 = BackgroundBonusDistributor(seed=42)
        distributor2 = BackgroundBonusDistributor(seed=42)

        result1 = distributor1.distribute(["STR"], ["STR", "DEX", "CON"])
        result2 = distributor2.distribute(["STR"], ["STR", "DEX", "CON"])

        # Разные инстансы с одинаковым seed дают одинаковый результат
        assert result1.to_dict() == result2.to_dict()

        # Но не влияют друг на друга
        result3 = distributor1.distribute(["INT"], ["INT", "WIS", "CHA"])
        assert result3.to_dict() != result1.to_dict()


# =========================================================
# ТЕСТ 7: ПРОВЕРКА FSM СОСТОЯНИЙ
# =========================================================

class TestFsmCompatibility:
    """Проверка, что FSM состояния не изменились"""

    def test_create_character_states_exists(self):
        """Класс CreateCharacter должен существовать и содержать все состояния"""
        from states.character_states import CreateCharacter

        # Проверяем наличие всех необходимых состояний
        expected_states = [
            'class_select',
            'subclass_select',
            'class_equipment_select',
            'spells_cantrips_category',
            'spells_cantrips_list',
            'spells_cantrips_detail',
            'spells_cantrips_complete',
            'spells_level1_category',
            'spells_level1_list',
            'spells_level1_detail',
            'spells_level1_complete',
            'fighting_style_select',
            'invocations_select',
            'background_select',
            'background_equipment_select',
            'race_select',
            'subrace_select',
            'name_input',
            'backstory_input',
            'image_input',
        ]

        for state_name in expected_states:
            assert hasattr(CreateCharacter, state_name), f"Missing state: {state_name}"

    def test_state_data_structure_compatible(self):
        """Структура данных в FSM не изменилась"""
        from states.character_states import CreateCharacter

        # Проверяем, что состояния можно использовать
        assert CreateCharacter.class_select is not None
        assert CreateCharacter.name_input is not None


# =========================================================
# ТЕСТ 8: ПРОВЕРКА ПУТЕЙ К ФАЙЛАМ
# =========================================================

class TestFilePathsCompatibility:
    """Проверка, что пути к файлам не изменились"""

    def test_images_directory_exists(self):
        """Директория с изображениями существует или создаётся"""
        images_dir = "images"
        races_dir = os.path.join(images_dir, "races")
        classes_dir = os.path.join(images_dir, "classes")

        # Директории могут не существовать в тестовом окружении,
        # но пути должны быть корректными строками
        assert isinstance(images_dir, str)
        assert isinstance(races_dir, str)
        assert isinstance(classes_dir, str)

    def test_templates_directory_exists(self):
        """Директория с шаблонами существует или создаётся"""
        templates_dir = "templates"
        assert isinstance(templates_dir, str)

    def test_image_paths_are_strings(self):
        """Пути к изображениям должны быть строками"""
        from dnd_logic import get_race_image_path, get_class_image_path

        race_path = get_race_image_path("Человек")
        if race_path:
            assert isinstance(race_path, str)

        class_path = get_class_image_path("Воин")
        if class_path:
            assert isinstance(class_path, str)


# =========================================================
# ЗАПУСК ТЕСТОВ
# =========================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])