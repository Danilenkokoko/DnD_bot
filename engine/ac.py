# engine/ac.py
"""
D&D 5.5e Armor Class Calculation Engine
Чистая игровая логика для расчёта Класса Брони персонажа
НЕ зависит от БД, aiogram, bot.py
"""

from typing import Optional, Tuple
from enum import Enum


# =========================================================
# КОНСТАНТЫ И НАСТРОЙКИ
# =========================================================

class ArmorType(Enum):
    """Типы брони в D&D 5.5e"""
    NONE = "none"
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_string(cls, value: str) -> Optional['ArmorType']:
        """Создаёт ArmorType из строки"""
        for armor_type in cls:
            if armor_type.value == value:
                return armor_type
        return None


class ShieldType(Enum):
    """Типы щитов"""
    NONE = "none"
    BASIC = "basic"  # +2 к AC
    MAGIC = "magic"  # +3 к AC (for future use)

    @classmethod
    def get_ac_bonus(cls, shield_type: 'ShieldType') -> int:
        """Возвращает бонус к AC для щита"""
        bonuses = {
            ShieldType.NONE: 0,
            ShieldType.BASIC: 2,
            ShieldType.MAGIC: 3,
        }
        return bonuses.get(shield_type, 0)


class AcCalculationMethod(Enum):
    """Методы расчёта AC"""
    BASE = "base"  # Базовая формула: 10 + DEX
    ARMOR = "armor"  # С учётом брони
    NATURAL = "natural"  # Естественная броня (for future use)
    UNARMORED = "unarmored"  # Бездоспешная защита (for future use)


# =========================================================
# ОСНОВНЫЕ ФУНКЦИИ РАСЧЁТА AC
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


def calculate_base_ac(dexterity: int) -> int:
    """
    Рассчитывает базовый AC без брони

    Формула: 10 + модификатор DEX

    Args:
        dexterity: значение характеристики Ловкость (1-30)

    Returns:
        int: базовый AC
    """
    dex_mod = calculate_modifier(dexterity)
    return 10 + dex_mod


def calculate_light_armor_ac(dexterity: int, armor_ac_base: int = 11) -> int:
    """
    Рассчитывает AC для лёгкой брони

    Правило: AC = базовая броня + модификатор DEX (без ограничений)

    Args:
        dexterity: значение характеристики Ловкость (1-30)
        armor_ac_base: базовая броня (обычно 11-12)

    Returns:
        int: AC в лёгкой броне
    """
    dex_mod = calculate_modifier(dexterity)
    return armor_ac_base + dex_mod


def calculate_medium_armor_ac(dexterity: int, armor_ac_base: int = 14) -> int:
    """
    Рассчитывает AC для средней брони

    Правило: AC = базовая броня + модификатор DEX (максимум +2)

    Args:
        dexterity: значение характеристики Ловкость (1-30)
        armor_ac_base: базовая броня (обычно 14-15)

    Returns:
        int: AC в средней броне
    """
    dex_mod = calculate_modifier(dexterity)
    dex_bonus = min(2, dex_mod)  # Максимум +2 от DEX
    return armor_ac_base + dex_bonus


def calculate_heavy_armor_ac(armor_ac_base: int = 16) -> int:
    """
    Рассчитывает AC для тяжёлой брони

    Правило: AC = базовая броня (бонус DEX не применяется)

    Args:
        armor_ac_base: базовая броня (обычно 16-18)

    Returns:
        int: AC в тяжёлой броне
    """
    return armor_ac_base


def calculate_ac_with_shield(ac_without_shield: int, has_shield: bool = False) -> int:
    """
    Добавляет бонус щита к AC

    Правило: щит даёт +2 к AC

    Args:
        ac_without_shield: AC без учёта щита
        has_shield: есть ли щит

    Returns:
        int: AC с учётом щита
    """
    if has_shield:
        return ac_without_shield + ShieldType.get_ac_bonus(ShieldType.BASIC)
    return ac_without_shield


def calculate_ac(
        dexterity: int,
        armor_type: Optional[ArmorType] = None,
        armor_base: int = 0,
        has_shield: bool = False
) -> int:
    """
    Основная функция расчёта AC с учётом всех параметров

    Args:
        dexterity: значение характеристики Ловкость (1-30)
        armor_type: тип брони (light, medium, heavy, none)
        armor_base: базовая броня (если не указана, используются стандартные)
        has_shield: наличие щита

    Returns:
        int: итоговый AC

    Raises:
        ValueError: если тип брони неизвестен или dexterity вне диапазона
    """
    # Валидация
    if not 1 <= dexterity <= 30:
        raise ValueError(
            f"dexterity должен быть в диапазоне 1-30, получено {dexterity}"
        )

    if armor_type is None:
        armor_type = ArmorType.NONE

    # Расчёт AC в зависимости от типа брони
    if armor_type == ArmorType.NONE:
        ac = calculate_base_ac(dexterity)

    elif armor_type == ArmorType.LIGHT:
        base = armor_base if armor_base > 0 else 11
        ac = calculate_light_armor_ac(dexterity, base)

    elif armor_type == ArmorType.MEDIUM:
        base = armor_base if armor_base > 0 else 14
        ac = calculate_medium_armor_ac(dexterity, base)

    elif armor_type == ArmorType.HEAVY:
        base = armor_base if armor_base > 0 else 16
        ac = calculate_heavy_armor_ac(base)

    else:
        raise ValueError(f"Неизвестный тип брони: {armor_type}")

    # Добавляем щит
    ac = calculate_ac_with_shield(ac, has_shield)

    return ac


