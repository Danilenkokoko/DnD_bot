# engine/hp.py
"""
D&D 5.5e Hit Points Calculation Engine
Чистая игровая логика для расчёта хитов персонажа
НЕ зависит от БД, aiogram, bot.py
"""

import math
from typing import Tuple, Optional
from enum import Enum


# =========================================================
# КОНСТАНТЫ И НАСТРОЙКИ
# =========================================================

class HitDice(Enum):
    """Возможные хитовые кубики в D&D 5.5e"""
    D6 = 6
    D8 = 8
    D10 = 10
    D12 = 12

    def __str__(self) -> str:
        return f"d{self.value}"

    @classmethod
    def from_int(cls, value: int) -> Optional['HitDice']:
        """Создаёт HitDice из целого числа"""
        for die in cls:
            if die.value == value:
                return die
        return None

    @classmethod
    def values(cls) -> list:
        """Возвращает список возможных значений"""
        return [die.value for die in cls]


class HpCalculationMethod(Enum):
    """Способы расчёта HP"""
    AVERAGE = "average"  # Среднее значение: hit_die/2 + 1
    ROLL = "roll"  # Случайный бросок (for future use)
    MAX = "max"  # Максимальное значение (for future use)


# =========================================================
# ОСНОВНЫЕ ФУНКЦИИ РАСЧЁТА HP
# =========================================================

def calculate_modifier(stat_value: int) -> int:
    """
    Рассчитывает модификатор характеристики

    Args:
        stat_value: значение характеристики (например, 15)

    Returns:
        int: модификатор (например, 2)
    """
    return (stat_value - 10) // 2


def calculate_hp_at_level(
        hit_die: int,
        constitution: int,
        level: int = 1,
        method: HpCalculationMethod = HpCalculationMethod.AVERAGE
) -> int:
    """
    Рассчитывает HP персонажа на указанном уровне

    Правила D&D 5.5e:
    - 1 уровень: максимальное значение hit_die + CON модификатор (минимум 1)
    - 2+ уровень: average или roll + CON модификатор за каждый уровень

    Args:
        hit_die: значение хитового кубика (6, 8, 10, 12)
        constitution: значение характеристики CON (1-30)
        level: уровень персонажа (1-20)
        method: способ расчёта (по умолчанию AVERAGE)

    Returns:
        int: общее количество HP

    Raises:
        ValueError: если hit_die невалидный, constitution вне диапазона, level вне диапазона
    """
    # Валидация входных данных
    if hit_die not in HitDice.values():
        raise ValueError(
            f"hit_die должен быть одним из {HitDice.values()}, получено {hit_die}"
        )

    if not 1 <= constitution <= 30:
        raise ValueError(
            f"constitution должен быть в диапазоне 1-30, получено {constitution}"
        )

    if not 1 <= level <= 20:
        raise ValueError(
            f"level должен быть в диапазоне 1-20, получено {level}"
        )

    # Модификатор CON (D&D 5.5e 2024 PHB):
    # бонус за уровень = CON_mod НАПРЯМУЮ (может быть отрицательным).
    # Только итоговое HP не должно быть меньше 1 — это финальная защита.
    con_modifier = calculate_modifier(constitution)
    hp_per_level_bonus = con_modifier

    # 1 уровень: максимальное значение hit_die + CON модификатор
    if level == 1:
        return max(1, hit_die + hp_per_level_bonus)

    # 2+ уровень: HP на 1 уровне + прирост за каждый последующий уровень
    hp = hit_die + hp_per_level_bonus

    for current_level in range(2, level + 1):
        hp += _calculate_hp_gain_for_level(hit_die, hp_per_level_bonus, method, current_level)

    # Финальная защита: персонаж не может иметь меньше 1 HP
    return max(1, hp)


