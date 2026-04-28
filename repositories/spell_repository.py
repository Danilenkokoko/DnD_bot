# repositories/spell_repository.py
"""
Репозиторий для работы с заклинаниями
"""

from typing import List, Dict, Any, Optional
import json
import logging
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class SpellRepository(BaseRepository):
    """Репозиторий для работы с заклинаниями"""

    def __init__(self):
        super().__init__()
        self._table_name = "spells"

    # =========================================================
    # ОСНОВНЫЕ МЕТОДЫ ДЛЯ ЗАКЛИНАНИЙ
    # =========================================================

    def get_by_id(self, spell_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает заклинание по ID с полным описанием"""
        query = """
            SELECT id, name, description, level, is_cantrip, 
                   COALESCE(category, 'Прочее') as category, school,
                   casting_time, range, components, duration, is_ritual,
                   requires_concentration
            FROM spells
            WHERE id = %s
        """
        return self._fetch_one(query, (spell_id,))

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Возвращает заклинание по названию"""
        query = """
            SELECT id, name, description, level, is_cantrip, 
                   COALESCE(category, 'Прочее') as category, school
            FROM spells
            WHERE name = %s
        """
        return self._fetch_one(query, (name,))

    def get_all(self, is_cantrip: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Возвращает список всех заклинаний, опционально фильтруя по типу"""
        if is_cantrip is not None:
            query = """
                SELECT id, name, level, is_cantrip, COALESCE(category, 'Прочее') as category
                FROM spells
                WHERE is_cantrip = %s
                ORDER BY name
            """
            return self._fetch_all(query, (is_cantrip,))
        else:
            query = """
                SELECT id, name, level, is_cantrip, COALESCE(category, 'Прочее') as category
                FROM spells
                ORDER BY level, name
            """
            return self._fetch_all(query)

    # =========================================================
    # ЗАКЛИНАНИЯ ДЛЯ КЛАССОВ
    # =========================================================

    def _get_class_id(self, class_name: str) -> Optional[int]:
        """Вспомогательный метод для получения ID класса"""
        query = "SELECT id FROM classes WHERE name = %s"
        result = self._fetch_one(query, (class_name,))
        return result['id'] if result else None

    def get_for_class(
            self,
            class_name: str,
            level: int = 1,
            is_cantrip: Optional[bool] = None,
            include_available_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Возвращает заклинания для указанного класса

        Args:
            class_name: название класса
            level: максимальный уровень заклинаний (для не-заговоров)
            is_cantrip: True - только заговоры, False - только заклинания 1+ уровня, None - всё
            include_available_only: учитывать ли флаг is_available
        """
        class_id = self._get_class_id(class_name)
        if not class_id:
            return []

        query = """
            SELECT s.id, s.name, s.level, s.is_cantrip, 
                   s.description, s.school, COALESCE(s.category, 'Прочее') as category
            FROM spells s
            JOIN class_spells cs ON s.id = cs.spell_id
            WHERE cs.class_id = %s
        """
        params = [class_id]

        if include_available_only:
            query += " AND cs.is_available = TRUE"

        if is_cantrip is not None:
            query += " AND s.is_cantrip = %s"
            params.append(is_cantrip)

        if not is_cantrip:
            query += " AND s.level <= %s"
            params.append(level)

        query += " ORDER BY s.level, s.name"

        return self._fetch_all(query, tuple(params))

    def get_cantrips_for_class(self, class_name: str) -> List[Dict[str, Any]]:
        """Возвращает заговоры для указанного класса"""
        return self.get_for_class(class_name, is_cantrip=True)

    def get_level1_spells_for_class(self, class_name: str) -> List[Dict[str, Any]]:
        """Возвращает заклинания 1 уровня для указанного класса"""
        return self.get_for_class(class_name, level=1, is_cantrip=False)

    def get_spells_by_level_for_class(
            self,
            class_name: str,
            spell_level: int
    ) -> List[Dict[str, Any]]:
        """Возвращает заклинания определённого уровня для класса"""
        class_id = self._get_class_id(class_name)
        if not class_id:
            return []

        query = """
            SELECT s.id, s.name, s.level, s.description, 
                   COALESCE(s.category, 'Прочее') as category
            FROM spells s
            JOIN class_spells cs ON s.id = cs.spell_id
            WHERE cs.class_id = %s AND cs.is_available = TRUE
            AND s.level = %s AND s.is_cantrip = FALSE
            ORDER BY s.name
        """
        return self._fetch_all(query, (class_id, spell_level))

    # =========================================================
    # КАТЕГОРИИ ЗАКЛИНАНИЙ
    # =========================================================

    def get_categories_for_class(
            self,
            class_name: str,
            is_cantrip: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Возвращает заклинания для класса, сгруппированные по категориям

        Returns:
            Dict: {категория: [список заклинаний]}
        """
        spells = self.get_for_class(class_name, is_cantrip=is_cantrip)

        result = {}
        for spell in spells:
            category = spell.get('category', 'Прочее')
            if category not in result:
                result[category] = []
            result[category].append(spell)

        # Сортируем категории в определённом порядке
        category_order = ["Урон", "Защита", "Лечение", "Контроль", "Утилита", "Иллюзии", "Природа", "Прочее"]

        sorted_result = {}
        for cat in category_order:
            if cat in result:
                sorted_result[cat] = result[cat]
        for cat in result:
            if cat not in sorted_result:
                sorted_result[cat] = result[cat]

        return sorted_result

    # =========================================================
    # РЕКОМЕНДОВАННЫЕ ЗАКЛИНАНИЯ
    # =========================================================

    def get_recommended_for_class(self, class_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """Возвращает рекомендованные заклинания для класса"""
        result = {"cantrips": [], "level1": []}

        class_id = self._get_class_id(class_name)
        if not class_id:
            return result

        query = """
            SELECT s.id, s.name, s.level, s.is_cantrip, s.description
            FROM spells s
            JOIN recommended_spells rs ON s.id = rs.spell_id
            WHERE rs.class_id = %s
            ORDER BY rs.priority, s.name
        """
        spells = self._fetch_all(query, (class_id,))

        for spell in spells:
            if spell.get('is_cantrip', False):
                result["cantrips"].append(spell)
            else:
                result["level1"].append(spell)

        return result

    # =========================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # =========================================================

    def is_spell_available_for_class(self, class_name: str, spell_id: int) -> bool:
        """Проверяет, доступно ли заклинание для указанного класса"""
        class_id = self._get_class_id(class_name)
        if not class_id:
            return False

        query = """
            SELECT 1 FROM class_spells
            WHERE class_id = %s AND spell_id = %s AND is_available = TRUE
            LIMIT 1
        """
        result = self._fetch_one(query, (class_id, spell_id))
        return result is not None


# =========================================================
# РЕПОЗИТОРИЙ ДЛЯ СВЯЗЕЙ КЛАССОВ И ЗАКЛИНАНИЙ
# =========================================================

class ClassSpellLinkRepository(BaseRepository):
    """Репозиторий для управления связями классов и заклинаний"""

    def __init__(self):
        super().__init__()
        self._table_name = "class_spells"

    def _get_class_id(self, class_name: str) -> Optional[int]:
        """Вспомогательный метод для получения ID класса"""
        query = "SELECT id FROM classes WHERE name = %s"
        result = self._fetch_one(query, (class_name,))
        return result['id'] if result else None

    def add_spell_to_class(self, class_name: str, spell_id: int, is_available: bool = True) -> bool:
        """Добавляет заклинание классу (права администратора)"""
        class_id = self._get_class_id(class_name)
        if not class_id:
            return False

        query = """
            INSERT INTO class_spells (class_id, spell_id, is_available)
            VALUES (%s, %s, %s)
            ON CONFLICT (class_id, spell_id) DO UPDATE SET is_available = EXCLUDED.is_available
        """
        self._execute_query(query, (class_id, spell_id, is_available))
        return True

    def remove_spell_from_class(self, class_name: str, spell_id: int) -> bool:
        """Удаляет заклинание у класса (или делает недоступным)"""
        return self.add_spell_to_class(class_name, spell_id, is_available=False)

    def get_spells_by_class(self, class_name: str) -> List[Dict[str, Any]]:
        """Возвращает все связи класса с заклинаниями"""
        class_id = self._get_class_id(class_name)
        if not class_id:
            return []

        query = """
            SELECT spell_id, is_available
            FROM class_spells
            WHERE class_id = %s
        """
        return self._fetch_all(query, (class_id,))