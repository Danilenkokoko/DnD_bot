# repositories/class_repository.py
"""
Репозиторий для работы с классами
"""

from typing import List, Dict, Any, Optional
import json
from repositories.base_repository import BaseRepository


class ClassRepository(BaseRepository):
    """Репозиторий для работы с классами"""

    def __init__(self):
        super().__init__()
        self._table_name = "classes"

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает список всех классов с полной информацией"""
        query = """
            SELECT id, name, hit_die, primary_stats, saving_throws,
                   skill_choices, description, image_path, is_spellcaster,
                   spellcasting_ability, cantrips_count, spells_count_level1, masteries_count
            FROM classes
            ORDER BY name
        """
        return self._fetch_all(query)

    def get_all_names(self) -> List[str]:
        """Возвращает список названий всех классов"""
        query = "SELECT name FROM classes ORDER BY name"
        return [row['name'] for row in self._fetch_all(query)]

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о классе по названию"""
        query = """
            SELECT id, name, hit_die, primary_stats, saving_throws,
                   skill_choices, description, image_path, is_spellcaster,
                   spellcasting_ability, cantrips_count, spells_count_level1, masteries_count
            FROM classes
            WHERE name = %s
        """
        row = self._fetch_one(query, (name,))
        if row:
            # Десериализуем JSON поля
            if isinstance(row.get('primary_stats'), str):
                try:
                    row['primary_stats'] = json.loads(row['primary_stats'])
                except:
                    row['primary_stats'] = []
            if isinstance(row.get('saving_throws'), str):
                try:
                    row['saving_throws'] = json.loads(row['saving_throws'])
                except:
                    row['saving_throws'] = []
        return row

    def get_by_id(self, class_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о классе по ID"""
        query = """
            SELECT id, name, hit_die, primary_stats, saving_throws,
                   skill_choices, description, image_path, is_spellcaster,
                   spellcasting_ability, cantrips_count, spells_count_level1, masteries_count
            FROM classes
            WHERE id = %s
        """
        row = self._fetch_one(query, (class_id,))
        if row:
            if isinstance(row.get('primary_stats'), str):
                try:
                    row['primary_stats'] = json.loads(row['primary_stats'])
                except:
                    row['primary_stats'] = []
            if isinstance(row.get('saving_throws'), str):
                try:
                    row['saving_throws'] = json.loads(row['saving_throws'])
                except:
                    row['saving_throws'] = []
        return row

    def get_primary_stats(self, class_name: str) -> List[str]:
        """Возвращает основные характеристики класса"""
        class_data = self.get_by_name(class_name)
        if not class_data:
            return ["STR"]

        primary_stats = class_data.get('primary_stats', [])
        if isinstance(primary_stats, str):
            try:
                primary_stats = json.loads(primary_stats)
            except:
                primary_stats = []
        return primary_stats or ["STR"]

    def get_hit_die(self, class_name: str) -> int:
        """Возвращает хитовый кубик класса"""
        class_data = self.get_by_name(class_name)
        return class_data.get('hit_die', 8) if class_data else 8

    def get_spell_counts(self, class_name: str) -> Dict[str, int]:
        """Возвращает количество заговоров и заклинаний 1 уровня"""
        class_data = self.get_by_name(class_name)
        if not class_data:
            return {'cantrips': 0, 'level1': 0}

        return {
            'cantrips': class_data.get('cantrips_count', 0),
            'level1': class_data.get('spells_count_level1', 0)
        }

    def get_masteries_count(self, class_name: str) -> int:
        """Возвращает количество оружейных приёмов для класса"""
        class_data = self.get_by_name(class_name)
        return class_data.get('masteries_count', 0) if class_data else 0

    def get_saving_throws(self, class_name: str) -> List[str]:
        """Возвращает спасброски класса"""
        class_data = self.get_by_name(class_name)
        if not class_data:
            return []

        saving_throws = class_data.get('saving_throws', [])
        if isinstance(saving_throws, str):
            try:
                saving_throws = json.loads(saving_throws)
            except:
                saving_throws = []
        return saving_throws or []

    def is_spellcaster(self, class_name: str) -> bool:
        """Проверяет, является ли класс заклинателем"""
        class_data = self.get_by_name(class_name)
        return class_data.get('is_spellcaster', False) if class_data else False

    def get_subclasses(self, class_name: str, level: int = 1) -> List[Dict[str, Any]]:
        """Возвращает подклассы для указанного класса и уровня"""
        class_data = self.get_by_name(class_name)
        if not class_data:
            return []

        query = """
            SELECT id, name, level_acquired, description, features
            FROM subclasses
            WHERE class_id = %s AND level_acquired <= %s
            ORDER BY level_acquired, name
        """
        return self._fetch_all(query, (class_data['id'], level))