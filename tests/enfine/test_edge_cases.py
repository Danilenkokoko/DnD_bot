# tests/engine/test_edge_cases.py
"""
Тесты для проверки крайних случаев и граничных значений
Проверяют корректность работы всех модулей engine на границах допустимых значений
"""

import pytest
import random
from engine.stats import (
    Stat, AbilityScores, BackgroundBonusDistributor,
    StatsValidator, ValidationError
)
from engine.hp import (
    calculate_hp_at_level, calculate_minimum_hp, calculate_maximum_hp,
    get_hp_range, validate_hp_calculation, HpCalculationMethod, HitDice
)
from engine.ac import (
    calculate_ac, calculate_base_ac, calculate_ac_with_armor,
    ArmorType, validate_ac, get_ac_range
)
from engine.proficiency import (
    calculate_proficiency_bonus, validate_proficiency_bonus,
    is_valid_level, ProficiencyLevel
)
from engine.dice import (
    DiceType, roll_dice, parse_dice_expression, roll_stats_array,
    calculate_average_roll, get_possible_range, set_random_seed
)
from engine.validators import (
    validate_positive_integer, validate_in_range, validate_level,
    validate_hit_die, validate_ability_score, validate_primary_stats,
    validate_background_stats
)


# =========================================================
# ТЕСТЫ КРАЙНИХ СЛУЧАЕВ ДЛЯ STATS МОДУЛЯ
# =========================================================

class TestStatsEdgeCases:
    """Тесты граничных значений для характеристик"""

    def test_ability_scores_minimum_values(self):
        """Проверка минимальных значений характеристик (1)"""
        scores = AbilityScores(
            strength=1, dexterity=1, constitution=1,
            intelligence=1, wisdom=1, charisma=1
        )

        assert scores.strength == 1
        assert scores.dexterity == 1
        assert scores.constitution == 1
        assert scores.intelligence == 1
        assert scores.wisdom == 1
        assert scores.charisma == 1

        # Проверка модификаторов для минимальных значений
        mod = (scores.strength - 10) // 2
        assert mod == -5

    def test_ability_scores_maximum_values(self):
        """Проверка максимальных значений характеристик (30)"""
        scores = AbilityScores(
            strength=30, dexterity=30, constitution=30,
            intelligence=30, wisdom=30, charisma=30
        )

        assert scores.strength == 30
        assert scores.dexterity == 30

        mod = (scores.strength - 10) // 2
        assert mod == 10

    def test_ability_scores_invalid_below_minimum(self):
        """Проверка, что значения ниже 1 не допускаются"""
        with pytest.raises(ValueError, match="диапазоне 1-30"):
            AbilityScores(
                strength=0, dexterity=10, constitution=10,
                intelligence=10, wisdom=10, charisma=10
            )

    def test_ability_scores_invalid_above_maximum(self):
        """Проверка, что значения выше 30 не допускаются"""
        with pytest.raises(ValueError, match="диапазоне 1-30"):
            AbilityScores(
                strength=31, dexterity=10, constitution=10,
                intelligence=10, wisdom=10, charisma=10
            )

    def test_background_bonus_distribution_always_sum_three(self):
        """Проверка, что сумма бонусов всегда равна 3 для любых входных данных"""
        distributor = BackgroundBonusDistributor(seed=42)

        # Все возможные комбинации primary (1 или 2 элемента)
        all_stats = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

        for primary_count in [1, 2]:
            for primary in [all_stats[:primary_count]]:
                for bg_start in range(len(all_stats) - 2):
                    background = all_stats[bg_start:bg_start + 3]

                    try:
                        bonuses = distributor.distribute(primary, background)
                        total = sum(bonuses.bonuses.values())
                        assert total == 3, f"primary={primary}, bg={background}, total={total}"
                    except Exception as e:
                        # Некоторые комбинации могут быть невалидны (дубликаты)
                        if "дубликаты" not in str(e):
                            raise

    def test_background_stats_validation_duplicates(self):
        """Проверка, что дубликаты в background_stats не допускаются"""
        with pytest.raises(ValidationError, match="дубликаты"):
            StatsValidator.validate_background_stats(["STR", "STR", "DEX"])

    def test_background_stats_validation_wrong_count(self):
        """Проверка, что количество background_stats должно быть ровно 3"""
        with pytest.raises(ValidationError, match="ровно 3 характеристики"):
            StatsValidator.validate_background_stats(["STR", "DEX"])

        with pytest.raises(ValidationError, match="ровно 3 характеристики"):
            StatsValidator.validate_background_stats(["STR", "DEX", "CON", "INT"])

    def test_primary_stats_validation(self):
        """Проверка валидации primary_stats"""
        # Допустимо 1 или 2 элемента
        valid = StatsValidator.validate_primary_stats(["STR"])
        assert len(valid) == 1

        valid = StatsValidator.validate_primary_stats(["STR", "DEX"])
        assert len(valid) == 2

        # Недопустимо 3 элемента
        with pytest.raises(ValidationError, match="1 или 2 характеристики"):
            StatsValidator.validate_primary_stats(["STR", "DEX", "CON"])


