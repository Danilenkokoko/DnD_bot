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
        for armor_type in cls:
            if armor_type.value == value:
                return armor_type
        return None


class ShieldType(Enum):
    """Типы щитов"""
    NONE = "none"
    BASIC = "basic"      # +2 к AC
    MAGIC = "magic"      # +3 к AC (for future use)
    
    @classmethod
    def get_ac_bonus(cls, shield_type: 'ShieldType') -> int:
        bonuses = {
            ShieldType.NONE: 0,
            ShieldType.BASIC: 2,
            ShieldType.MAGIC: 3,
        }
        return bonuses.get(shield_type, 0)


class AcCalculationMethod(Enum):
    """Методы расчёта AC"""
    BASE = "base"
    ARMOR = "armor"
    NATURAL = "natural"
    UNARMORED = "unarmored"


# =========================================================
# ОСНОВНЫЕ ФУНКЦИИ РАСЧЁТА AC
# =========================================================

def calculate_modifier(stat_value: int) -> int:
    """Рассчитывает модификатор характеристики"""
    return (stat_value - 10) // 2


def calculate_base_ac(dexterity: int) -> int:
    """Базовый AC без брони: 10 + модификатор DEX"""
    dex_mod = calculate_modifier(dexterity)
    return 10 + dex_mod


def calculate_light_armor_ac(dexterity: int, armor_ac_base: int = 11) -> int:
    """Лёгкая броня: базовая + полный модификатор DEX"""
    dex_mod = calculate_modifier(dexterity)
    return armor_ac_base + dex_mod


def calculate_medium_armor_ac(dexterity: int, armor_ac_base: int = 14) -> int:
    """Средняя броня: базовая + DEX (максимум +2)"""
    dex_mod = calculate_modifier(dexterity)
    dex_bonus = min(2, dex_mod)
    return armor_ac_base + dex_bonus


def calculate_heavy_armor_ac(armor_ac_base: int = 16) -> int:
    """Тяжёлая броня: только базовая"""
    return armor_ac_base


def calculate_ac_with_shield(ac_without_shield: int, has_shield: bool = False) -> int:
    """Добавляет бонус щита (+2)"""
    if has_shield:
        return ac_without_shield + ShieldType.get_ac_bonus(ShieldType.BASIC)
    return ac_without_shield


def calculate_unarmored_ac(class_name: str, dexterity: int, second_stat: int) -> int:
    """
    Рассчитывает AC для бездоспешной защиты (Unarmored Defense).
    
    Варвар: 10 + модификатор Ловкости + модификатор Телосложения
    Монах:  10 + модификатор Ловкости + модификатор Мудрости
    
    Args:
        class_name: название класса ("Варвар" или "Монах")
        dexterity: значение Ловкости
        second_stat: Телосложение (для Варвара) или Мудрость (для Монаха)
    
    Returns:
        int: AC без учёта щита и брони
    """
    dex_mod = calculate_modifier(dexterity)
    second_mod = calculate_modifier(second_stat)
    
    if class_name in ["Варвар", "Монах"]:
        return 10 + dex_mod + second_mod
    else:
        # Fallback – базовый AC
        return 10 + dex_mod


