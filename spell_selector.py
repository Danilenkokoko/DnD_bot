# spell_selector.py
"""
Модуль для управления выбором заклинаний с группировкой, описаниями и подтверждением
Поддерживает пошаговый выбор: категория → список заклинаний → детали → подтверждение
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from db import get_connection, get_spells_by_category, get_spell_by_id

logger = logging.getLogger(__name__)

# Категории заклинаний с иконками и описаниями
SPELL_CATEGORIES = {
    "Урон": {
        "icon": "💥",
        "description": "Атакующие заклинания, наносящие урон врагам",
        "order": 1
    },
    "Защита": {
        "icon": "🛡️",
        "description": "Защитные заклинания: щиты, броня, сопротивление урону",
        "order": 2
    },
    "Лечение": {
        "icon": "❤️",
        "description": "Заклинания восстановления здоровья и лечения ран",
        "order": 3
    },
    "Контроль": {
        "icon": "🎭",
        "description": "Заклинания контроля: страх, очарование, сон, обездвиживание",
        "order": 4
    },
    "Утилита": {
        "icon": "🧭",
        "description": "Полезные заклинания: движение, свет, связь, бытовые эффекты",
        "order": 5
    },
    "Иллюзии": {
        "icon": "🧠",
        "description": "Иллюзии и обман восприятия",
        "order": 6
    },
    "Природа": {
        "icon": "🌿",
        "description": "Природные заклинания: элементы, растения, погода",
        "order": 7
    },
    "Прочее": {
        "icon": "⚙️",
        "description": "Особые и ситуативные эффекты",
        "order": 8
    }
}


class SpellType(Enum):
    """Тип заклинания"""
    CANTRIP = "cantrip"
    LEVEL1 = "level1"


@dataclass
class SpellSelectionState:
    """
    Состояние выбора заклинаний для одного персонажа
    Хранит все данные о процессе выбора
    """
    class_name: str
    spell_type: SpellType
    required_count: int
    selected_spells: List[str] = field(default_factory=list)
    current_category: Optional[str] = None
    current_spell_id: Optional[int] = None
    current_spell_name: Optional[str] = None
    pending_confirmation: bool = False
    is_completed: bool = False

    @property
    def remaining_count(self) -> int:
        """Осталось выбрать заклинаний"""
        return self.required_count - len(self.selected_spells)

    @property
    def progress_text(self) -> str:
        """Текст прогресса выбора"""
        return f"Выбрано: {len(self.selected_spells)}/{self.required_count}"

    def can_add(self, spell_name: str) -> bool:
        """Можно ли добавить заклинание"""
        return (self.remaining_count > 0 and
                spell_name not in self.selected_spells and
                not self.is_completed)

    def add_spell(self, spell_name: str) -> bool:
        """Добавляет заклинание"""
        if self.can_add(spell_name):
            self.selected_spells.append(spell_name)
            logger.info(f"[SpellSelector] Добавлено {spell_name} для {self.class_name}, "
                        f"осталось {self.remaining_count}")
            return True
        return False

    def remove_spell(self, spell_name: str) -> bool:
        """Удаляет заклинание"""
        if spell_name in self.selected_spells and not self.is_completed:
            self.selected_spells.remove(spell_name)
            logger.info(f"[SpellSelector] Удалено {spell_name} для {self.class_name}")
            return True
        return False

    def complete(self) -> bool:
        """Завершает выбор, если выбрано нужное количество"""
        if len(self.selected_spells) == self.required_count:
            self.is_completed = True
            logger.info(f"[SpellSelector] Выбор завершён для {self.class_name}: "
                        f"{self.selected_spells}")
            return True
        return False


class SpellSelector:
    """
    Основной класс для управления выбором заклинаний
    Поддерживает отдельные сессии для заговоров и заклинаний 1 уровня
    """

    def __init__(self, class_name: str, user_id: Optional[int] = None):
        """
        Инициализирует селектор заклинаний для класса

        Args:
            class_name: имя класса (Волшебник, Жрец и т.д.)
            user_id: ID пользователя (опционально, для логирования)
        """
        self.class_name = class_name
        self.user_id = user_id
        self._cantrip_state: Optional[SpellSelectionState] = None
        self._level1_state: Optional[SpellSelectionState] = None
        self._cached_categories: Dict[str, Dict[str, List[Dict]]] = {}

        # Загружаем количество заклинаний из БД
        self._load_spell_counts()

    def _load_spell_counts(self):
        """Загружает количество заклинаний для класса из БД"""
        from db import get_class_spell_counts

        counts = get_class_spell_counts(self.class_name)

        if counts['cantrips'] > 0:
            self._cantrip_state = SpellSelectionState(
                class_name=self.class_name,
                spell_type=SpellType.CANTRIP,
                required_count=counts['cantrips']
            )

        if counts['level1'] > 0:
            self._level1_state = SpellSelectionState(
                class_name=self.class_name,
                spell_type=SpellType.LEVEL1,
                required_count=counts['level1']
            )

        logger.info(f"[SpellSelector] Инициализирован для {self.class_name}: "
                    f"заговоров={counts['cantrips']}, заклинаний={counts['level1']}")

    # =========================================================
    # СВОЙСТВА ДЛЯ ДОСТУПА К СОСТОЯНИЯМ
    # =========================================================

    @property
    def has_cantrips(self) -> bool:
        """Есть ли у класса заговоры"""
        return self._cantrip_state is not None and self._cantrip_state.required_count > 0

    @property
    def has_level1_spells(self) -> bool:
        """Есть ли у класса заклинания 1 уровня"""
        return self._level1_state is not None and self._level1_state.required_count > 0

    @property
    def cantrip_state(self) -> Optional[SpellSelectionState]:
        """Состояние выбора заговоров"""
        return self._cantrip_state

    @property
    def level1_state(self) -> Optional[SpellSelectionState]:
        """Состояние выбора заклинаний 1 уровня"""
        return self._level1_state

    @property
    def all_spells_selected(self) -> bool:
        """Выбраны ли все заклинания (и заговоры, и заклинания)"""
        cantrip_ok = not self.has_cantrips or (self._cantrip_state and self._cantrip_state.is_completed)
        level1_ok = not self.has_level1_spells or (self._level1_state and self._level1_state.is_completed)
        return cantrip_ok and level1_ok

    # =========================================================
    # ПОЛУЧЕНИЕ ДАННЫХ ИЗ БД
    # =========================================================

    def get_categories(self, spell_type: SpellType) -> Dict[str, Dict[str, Any]]:
        """
        Возвращает категории с заклинаниями для указанного типа

        Returns:
            Dict с ключами: название категории -> {icon, description, spells}
        """
        is_cantrip = (spell_type == SpellType.CANTRIP)

        # Проверяем кэш
        cache_key = f"{self.class_name}_{is_cantrip}"
        if cache_key in self._cached_categories:
            return self._cached_categories[cache_key]

        # Получаем заклинания из БД
        spells_by_category = get_spells_by_category(self.class_name, is_cantrip)

        # Форматируем результат с иконками
        result = {}
        for category_name, spells in spells_by_category.items():
            cat_info = SPELL_CATEGORIES.get(category_name, {
                "icon": "✨",
                "description": "Разные заклинания",
                "order": 99
            })
            result[category_name] = {
                "icon": cat_info["icon"],
                "description": cat_info["description"],
                "order": cat_info["order"],
                "spells": spells
            }

        # Сортируем по order
        result = dict(sorted(result.items(), key=lambda x: x[1]["order"]))

        # Сохраняем в кэш
        self._cached_categories[cache_key] = result
        return result

    def get_spells_in_category(self, spell_type: SpellType, category: str) -> List[Dict[str, Any]]:
        """Возвращает список заклинаний в указанной категории"""
        categories = self.get_categories(spell_type)
        if category in categories:
            return categories[category]["spells"]
        return []

    def get_spell_details(self, spell_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает детальную информацию о заклинании"""
        return get_spell_by_id(spell_id)

    # =========================================================
    # ОПЕРАЦИИ С ЗАГОВОРАМИ (CANTRIPS)
    # =========================================================

    def get_cantrip_categories(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает категории заговоров"""
        if not self.has_cantrips:
            return {}
        return self.get_categories(SpellType.CANTRIP)

    def get_cantrips_in_category(self, category: str) -> List[Dict[str, Any]]:
        """Возвращает заговоры в указанной категории"""
        return self.get_spells_in_category(SpellType.CANTRIP, category)

    def can_add_cantrip(self, spell_name: str) -> bool:
        """Можно ли добавить заговор"""
        if not self._cantrip_state:
            return False
        return self._cantrip_state.can_add(spell_name)

    def add_cantrip(self, spell_name: str) -> Tuple[bool, str]:
        """
        Добавляет заговор

        Returns:
            (успех, сообщение)
        """
        if not self._cantrip_state:
            return False, "У этого класса нет заговоров"

        if self._cantrip_state.is_completed:
            return False, "Вы уже выбрали все заговоры"

        if not self._cantrip_state.can_add(spell_name):
            remaining = self._cantrip_state.remaining_count
            return False, f"Нельзя добавить больше {self._cantrip_state.required_count} заговоров (осталось {remaining})"

        self._cantrip_state.add_spell(spell_name)

        if self._cantrip_state.remaining_count == 0:
            return True, f"✅ Заговор '{spell_name}' добавлен! Вы выбрали все заговоры."
        else:
            return True, f"✅ Заговор '{spell_name}' добавлен. Осталось выбрать {self._cantrip_state.remaining_count}."

    def remove_cantrip(self, spell_name: str) -> Tuple[bool, str]:
        """
        Удаляет заговор

        Returns:
            (успех, сообщение)
        """
        if not self._cantrip_state:
            return False, "У этого класса нет заговоров"

        if self._cantrip_state.is_completed:
            return False, "Выбор уже завершён, нельзя удалить"

        if self._cantrip_state.remove_spell(spell_name):
            return True, f"❌ Заговор '{spell_name}' удалён"
        return False, f"Заговор '{spell_name}' не найден в выбранных"

    def get_selected_cantrips(self) -> List[str]:
        """Возвращает список выбранных заговоров"""
        if self._cantrip_state:
            return self._cantrip_state.selected_spells.copy()
        return []

    def get_cantrip_progress(self) -> Tuple[int, int]:
        """Возвращает прогресс выбора заговоров (выбрано, всего)"""
        if self._cantrip_state:
            return (len(self._cantrip_state.selected_spells), self._cantrip_state.required_count)
        return (0, 0)

    def complete_cantrips(self) -> Tuple[bool, str]:
        """
        Завершает выбор заговоров

        Returns:
            (успех, сообщение)
        """
        if not self._cantrip_state:
            return False, "У этого класса нет заговоров"

        if self._cantrip_state.is_completed:
            return False, "Выбор уже завершён"

        if len(self._cantrip_state.selected_spells) != self._cantrip_state.required_count:
            remaining = self._cantrip_state.remaining_count
            return False, f"Нужно выбрать ещё {remaining} заговор(ов)"

        self._cantrip_state.complete()
        return True, f"✅ Выбрано {len(self._cantrip_state.selected_spells)} заговоров"

    # =========================================================
    # ОПЕРАЦИИ С ЗАКЛИНАНИЯМИ 1 УРОВНЯ
    # =========================================================

    def get_level1_categories(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает категории заклинаний 1 уровня"""
        if not self.has_level1_spells:
            return {}
        return self.get_categories(SpellType.LEVEL1)

    def get_level1_spells_in_category(self, category: str) -> List[Dict[str, Any]]:
        """Возвращает заклинания 1 уровня в указанной категории"""
        return self.get_spells_in_category(SpellType.LEVEL1, category)

    def can_add_level1_spell(self, spell_name: str) -> bool:
        """Можно ли добавить заклинание 1 уровня"""
        if not self._level1_state:
            return False
        return self._level1_state.can_add(spell_name)

    def add_level1_spell(self, spell_name: str) -> Tuple[bool, str]:
        """
        Добавляет заклинание 1 уровня

        Returns:
            (успех, сообщение)
        """
        if not self._level1_state:
            return False, "У этого класса нет заклинаний 1 уровня"

        if self._level1_state.is_completed:
            return False, "Вы уже выбрали все заклинания"

        if not self._level1_state.can_add(spell_name):
            remaining = self._level1_state.remaining_count
            return False, f"Нельзя добавить больше {self._level1_state.required_count} заклинаний (осталось {remaining})"

        self._level1_state.add_spell(spell_name)

        if self._level1_state.remaining_count == 0:
            return True, f"✅ Заклинание '{spell_name}' добавлено! Вы выбрали все заклинания."
        else:
            return True, f"✅ Заклинание '{spell_name}' добавлено. Осталось выбрать {self._level1_state.remaining_count}."

    def remove_level1_spell(self, spell_name: str) -> Tuple[bool, str]:
        """
        Удаляет заклинание 1 уровня

        Returns:
            (успех, сообщение)
        """
        if not self._level1_state:
            return False, "У этого класса нет заклинаний 1 уровня"

        if self._level1_state.is_completed:
            return False, "Выбор уже завершён, нельзя удалить"

        if self._level1_state.remove_spell(spell_name):
            return True, f"❌ Заклинание '{spell_name}' удалено"
        return False, f"Заклинание '{spell_name}' не найдено в выбранных"

    def get_selected_level1_spells(self) -> List[str]:
        """Возвращает список выбранных заклинаний 1 уровня"""
        if self._level1_state:
            return self._level1_state.selected_spells.copy()
        return []

    def get_level1_progress(self) -> Tuple[int, int]:
        """Возвращает прогресс выбора заклинаний (выбрано, всего)"""
        if self._level1_state:
            return (len(self._level1_state.selected_spells), self._level1_state.required_count)
        return (0, 0)

    def complete_level1_spells(self) -> Tuple[bool, str]:
        """
        Завершает выбор заклинаний 1 уровня

        Returns:
            (успех, сообщение)
        """
        if not self._level1_state:
            return False, "У этого класса нет заклинаний 1 уровня"

        if self._level1_state.is_completed:
            return False, "Выбор уже завершён"

        if len(self._level1_state.selected_spells) != self._level1_state.required_count:
            remaining = self._level1_state.remaining_count
            return False, f"Нужно выбрать ещё {remaining} заклинание(й)"

        self._level1_state.complete()
        return True, f"✅ Выбрано {len(self._level1_state.selected_spells)} заклинаний 1 уровня"

    # =========================================================
    # ОБЩИЕ МЕТОДЫ
    # =========================================================

    def reset(self):
        """Сбрасывает все выборы"""
        if self._cantrip_state:
            self._cantrip_state = SpellSelectionState(
                class_name=self.class_name,
                spell_type=SpellType.CANTRIP,
                required_count=self._cantrip_state.required_count
            )
        if self._level1_state:
            self._level1_state = SpellSelectionState(
                class_name=self.class_name,
                spell_type=SpellType.LEVEL1,
                required_count=self._level1_state.required_count
            )
        self._cached_categories.clear()
        logger.info(f"[SpellSelector] Сброшен для {self.class_name}")

    def get_all_selected_spells(self) -> List[str]:
        """Возвращает все выбранные заклинания (и заговоры, и заклинания 1 уровня)"""
        result = []
        if self._cantrip_state:
            result.extend(self._cantrip_state.selected_spells)
        if self._level1_state:
            result.extend(self._level1_state.selected_spells)
        return result

    def format_selection_summary(self) -> str:
        """Форматирует сводку выбранных заклинаний для отображения пользователю"""
        lines = []

        if self._cantrip_state and self._cantrip_state.selected_spells:
            lines.append(
                f"📖 **Заговоры** ({len(self._cantrip_state.selected_spells)}/{self._cantrip_state.required_count}):")
            for spell in self._cantrip_state.selected_spells:
                lines.append(f"   • {spell}")
            lines.append("")

        if self._level1_state and self._level1_state.selected_spells:
            lines.append(
                f"🔮 **Заклинания 1 уровня** ({len(self._level1_state.selected_spells)}/{self._level1_state.required_count}):")
            for spell in self._level1_state.selected_spells:
                lines.append(f"   • {spell}")
            lines.append("")

        if not lines:
            return "❌ Заклинания не выбраны"

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Сериализует состояние для сохранения в FSM"""
        return {
            "class_name": self.class_name,
            "user_id": self.user_id,
            "cantrip_state": {
                "selected_spells": self._cantrip_state.selected_spells if self._cantrip_state else [],
                "required_count": self._cantrip_state.required_count if self._cantrip_state else 0,
                "is_completed": self._cantrip_state.is_completed if self._cantrip_state else False
            } if self._cantrip_state else None,
            "level1_state": {
                "selected_spells": self._level1_state.selected_spells if self._level1_state else [],
                "required_count": self._level1_state.required_count if self._level1_state else 0,
                "is_completed": self._level1_state.is_completed if self._level1_state else False
            } if self._level1_state else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpellSelector":
        """Восстанавливает состояние из словаря"""
        selector = cls(data["class_name"], data.get("user_id"))

        if data.get("cantrip_state") and selector._cantrip_state:
            cs = data["cantrip_state"]
            selector._cantrip_state.selected_spells = cs["selected_spells"].copy()
            selector._cantrip_state.is_completed = cs["is_completed"]

        if data.get("level1_state") and selector._level1_state:
            ls = data["level1_state"]
            selector._level1_state.selected_spells = ls["selected_spells"].copy()
            selector._level1_state.is_completed = ls["is_completed"]

        return selector


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ КЛАВИАТУР
# =========================================================

def get_category_icon(category_name: str) -> str:
    """Возвращает иконку для категории"""
    return SPELL_CATEGORIES.get(category_name, {}).get("icon", "✨")


def get_category_description(category_name: str) -> str:
    """Возвращает описание категории"""
    return SPELL_CATEGORIES.get(category_name, {}).get("description", "Разные заклинания")


def sort_categories(categories: Dict[str, Any]) -> Dict[str, Any]:
    """Сортирует категории по порядку"""
    return dict(sorted(categories.items(), key=lambda x: x[1].get("order", 99)))


# =========================================================
# ТЕСТИРОВАНИЕ
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧙 ТЕСТ МОДУЛЯ SPELL_SELECTOR")
    print("=" * 60)

    # Тест 1: Создание селектора для Волшебника
    print("\n1. ТЕСТ СОЗДАНИЯ СЕЛЕКТОРА ДЛЯ ВОЛШЕБНИКА")
    wizard_selector = SpellSelector("Волшебник")
    print(f"   Класс: {wizard_selector.class_name}")
    print(f"   Есть заговоры: {wizard_selector.has_cantrips}")
    print(f"   Есть заклинания 1 уровня: {wizard_selector.has_level1_spells}")

    if wizard_selector.has_cantrips:
        progress = wizard_selector.get_cantrip_progress()
        print(f"   Заговоры: нужно выбрать {progress[1]}, выбрано {progress[0]}")

    if wizard_selector.has_level1_spells:
        progress = wizard_selector.get_level1_progress()
        print(f"   Заклинания 1 ур.: нужно выбрать {progress[1]}, выбрано {progress[0]}")

    # Тест 2: Получение категорий заговоров
    print("\n2. ТЕСТ КАТЕГОРИЙ ЗАГОВОРОВ")
    categories = wizard_selector.get_cantrip_categories()
    for cat_name, cat_data in categories.items():
        print(f"   {cat_data['icon']} {cat_name}: {len(cat_data['spells'])} заклинаний")
        if cat_data['spells']:
            print(f"      Примеры: {', '.join([s['name'] for s in cat_data['spells'][:3]])}")

    # Тест 3: Добавление заговора
    print("\n3. ТЕСТ ДОБАВЛЕНИЯ ЗАГОВОРА")
    # Берём первый заговор из списка
    test_spell = None
    for cat_data in categories.values():
        if cat_data['spells']:
            test_spell = cat_data['spells'][0]['name']
            break

    if test_spell:
        success, msg = wizard_selector.add_cantrip(test_spell)
        print(f"   Добавление '{test_spell}': {msg}")
        progress = wizard_selector.get_cantrip_progress()
        print(f"   Прогресс: {progress[0]}/{progress[1]}")

    # Тест 4: Удаление заговора
    print("\n4. ТЕСТ УДАЛЕНИЯ ЗАГОВОРА")
    if test_spell and test_spell in wizard_selector.get_selected_cantrips():
        success, msg = wizard_selector.remove_cantrip(test_spell)
        print(f"   Удаление '{test_spell}': {msg}")

    # Тест 5: Получение деталей заклинания
    print("\n5. ТЕСТ ПОЛУЧЕНИЯ ДЕТАЛЕЙ ЗАКЛИНАНИЯ")
    # Берём первое заклинание из категории "Урон"
    for cat_data in categories.values():
        if cat_data['spells'] and cat_data['icon'] == '💥':
            spell = cat_data['spells'][0]
            details = wizard_selector.get_spell_details(spell['id'])
            if details:
                print(f"   Название: {details.get('name')}")
                print(f"   Уровень: {details.get('level')}")
                print(f"   Категория: {details.get('category')}")
                print(f"   Описание: {details.get('description', 'Нет описания')[:80]}...")
            break

    # Тест 6: Сериализация и десериализация
    print("\n6. ТЕСТ СЕРИАЛИЗАЦИИ")
    wizard_selector.add_cantrip("Огненный снаряд")
    serialized = wizard_selector.to_dict()
    print(f"   Сериализовано: {list(serialized.keys())}")

    restored = SpellSelector.from_dict(serialized)
    print(f"   Восстановлено: выбранные заговоры = {restored.get_selected_cantrips()}")

    # Тест 7: Форматирование сводки
    print("\n7. ТЕСТ ФОРМАТИРОВАНИЯ СВОДКИ")
    print(wizard_selector.format_selection_summary())

    print("\n" + "=" * 60)
    print("✅ МОДУЛЬ SPELL_SELECTOR ГОТОВ К ИСПОЛЬЗОВАНИЮ!")
    print("=" * 60)