# =========================================================
# ТЕСТЫ КРАЙНИХ СЛУЧАЕВ ДЛЯ HP МОДУЛЯ
# =========================================================

class TestHpEdgeCases:
    """Тесты граничных значений для расчёта HP"""

    def test_hp_at_level_1_constitution_1(self):
        """HP на 1 уровне с CON=1 (модификатор -5, минимум +1)"""
        hp = calculate_hp_at_level(10, 1, level=1)
        # 10 (hit_die) + min(1, -5) = 10 + 1 = 11
        assert hp == 11

    def test_hp_at_level_1_constitution_30(self):
        """HP на 1 уровне с CON=30 (модификатор +10)"""
        hp = calculate_hp_at_level(6, 30, level=1)
        # 6 (hit_die) + 10 = 16
        assert hp == 16

    def test_hp_at_level_20_maximum(self):
        """Максимальные HP на 20 уровне (все броски максимальные)"""
        hp = calculate_hp_at_level(12, 20, level=20, method=HpCalculationMethod.MAX)
        # 1 уровень: 12 + 5 = 17
        # 19 уровней: 19 * (12 + 5) = 323
        # Итого: 340
        assert hp == 17 + 19 * 17  # 340

    def test_hp_minimum_range(self):
        """Проверка минимального диапазона HP"""
        min_hp = calculate_minimum_hp(6, 8, level=5)
        # CON=8 → модификатор -1 → минимум +1
        # 1 уровень: 1
        # 4 уровня: 4 * 1 = 4
        # Итого: 5
        assert min_hp == 5

    def test_hp_maximum_range(self):
        """Проверка максимального диапазона HP"""
        max_hp = calculate_maximum_hp(12, 20, level=5)
        # 1 уровень: 12 + 5 = 17
        # 4 уровня: 4 * (12 + 5) = 68
        # Итого: 85
        assert max_hp == 85

    def test_hp_validate_calculation_edge_cases(self):
        """Проверка валидации HP на граничных значениях"""
        # Валидный HP
        valid, msg = validate_hp_calculation(10, 15, 3, 30)
        assert valid is True

        # HP ниже минимального
        valid, msg = validate_hp_calculation(10, 15, 3, 5)
        assert valid is False
        assert "ниже минимального" in msg

        # HP выше максимального
        valid, msg = validate_hp_calculation(10, 15, 3, 100)
        assert valid is False
        assert "выше максимального" in msg

    def test_hp_invalid_hit_die(self):
        """Проверка, что недопустимые hit_die вызывают ошибку"""
        with pytest.raises(ValueError, match="должен быть одним из"):
            calculate_hp_at_level(7, 10, level=1)  # 7 не в [6,8,10,12]

        with pytest.raises(ValueError, match="должен быть одним из"):
            calculate_hp_at_level(20, 10, level=1)  # 20 не в [6,8,10,12]

    def test_hp_invalid_level(self):
        """Проверка, что недопустимые уровни вызывают ошибку"""
        with pytest.raises(ValueError, match="в диапазоне 1-20"):
            calculate_hp_at_level(10, 10, level=0)

        with pytest.raises(ValueError, match="в диапазоне 1-20"):
            calculate_hp_at_level(10, 10, level=21)

    def test_hp_invalid_constitution(self):
        """Проверка, что недопустимые значения CON вызывают ошибку"""
        with pytest.raises(ValueError, match="в диапазоне 1-30"):
            calculate_hp_at_level(10, 0, level=1)

        with pytest.raises(ValueError, match="в диапазоне 1-30"):
            calculate_hp_at_level(10, 31, level=1)