def calculate_ac(
    dexterity: int,
    armor_type: Optional[ArmorType] = None,
    armor_base: int = 0,
    has_shield: bool = False,
    class_name: Optional[str] = None,
    second_stat: Optional[int] = None
) -> int:
    """
    Основная функция расчёта AC с учётом брони, щита и Unarmored Defense.
    
    Args:
        dexterity: значение Ловкости
        armor_type: тип брони (light, medium, heavy, none)
        armor_base: базовая броня (если не указана, используются стандартные)
        has_shield: наличие щита
        class_name: название класса (для Unarmored Defense)
        second_stat: вторая характеристика (CON для Варвара, WIS для Монаха)
    
    Returns:
        int: итоговый AC
    """
    # Валидация
    if not 1 <= dexterity <= 30:
        raise ValueError(f"dexterity должен быть в диапазоне 1-30, получено {dexterity}")
    
    # Если нет брони и подходит класс – используем Unarmored Defense
    if (armor_type is None or armor_type == ArmorType.NONE) and class_name in ["Варвар", "Монах"] and second_stat is not None:
        ac = calculate_unarmored_ac(class_name, dexterity, second_stat)
    else:
        # Обычный расчёт с бронёй
        if armor_type is None:
            armor_type = ArmorType.NONE
        
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
        # Имена брони синхронизированы с seed_data.ARMOR_DATA (реальная БД).
        # Значения AC и тип — по PHB 2024 (D&D 5.5e).
        armor_map = {
            # ── Лёгкая броня (LIGHT, +DEX полностью) ──────────────────
            "Стёганый доспех":              (ArmorType.LIGHT, 11),
            "Кожаный доспех":               (ArmorType.LIGHT, 11),
            "Проклёпанный кожаный доспех":  (ArmorType.LIGHT, 12),
            # ── Средняя броня (MEDIUM, +DEX max 2) ────────────────────
            "Шкурный доспех":               (ArmorType.MEDIUM, 12),
            "Кольчужная рубаха":            (ArmorType.MEDIUM, 13),
            "Кираса":                       (ArmorType.MEDIUM, 14),
            "Чешуйчатый доспех":            (ArmorType.MEDIUM, 14),
            "Полулаты":                     (ArmorType.MEDIUM, 15),
            # ── Тяжёлая броня (HEAVY, без DEX) ────────────────────────
            "Кольчужный доспех":            (ArmorType.HEAVY, 16),  # Chain Mail (PHB 2024: AC 16)
            "Колечный доспех":              (ArmorType.HEAVY, 14),  # Ring Mail
            "Пластинчатый доспех":          (ArmorType.HEAVY, 17),  # Splint (PHB 2024: AC 17)
            "Латный доспех":                (ArmorType.HEAVY, 18),  # Plate
        }

        # Точное совпадение приоритетнее (избегает «Кожаный доспех» ⊂ «Проклёпанный кожаный доспех»).
        if armor_name in armor_map:
            armor_type, base_ac = armor_map[armor_name]
            return calculate_ac(dexterity, armor_type, base_ac, has_shield)

        # Fallback: подстрочное совпадение (для совместимости со старыми именами).
        for name, (armor_type, base_ac) in armor_map.items():
            if armor_name in name or name in armor_name:
                return calculate_ac(dexterity, armor_type, base_ac, has_shield)

        # Если броня не найдена, используем базовый расчёт
        return calculate_base_ac(dexterity)


def calculate_ac_with_armor(
    dexterity: int,
    armor_name: Optional[str] = None,
    has_shield: bool = False,
    class_name: Optional[str] = None,
    second_stat: Optional[int] = None
) -> int:
    """
    Упрощённая функция для расчёта AC с учётом брони по названию
    """
    if not armor_name:
        # Если нет брони и есть данные для Unarmored Defense
        if class_name in ["Варвар", "Монах"] and second_stat is not None:
            return calculate_unarmored_ac(class_name, dexterity, second_stat) + (2 if has_shield else 0)
        return calculate_base_ac(dexterity) + (2 if has_shield else 0)

    return StandardArmor.get_ac_for_armor(armor_name, dexterity, has_shield)


def validate_ac(ac: int, min_ac: int = 0, max_ac: int = 30) -> Tuple[bool, Optional[str]]:
    if ac < min_ac:
        return False, f"AC ({ac}) ниже минимального ({min_ac})"
    if ac > max_ac:
        return False, f"AC ({ac}) выше максимального ({max_ac})"
    return True, None


def get_ac_range(
    dexterity: int,
    has_shield: bool = False,
    armor_type: Optional[ArmorType] = None,
) -> Tuple[int, int]:
    """
    Возвращает диапазон AC с учётом типа брони.

    PHB 2024:
      • Без брони:  10 + DEX_mod (+ щит).
      • Лёгкая:     армор_base + DEX_mod (+ щит). База 11..12.
      • Средняя:    армор_base + min(2, DEX_mod) (+ щит). База 12..15.
      • Тяжёлая:    армор_base (+ щит), без DEX. База 14..18.
    """
    dex_mod = calculate_modifier(dexterity)
    shield = 2 if has_shield else 0

    if armor_type is None or armor_type == ArmorType.NONE:
        ac = 10 + dex_mod + shield
        return (max(0, ac), ac)

    if armor_type == ArmorType.LIGHT:
        # 11..12 base + полный DEX
        return (max(0, 11 + dex_mod + shield), 12 + dex_mod + shield)

    if armor_type == ArmorType.MEDIUM:
        # 12..15 base + min(2, DEX_mod)
        dex_bonus = min(2, dex_mod)
        return (max(0, 12 + dex_bonus + shield), 15 + dex_bonus + shield)

    if armor_type == ArmorType.HEAVY:
        # 14..18 base, DEX игнорируется
        return (14 + shield, 18 + shield)

    # Fallback на безбронник
    ac = 10 + dex_mod + shield
    return (max(0, ac), ac)
