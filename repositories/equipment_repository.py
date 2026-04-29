# repositories/equipment_repository.py
"""
Репозиторий для работы со снаряжением, броней, оружием, боевыми стилями и возваниями
"""

from typing import List, Dict, Any, Optional
import json
import random
import logging
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class EquipmentRepository(BaseRepository):
    """Репозиторий для работы со снаряжением классов"""

    def __init__(self):
        super().__init__()
        self._table_name = "class_equipment"

    def _get_class_id(self, class_name: str) -> Optional[int]:
        """Вспомогательный метод для получения ID класса по имени"""
        query = "SELECT id FROM classes WHERE name = %s"
        result = self._fetch_one(query, (class_name,))
        return result['id'] if result else None

    def get_class_equipment(self, class_name: str, choice: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получает снаряжение для класса"""
        class_id = self._get_class_id(class_name)
        if not class_id:
            return []

        if choice:
            query = """
                SELECT class_id, choice, armor, weapon, secondary_weapon, other_items, coins
                FROM class_equipment
                WHERE class_id = %s AND choice = %s
            """
            params = (class_id, choice)
        else:
            query = """
                SELECT class_id, choice, armor, weapon, secondary_weapon, other_items, coins
                FROM class_equipment
                WHERE class_id = %s
                ORDER BY choice
            """
            params = (class_id,)

        return self._fetch_all(query, params)

    def get_armor_by_name(self, armor_name: str) -> Optional[Dict[str, Any]]:
        """Получает броню по названию"""
        query = """
            SELECT id, name, ac_base, ac_modifier, has_shield
            FROM armor
            WHERE name = %s
        """
        return self._fetch_one(query, (armor_name,))

    def get_all_armor(self) -> List[Dict[str, Any]]:
        """Возвращает список всей брони"""
        query = """
            SELECT id, name, ac_base, ac_modifier, has_shield
            FROM armor
            ORDER BY ac_base, name
        """
        return self._fetch_all(query)

    def get_all_armors(self) -> List[Dict[str, Any]]:
        """Алиас для get_all_armor (множественное число) для совместимости с тестами"""
        return self.get_all_armor()

    def get_weapon_by_name(self, weapon_name: str) -> Optional[Dict[str, Any]]:
        """Получает оружие по названию"""
        query = """
            SELECT id, name, category, damage_dice, damage_type, properties,
                   suitable_masteries, detailed_masteries
            FROM weapons
            WHERE name = %s
        """
        row = self._fetch_one(query, (weapon_name,))
        if not row:
            return None

        # Преобразуем JSON поля
        properties = row.get('properties', [])
        if isinstance(properties, str):
            try:
                properties = json.loads(properties)
            except:
                properties = []

        suitable_masteries = row.get('suitable_masteries', [])
        if isinstance(suitable_masteries, str):
            try:
                suitable_masteries = json.loads(suitable_masteries)
            except:
                suitable_masteries = []

        detailed_masteries = row.get('detailed_masteries', [])
        if isinstance(detailed_masteries, str):
            try:
                detailed_masteries = json.loads(detailed_masteries)
            except:
                detailed_masteries = []

        return {
            'id': row['id'],
            'name': row['name'],
            'category': row['category'],
            'damage_dice': row['damage_dice'],
            'damage_type': row['damage_type'],
            'properties': properties,
            'suitable_masteries': suitable_masteries,
            'detailed_masteries': detailed_masteries,
        }

    def get_all_weapons(self) -> List[Dict[str, Any]]:
        """Возвращает список всего оружия"""
        query = "SELECT id, name, category, damage_dice FROM weapons ORDER BY name"
        return self._fetch_all(query)

    def get_weapons_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Возвращает оружие по категории (simple, martial, etc.)"""
        query = """
            SELECT id, name, category, damage_dice, damage_type
            FROM weapons
            WHERE category = %s
            ORDER BY name
        """
        return self._fetch_all(query, (category,))

    def get_detailed_masteries_for_weapon(self, weapon_name: str) -> List[Dict[str, Any]]:
        """Возвращает детальные оружейные приёмы для указанного оружия"""
        weapon = self.get_weapon_by_name(weapon_name)
        if not weapon:
            return []
        return weapon.get('detailed_masteries', [])

    def get_all_weapon_masteries(self) -> List[Dict[str, Any]]:
        """Возвращает список всех базовых оружейных приёмов"""
        query = """
            SELECT id, name, trigger_condition, effect, weapons
            FROM weapon_masteries
            ORDER BY name
        """
        return self._fetch_all(query)

    def get_mastery_by_name(self, mastery_name: str) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о приёме по названию"""
        query = """
            SELECT id, name, trigger_condition, effect, weapons
            FROM weapon_masteries
            WHERE name = %s
        """
        return self._fetch_one(query, (mastery_name,))

    def auto_assign_masteries(self, weapon_name: str, class_name: str) -> List[str]:
        """Автоматически выбирает оружейные приёмы для оружия"""
        # Получаем количество приёмов из класса
        from repositories.class_repository import ClassRepository
        class_repo = ClassRepository()
        masteries_count = class_repo.get_masteries_count(class_name)

        if masteries_count == 0:
            return []

        masteries = self.get_detailed_masteries_for_weapon(weapon_name)
        if not masteries:
            return []

        if len(masteries) <= masteries_count:
            return [m['name'] for m in masteries]

        optimal = [m for m in masteries if m.get('optimal', False)]

        if len(optimal) >= masteries_count:
            selected = [m['name'] for m in optimal[:masteries_count]]
        else:
            selected = [m['name'] for m in optimal]
            remaining = [m for m in masteries if m not in optimal]
            needed = masteries_count - len(selected)
            if remaining and needed > 0:
                random.shuffle(remaining)
                selected += [m['name'] for m in remaining[:needed]]

        logger.info(f"[Masteries] {class_name} выбрал {len(selected)} приём(ов) для {weapon_name}: {selected}")
        return selected


# =========================================================
# РЕПОЗИТОРИЙ ДЛЯ БОЕВЫХ СТИЛЕЙ
# =========================================================

class FightingStyleRepository(BaseRepository):
    """Репозиторий для работы с боевыми стилями"""

    def __init__(self):
        super().__init__()
        self._table_name = "fighting_styles"

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает список всех боевых стилей"""
        query = "SELECT id, name, description FROM fighting_styles ORDER BY name"
        return self._fetch_all(query)

    def get_by_id(self, style_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает боевой стиль по ID"""
        query = "SELECT id, name, description FROM fighting_styles WHERE id = %s"
        return self._fetch_one(query, (style_id,))

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Возвращает боевой стиль по названию"""
        query = "SELECT id, name, description FROM fighting_styles WHERE name = %s"
        return self._fetch_one(query, (name,))

    def get_for_class(self, class_name: str) -> List[Dict[str, Any]]:
        """Возвращает боевые стили, доступные для класса"""
        from repositories.class_repository import ClassRepository
        class_repo = ClassRepository()
        class_data = class_repo.get_by_name(class_name)
        if not class_data:
            return []

        query = """
            SELECT fs.id, fs.name, fs.description
            FROM fighting_styles fs
            JOIN class_fighting_styles cfs ON fs.id = cfs.style_id
            WHERE cfs.class_id = %s
            ORDER BY fs.name
        """
        return self._fetch_all(query, (class_data['id'],))

    def get_available_for_class_with_weapon(
            self,
            class_name: str,
            weapon_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Возвращает доступные боевые стили с учётом типа оружия"""
        styles = self.get_for_class(class_name)

        if not weapon_type:
            return styles

        weapon_type_map = {
            "melee": ["melee"],
            "ranged": ["ranged"],
            "light": ["light", "melee"],
            "heavy": ["heavy", "two_handed"],
            "thrown": ["thrown", "ranged"],
            "unarmed": ["unarmed"]
        }

        compatible_types = weapon_type_map.get(weapon_type, ["any"])

        style_weapon_map = {
            "Дуэлянт": ["melee"],
            "Защита": ["any"],
            "Оборона": ["any"],
            "Перехват": ["any"],
            "Сражение без оружия": ["unarmed"],
            "Сражение большим оружием": ["heavy", "two_handed"],
            "Сражение вслепую": ["any"],
            "Сражение двумя оружиями": ["light"],
            "Сражение метательным оружием": ["thrown"],
            "Стрельба": ["ranged"]
        }

        return [
            style for style in styles
            if "any" in style_weapon_map.get(style['name'], ["any"]) or
               any(t in compatible_types for t in style_weapon_map.get(style['name'], []))
        ]


# =========================================================
# РЕПОЗИТОРИЙ ДЛЯ ВОЗВАНИЙ
# =========================================================

class InvocationRepository(BaseRepository):
    """Репозиторий для работы с таинственными возваниями колдуна"""

    def __init__(self):
        super().__init__()
        self._table_name = "invocations"

    def get_all(self, level: int = 1) -> List[Dict[str, Any]]:
        """Возвращает список доступных возваний для указанного уровня"""
        query = """
            SELECT id, name, level_required, effect, requires_pact_boon, pact_boon_type
            FROM invocations
            WHERE level_required <= %s
            ORDER BY level_required, name
        """
        return self._fetch_all(query, (level,))

    def get_by_id(self, inv_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает возвание по ID"""
        query = """
            SELECT id, name, level_required, effect, requires_pact_boon, pact_boon_type
            FROM invocations
            WHERE id = %s
        """
        return self._fetch_one(query, (inv_id,))

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Возвращает возвание по названию"""
        query = """
            SELECT id, name, level_required, effect, requires_pact_boon, pact_boon_type
            FROM invocations
            WHERE name = %s
        """
        return self._fetch_one(query, (name,))