# =========================================================
# ТЕСТЫ КРАЙНИХ СЛУЧАЕВ ДЛЯ AC МОДУЛЯ
# =========================================================

class TestAcEdgeCases:
    """Тесты граничных значений для расчёта AC"""

    def test_ac_minimum_dexterity(self):
        """AC с минимальной Ловкостью (DEX=1, модификатор -5)"""
        ac = calculate_base_ac(1)
        assert ac == 10 - 5  # 5

    def test_ac_maximum_dexterity(self):
        """AC с максимальной Ловкостью (DEX=30, модификатор +10)"""
        ac = calculate_base_ac(30)
        assert ac == 10 + 10  # 20

    def test_ac_heavy_armor_no_dex_bonus(self):
        """Тяжёлая броня не получает бонус DEX"""
        ac_low_dex = calculate_ac(1, ArmorType.HEAVY, 16)
        ac_high_dex = calculate_ac(30, ArmorType.HEAVY, 16)
        assert ac_low_dex == ac_high_dex == 16

    def test_ac_medium_armor_dex_cap(self):
        """Средняя броня ограничивает бонус DEX до +2"""
        # DEX=14 (мод +2) → бонус +2
        ac = calculate_ac(14, ArmorType.MEDIUM, 14)
        assert ac == 14 + 2  # 16

        # DEX=30 (мод +10) → бонус всё равно +2
        ac = calculate_ac(30, ArmorType.MEDIUM, 14)
        assert ac == 14 + 2  # 16

    def test_ac_with_shield_edge_cases(self):
        """AC с щитом на граничных значениях"""
        # Без брони, DEX=1, щит
        ac = calculate_ac(1, ArmorType.NONE, 0, has_shield=True)
        assert ac == 5 + 2  # 7

        # Тяжёлая броня, DEX=30, щит
        ac = calculate_ac(30, ArmorType.HEAVY, 18, has_shield=True)
        assert ac == 18 + 2  # 20

    def test_ac_range_edge_cases(self):
        """Проверка диапазона AC на границах"""
        min_ac, max_ac = get_ac_range(1, has_shield=True)
        assert min_ac <= max_ac

        min_ac, max_ac = get_ac_range(30, has_shield=False)
        assert min_ac <= max_ac

    def test_ac_validation_edge_cases(self):
        """Проверка валидации AC на граничных значениях"""
        # Нулевой AC (теоретически возможен при отрицательных модификаторах)
        valid, msg = validate_ac(0, min_ac=0)
        assert valid is True

        # Очень высокий AC
        valid, msg = validate_ac(30)
        assert valid is True

        # Недопустимо высокий AC
        valid, msg = validate_ac(31, max_ac=30)
        assert valid is False


# =========================================================
# ТЕСТЫ КРАЙНИХ СЛУЧАЕВ ДЛЯ PROFICIENCY МОДУЛЯ
# =========================================================

