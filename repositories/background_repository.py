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
            SELECT id, name, characteristic1, characteristic2, characteristic3,
                   trait, skills, tools, equipment_a, equipment_b, description, origin_feat
            FROM backgrounds
            ORDER BY name
        """
        return self._fetch_all(query)
    
    def get_all_names(self) -> List[str]:
        """Возвращает список названий всех предысторий"""
        query = "SELECT name FROM backgrounds ORDER BY name"
        return [row['name'] for row in self._fetch_all(query)]
    
    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Возвращает информацию о предыстории по названию"""
        query = """
            SELECT id, name, characteristic1, characteristic2, characteristic3,
                   trait, skills, tools, equipment_a, equipment_b, description, origin_feat
            FROM backgrounds
            WHERE name = %s
        """
        row = self._fetch_one(query, (name,))
        if not row:
            return None
        
        # Преобразуем данные в удобный формат
        skills = row.get('skills', [])
        if isinstance(skills, str):
            try:
                skills = json.loads(skills)
            except:
                skills = []
        elif skills is None:
            skills = []
        
        return {
            'id': row['id'],
            'name': row['name'],
            'characteristics': [
                row.get('characteristic1', 'Ловкость'),
                row.get('characteristic2', 'Ловкость'),
                row.get('characteristic3', 'Ловкость')
            ],
            'trait': row.get('trait', 'Нет'),
            'skills': skills,
            'tools': row.get('tools', 'Нет'),
            'equipment_a': row.get('equipment_a', 'Нет описания'),
            'equipment_b': row.get('equipment_b', 'Нет описания'),
            'description': row.get('description', ''),
            'origin_feat': row.get('origin_feat', '')
        }
    
    def get_origin_feat(self, background_name: str) -> str:
        """Возвращает черту происхождения для предыстории"""
        bg = self.get_by_name(background_name)
        return bg.get('origin_feat', '') if bg else ''
    
    def get_characteristics(self, background_name: str) -> List[str]:
        """Возвращает бонусы к характеристикам от предыстории"""
        bg = self.get_by_name(background_name)
        return bg['characteristics'] if bg else ["Ловкость", "Ловкость", "Ловкость"]
    
    def get_trait(self, background_name: str) -> str:
        """Возвращает черту предыстории"""
        bg = self.get_by_name(background_name)
        return bg['trait'] if bg else "Нет"
    
    def get_skills(self, background_name: str) -> List[str]:
        """Возвращает навыки от предыстории"""
        bg = self.get_by_name(background_name)
        return bg['skills'] if bg else []
    
    def get_tools(self, background_name: str) -> str:
        """Возвращает инструменты от предыстории"""
        bg = self.get_by_name(background_name)
        return bg['tools'] if bg else "Нет"
    
    def get_description(self, background_name: str) -> str:
        """Возвращает описание предыстории"""
        bg = self.get_by_name(background_name)
        return bg['description'] if bg else ""
    
    def get_equipment_choice(self, background_name: str, choice: str = "A") -> str:
        """Возвращает снаряжение предыстории по выбору А или Б"""
        bg = self.get_by_name(background_name)
        if not bg:
            return ""
        return bg['equipment_a'] if choice.upper() == "A" else bg['equipment_b']
    
    def get_equipment_options(self, background_name: str) -> tuple:
        """Возвращает оба варианта снаряжения для предыстории"""
        bg = self.get_by_name(background_name)
        if not bg:
            return ("", "")
        return (bg['equipment_a'], bg['equipment_b'])
