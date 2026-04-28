# engine/__init__.py
"""
D&D 5.5e Game Engine
Чистая игровая логика для D&D Character Creator

Этот модуль содержит все игровые механики, не зависящие от:
- Базы данных
- Telegram API
- Внешних сервисов

Версия: 2.0.0
"""

# =========================================================
# МОДУЛЬ STATS (ХАРАКТЕРИСТИКИ)
# =========================================================

from engine.stats import (
    Stat,
    AbilityScores,
    BonusDistribution,
    StatsValidator,
    ValidationError as StatsValidationError,
    BackgroundBonusDistributor
)

# =========================================================
# МОДУЛЬ HP (ХИТЫ)
# =========================================================

from engine.hp import (
    HitDice,
    HpCalculationMethod,
    calculate_modifier as hp_calculate_modifier,
    calculate_hp_at_level,
    calculate_average_hp_gain,
    calculate_minimum_hp,
    calculate_maximum_hp,
    get_hp_range,
    validate_hp_calculation,
    calculate_hp
)

# =========================================================
# МОДУЛЬ AC (КЛАСС БРОНИ)
# =========================================================

from engine.ac import (
    ArmorType,
    ShieldType,
    AcCalculationMethod,
    calculate_modifier as ac_calculate_modifier,
    calculate_base_ac,
    calculate_light_armor_ac,
    calculate_medium_armor_ac,
    calculate_heavy_armor_ac,
    calculate_ac_with_shield,
    calculate_ac,
    StandardArmor,
    calculate_ac_with_armor,
    validate_ac,
    get_ac_range
)

# =========================================================
# МОДУЛЬ PROFICIENCY (БОНУС МАСТЕРСТВА)
# =========================================================

from engine.proficiency import (
    ProficiencyLevel,
    calculate_proficiency_bonus,
    calculate_saving_throw_modifier,
    calculate_skill_modifier,
    calculate_passive_score,
    get_proficiency_bonus_at_level,
    is_valid_level,
    get_proficiency_tier,
    calculate_proficiency_bonus_range,
    get_all_proficiency_bonuses,
    validate_proficiency_bonus
)

# =========================================================
# МОДУЛЬ DICE (КУБЫ)
# =========================================================

from engine.dice import (
    DiceType,
    roll_dice,
    roll_dice_with_advantage,
    roll_dice_with_disadvantage,
    roll_dice_with_modifier,
    parse_dice_expression,
    roll_from_expression,
    calculate_average_roll,
    calculate_average_roll_from_expression,
    get_possible_range,
    roll_stats_array,
    calculate_critical_hit_damage,
    set_random_seed,
    get_random_state,
    set_random_state
)

# =========================================================
# МОДУЛЬ VALIDATORS (ОБЩИЕ ВАЛИДАТОРЫ)
# =========================================================

from engine.validators import (
    ValidationError,
    ValidationWarning,
    validate_positive_integer,
    validate_in_range,
    validate_not_empty,
    validate_enum_value,
    validate_level,
    validate_hit_die,
    validate_armor_type,
    validate_ability_score,
    validate_all_ability_scores,
    validate_stat_list,
    validate_primary_stats,
    validate_background_stats,
    validate_dice_expression,
    validate_character_creation_data,
    validate_combat_stats,
    validate_name,  # добавлен
)

# =========================================================
# ВЕРСИЯ МОДУЛЯ
# =========================================================

__version__ = "2.0.0"
__author__ = "D&D Character Creator Team"
__description__ = "Pure game logic engine for D&D 5.5e"

# =========================================================
# ПУБЛИЧНЫЙ API
# =========================================================

__all__ = [
    # Stats module
    'Stat',
    'AbilityScores',
    'BonusDistribution',
    'StatsValidator',
    'StatsValidationError',
    'BackgroundBonusDistributor',

    # HP module
    'HitDice',
    'HpCalculationMethod',
    'hp_calculate_modifier',
    'calculate_hp_at_level',
    'calculate_average_hp_gain',
    'calculate_minimum_hp',
    'calculate_maximum_hp',
    'get_hp_range',
    'validate_hp_calculation',
    'calculate_hp',

    # AC module
    'ArmorType',
    'ShieldType',
    'AcCalculationMethod',
    'ac_calculate_modifier',
    'calculate_base_ac',
    'calculate_light_armor_ac',
    'calculate_medium_armor_ac',
    'calculate_heavy_armor_ac',
    'calculate_ac_with_shield',
    'calculate_ac',
    'StandardArmor',
    'calculate_ac_with_armor',
    'validate_ac',
    'get_ac_range',

    # Proficiency module
    'ProficiencyLevel',
    'calculate_proficiency_bonus',
    'calculate_saving_throw_modifier',
    'calculate_skill_modifier',
    'calculate_passive_score',
    'get_proficiency_bonus_at_level',
    'is_valid_level',
    'get_proficiency_tier',
    'calculate_proficiency_bonus_range',
    'get_all_proficiency_bonuses',
    'validate_proficiency_bonus',

    # Dice module
    'DiceType',
    'roll_dice',
    'roll_dice_with_advantage',
    'roll_dice_with_disadvantage',
    'roll_dice_with_modifier',
    'parse_dice_expression',
    'roll_from_expression',
    'calculate_average_roll',
    'calculate_average_roll_from_expression',
    'get_possible_range',
    'roll_stats_array',
    'calculate_critical_hit_damage',
    'set_random_seed',
    'get_random_state',
    'set_random_state',

    # Validators module
    'ValidationError',
    'ValidationWarning',
    'validate_positive_integer',
    'validate_in_range',
    'validate_not_empty',
    'validate_enum_value',
    'validate_level',
    'validate_hit_die',
    'validate_armor_type',
    'validate_ability_score',
    'validate_all_ability_scores',
    'validate_stat_list',
    'validate_primary_stats',
    'validate_background_stats',
    'validate_dice_expression',
    'validate_character_creation_data',
    'validate_combat_stats',
    'validate_name',  # добавлен
]


# =========================================================
# КРАТКАЯ ДОКУМЕНТАЦИЯ
# =========================================================

def info() -> str:
    """
    Возвращает информацию о модуле engine

    Returns:
        str: информация о версии и доступных подмодулях
    """
    return f"""
    ⚙️ D&D 5.5e Game Engine v{__version__}

    Доступные подмодули:
    - stats: работа с характеристиками (Stat, AbilityScores, BackgroundBonusDistributor)
    - hp: расчёт хитов (calculate_hp_at_level, get_hp_range)
    - ac: расчёт КБ (calculate_ac_with_armor, calculate_ac)
    - proficiency: бонус мастерства (calculate_proficiency_bonus)
    - dice: броски кубов (roll_dice, roll_from_expression)
    - validators: общие валидаторы (validate_level, validate_ability_score, validate_name)

    Пример использования:
        from engine import calculate_proficiency_bonus, calculate_hp_at_level, validate_name

        bonus = calculate_proficiency_bonus(5)  # +3
        hp = calculate_hp_at_level(10, 15, 3)   # HP для Воина 3 уровня
        valid, msg = validate_name("Арагорн")   # (True, "✅ Имя корректно")
    """