class TestProficiencyEdgeCases:
    """Тесты граничных значений для бонуса мастерства"""

    def test_proficiency_bonus_level_1(self):
        """Бонус мастерства на 1 уровне"""
        bonus = calculate_proficiency_bonus(1)
        assert bonus == 2

    def test_proficiency_bonus_level_20(self):
        """Бонус мастерства на 20 уровне"""
        bonus = calculate_proficiency_bonus(20)
        assert bonus == 6

    def test_proficiency_bonus_invalid_level(self):
        """Проверка, что недопустимые уровни вызывают ошибку"""
        with pytest.raises(ValueError, match="в диапазоне 1-20"):
            calculate_proficiency_bonus(0)

        with pytest.raises(ValueError, match="в диапазоне 1-20"):
            calculate_proficiency_bonus(21)

    def test_proficiency_bonus_validation(self):
        """Проверка валидации бонуса мастерства"""
        valid, msg = validate_proficiency_bonus(2)
        assert valid is True

        valid, msg = validate_proficiency_bonus(6)
        assert valid is True

        valid, msg = validate_proficiency_bonus(1)
        assert valid is False
        assert "меньше 2" in msg

        valid, msg = validate_proficiency_bonus(7)
        assert valid is False
        assert "больше 6" in msg

    def test_proficiency_level_validation(self):
        """Проверка валидации уровня"""
        assert is_valid_level(1) is True
        assert is_valid_level(20) is True
        assert is_valid_level(0) is False
        assert is_valid_level(21) is False

    def test_saving_throw_modifier_edge_cases(self):
        """Модификаторы спасбросков на границах"""
        # Отрицательный модификатор стата
        mod = (1 - 10) // 2  # -5
        result = mod + (2 * 2)  # proficiency bonus 2, trained
        assert result == -5 + 2  # -3


# =========================================================
# ТЕСТЫ КРАЙНИХ СЛУЧАЕВ ДЛЯ DICE МОДУЛЯ
# =========================================================

class TestDiceEdgeCases:
    """Тесты граничных значений для бросков кубов"""

    def setup_method(self):
        """Устанавливаем фиксированный seed для воспроизводимости"""
        set_random_seed(42)

    def test_dice_minimum_roll(self):
        """Минимальные значения бросков кубов"""
        # Монте-Карло проверка: после множества бросков минимум должен быть 1
        for _ in range(100):
            roll = roll_dice(DiceType.D20)
            assert 1 <= roll <= 20

    def test_dice_maximum_roll(self):
        """Максимальные значения бросков кубов"""
        # Максимум не должен превышать значение куба
        for _ in range(100):
            roll = roll_dice(DiceType.D12)
            assert roll <= 12

    def test_multiple_dice_range(self):
        """Диапазон суммы нескольких кубов"""
        min_possible, max_possible = get_possible_range(DiceType.D6, count=3, modifier=0)
        assert min_possible == 3  # 3 * 1
        assert max_possible == 18  # 3 * 6

    def test_parse_dice_expression_edge_cases(self):
        """Парсинг выражений кубов на граничных значениях"""
        # Один куб
        dice_type, count, mod = parse_dice_expression("d20")
        assert count == 1

        # Много кубов
        dice_type, count, mod = parse_dice_expression("100d4")
        assert count == 100
        assert dice_type == DiceType.D4

        # Отрицательный модификатор
        dice_type, count, mod = parse_dice_expression("2d10-5")
        assert mod == -5

        # Максимальное количество кубов
        dice_type, count, mod = parse_dice_expression("100d6")
        assert count == 100

    def test_parse_dice_expression_invalid(self):
        """Проверка, что некорректные выражения вызывают ошибку"""
        with pytest.raises(ValueError, match="Некорректное выражение"):
            parse_dice_expression("")

        with pytest.raises(ValueError, match="Некорректное выражение"):
            parse_dice_expression("2fx+3")

        with pytest.raises(ValueError, match="Неподдерживаемый тип куба"):
            parse_dice_expression("d1000")

    def test_roll_stats_array_edge_cases(self):
        """Генерация характеристик на границах"""
        # 4d6 метод: минимум 3 (1,1,1,1 → отбрасываем 1 → 1+1+1=3)
        # максимум 18 (6,6,6,6 → отбрасываем 6 → 6+6+6=18)
        stats = roll_stats_array("4d6")
        for stat in stats:
            assert 3 <= stat <= 18

        # Стандартный набор
        stats = roll_stats_array("standard")
        assert len(stats) == 6
        assert sum(stats) == 15 + 14 + 13 + 12 + 10 + 8  # 72

    def test_roll_stats_array_invalid_method(self):
        """Проверка, что неизвестный метод вызывает ошибку"""
        with pytest.raises(ValueError, match="Неизвестный метод генерации"):
            roll_stats_array("invalid_method")


# =========================================================
# ТЕСТЫ КРАЙНИХ СЛУЧАЕВ ДЛЯ ВАЛИДАТОРОВ
# =========================================================