# =========================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С КОНКРЕТНЫМИ ВИДАМИ БРОНИ
# =========================================================

class StandardArmor:
    """Стандартные виды брони в D&D 5.5e"""

    # Лёгкая броня
    PADDED = ("padded", ArmorType.LIGHT, 11)
    LEATHER = ("leather", ArmorType.LIGHT, 11)
    STUDDED_LEATHER = ("studded_leather", ArmorType.LIGHT, 12)

    # Средняя броня
    HIDE = ("hide", ArmorType.MEDIUM, 12)
    CHAIN_SHIRT = ("chain_shirt", ArmorType.MEDIUM, 13)
    BREASTPLATE = ("breastplate", ArmorType.MEDIUM, 14)
    HALF_PLATE = ("half_plate", ArmorType.MEDIUM, 15)

    # Тяжёлая броня
    RING_MAIL = ("ring_mail", ArmorType.HEAVY, 14)
    CHAIN_MAIL = ("chain_mail", ArmorType.HEAVY, 16)
    SPLINT = ("splint", ArmorType.HEAVY, 17)
    PLATE = ("plate", ArmorType.HEAVY, 18)

    @classmethod
    def get_ac_for_armor(cls, armor_name: str, dexterity: int, has_shield: bool = False) -> int:
        """
        Рассчитывает AC для конкретного вида брони по названию

        Args:
            armor_name: название брони (на русском)
            dexterity: значение Ловкости
            has_shield: наличие щита

        Returns:
            int: AC
        """
        armor_map = {
            "Стёганая броня": (ArmorType.LIGHT, 11),
            "Кожаная броня": (ArmorType.LIGHT, 11),
            "Кольчуга": (ArmorType.MEDIUM, 16),
            "Ламелляр": (ArmorType.MEDIUM, 14),
            "Латы": (ArmorType.HEAVY, 18),
            "Кираса": (ArmorType.MEDIUM, 14),
            "Полулаты": (ArmorType.MEDIUM, 15),
            "Кольчужная рубаха": (ArmorType.LIGHT, 13),
            "Кольчужная броня": (ArmorType.MEDIUM, 16),
            "Сплит-броня": (ArmorType.HEAVY, 17),
        }

        # Поиск по русским названиям
        for name, (armor_type, base_ac) in armor_map.items():
            if armor_name == name or armor_name in name:
                return calculate_ac(dexterity, armor_type, base_ac, has_shield)

        # Если броня не найдена, используем базовый расчёт
        return calculate_base_ac(dexterity)


def calculate_ac_with_armor(
        dexterity: int,
        armor_name: Optional[str] = None,
        has_shield: bool = False
) -> int:
    """
    Упрощённая функция для расчёта AC с учётом брони по названию

    Args:
        dexterity: значение Ловкости
        armor_name: название брони (на русском)
        has_shield: наличие щита

    Returns:
        int: итоговый AC
    """
    if not armor_name:
        return calculate_base_ac(dexterity)

    return StandardArmor.get_ac_for_armor(armor_name, dexterity, has_shield)


# =========================================================
# ВАЛИДАЦИЯ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =========================================================

def validate_ac(ac: int, min_ac: int = 0, max_ac: int = 30) -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность рассчитанного AC

    Args:
        ac: рассчитанный AC
        min_ac: минимально допустимый AC
        max_ac: максимально допустимый AC

    Returns:
        Tuple[bool, Optional[str]]: (валидно ли, сообщение об ошибке)
    """
    if ac < min_ac:
        return False, f"AC ({ac}) ниже минимального ({min_ac})"

    if ac > max_ac:
        return False, f"AC ({ac}) выше максимального ({max_ac})"

    return True, None


def get_ac_range(dexterity: int, has_shield: bool = False) -> Tuple[int, int]:
    """
    Возвращает диапазон возможного AC при заданной Ловкости

    Мин: без брони с минимальным DEX
    Макс: тяжёлая броня с максимальным DEX (без учёта DEX)

    Args:
        dexterity: значение Ловкости
        has_shield: наличие щита

    Returns:
        Tuple[int, int]: (минимальный AC, максимальный AC)
    """
    dex_mod = calculate_modifier(dexterity)
    shield_bonus = 2 if has_shield else 0

    # Минимум: без брони с отрицательным DEX (но не менее 10 + DEX)
    min_ac = max(0, 10 + dex_mod + shield_bonus)

    # Максимум: тяжёлая броня (латы = 18) + щит
    max_ac = 18 + shield_bonus

    return (min_ac, max_ac)