# engine/dice.py
"""
D&D 5.5e Dice Rolling Engine
Чистая игровая логика для работы с игровыми кубами
Поддерживает все типы кубов D&D: d4, d6, d8, d10, d12, d20
НЕ зависит от БД, aiogram, bot.py
"""

import random
from typing import Tuple, Optional, List, Union
from enum import Enum
import re


# =========================================================
# КОНСТАНТЫ И НАСТРОЙКИ
# =========================================================

class DiceType(Enum):
    """Типы игровых кубов в D&D 5.5e"""
    D4 = 4
    D6 = 6
    D8 = 8
    D10 = 10
    D12 = 12
    D20 = 20
    D100 = 100

    def __str__(self) -> str:
        return f"d{self.value}"

    @classmethod
    def from_value(cls, value: int) -> Optional['DiceType']:
        """Создаёт DiceType из целого числа"""
        for dice in cls:
            if dice.value == value:
                return dice
        return None

    @classmethod
    def values(cls) -> List[int]:
        """Возвращает список возможных значений кубов"""
        return [dice.value for dice in cls]

    @classmethod
    def get_average(cls, dice_type: 'DiceType') -> float:
        """Возвращает среднее значение для куба"""
        return (dice_type.value + 1) / 2

    @classmethod
    def get_average_roll(cls, dice_type: 'DiceType') -> int:
        """Возвращает средний результат броска (округлённый вниз)"""
        return (dice_type.value // 2) + 1


# =========================================================
# ОСНОВНЫЕ ФУНКЦИИ БРОСКА КУБОВ
# =========================================================

def roll_dice(dice_type: DiceType, count: int = 1) -> int:
    """
    Бросает указанное количество кубов и возвращает сумму

    Args:
        dice_type: тип куба (D4, D6, D8, D10, D12, D20, D100)
        count: количество кубов (1-100)

    Returns:
        int: сумма результатов бросков

    Raises:
        ValueError: если количество кубов вне диапазона
    """
    if not 1 <= count <= 100:
        raise ValueError(
            f"Количество кубов должно быть в диапазоне 1-100, получено {count}"
        )

    total = 0
    for _ in range(count):
        total += random.randint(1, dice_type.value)

    return total


def roll_dice_with_advantage(dice_type: DiceType = DiceType.D20) -> int:
    """
    Бросает куб с преимуществом (два броска, берётся больший)

    Args:
        dice_type: тип куба (по умолчанию d20)

    Returns:
        int: результат броска (больший из двух)
    """
    roll1 = random.randint(1, dice_type.value)
    roll2 = random.randint(1, dice_type.value)
    return max(roll1, roll2)


def roll_dice_with_disadvantage(dice_type: DiceType = DiceType.D20) -> int:
    """
    Бросает куб с помехой (два броска, берётся меньший)

    Args:
        dice_type: тип куба (по умолчанию d20)

    Returns:
        int: результат броска (меньший из двух)
    """
    roll1 = random.randint(1, dice_type.value)
    roll2 = random.randint(1, dice_type.value)
    return min(roll1, roll2)


def roll_dice_with_modifier(
        dice_type: DiceType,
        modifier: int = 0,
        count: int = 1
) -> int:
    """
    Бросает кубы и добавляет модификатор

    Args:
        dice_type: тип куба
        modifier: модификатор (может быть отрицательным)
        count: количество кубов

    Returns:
        int: сумма бросков + модификатор (без клампа — d20 атаки и неудачные
        проверки могут давать значения <1; для урона используйте
        roll_damage_with_modifier с клампом на 0).
    """
    roll = roll_dice(dice_type, count)
    return roll + modifier


def roll_damage_with_modifier(
        dice_type: DiceType,
        modifier: int = 0,
        count: int = 1
) -> int:
    """
    Бросает урон с модификатором. Пол — 0 (а не 1): после резистов и
    отрицательных модификаторов цель может получить 0 урона, что в правилах
    D&D 5.5e разрешено.
    """
    return max(0, roll_dice_with_modifier(dice_type, modifier, count))


# =========================================================
# ПАРСИНГ И ВАЛИДАЦИЯ
# =========================================================

def parse_dice_expression(expression: str) -> Tuple[DiceType, int, int]:
    """
    Парсит строковое выражение куба

    Поддерживаемые форматы:
    - "d6" -> (D6, 1, 0)
    - "2d8" -> (D8, 2, 0)
    - "d20+5" -> (D20, 1, 5)
    - "3d10-2" -> (D10, 3, -2)

    Args:
        expression: строковое выражение (например, "2d6+3")

    Returns:
        Tuple[DiceType, int, int]: (тип куба, количество, модификатор)

    Raises:
        ValueError: если выражение некорректно
    """
    # Убираем пробелы целиком: PHB 2024 нотация терпит "1d20 + 5" как и "1d20+5".
    expression = re.sub(r"\s+", "", expression.lower().strip())

    # Регулярное выражение для парсинга
    # Формат: [количество]d[тип][+/-модификатор]
    pattern = r'^(\d*)d(\d+)([+-]\d+)?$'
    match = re.match(pattern, expression)

    if not match:
        raise ValueError(
            f"Некорректное выражение куба: {expression}. "
            f"Ожидается формат: XdY[+Z] (например, 2d6+3)"
        )

    count_str = match.group(1)
    dice_value = int(match.group(2))
    modifier_str = match.group(3)

    # Количество кубов (по умолчанию 1)
    count = int(count_str) if count_str else 1

    # Модификатор (по умолчанию 0)
    modifier = int(modifier_str) if modifier_str else 0

    # Проверяем тип куба
    dice_type = DiceType.from_value(dice_value)
    if dice_type is None:
        raise ValueError(
            f"Неподдерживаемый тип куба: d{dice_value}. "
            f"Допустимые типы: {DiceType.values()}"
        )

    # Проверяем количество
    if not 1 <= count <= 100:
        raise ValueError(f"Количество кубов должно быть 1-100, получено {count}")

    return dice_type, count, modifier


def roll_from_expression(expression: str) -> int:
    """
    Бросает кубы на основе строкового выражения

    Args:
        expression: строковое выражение (например, "2d6+3")

    Returns:
        int: результат броска
    """
    dice_type, count, modifier = parse_dice_expression(expression)
    return roll_dice_with_modifier(dice_type, modifier, count)


# =========================================================
# ФУНКЦИИ ДЛЯ РАСЧЁТА СРЕДНИХ ЗНАЧЕНИЙ
# =========================================================

def calculate_average_roll(dice_type: DiceType, count: int = 1, modifier: int = 0) -> float:
    """
    Рассчитывает среднее значение броска

    Args:
        dice_type: тип куба
        count: количество кубов
        modifier: модификатор

    Returns:
        float: среднее значение
    """
    avg_per_die = DiceType.get_average(dice_type)
    return (avg_per_die * count) + modifier


def calculate_average_roll_from_expression(expression: str) -> float:
    """
    Рассчитывает среднее значение броска из строкового выражения

    Args:
        expression: строковое выражение (например, "2d6+3")

    Returns:
        float: среднее значение
    """
    dice_type, count, modifier = parse_dice_expression(expression)
    return calculate_average_roll(dice_type, count, modifier)


def get_possible_range(dice_type: DiceType, count: int = 1, modifier: int = 0) -> Tuple[int, int]:
    """
    Возвращает возможный диапазон результатов броска

    Args:
        dice_type: тип куба
        count: количество кубов
        modifier: модификатор

    Returns:
        Tuple[int, int]: (минимальное значение, максимальное значение)
    """
    min_value = count + modifier  # Минимум: все единицы
    max_value = (dice_type.value * count) + modifier  # Максимум: все максимальные значения
    return (min_value, max_value)


# =========================================================
# СТАТИСТИЧЕСКИЕ ФУНКЦИИ
# =========================================================

def roll_stats_array(method: str = "4d6") -> List[int]:
    """
    Генерирует массив характеристик указанным методом

    Поддерживаемые методы:
    - "4d6": 4d6, отбрасываем минимальный (стандартный)
    - "3d6": 3d6 (старый стиль)
    - "standard": стандартный набор (15,14,13,12,10,8)
    - "hero": героический (16,15,14,12,10,8)

    Args:
        method: метод генерации

    Returns:
        List[int]: массив из 6 характеристик

    Raises:
        ValueError: если метод не поддерживается
    """
    if method == "4d6":
        stats = []
        for _ in range(6):
            rolls = [random.randint(1, 6) for _ in range(4)]
            rolls.remove(min(rolls))
            stats.append(sum(rolls))
        return sorted(stats, reverse=True)

    elif method == "3d6":
        stats = [sum(random.randint(1, 6) for _ in range(3)) for _ in range(6)]
        return sorted(stats, reverse=True)

    elif method == "standard":
        return [15, 14, 13, 12, 10, 8]

    elif method == "hero":
        return [16, 15, 14, 12, 10, 8]

    else:
        raise ValueError(
            f"Неизвестный метод генерации: {method}. "
            f"Доступные методы: '4d6', '3d6', 'standard', 'hero'"
        )


def calculate_critical_hit_damage(
        damage_expression: str,
        critical_multiplier: int = 2
) -> int:
    """
    Рассчитывает урон при критическом попадании

    Args:
        damage_expression: выражение урона (например, "2d6+3")
        critical_multiplier: множитель критического урона (обычно 2)

    Returns:
        int: урон при критическом попадании
    """
    dice_type, count, modifier = parse_dice_expression(damage_expression)

    # При критическом попадании бросаем все кубы дважды
    critical_count = count * critical_multiplier
    return roll_dice_with_modifier(dice_type, modifier, critical_count)


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def set_random_seed(seed: int) -> None:
    """
    Устанавливает seed для генератора случайных чисел
    Используется для тестирования и отладки

    Args:
        seed: целое число для инициализации генератора
    """
    random.seed(seed)


def get_random_state() -> Tuple:
    """
    Возвращает текущее состояние генератора случайных чисел
    Используется для сохранения состояния между вызовами

    Returns:
        Tuple: состояние генератора
    """
    return random.getstate()


def set_random_state(state: Tuple) -> None:
    """
    Восстанавливает состояние генератора случайных чисел

    Args:
        state: состояние генератора из get_random_state()
    """
    random.setstate(state)