# repositories/character_repository.py
"""
Репозиторий для работы с персонажами (CRUD операции)
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class CharacterRepository(BaseRepository):
    """Репозиторий для работы с персонажами"""

    def __init__(self):
        super().__init__()
        self._table_name = "characters"

    # =========================================================
    # CREATE (СОЗДАНИЕ)
    # =========================================================

    def create(self, character_data: Dict[str, Any]) -> int:
        """
        Создаёт нового персонажа в базе данных

        Args:
            character_data: словарь с данными персонажа, должен содержать:
                - user_id: int
                - name: str
                - race_id: Optional[int]
                - subrace_id: Optional[int]
                - class_id: Optional[int]
                - subclass_id: Optional[int]
                - background_id: Optional[int]
                - level: int
                - experience: int
                - stats: Dict[str, int] (STR, DEX, CON, INT, WIS, CHA)
                - hp: int
                - ac: int
                - speed: int
                - selected_skills: List[str]
                - selected_masteries: List[str]
                - selected_fighting_style: Optional[str]
                - selected_invocations: List[str]
                - selected_spells: List[str]
                - selected_weapon: Optional[str]
                - selected_armor: Optional[str]
                - selected_equipment_choice: str
                - backstory: str
                - image_file_id: Optional[str]
                - alignment: str

        Returns:
            int: ID созданного персонажа
        """
        stats = character_data.get('stats', {})

        query = """
            INSERT INTO characters (
                user_id, name, race_id, subrace_id, class_id, subclass_id,
                background_id, level, experience, str, dex, con, int, wis, cha,
                hp, ac, speed, selected_skills, selected_masteries,
                selected_fighting_style, selected_invocations, selected_spells,
                selected_weapon, selected_armor, selected_equipment_choice,
                backstory, image_file_id, alignment, created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id
        """

        params = (
            character_data.get('user_id'),
            character_data.get('name'),
            character_data.get('race_id'),
            character_data.get('subrace_id'),
            character_data.get('class_id'),
            character_data.get('subclass_id'),
            character_data.get('background_id'),
            character_data.get('level', 1),
            character_data.get('experience', 0),
            stats.get('STR', 10),
            stats.get('DEX', 10),
            stats.get('CON', 10),
            stats.get('INT', 10),
            stats.get('WIS', 10),
            stats.get('CHA', 10),
            character_data.get('hp', 0),
            character_data.get('ac', 10),
            character_data.get('speed', 30),
            json.dumps(character_data.get('selected_skills', [])),
            json.dumps(character_data.get('selected_masteries', [])),
            character_data.get('selected_fighting_style'),
            json.dumps(character_data.get('selected_invocations', [])),
            json.dumps(character_data.get('selected_spells', [])),
            character_data.get('selected_weapon'),
            character_data.get('selected_armor'),
            character_data.get('selected_equipment_choice', 'A'),
            character_data.get('backstory', ''),
            character_data.get('image_file_id'),
            character_data.get('alignment', 'Нейтральное')
        )

        result = self._fetch_one(query, params)
        char_id = result['id'] if result else None

        if char_id:
            logger.info(f"✅ Персонаж сохранён: ID={char_id}, Name={character_data.get('name')}")
        else:
            logger.error(f"❌ Не удалось сохранить персонажа: {character_data.get('name')}")

        return char_id

    # =========================================================
    # READ (ЧТЕНИЕ)
    # =========================================================

    def get_by_id(self, char_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Возвращает персонажа по ID. Если указан user_id, проверяет принадлежность.

        Args:
            char_id: ID персонажа
            user_id: ID пользователя (опционально, для проверки прав)

        Returns:
            Dict с данными персонажа или None
        """
        if user_id:
            query = """
                SELECT c.*, 
                       cls.name as class_name, cls.hit_die, cls.primary_stats, cls.saving_throws,
                       r.name as race_name, r.speed as race_speed, r.size as race_size,
                       bg.name as background_name, bg.trait as background_trait
                FROM characters c
                LEFT JOIN classes cls ON c.class_id = cls.id
                LEFT JOIN races r ON c.race_id = r.id
                LEFT JOIN backgrounds bg ON c.background_id = bg.id
                WHERE c.id = %s AND c.user_id = %s
            """
            params = (char_id, user_id)
        else:
            query = """
                SELECT c.*, 
                       cls.name as class_name, cls.hit_die, cls.primary_stats, cls.saving_throws,
                       r.name as race_name, r.speed as race_speed, r.size as race_size,
                       bg.name as background_name, bg.trait as background_trait
                FROM characters c
                LEFT JOIN classes cls ON c.class_id = cls.id
                LEFT JOIN races r ON c.race_id = r.id
                LEFT JOIN backgrounds bg ON c.background_id = bg.id
                WHERE c.id = %s
            """
            params = (char_id,)

        result = self._fetch_one(query, params)
        if result:
            result = self._parse_character_row(result)
        return result

    def get_by_user_id(self, user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Возвращает всех персонажей пользователя

        Args:
            user_id: ID пользователя
            limit: максимальное количество записей (опционально)

        Returns:
            Список персонажей
        """
        query = """
            SELECT c.id, c.name, c.level, c.hp, c.ac, c.created_at,
                   cls.name as class_name, r.name as race_name, bg.name as background_name
            FROM characters c
            LEFT JOIN classes cls ON c.class_id = cls.id
            LEFT JOIN races r ON c.race_id = r.id
            LEFT JOIN backgrounds bg ON c.background_id = bg.id
            WHERE c.user_id = %s
            ORDER BY c.id DESC
        """

        if limit:
            query += f" LIMIT {int(limit)}"

        results = self._fetch_all(query, (user_id,))
        return [self._parse_character_row(row) for row in results]

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Возвращает список всех персонажей (для администрирования)"""
        query = """
            SELECT c.id, c.name, c.level, c.user_id,
                   cls.name as class_name, r.name as race_name
            FROM characters c
            LEFT JOIN classes cls ON c.class_id = cls.id
            LEFT JOIN races r ON c.race_id = r.id
            ORDER BY c.id DESC
            LIMIT %s OFFSET %s
        """
        return self._fetch_all(query, (limit, offset))

    def get_count_by_user(self, user_id: int) -> int:
        """Возвращает количество персонажей пользователя"""
        query = "SELECT COUNT(*) FROM characters WHERE user_id = %s"
        return self._fetch_value(query, (user_id,)) or 0

    def get_total_count(self) -> int:
        """Возвращает общее количество персонажей в базе"""
        query = "SELECT COUNT(*) FROM characters"
        return self._fetch_value(query) or 0

    # =========================================================
    # UPDATE (ОБНОВЛЕНИЕ)
    # =========================================================

    def update(self, char_id: int, user_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Обновляет данные персонажа

        Args:
            char_id: ID персонажа
            user_id: ID пользователя (для проверки прав)
            update_data: словарь с полями для обновления

        Returns:
            True если обновление успешно, иначе False
        """
        if not self._check_ownership(char_id, user_id):
            logger.warning(f"Попытка обновления чужого персонажа: user={user_id}, char={char_id}")
            return False

        allowed_fields = {
            'name': '%s',
            'level': '%s',
            'experience': '%s',
            'hp': '%s',
            'ac': '%s',
            'selected_skills': '%s',
            'selected_masteries': '%s',
            'selected_fighting_style': '%s',
            'selected_invocations': '%s',
            'selected_spells': '%s',
            'selected_weapon': '%s',
            'selected_armor': '%s',
            'backstory': '%s',
            'image_file_id': '%s',
            'alignment': '%s'
        }

        set_clauses = []
        params = []

        for field, placeholder in allowed_fields.items():
            if field in update_data:
                value = update_data[field]
                if field in ['selected_skills', 'selected_masteries', 'selected_invocations', 'selected_spells']:
                    value = json.dumps(value)
                set_clauses.append(f"{field} = {placeholder}")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = NOW()")
        query = f"UPDATE characters SET {', '.join(set_clauses)} WHERE id = %s AND user_id = %s"
        params.extend([char_id, user_id])

        self._execute_query(query, tuple(params))
        logger.info(f"✅ Персонаж обновлён: ID={char_id}, User={user_id}")
        return True

    def update_stats(self, char_id: int, user_id: int, stats: Dict[str, int]) -> bool:
        """Обновляет характеристики персонажа"""
        update_data = {
            'str': stats.get('STR', 10),
            'dex': stats.get('DEX', 10),
            'con': stats.get('CON', 10),
            'int': stats.get('INT', 10),
            'wis': stats.get('WIS', 10),
            'cha': stats.get('CHA', 10),
        }

        set_clauses = [f"{k} = %s" for k in update_data.keys()]
        params = list(update_data.values())

        query = f"UPDATE characters SET {', '.join(set_clauses)}, updated_at = NOW() WHERE id = %s AND user_id = %s"
        params.extend([char_id, user_id])

        self._execute_query(query, tuple(params))
        return True

    # =========================================================
    # DELETE (УДАЛЕНИЕ)
    # =========================================================

    def delete(self, char_id: int, user_id: int) -> bool:
        """
        Удаляет персонажа

        Args:
            char_id: ID персонажа
            user_id: ID пользователя (для проверки прав)

        Returns:
            True если удаление успешно, иначе False
        """
        if not self._check_ownership(char_id, user_id):
            logger.warning(f"Попытка удаления чужого персонажа: user={user_id}, char={char_id}")
            return False

        query = "DELETE FROM characters WHERE id = %s AND user_id = %s"
        self._execute_query(query, (char_id, user_id))

        logger.info(f"🗑️ Персонаж удалён: ID={char_id}, User={user_id}")
        return True

    def delete_all_for_user(self, user_id: int) -> int:
        """Удаляет всех персонажей пользователя (для тестирования/администрирования)"""
        count = self.get_count_by_user(user_id)
        query = "DELETE FROM characters WHERE user_id = %s"
        self._execute_query(query, (user_id,))
        logger.info(f"🗑️ Удалено {count} персонажей пользователя {user_id}")
        return count

    # =========================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # =========================================================

    def _check_ownership(self, char_id: int, user_id: int) -> bool:
        """Проверяет, принадлежит ли персонаж пользователю"""
        query = "SELECT 1 FROM characters WHERE id = %s AND user_id = %s LIMIT 1"
        result = self._fetch_one(query, (char_id, user_id))
        return result is not None

    def _parse_character_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразует строку из БД в удобный для использования словарь"""
        if not row:
            return {}

        # Десериализация JSON полей
        json_fields = ['selected_skills', 'selected_masteries', 'selected_invocations', 'selected_spells']
        for field in json_fields:
            if field in row and row[field]:
                if isinstance(row[field], str):
                    try:
                        row[field] = json.loads(row[field])
                    except:
                        row[field] = []
            elif field in row and not row[field]:
                row[field] = []

        # Нормализация характеристик
        stats = {
            'STR': row.get('str', 10),
            'DEX': row.get('dex', 10),
            'CON': row.get('con', 10),
            'INT': row.get('int', 10),
            'WIS': row.get('wis', 10),
            'CHA': row.get('cha', 10),
        }
        row['stats'] = stats

        return row

    def get_character_sheet_data(self, char_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает полные данные персонажа для отображения (связанные сущности)"""
        character = self.get_by_id(char_id, user_id)
        if not character:
            return None

        return {
            'id': character.get('id'),
            'name': character.get('name'),
            'class_name': character.get('class_name'),
            'race_name': character.get('race_name'),
            'background_name': character.get('background_name'),
            'level': character.get('level'),
            'stats': character.get('stats'),
            'hp': character.get('hp'),
            'ac': character.get('ac'),
            'speed': character.get('speed'),
            'selected_skills': character.get('selected_skills', []),
            'selected_masteries': character.get('selected_masteries', []),
            'selected_fighting_style': character.get('selected_fighting_style'),
            'selected_invocations': character.get('selected_invocations', []),
            'selected_spells': character.get('selected_spells', []),
            'selected_weapon': character.get('selected_weapon'),
            'selected_armor': character.get('selected_armor'),
            'backstory': character.get('backstory'),
            'image_file_id': character.get('image_file_id'),
            'alignment': character.get('alignment'),
            'created_at': character.get('created_at'),
            'updated_at': character.get('updated_at'),
        }