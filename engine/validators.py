# engine/validators.py
"""
D&D 5.5e Common Validators Engine
Общие валидаторы для всех модулей engine
НЕ зависит от БД, aiogram, bot.py
"""

from typing import Tuple, Optional, Any, List, Union
from enum import Enum


# =========================================================
# БАЗОВЫЕ ВАЛИДАТОРЫ
# =========================================================

class ValidationError(Exception):
    """Базовое исключение для ошибок валидации"""
    pass


class ValidationWarning(Warning):
    """Предупреждение при валидации (не фатальное)"""
    pass


def validate_positive_integer(
        value: Any,
        name: str,
        min_value: int = 1,
        max_value: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Проверяет, что значение является положительным целым числом
    """
    if not isinstance(value, int):
        return False, f"{name} должен быть целым числом, получен {type(value).__name__}"

    if value < min_value:
        return False, f"{name} не может быть меньше {min_value}, получено {value}"

    if max_value is not None and value > max_value:
        return False, f"{name} не может быть больше {max_value}, получено {value}"

    return True, None


def validate_in_range(
        value: Any,
        name: str,
        min_value: Union[int, float],
        max_value: Union[int, float],
        include_bounds: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Проверяет, что значение находится в указанном диапазоне
    """
    try:
        num_value = float(value)
    except (TypeError, ValueError):
        return False, f"{name} должен быть числом, получен {type(value).__name__}"

    if include_bounds:
        if num_value < min_value or num_value > max_value:
            return False, f"{name} должен быть в диапазоне [{min_value}, {max_value}], получено {num_value}"
    else:
        if num_value <= min_value or num_value >= max_value:
            return False, f"{name} должен быть в диапазоне ({min_value}, {max_value}), получено {num_value}"

    return True, None


def validate_not_empty(
        value: Any,
        name: str
) -> Tuple[bool, Optional[str]]:
    """
    Проверяет, что значение не пустое
    """
    if value is None:
        return False, f"{name} не может быть None"

    if isinstance(value, str) and not value.strip():
        return False, f"{name} не может быть пустой строкой"

    if isinstance(value, (list, dict, set)) and len(value) == 0:
        return False, f"{name} не может быть пустым"

    return True, None


def validate_enum_value(
        value: Any,
        enum_class: type,
        name: str
) -> Tuple[bool, Optional[str]]:
    """
    Проверяет, что значение является допустимым значением Enum
    """
    if not issubclass(enum_class, Enum):
        return False, f"{enum_class.__name__} не является классом Enum"

    valid_values = [e.value for e in enum_class]

    if value not in valid_values:
        valid_str = ", ".join(str(v) for v in valid_values)
        return False, f"{name} должен быть одним из [{valid_str}], получено {value}"

    return True, None


# =========================================================
# СПЕЦИАЛЬНЫЕ ВАЛИДАТОРЫ ДЛЯ D&D
# =========================================================

def validate_level(level: int) -> Tuple[bool, Optional[str]]:
    """Проверяет валидность уровня персонажа (1-20)"""
    return validate_positive_integer(level, "Уровень", 1, 20)


def validate_hit_die(hit_die: int) -> Tuple[bool, Optional[str]]:
    """Проверяет валидность хитового кубика (6, 8, 10, 12)"""
    valid_hit_dice = [6, 8, 10, 12]
    if not isinstance(hit_die, int):
        return False, f"Хитовый кубик должен быть целым числом, получен {type(hit_die).__name__}"
    if hit_die not in valid_hit_dice:
        return False, f"Хитовый кубик должен быть одним из {valid_hit_dice}, получено {hit_die}"
    return True, None


def validate_armor_type(armor_type: str) -> Tuple[bool, Optional[str]]:
    """Проверяет валидность типа брони (light, medium, heavy, none)"""
    valid_types = ["light", "medium", "heavy", "none"]
    if armor_type not in valid_types:
        return False, f"Тип брони должен быть одним из {valid_types}, получено {armor_type}"
    return True, None


def validate_ability_score(score: int, name: str = "Характеристика") -> Tuple[bool, Optional[str]]:
    """Проверяет валидность значения характеристики (1-30)"""
    return validate_positive_integer(score, name, 1, 30)


def validate_all_ability_scores(scores: dict) -> Tuple[bool, Optional[str]]:
    """Проверяет, что словарь содержит все 6 характеристик с валидными значениями"""
    required_stats = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

    missing = [stat for stat in required_stats if stat not in scores]
    if missing:
        return False, f"Отсутствуют характеристики: {missing}"

    extra = [stat for stat in scores.keys() if stat not in required_stats]
    if extra:
        return False, f"Лишние характеристики: {extra}"

    for stat, value in scores.items():
        valid, msg = validate_ability_score(value, stat)
        if not valid:
            return False, msg

    return True, None


def validate_stat_list(stats: List[str], name: str, expected_count: int) -> Tuple[bool, Optional[str]]:
    """Проверяет список характеристик на валидность"""
    valid_stats = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    if not isinstance(stats, list):
        return False, f"{name} должен быть списком, получен {type(stats).__name__}"
    if len(stats) != expected_count:
        return False, f"{name} должен содержать {expected_count} элементов, получено {len(stats)}"
    if len(set(stats)) != len(stats):
        return False, f"{name} содержит дубликаты"
    for stat in stats:
        if stat not in valid_stats:
            return False, f"Некорректная характеристика {stat} в {name}. Допустимые: {valid_stats}"
    return True, None


def validate_primary_stats(stats: List[str]) -> Tuple[bool, Optional[str]]:
    """Проверяет основные характеристики класса (1 или 2 элемента)"""
    if len(stats) not in [1, 2]:
        return False, f"Основные характеристики должны содержать 1 или 2 элемента, получено {len(stats)}"
    return validate_stat_list(stats, "Основные характеристики", len(stats))


def validate_background_stats(stats: List[str]) -> Tuple[bool, Optional[str]]:
    """Проверяет характеристики предыстории (ровно 3 элемента)"""
    return validate_stat_list(stats, "Характеристики предыстории", 3)


def validate_dice_expression(expression: str) -> Tuple[bool, Optional[str]]:
    """Проверяет корректность выражения куба (например, "2d6+3")"""
    import re
    if not isinstance(expression, str):
        return False, f"Выражение куба должно быть строкой, получен {type(expression).__name__}"
    pattern = r'^(\d*)d(\d+)([+-]\d+)?$'
    if not re.match(pattern, expression.lower().strip()):
        return False, f"Некорректный формат выражения куба: {expression}. Ожидается формат: XdY[+Z]"
    return True, None


def validate_character_creation_data(
        name: str,
        level: int,
        class_name: str,
        race: str,
        background: str,
        stats: dict
) -> List[str]:
    """Комплексная проверка данных для создания персонажа"""
    errors = []

    if not name or len(name.strip()) < 2:
        errors.append("Имя должно содержать минимум 2 символа")
    elif len(name) > 50:
        errors.append("Имя не может быть длиннее 50 символов")

    valid, msg = validate_level(level)
    if not valid:
        errors.append(msg)

    if not class_name or not isinstance(class_name, str):
        errors.append("Класс должен быть указан")
    if not race or not isinstance(race, str):
        errors.append("Раса должна быть указана")
    if not background or not isinstance(background, str):
        errors.append("Предыстория должна быть указана")

    valid, msg = validate_all_ability_scores(stats)
    if not valid:
        errors.append(msg)

    return errors


def validate_combat_stats(hp: int, ac: int, speed: int) -> List[str]:
    """Проверка боевых характеристик"""
    errors = []
    valid, msg = validate_positive_integer(hp, "HP", 1, 1000)
    if not valid:
        errors.append(msg)
    valid, msg = validate_positive_integer(ac, "AC", 0, 30)
    if not valid:
        errors.append(msg)
    valid, msg = validate_positive_integer(speed, "Скорость", 5, 120)
    if not valid:
        errors.append(msg)
    return errors


# =========================================================
# ДОПОЛНИТЕЛЬНЫЙ ВАЛИДАТОР ИМЕНИ (добавлен для совместимости)
# =========================================================

def validate_name(name: str) -> Tuple[bool, str]:
    """
    Проверяет имя персонажа: не пустое, длина от 2 до 50 символов.

    Args:
        name: имя персонажа

    Returns:
        Tuple[bool, str]: (валидно ли, сообщение)
    """
    if not name or len(name.strip()) == 0:
        return False, "❌ Имя не может быть пустым"
    if len(name) > 50:
        return False, "❌ Имя слишком длинное (максимум 50 символов)"
    if len(name) < 2:
        return False, "❌ Имя слишком короткое (минимум 2 символа)"
    return True, "✅ Имя корректно"


# =========================================================
# ПУБЛИЧНЫЙ API
# =========================================================

__all__ = [
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