# repositories/race_repository.py
"""
Репозиторий для работы с расами
"""

from typing import List, Dict, Any, Optional
from repositories.base_repository import BaseRepository


class RaceRepository(BaseRepository):
    """Репозиторий для работы с расами"""

    def __init__(self):
        super().__init__()
        self._table_name = "races"

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает список всех рас с полной информацией"""
        query = """
            SELECT id, name, speed, size, description, image_path
            FROM races
            ORDER BY name
        """
        return self._fetch_all(query)

    def get_all_names(self) -> List[str]:
        """Возвращает список названий всех рас"""
        query = "SELECT name FROM races ORDER BY name"
        return [row['name'] for row in self._fetch_all(query)]

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о расе по названию"""
        query = """
            SELECT id, name, speed, size, description, image_path
            FROM races
            WHERE name = %s
        """
        return self._fetch_one(query, (name,))

    def get_by_id(self, race_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о расе по ID"""
        query = """
            SELECT id, name, speed, size, description, image_path
            FROM races
            WHERE id = %s
        """
        return self._fetch_one(query, (race_id,))

    def has_subraces(self, race_name: str) -> bool:
        """Проверяет, есть ли у расы подрасы"""
        race = self.get_by_name(race_name)
        if not race:
            return False

        query = "SELECT COUNT(*) FROM subraces WHERE race_id = %s"
        count = self._fetch_value(query, (race['id'],))
        return count > 0

    def get_subraces(self, race_name: str) -> List[Dict[str, Any]]:
        """Возвращает список подрас для указанной расы"""
        race = self.get_by_name(race_name)
        if not race:
            return []

        query = """
            SELECT id, name, trait, description, extra_speed, extra_traits
            FROM subraces
            WHERE race_id = %s
            ORDER BY name
        """
        return self._fetch_all(query, (race['id'],))

    def get_subrace_by_name(self, race_name: str, subrace_name: str) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о подрасе"""
        race = self.get_by_name(race_name)
        if not race:
            return None

        query = """
            SELECT id, name, trait, description, extra_speed, extra_traits
            FROM subraces
            WHERE race_id = %s AND name = %s
        """
        return self._fetch_one(query, (race['id'], subrace_name))

    def get_subrace_names(self, race_name: str) -> List[str]:
        """Возвращает список названий подрас"""
        subraces = self.get_subraces(race_name)
        return [s['name'] for s in subraces]