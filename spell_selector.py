# spell_selector.py
"""
D&D 5.5e Spell Selection Module
Модуль для управления выбором заклинаний при создании персонажа
Поддерживает заговоры (cantrips) и заклинания 1 уровня
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from dnd_logic import (
    get_spells_grouped_by_category,
    get_class_spell_counts
)

logger = logging.getLogger(__name__)


# =========================================================
# КАТЕГОРИИ ЗАКЛИНАНИЙ С ИКОНКАМИ
# =========================================================

class SpellCategory(Enum):
    """Категории заклинаний для отображения"""
    DAMAGE = "Урон"
    DEFENSE = "Защита"
    HEALING = "Лечение"
    CONTROL = "Контроль"
    UTILITY = "Утилита"
    ILLUSION = "Иллюзии"
    NATURE = "Природа"
    OTHER = "Прочее"

    @classmethod
    def get_icon(cls, category: str) -> str:
        """Возвращает иконку для категории"""
        icons = {
            "Урон": "💥",
            "Защита": "🛡️",
            "Лечение": "❤️",
            "Контроль": "🎭",
            "Утилита": "🧭",
            "Иллюзии": "🧠",
            "Природа": "🌿",
            "Прочее": "⚙️"
        }
        return icons.get(category, "✨")


def get_category_icon(category: str) -> str:
    """Утилитарная функция для получения иконки категории"""
    return SpellCategory.get_icon(category)


# =========================================================
# ДАТАКЛАССЫ ДЛЯ ХРАНЕНИЯ СОСТОЯНИЯ
# =========================================================

@dataclass
class SpellSelectionState:
    """Состояние выбора заклинаний определённого типа"""
    required_count: int
    selected_spells: List[str] = field(default_factory=list)

    @property
    def remaining_count(self) -> int:
        """Количество заклинаний, которые ещё нужно выбрать"""
        return max(0, self.required_count - len(self.selected_spells))

    @property
    def is_complete(self) -> bool:
        """Проверяет, выбраны ли все заклинания"""
        return len(self.selected_spells) >= self.required_count

    def add_spell(self, spell_name: str) -> tuple[bool, str]:
        """
        Добавляет заклинание в выбранные

        Returns:
            (success, message)
        """
        if spell_name in self.selected_spells:
            return False, f"❌ Заклинание '{spell_name}' уже выбрано"

        if self.remaining_count <= 0:
            return False, f"⚠️ Вы уже выбрали максимальное количество ({self.required_count}) заклинаний"

        self.selected_spells.append(spell_name)

        if self.remaining_count == 0:
            return True, f"✅ Заклинание '{spell_name}' добавлено! Вы выбрали все {self.required_count} заклинаний."
        else:
            return True, f"✅ Заклинание '{spell_name}' добавлено. Осталось выбрать: {self.remaining_count}"

    def remove_spell(self, spell_name: str) -> tuple[bool, str]:
        """
        Удаляет заклинание из выбранных

        Returns:
            (success, message)
        """
        if spell_name not in self.selected_spells:
            return False, f"❌ Заклинание '{spell_name}' не было выбрано"

        self.selected_spells.remove(spell_name)
        return True, f"✅ Заклинание '{spell_name}' удалено. Осталось выбрать: {self.remaining_count}"

    def to_dict(self) -> Dict[str, Any]:
        """Сериализует состояние в словарь"""
        return {
            'required_count': self.required_count,
            'selected_spells': self.selected_spells.copy()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpellSelectionState':
        """Восстанавливает состояние из словаря"""
        state = cls(required_count=data['required_count'])
        state.selected_spells = data.get('selected_spells', []).copy()
        return state


# =========================================================
# ОСНОВНОЙ КЛАСС ДЛЯ ВЫБОРА ЗАКЛИНАНИЙ
# =========================================================

class SpellSelector:
    """
    Управляет выбором заклинаний для персонажа
    Поддерживает заговоры (cantrips) и заклинания 1 уровня
    """

    def __init__(self, class_name: str):
        """
        Инициализирует селектор заклинаний для указанного класса

        Args:
            class_name: название класса (например, "Волшебник", "Жрец")
        """
        self.class_name = class_name

        # Получаем количество заклинаний из БД
        spell_counts = get_class_spell_counts(class_name)
        cantrips_required = spell_counts.get('cantrips', 0)
        level1_required = spell_counts.get('level1', 0)

        # Создаём состояния для заклинаний
        self.cantrip_state = SpellSelectionState(required_count=cantrips_required) if cantrips_required > 0 else None
        self.level1_state = SpellSelectionState(required_count=level1_required) if level1_required > 0 else None

        # Кэш для категорий заклинаний
        self._cantrip_categories_cache: Optional[Dict[str, Dict]] = None
        self._level1_categories_cache: Optional[Dict[str, Dict]] = None

    # =====================================================
    # СВОЙСТВА ДЛЯ ПРОВЕРКИ СОСТОЯНИЯ
    # =====================================================

    @property
    def has_cantrips(self) -> bool:
        """Проверяет, нужно ли выбирать заговоры"""
        return self.cantrip_state is not None and self.cantrip_state.required_count > 0

    @property
    def has_level1_spells(self) -> bool:
        """Проверяет, нужно ли выбирать заклинания 1 уровня"""
        return self.level1_state is not None and self.level1_state.required_count > 0

    @property
    def is_cantrips_complete(self) -> bool:
        """Проверяет, завершён ли выбор заговоров"""
        return self.cantrip_state is None or self.cantrip_state.is_complete

    @property
    def is_level1_complete(self) -> bool:
        """Проверяет, завершён ли выбор заклинаний 1 уровня"""
        return self.level1_state is None or self.level1_state.is_complete

    @property
    def is_complete(self) -> bool:
        """Проверяет, завершён ли выбор всех заклинаний"""
        return self.is_cantrips_complete and self.is_level1_complete

    # =====================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С КАТЕГОРИЯМИ
    # =====================================================

    def _get_cached_cantrips(self) -> Dict[str, Dict]:
        """Получает кэшированные категории заговоров"""
        if self._cantrip_categories_cache is None:
            categories = get_spells_grouped_by_category(self.class_name, is_cantrip=True)
            self._cantrip_categories_cache = self._add_icons_to_categories(categories)
        return self._cantrip_categories_cache

    def _get_cached_level1(self) -> Dict[str, Dict]:
        """Получает кэшированные категории заклинаний 1 уровня"""
        if self._level1_categories_cache is None:
            categories = get_spells_grouped_by_category(self.class_name, is_cantrip=False)
            self._level1_categories_cache = self._add_icons_to_categories(categories)
        return self._level1_categories_cache

    @staticmethod
    def _add_icons_to_categories(categories: Dict[str, List[Dict]]) -> Dict[str, Dict]:
        """Добавляет иконки к категориям"""
        result = {}
        for cat_name, spells in categories.items():
            result[cat_name] = {
                'icon': get_category_icon(cat_name),
                'spells': spells
            }
        return result

    # =====================================================
    # МЕТОДЫ ДЛЯ ЗАГОВОРОВ (CANTRIPS)
    # =====================================================

    def get_cantrip_categories(self) -> Dict[str, Dict]:
        """
        Возвращает категории заговоров с иконками

        Returns:
            Dict: {категория: {'icon': str, 'spells': List[Dict]}}
        """
        if not self.has_cantrips:
            return {}
        return self._get_cached_cantrips()

    def get_cantrips_in_category(self, category: str) -> List[Dict]:
        """
        Возвращает список заговоров в указанной категории

        Args:
            category: название категории

        Returns:
            List[Dict]: список заклинаний с id, name, description
        """
        categories = self._get_cached_cantrips()
        if category in categories:
            return categories[category]['spells']
        return []

    def get_selected_cantrips(self) -> List[str]:
        """Возвращает список выбранных заговоров"""
        if self.cantrip_state is None:
            return []
        return self.cantrip_state.selected_spells.copy()

    def get_cantrip_progress(self) -> tuple[int, int]:
        """
        Возвращает прогресс выбора заговоров

        Returns:
            (selected_count, required_count)
        """
        if self.cantrip_state is None:
            return 0, 0
        return len(self.cantrip_state.selected_spells), self.cantrip_state.required_count

    def add_cantrip(self, spell_name: str) -> tuple[bool, str]:
        """
        Добавляет заговор в выбранные

        Args:
            spell_name: название заклинания

        Returns:
            (success, message)
        """
        if self.cantrip_state is None:
            return False, "❌ Этот класс не может выбирать заговоры"
        return self.cantrip_state.add_spell(spell_name)

    def remove_cantrip(self, spell_name: str) -> tuple[bool, str]:
        """
        Удаляет заговор из выбранных

        Args:
            spell_name: название заклинания

        Returns:
            (success, message)
        """
        if self.cantrip_state is None:
            return False, "❌ Этот класс не может выбирать заговоры"
        return self.cantrip_state.remove_spell(spell_name)

    # =====================================================
    # МЕТОДЫ ДЛЯ ЗАКЛИНАНИЙ 1 УРОВНЯ
    # =====================================================

    def get_level1_categories(self) -> Dict[str, Dict]:
        """
        Возвращает категории заклинаний 1 уровня с иконками

        Returns:
            Dict: {категория: {'icon': str, 'spells': List[Dict]}}
        """
        if not self.has_level1_spells:
            return {}
        return self._get_cached_level1()

    def get_level1_spells_in_category(self, category: str) -> List[Dict]:
        """
        Возвращает список заклинаний 1 уровня в указанной категории

        Args:
            category: название категории

        Returns:
            List[Dict]: список заклинаний с id, name, description
        """
        categories = self._get_cached_level1()
        if category in categories:
            return categories[category]['spells']
        return []

    def get_selected_level1_spells(self) -> List[str]:
        """Возвращает список выбранных заклинаний 1 уровня"""
        if self.level1_state is None:
            return []
        return self.level1_state.selected_spells.copy()

    def get_level1_progress(self) -> tuple[int, int]:
        """
        Возвращает прогресс выбора заклинаний 1 уровня

        Returns:
            (selected_count, required_count)
        """
        if self.level1_state is None:
            return 0, 0
        return len(self.level1_state.selected_spells), self.level1_state.required_count

    def add_level1_spell(self, spell_name: str) -> tuple[bool, str]:
        """
        Добавляет заклинание 1 уровня в выбранные

        Args:
            spell_name: название заклинания

        Returns:
            (success, message)
        """
        if self.level1_state is None:
            return False, "❌ Этот класс не может выбирать заклинания 1 уровня"
        return self.level1_state.add_spell(spell_name)

    def remove_level1_spell(self, spell_name: str) -> tuple[bool, str]:
        """
        Удаляет заклинание 1 уровня из выбранных

        Args:
            spell_name: название заклинания

        Returns:
            (success, message)
        """
        if self.level1_state is None:
            return False, "❌ Этот класс не может выбирать заклинания 1 уровня"
        return self.level1_state.remove_spell(spell_name)

    # =====================================================
    # ОБЩИЕ МЕТОДЫ
    # =====================================================

    def get_all_selected_spells(self) -> List[str]:
        """
        Возвращает список всех выбранных заклинаний

        Returns:
            List[str]: объединённый список заговоров и заклинаний 1 уровня
        """
        result = []
        if self.cantrip_state:
            result.extend(self.cantrip_state.selected_spells)
        if self.level1_state:
            result.extend(self.level1_state.selected_spells)
        return result

    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализует состояние селектора в словарь для сохранения в FSM

        Returns:
            Dict: сериализованное состояние
        """
        return {
            'class_name': self.class_name,
            'cantrip_state': self.cantrip_state.to_dict() if self.cantrip_state else None,
            'level1_state': self.level1_state.to_dict() if self.level1_state else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpellSelector':
        """
        Восстанавливает селектор из словаря (из FSM)

        Args:
            data: сериализованное состояние

        Returns:
            SpellSelector: восстановленный селектор
        """
        selector = cls(class_name=data['class_name'])

        if data.get('cantrip_state') and selector.cantrip_state:
            selector.cantrip_state = SpellSelectionState.from_dict(data['cantrip_state'])

        if data.get('level1_state') and selector.level1_state:
            selector.level1_state = SpellSelectionState.from_dict(data['level1_state'])

        return selector

    def get_summary(self) -> str:
        """
        Возвращает сводку по выбранным заклинаниям

        Returns:
            str: отформатированная сводка
        """
        lines = []

        if self.has_cantrips:
            selected = self.get_selected_cantrips()
            required = self.cantrip_state.required_count
            lines.append(f"📖 Заговоры: {len(selected)}/{required}")
            if selected:
                lines.append(f"   • {', '.join(selected)}")

        if self.has_level1_spells:
            selected = self.get_selected_level1_spells()
            required = self.level1_state.required_count
            lines.append(f"🔮 Заклинания 1 уровня: {len(selected)}/{required}")
            if selected:
                lines.append(f"   • {', '.join(selected)}")

        return "\n".join(lines) if lines else "📖 Нет заклинаний для выбора"


# =========================================================
# ТЕСТИРОВАНИЕ
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ МОДУЛЯ SPELL_SELECTOR")
    print("=" * 60)

    # Тест 1: Создание селектора для Волшебника
    print("\n1. Создание селектора для Волшебника")
    wizard_selector = SpellSelector("Волшебник")
    print(f"   Класс: {wizard_selector.class_name}")
    print(f"   Есть заговоры: {wizard_selector.has_cantrips}")
    print(f"   Есть заклинания 1 уровня: {wizard_selector.has_level1_spells}")

    # Тест 2: Получение категорий заговоров
    print("\n2. Категории заговоров Волшебника:")
    categories = wizard_selector.get_cantrip_categories()
    for cat_name, cat_data in categories.items():
        print(f"   {cat_data['icon']} {cat_name}: {len(cat_data['spells'])} шт.")

    # Тест 3: Выбор заговора
    print("\n3. Выбор заговоров:")
    print(f"   Прогресс: {wizard_selector.get_cantrip_progress()}")

    success, msg = wizard_selector.add_cantrip("Огненный снаряд")
    print(f"   {msg}")

    success, msg = wizard_selector.add_cantrip("Рука мага")
    print(f"   {msg}")

    success, msg = wizard_selector.add_cantrip("Свет")
    print(f"   {msg}")

    print(f"   Выбранные заговоры: {wizard_selector.get_selected_cantrips()}")
    print(f"   Прогресс: {wizard_selector.get_cantrip_progress()}")

    # Тест 4: Удаление заговора
    print("\n4. Удаление заговора:")
    success, msg = wizard_selector.remove_cantrip("Рука мага")
    print(f"   {msg}")
    print(f"   Выбранные заговоры: {wizard_selector.get_selected_cantrips()}")

    # Тест 5: Сериализация и десериализация
    print("\n5. Сериализация и восстановление:")
    serialized = wizard_selector.to_dict()
    print(f"   Сериализовано: {serialized['class_name']}")

    restored = SpellSelector.from_dict(serialized)
    print(f"   Восстановлено: {restored.class_name}")
    print(f"   Выбранные заговоры: {restored.get_selected_cantrips()}")

    # Тест 6: Сводка по заклинаниям
    print("\n6. Сводка по заклинаниям:")
    print(wizard_selector.get_summary())

    # Тест 7: Класс без заклинаний
    print("\n7. Класс без заклинаний (Воин):")
    fighter_selector = SpellSelector("Воин")
    print(f"   Есть заговоры: {fighter_selector.has_cantrips}")
    print(f"   Есть заклинания 1 уровня: {fighter_selector.has_level1_spells}")
    print(f"   Сводка: {fighter_selector.get_summary()}")

    # Тест 8: Класс с заклинаниями, но без заговоров (Паладин)
    print("\n8. Класс Паладин (только заклинания 1 уровня):")
    paladin_selector = SpellSelector("Паладин")
    print(f"   Есть заговоры: {paladin_selector.has_cantrips}")
    print(f"   Есть заклинания 1 уровня: {paladin_selector.has_level1_spells}")
    print(f"   Прогресс заклинаний: {paladin_selector.get_level1_progress()}")

    print("\n" + "=" * 60)
    print("✅ ТЕСТ ПРОЙДЕН")
    print("=" * 60)