# repositories/background_repository.py
"""
Репозиторий для работы с предысториями
"""

from typing import List, Dict, Any, Optional
import json
from repositories.base_repository import BaseRepository


class BackgroundRepository(BaseRepository):
    """Репозиторий для работы с предысториями"""

    def __init__(self):
        super().__init__()
        self._table_name = "backgrounds"

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает список всех предысторий"""
        query = """
            SELECT id, name, description, trait, skills, tools, equipment_a, equipment_b
            FROM backgrounds
            ORDER BY name
        """
        rows = self._fetch_all(query)
        for row in rows:
            # Десериализация skills
            if isinstance(row.get('skills'), str):
                try:
                    row['skills'] = json.loads(row['skills'])
                except:
                    row['skills'] = []
        return rows

    def get_all_names(self) -> List[str]:
        """Возвращает список названий предысторий"""
        query = "SELECT name FROM backgrounds ORDER BY name"
        return [row['name'] for row in self._fetch_all(query)]

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Возвращает предысторию по названию с десериализацией JSON полей"""
        query = """
            SELECT id, name, characteristic1, characteristic2, characteristic3,
                   trait, skills, tools, equipment_a, equipment_b, description
            FROM backgrounds
            WHERE name = %s
        """
        row = self._fetch_one(query, (name,))
        if not row:
            return None

        # Собираем характеристики в список
        characteristics = []
        if row.get('characteristic1'):
            characteristics.append(row['characteristic1'])
        if row.get('characteristic2'):
            characteristics.append(row['characteristic2'])
        if row.get('characteristic3'):
            characteristics.append(row['characteristic3'])
        row['characteristics'] = characteristics

        # Десериализация skills
        skills = row.get('skills')
        if isinstance(skills, str):
            try:
                row['skills'] = json.loads(skills)
            except:
                row['skills'] = []
        elif not isinstance(skills, list):
            row['skills'] = []

        # Удаляем исходные поля, чтобы не дублировать
        row.pop('characteristic1', None)
        row.pop('characteristic2', None)
        row.pop('characteristic3', None)

        return row

    def get_characteristics(self, background_name: str) -> List[str]:
        """Возвращает три характеристики предыстории"""
        bg = self.get_by_name(background_name)
        return bg.get('characteristics', []) if bg else []

    def get_trait(self, background_name: str) -> str:
        """Возвращает черту предыстории"""
        bg = self.get_by_name(background_name)
        return bg.get('trait', '') if bg else ''

    def get_skills(self, background_name: str) -> List[str]:
        """Возвращает навыки предыстории"""
        bg = self.get_by_name(background_name)
        skills = bg.get('skills', []) if bg else []
        return skills if isinstance(skills, list) else []

    def get_tools(self, background_name: str) -> str:
        """Возвращает инструменты предыстории"""
        bg = self.get_by_name(background_name)
        return bg.get('tools', '') if bg else ''

    def get_description(self, background_name: str) -> str:
        """Возвращает описание предыстории"""
        bg = self.get_by_name(background_name)
        return bg.get('description', '') if bg else ''

    def get_equipment_choice(self, background_name: str, choice: str = "A") -> str:
        """Возвращает снаряжение предыстории по выбору А или Б"""
        bg = self.get_by_name(background_name)
        if not bg:
            return "Нет данных"
        if choice.upper() == "A":
            return bg.get('equipment_a', 'Нет данных')
        elif choice.upper() == "B":
            return bg.get('equipment_b', 'Нет данных')
        return "Неверный выбор"