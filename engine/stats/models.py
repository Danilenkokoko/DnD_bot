# engine/stats/models.py
"""
Модели данных для работы с характеристиками
Строгая типизация, использование Enum вместо строк
"""

from enum import Enum
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from functools import total_ordering


class Stat(Enum):
    """Характеристики персонажа D&D (строгая типизация)"""
    STRENGTH = "STR"
    DEXTERITY = "DEX"
    CONSTITUTION = "CON"
    INTELLIGENCE = "INT"
    WISDOM = "WIS"
    CHARISMA = "CHA"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def all(cls) -> List['Stat']:
        """Возвращает список всех характеристик"""
        return list(cls)

    @classmethod
    def values(cls) -> List[str]:
        """Возвращает список строковых значений"""
        return [stat.value for stat in cls]

    @classmethod
    def from_string(cls, value: str) -> Optional['Stat']:
        """Создаёт Stat из строки (STR -> Stat.STRENGTH)"""
        for stat in cls:
            if stat.value == value:
                return stat
        return None

    @classmethod
    def from_string_strict(cls, value: str) -> 'Stat':
        """Строгая версия: выбрасывает исключение если не найден"""
        result = cls.from_string(value)
        if result is None:
            raise ValueError(f"Invalid stat: {value}. Must be one of {cls.values()}")
        return result


@total_ordering
@dataclass(frozen=True)
class AbilityScores:
    """
    Неизменяемый контейнер для характеристик
    Все 6 характеристик всегда присутствуют
    """
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int

    def __post_init__(self):
        """Валидация при создании"""
        for field, value in self.__dict__.items():
            if not 1 <= value <= 30:
                raise ValueError(
                    f"{field} должен быть в диапазоне 1-30, получено {value}"
                )

    def get(self, stat: Stat) -> int:
        """Получает значение характеристики по Stat"""
        mapping = {
            Stat.STRENGTH: self.strength,
            Stat.DEXTERITY: self.dexterity,
            Stat.CONSTITUTION: self.constitution,
            Stat.INTELLIGENCE: self.intelligence,
            Stat.WISDOM: self.wisdom,
            Stat.CHARISMA: self.charisma,
        }
        return mapping[stat]

    def set(self, stat: Stat, value: int) -> 'AbilityScores':
        """Устанавливает значение (возвращает новый объект)"""
        kwargs = {
            'strength': self.strength,
            'dexterity': self.dexterity,
            'constitution': self.constitution,
            'intelligence': self.intelligence,
            'wisdom': self.wisdom,
            'charisma': self.charisma,
        }
        attr_name = stat.name.lower()
        kwargs[attr_name] = max(1, min(30, value))
        return AbilityScores(**kwargs)

    def add_bonus(self, stat: Stat, bonus: int) -> 'AbilityScores':
        """Добавляет бонус (возвращает новый объект)"""
        return self.set(stat, self.get(stat) + bonus)

    def to_dict(self) -> Dict[Stat, int]:
        """Возвращает словарь с ключами Stat"""
        return {
            Stat.STRENGTH: self.strength,
            Stat.DEXTERITY: self.dexterity,
            Stat.CONSTITUTION: self.constitution,
            Stat.INTELLIGENCE: self.intelligence,
            Stat.WISDOM: self.wisdom,
            Stat.CHARISMA: self.charisma,
        }

    def to_str_dict(self) -> Dict[str, int]:
        """Возвращает словарь с ключами-строками (для совместимости)"""
        return {stat.value: value for stat, value in self.to_dict().items()}

    @classmethod
    def from_dict(cls, data: Dict[Union[Stat, str], int]) -> 'AbilityScores':
        """Создаёт из словаря с ключами Stat или str"""
        if not data:
            return cls.create_default()

        # Нормализуем ключи
        normalized = {}
        for key, value in data.items():
            if isinstance(key, Stat):
                normalized[key.name.lower()] = value
            elif isinstance(key, str):
                stat = Stat.from_string(key)
                if stat:
                    normalized[stat.name.lower()] = value
                else:
                    raise ValueError(f"Invalid stat key: {key}")

        return cls(
            strength=normalized.get('strength', 10),
            dexterity=normalized.get('dexterity', 10),
            constitution=normalized.get('constitution', 10),
            intelligence=normalized.get('intelligence', 10),
            wisdom=normalized.get('wisdom', 10),
            charisma=normalized.get('charisma', 10),
        )

    @classmethod
    def create_default(cls) -> 'AbilityScores':
        """Создаёт стандартные характеристики (все 10)"""
        return cls(
            strength=10, dexterity=10, constitution=10,
            intelligence=10, wisdom=10, charisma=10
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AbilityScores):
            return NotImplemented
        return (
                self.strength == other.strength and
                self.dexterity == other.dexterity and
                self.constitution == other.constitution and
                self.intelligence == other.intelligence and
                self.wisdom == other.wisdom and
                self.charisma == other.charisma
        )

    def __lt__(self, other: 'AbilityScores') -> bool:
        """Для total_ordering (сравниваем сумму)"""
        return sum(self.to_dict().values()) < sum(other.to_dict().values())


@dataclass(frozen=True)
class BonusDistribution:
    """
    Результат распределения бонусов
    Гарантирует: сумма бонусов = 3
    """
    bonuses: Dict[Stat, int]

    def __post_init__(self):
        """Проверяет сумму бонусов и тип ключей"""
        # Проверяем, что все ключи - Stat
        for key in self.bonuses.keys():
            if not isinstance(key, Stat):
                raise TypeError(f"Ключи должны быть типа Stat, получен {type(key)}")

        # Проверяем, что все значения - неотрицательные целые
        for value in self.bonuses.values():
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"Бонусы должны быть неотрицательными целыми, получен {value}")

        # Проверяем сумму
        total = sum(self.bonuses.values())
        if total != 3:
            raise ValueError(f"Сумма бонусов должна быть 3, получено {total}")

    def to_dict(self) -> Dict[Stat, int]:
        """Возвращает словарь с бонусами"""
        return self.bonuses.copy()

    def to_str_dict(self) -> Dict[str, int]:
        """Возвращает словарь с ключами-строками"""
        return {stat.value: bonus for stat, bonus in self.bonuses.items()}

    def apply_to(self, scores: AbilityScores) -> AbilityScores:
        """Применяет бонусы к характеристикам"""
        result = scores
        for stat, bonus in self.bonuses.items():
            if bonus > 0:
                result = result.add_bonus(stat, bonus)
        return result

    @classmethod
    def create_empty(cls) -> 'BonusDistribution':
        """Создаёт пустое распределение (все бонусы = 0) - для тестов"""
        return cls(bonuses={stat: 0 for stat in Stat.all()})