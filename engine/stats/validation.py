# engine/stats/validation.py
"""
Валидация входных данных для распределения бонусов
Строгая типизация и проверки
"""

from typing import List, Set, Dict, Union
from engine.stats.models import Stat, AbilityScores


class ValidationError(Exception):
    """Ошибка валидации"""
    pass


class StatsValidator:
    """Валидатор для характеристик и бонусов"""

    @staticmethod
    def validate_background_stats(stats: List[Union[str, Stat]]) -> List[Stat]:
        """
        Проверяет, что background_stats содержит ровно 3 УНИКАЛЬНЫХ характеристики

        Args:
            stats: список характеристик (строки или Stat)

        Returns:
            List[Stat]: список валидных Stat объектов

        Raises:
            ValidationError: если данные некорректны
        """
        if not stats:
            raise ValidationError("background_stats не может быть пустым")

        if len(stats) != 3:
            raise ValidationError(
                f"background_stats должен содержать ровно 3 характеристики, "
                f"получено {len(stats)}: {stats}"
            )

        # Преобразуем в Stat
        abilities = []
        for stat in stats:
            if isinstance(stat, Stat):
                abilities.append(stat)
            elif isinstance(stat, str):
                ability = Stat.from_string(stat)
                if ability is None:
                    raise ValidationError(
                        f"Некорректная характеристика '{stat}'. "
                        f"Допустимые значения: {Stat.values()}"
                    )
                abilities.append(ability)
            else:
                raise ValidationError(
                    f"Некорректный тип характеристики: {type(stat)}. "
                    f"Ожидается Stat или str"
                )

        # Проверяем уникальность (строго!)
        if len(set(abilities)) != 3:
            # Находим дубликаты
            seen: Set[Stat] = set()
            duplicates: List[Stat] = []
            for ability in abilities:
                if ability in seen:
                    duplicates.append(ability)
                seen.add(ability)
            raise ValidationError(
                f"background_stats содержит дубликаты: {[d.value for d in duplicates]}"
            )

        return abilities

    @staticmethod
    def validate_primary_stats(stats: List[Union[str, Stat]]) -> List[Stat]:
        """
        Проверяет, что primary_stats содержит 1 или 2 УНИКАЛЬНЫХ характеристики

        Args:
            stats: список характеристик (строки или Stat)

        Returns:
            List[Stat]: список валидных Stat объектов

        Raises:
            ValidationError: если данные некорректны
        """
        if not stats:
            raise ValidationError("primary_stats не может быть пустым")

        if len(stats) not in [1, 2]:
            raise ValidationError(
                f"primary_stats должен содержать 1 или 2 характеристики, "
                f"получено {len(stats)}: {stats}"
            )

        # Преобразуем в Stat
        abilities = []
        for stat in stats:
            if isinstance(stat, Stat):
                abilities.append(stat)
            elif isinstance(stat, str):
                ability = Stat.from_string(stat)
                if ability is None:
                    raise ValidationError(
                        f"Некорректная характеристика '{stat}'. "
                        f"Допустимые значения: {Stat.values()}"
                    )
                abilities.append(ability)
            else:
                raise ValidationError(
                    f"Некорректный тип характеристики: {type(stat)}"
                )

        # Проверяем уникальность
        if len(set(abilities)) != len(abilities):
            raise ValidationError(
                f"primary_stats содержит дубликаты: {[a.value for a in abilities]}"
            )

        return abilities

    @staticmethod
    def validate_base_stats(stats: Union[Dict, AbilityScores]) -> None:
        """
        Проверяет, что base_stats содержит ровно 6 характеристик
        и нет лишних ключей

        Args:
            stats: словарь с характеристиками или AbilityScores

        Raises:
            ValidationError: если данные некорректны
        """
        # Если это AbilityScores - всегда валидны
        if isinstance(stats, AbilityScores):
            return

        if not isinstance(stats, dict):
            raise ValidationError(
                f"base_stats должен быть dict или AbilityScores, получен {type(stats)}"
            )

        expected_stats = set(Stat.values())
        actual_stats = set(stats.keys())

        # Проверяем, что все ключи - строки (Stat из строки)
        for key in actual_stats:
            if not isinstance(key, str):
                raise ValidationError(
                    f"Ключи должны быть строками, получен {type(key)}: {key}"
                )

        # Проверяем наличие всех характеристик
        missing = expected_stats - actual_stats
        if missing:
            raise ValidationError(
                f"base_stats не содержит обязательные характеристики: {missing}"
            )

        # Проверяем, что нет лишних ключей
        extra = actual_stats - expected_stats
        if extra:
            raise ValidationError(
                f"base_stats содержит лишние характеристики: {extra}"
            )

        # Проверяем значения
        for stat, value in stats.items():
            if not isinstance(value, int):
                raise ValidationError(
                    f"Значение для {stat} должно быть int, получен {type(value)}"
                )
            if not 1 <= value <= 30:
                raise ValidationError(
                    f"Характеристика {stat} должна быть в диапазоне 1-30, "
                    f"получено {value}"
                )

    @staticmethod
    def validate_bonus_sum(bonuses: Dict[Stat, int], expected: int = 3) -> None:
        """
        Проверяет, что сумма бонусов равна expected

        Args:
            bonuses: словарь бонусов
            expected: ожидаемая сумма

        Raises:
            ValidationError: если сумма не совпадает
        """
        total = sum(bonuses.values())
        if total != expected:
            raise ValidationError(
                f"Сумма бонусов должна быть {expected}, получено {total}. "
                f"Бонусы: {bonuses}"
            )