def _calculate_hp_gain_for_level(
        hit_die: int,
        hp_per_level_bonus: int,
        method: HpCalculationMethod,
        level: int
) -> int:
    """
    Рассчитывает прирост HP за один уровень

    Args:
        hit_die: значение хитового кубика
        hp_per_level_bonus: бонус CON модификатор (минимум 1)
        method: способ расчёта
        level: текущий уровень (для логирования)

    Returns:
        int: прирост HP за уровень
    """
    if method == HpCalculationMethod.AVERAGE:
        # Среднее значение: (hit_die / 2) + 1
        average_roll = (hit_die // 2) + 1
        return max(1, average_roll + hp_per_level_bonus)

    elif method == HpCalculationMethod.ROLL:
        # Бросок кубика (будет реализовано в engine/dice.py)
        # Пока возвращаем среднее как fallback
        average_roll = (hit_die // 2) + 1
        return max(1, average_roll + hp_per_level_bonus)

    elif method == HpCalculationMethod.MAX:
        # Максимальное значение (для мощных NPC)
        return max(1, hit_die + hp_per_level_bonus)

    else:
        raise ValueError(f"Неизвестный метод расчёта HP: {method}")


def calculate_average_hp_gain(hit_die: int, constitution: int) -> int:
    """
    Рассчитывает средний прирост HP за один уровень

    Args:
        hit_die: значение хитового кубика
        constitution: значение характеристики CON

    Returns:
        int: средний прирост HP
    """
    con_modifier = calculate_modifier(constitution)
    hp_per_level_bonus = max(1, con_modifier)
    average_roll = (hit_die // 2) + 1
    return max(1, average_roll + hp_per_level_bonus)


def calculate_minimum_hp(hit_die: int, constitution: int, level: int) -> int:
    """
    Рассчитывает минимально возможные HP при плохих бросках

    Args:
        hit_die: значение хитового кубика
        constitution: значение характеристики CON
        level: уровень персонажа

    Returns:
        int: минимальные HP
    """
    con_modifier = calculate_modifier(constitution)
    hp_per_level_bonus = max(1, con_modifier)

    # Минимум на 1 уровне: 1 + CON бонус
    min_hp = max(1, 1 + hp_per_level_bonus)

    # На каждом последующем уровне минимум: 1 + CON бонус
    for _ in range(2, level + 1):
        min_hp += max(1, 1 + hp_per_level_bonus)

    return min_hp


def calculate_maximum_hp(hit_die: int, constitution: int, level: int) -> int:
    """
    Рассчитывает максимально возможные HP при идеальных бросках

    Args:
        hit_die: значение хитового кубика
        constitution: значение характеристики CON
        level: уровень персонажа

    Returns:
        int: максимальные HP
    """
    con_modifier = calculate_modifier(constitution)
    hp_per_level_bonus = max(1, con_modifier)

    # Максимум на 1 уровне: hit_die + CON бонус
    max_hp = max(1, hit_die + hp_per_level_bonus)

    # На каждом последующем уровне максимум: hit_die + CON бонус
    for _ in range(2, level + 1):
        max_hp += max(1, hit_die + hp_per_level_bonus)

    return max_hp


def get_hp_range(hit_die: int, constitution: int, level: int) -> Tuple[int, int]:
    """
    Возвращает диапазон возможных HP (мин - макс)

    Args:
        hit_die: значение хитового кубика
        constitution: значение характеристики CON
        level: уровень персонажа

    Returns:
        Tuple[int, int]: (минимальные HP, максимальные HP)
    """
    return (
        calculate_minimum_hp(hit_die, constitution, level),
        calculate_maximum_hp(hit_die, constitution, level)
    )


def validate_hp_calculation(
        hit_die: int,
        constitution: int,
        level: int,
        calculated_hp: int
) -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность рассчитанных HP

    Args:
        hit_die: значение хитового кубика
        constitution: значение характеристики CON
        level: уровень персонажа
        calculated_hp: рассчитанное значение HP

    Returns:
        Tuple[bool, Optional[str]]: (валидно ли, сообщение об ошибке)
    """
    min_hp, max_hp = get_hp_range(hit_die, constitution, level)

    if calculated_hp < min_hp:
        return False, f"HP ({calculated_hp}) ниже минимального ({min_hp})"

    if calculated_hp > max_hp:
        return False, f"HP ({calculated_hp}) выше максимального ({max_hp})"

    return True, None


def calculate_hp(
        hit_die: int,
        constitution: int,
        level: int = 1,
        use_average: bool = True
) -> int:
    """
    Упрощённая функция для расчёта HP (для обратной совместимости)

    Args:
        hit_die: значение хитового кубика
        constitution: значение характеристики CON
        level: уровень персонажа
        use_average: использовать среднее значение (True) или максимальное (False)

    Returns:
        int: рассчитанные HP
    """
    method = HpCalculationMethod.AVERAGE if use_average else HpCalculationMethod.MAX
    return calculate_hp_at_level(hit_die, constitution, level, method)
