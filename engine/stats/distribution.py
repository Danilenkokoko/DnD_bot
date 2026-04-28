# engine/stats/distribution.py
"""
Распределение бонусов предыстории по правилам D&D 5.5e
Гарантирует: сумма бонусов = 3
"""

import random
from typing import List, Union, Optional
from engine.stats.models import Stat, BonusDistribution
from engine.stats.validation import StatsValidator, ValidationError


class BackgroundBonusDistributor:
    """
    Распределитель бонусов предыстории

    Правила:
    - Бонусы применяются ТОЛЬКО к 3 характеристикам background_stats
    - Сумма бонусов ВСЕГДА = 3 (гарантируется)

    Случай 1: primary_stats содержит 1 характеристику
        - Если primary ∈ background_stats: primary +2, случайная из оставшихся +1
        - Если primary ∉ background_stats: все 3 характеристики background +1

    Случай 2: primary_stats содержит 2 характеристики
        - Случай A (обе входят): все 3 +1
        - Случай B (ровно одна входит):
            совпавшая +2
            если вторая primary входит → ей +1
            иначе +1 случайной из оставшихся
        - Случай C (ни одна не входит): все 3 +1
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Args:
            seed: опциональный seed для random (для тестирования)
        """
        if seed is not None:
            random.seed(seed)

    @staticmethod
    def _get_intersection(
            primary: List[Stat],
            background: List[Stat]
    ) -> dict:
        """
        Анализирует пересечение primary и background

        Returns:
            Dict с ключами:
                'in_both': характеристики, которые есть и там, и там
                'only_primary': характеристики только в primary
                'only_background': характеристики только в background
        """
        primary_set = set(primary)
        background_set = set(background)

        return {
            'in_both': list(primary_set & background_set),
            'only_primary': list(primary_set - background_set),
            'only_background': list(background_set - primary_set)
        }

    def distribute(
            self,
            primary_stats: List[Union[str, Stat]],
            background_stats: List[Union[str, Stat]]
    ) -> BonusDistribution:
        """
        Распределяет бонусы по правилам

        Args:
            primary_stats: основные характеристики класса (1 или 2 шт)
            background_stats: три характеристики предыстории (строго 3, уникальные)

        Returns:
            BonusDistribution: объект с распределёнными бонусами (сумма = 3)

        Raises:
            ValidationError: если входные данные некорректны
        """
        # Строгая валидация
        primary_abilities = StatsValidator.validate_primary_stats(primary_stats)
        background_abilities = StatsValidator.validate_background_stats(background_stats)

        # Инициализация бонусов (все 0)
        bonuses = {ability: 0 for ability in background_abilities}

        # Анализ пересечения
        intersection = self._get_intersection(primary_abilities, background_abilities)
        in_both_count = len(intersection['in_both'])

        # =========================================================
        # СЛУЧАЙ 1: ОДНА primary характеристика
        # =========================================================
        if len(primary_abilities) == 1:
            primary = primary_abilities[0]

            if primary in background_abilities:
                # Правило А: primary +2, случайная из оставшихся +1
                bonuses[primary] = 2
                remaining = [a for a in background_abilities if a != primary]
                chosen = random.choice(remaining)
                bonuses[chosen] = 1
                # Третья остаётся 0
            else:
                # Правило Б: все три +1
                for ability in background_abilities:
                    bonuses[ability] = 1

        # =========================================================
        # СЛУЧАЙ 2: ДВЕ primary характеристики
        # =========================================================
        elif len(primary_abilities) == 2:
            if in_both_count == 2:
                # Случай A: обе входят → все +1
                for ability in background_abilities:
                    bonuses[ability] = 1

            elif in_both_count == 1:
                # Случай B: ровно одна входит
                matched = intersection['in_both'][0]
                other_primary = intersection['only_primary'][0]

                bonuses[matched] = 2

                # Проверяем, входит ли вторая primary в background
                if other_primary in background_abilities:
                    bonuses[other_primary] = 1
                else:
                    # +1 случайной из оставшихся
                    remaining = [a for a in background_abilities if a != matched]
                    chosen = random.choice(remaining)
                    bonuses[chosen] = 1

            else:  # in_both_count == 0
                # Случай C: ни одна не входит → все +1
                for ability in background_abilities:
                    bonuses[ability] = 1

        # Финальная проверка суммы (гарантия!)
        StatsValidator.validate_bonus_sum(bonuses, expected=3)

        # Создаём неизменяемый результат
        return BonusDistribution(bonuses=bonuses)

    def distribute_deterministic(
            self,
            primary_stats: List[Union[str, Stat]],
            background_stats: List[Union[str, Stat]],
            deterministic_choice: int = 0
    ) -> BonusDistribution:
        """
        Детерминированная версия (для тестирования)

        Args:
            deterministic_choice: 0 = выбрать первый, 1 = выбрать второй и т.д.
        """
        original_choice = random.choice

        def deterministic_choice_func(seq):
            return seq[deterministic_choice % len(seq)]

        try:
            random.choice = deterministic_choice_func
            return self.distribute(primary_stats, background_stats)
        finally:
            random.choice = original_choice