class TestValidatorsEdgeCases:
    """Тесты граничных значений для общих валидаторов"""

    def test_validate_positive_integer_edge_cases(self):
        """Проверка положительных целых чисел на границах"""
        # Граничные значения
        valid, msg = validate_positive_integer(1, "value", min_value=1)
        assert valid is True

        valid, msg = validate_positive_integer(0, "value", min_value=1)
        assert valid is False

        valid, msg = validate_positive_integer(100, "value", max_value=100)
        assert valid is True

        valid, msg = validate_positive_integer(101, "value", max_value=100)
        assert valid is False

    def test_validate_in_range_edge_cases(self):
        """Проверка диапазонов на границах"""
        # Включение границ
        valid, msg = validate_in_range(1, "value", 1, 10, include_bounds=True)
        assert valid is True

        valid, msg = validate_in_range(10, "value", 1, 10, include_bounds=True)
        assert valid is True

        # Исключение границ
        valid, msg = validate_in_range(1, "value", 1, 10, include_bounds=False)
        assert valid is False

        valid, msg = validate_in_range(10, "value", 1, 10, include_bounds=False)
        assert valid is False

        valid, msg = validate_in_range(5, "value", 1, 10, include_bounds=False)
        assert valid is True

    def test_validate_level_edge_cases(self):
        """Проверка уровня на границах"""
        valid, msg = validate_level(1)
        assert valid is True

        valid, msg = validate_level(20)
        assert valid is True

        valid, msg = validate_level(0)
        assert valid is False

        valid, msg = validate_level(21)
        assert valid is False

    def test_validate_hit_die_edge_cases(self):
        """Проверка хитового кубика"""
        valid_hit_dice = [6, 8, 10, 12]
        for hd in valid_hit_dice:
            valid, msg = validate_hit_die(hd)
            assert valid is True, f"hit_die {hd} должен быть валидным"

        invalid_hit_dice = [4, 14, 20, 100]
        for hd in invalid_hit_dice:
            valid, msg = validate_hit_die(hd)
            assert valid is False, f"hit_die {hd} должен быть невалидным"

    def test_validate_ability_score_edge_cases(self):
        """Проверка характеристик на границах"""
        # Минимум
        valid, msg = validate_ability_score(1, "STR")
        assert valid is True

        # Максимум
        valid, msg = validate_ability_score(30, "STR")
        assert valid is True

        # Ниже минимума
        valid, msg = validate_ability_score(0, "STR")
        assert valid is False

        # Выше максимума
        valid, msg = validate_ability_score(31, "STR")
        assert valid is False


# =========================================================
# ТЕСТЫ НА ДЕТЕРМИНИРОВАННОСТЬ
# =========================================================

class TestDeterministicBehavior:
    """Тесты для проверки детерминированности там, где это возможно"""

    def test_bonus_distribution_deterministic_with_seed(self):
        """Проверка, что с одинаковым seed результаты одинаковы"""
        distributor1 = BackgroundBonusDistributor(seed=42)
        distributor2 = BackgroundBonusDistributor(seed=42)

        result1 = distributor1.distribute(["STR"], ["STR", "DEX", "CON"])
        result2 = distributor2.distribute(["STR"], ["STR", "DEX", "CON"])

        assert result1.to_dict() == result2.to_dict()

    def test_bonus_distribution_deterministic_mode(self):
        """Проверка детерминированного режима распределения"""
        distributor = BackgroundBonusDistributor()

        result1 = distributor.distribute_deterministic(
            ["STR"], ["STR", "DEX", "CON"], deterministic_choice=0
        )
        result2 = distributor.distribute_deterministic(
            ["STR"], ["STR", "DEX", "CON"], deterministic_choice=0
        )

        assert result1.to_dict() == result2.to_dict()

    def test_dice_deterministic_with_seed(self):
        """Проверка, что с одинаковым seed броски кубов одинаковы"""
        set_random_seed(42)
        roll1 = roll_dice(DiceType.D20)

        set_random_seed(42)
        roll2 = roll_dice(DiceType.D20)

        assert roll1 == roll2


# =========================================================
# ЗАПУСК ТЕСТОВ
# =========================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])