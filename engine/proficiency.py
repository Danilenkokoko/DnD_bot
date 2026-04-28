# engine/proficiency.py
"""
D&D 5.5e Proficiency Bonus Calculation Engine
Чистая игровая логика для расчёта бонуса мастерства
НЕ зависит от БД, aiogram, bot.py
"""

from typing import Tuple, Optional, Dict
from enum import IntEnum


# =========================================================
# КОНСТАНТЫ И НАСТРОЙКИ
# =========================================================

class ProficiencyLevel(IntEnum):
    """Уровни владения навыком/спасброском"""
    UNTRAINED = 0  # Не владеет
    TRAINED = 1  # Владеет
    EXPERT = 2  # Эксперт (удвоенный бонус)

    @classmethod
    def get_multiplier(cls, level: 'ProficiencyLevel') -> int:
        """Возвращает множитель для бонуса мастерства"""
        multipliers = {
            cls.UNTRAINED: 0,
            cls.TRAINED: 1,
            cls.EXPERT: 2,
        }
        return multipliers.get(level, 0)


# Таблица бонусов мастерства по уровням
_PROFICIENCY_BONUS_TABLE: Dict[int, int] = {
    1: 2,
    2: 2,
    3: 2,
    4: 2,
    5: 3,
    6: 3,
    7: 3,
    8: 3,
    9: 4,
    10: 4,
    11: 4,
    12: 4,
    13: 5,
    14: 5,
    15: 5,
    16: 5,
    17: 6,
    18: 6,
    19: 6,
    20: 6,
}


# =========================================================
# ОСНОВНЫЕ ФУНКЦИИ
# =========================================================

def calculate_proficiency_bonus(level: int) -> int:
    """
    Рассчитывает бонус мастерства в зависимости от уровня

    Правила D&D 5.5e:
    - Уровни 1-4: +2
    - Уровни 5-8: +3
    - Уровни 9-12: +4
    - Уровни 13-16: +5
    - Уровни 17-20: +6

    Args:
        level: уровень персонажа (1-20)

    Returns:
        int: бонус мастерства

    Raises:
        ValueError: если уровень вне диапазона 1-20
    """
    if not 1 <= level <= 20:
        raise ValueError(
            f"level должен быть в диапазоне 1-20, получено {level}"
        )

    return _PROFICIENCY_BONUS_TABLE.get(level, 2)


def calculate_saving_throw_modifier(
        stat_modifier: int,
        proficiency_level: ProficiencyLevel,
        proficiency_bonus: Optional[int] = None,
        level: Optional[int] = None
) -> int:
    """
    Рассчитывает модификатор спасброска

    Формула: stat_modifier + (proficiency_bonus * multiplier)

    Args:
        stat_modifier: модификатор соответствующей характеристики
        proficiency_level: уровень владения (UNTRAINED, TRAINED, EXPERT)
        proficiency_bonus: бонус мастерства (если None, рассчитывается по level)
        level: уровень персонажа (нужен если proficiency_bonus не указан)

    Returns:
        int: итоговый модификатор спасброска

    Raises:
        ValueError: если недостаточно данных для расчёта
    """
    # Определяем бонус мастерства
    if proficiency_bonus is None:
        if level is None:
            raise ValueError(
                "Необходимо указать либо proficiency_bonus, либо level"
            )
        proficiency_bonus = calculate_proficiency_bonus(level)

    # Рассчитываем множитель
    multiplier = ProficiencyLevel.get_multiplier(proficiency_level)

    return stat_modifier + (proficiency_bonus * multiplier)


def calculate_skill_modifier(
        stat_modifier: int,
        proficiency_level: ProficiencyLevel,
        proficiency_bonus: Optional[int] = None,
        level: Optional[int] = None,
        expertise: bool = False
) -> int:
    """
    Рассчитывает модификатор навыка

    Формула: stat_modifier + (proficiency_bonus * multiplier)

    Args:
        stat_modifier: модификатор соответствующей характеристики
        proficiency_level: уровень владения (UNTRAINED, TRAINED, EXPERT)
        proficiency_bonus: бонус мастерства (если None, рассчитывается по level)
        level: уровень персонажа (нужен если proficiency_bonus не указан)
        expertise: флаг экспертности (удваивает бонус, используется если proficiency_level = TRAINED)

    Returns:
        int: итоговый модификатор навыка
    """
    # Если указан флаг expertise, повышаем уровень до EXPERT
    if expertise and proficiency_level == ProficiencyLevel.TRAINED:
        actual_level = ProficiencyLevel.EXPERT
    else:
        actual_level = proficiency_level

    return calculate_saving_throw_modifier(
        stat_modifier,
        actual_level,
        proficiency_bonus,
        level
    )


def calculate_passive_score(active_modifier: int, base: int = 10) -> int:
    """
    Рассчитывает пассивное значение навыка/восприятия

    Формула: base + модификатор

    Args:
        active_modifier: модификатор активной проверки
        base: базовое значение (обычно 10)

    Returns:
        int: пассивное значение
    """
    return base + active_modifier


# =========================================================
# ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def get_proficiency_bonus_at_level(level: int) -> int:
    """
    Алиас для calculate_proficiency_bonus (для совместимости)
    """
    return calculate_proficiency_bonus(level)


def is_valid_level(level: int) -> bool:
    """
    Проверяет, является ли уровень валидным (1-20)

    Args:
        level: уровень для проверки

    Returns:
        bool: True если уровень валиден
    """
    return 1 <= level <= 20


def get_proficiency_tier(level: int) -> str:
    """
    Возвращает "тир" бонуса мастерства для отображения

    Args:
        level: уровень персонажа

    Returns:
        str: текстовое описание тира
    """
    bonus = calculate_proficiency_bonus(level)

    tiers = {
        2: "Низкий уровень (1-4)",
        3: "Средний уровень (5-8)",
        4: "Высокий уровень (9-12)",
        5: "Продвинутый уровень (13-16)",
        6: "Эпический уровень (17-20)",
    }

    return tiers.get(bonus, f"Бонус +{bonus}")


def calculate_proficiency_bonus_range() -> Tuple[int, int]:
    """
    Возвращает диапазон бонусов мастерства

    Returns:
        Tuple[int, int]: (минимальный бонус, максимальный бонус)
    """
    return (2, 6)


def get_all_proficiency_bonuses() -> Dict[int, int]:
    """
    Возвращает словарь со всеми бонусами мастерства по уровням

    Returns:
        Dict[int, int]: {level: proficiency_bonus}
    """
    return _PROFICIENCY_BONUS_TABLE.copy()


def validate_proficiency_bonus(proficiency_bonus: int) -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность бонуса мастерства

    Args:
        proficiency_bonus: бонус для проверки

    Returns:
        Tuple[bool, Optional[str]]: (валидно ли, сообщение об ошибке)
    """
    if not isinstance(proficiency_bonus, int):
        return False, f"Бонус мастерства должен быть целым числом, получен {type(proficiency_bonus)}"

    if proficiency_bonus < 2:
        return False, f"Бонус мастерства не может быть меньше 2, получено {proficiency_bonus}"

    if proficiency_bonus > 6:
        return False, f"Бонус мастерства не может быть больше 6, получено {proficiency_bonus}"

    return True, None