# repositories/character_repository.py
"""
Репозиторий для работы с персонажами
"""

import json
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import Json
from repositories.base_repository import BaseRepository
from db import get_connection


class CharacterRepository(BaseRepository):
    """Репозиторий для работы с персонажами"""

    def __init__(self):
        super().__init__()
        self._table_name = "characters"

    def create(self, data: Dict[str, Any]) -> int:
        """
        Создаёт нового персонажа и возвращает его ID.
        """
        stats = data.get('stats', {})
        query = """
            INSERT INTO characters (
                user_id, name, race_id, subrace_id, class_id, background_id,
                level, experience, str, dex, con, int, wis, cha,
                hp, ac, speed,
                selected_skills, selected_masteries, selected_fighting_style,
                selected_invocations, selected_spells,
                selected_weapon, selected_armor,
                backstory, image_file_id, origin_feat, alignment,
                druid_order, cleric_order, warlock_pact,
                rogue_expertise, rogue_extra_language,
                auto_spells, pact_tome_cantrips, pact_tome_rituals, pact_blade_weapon
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s,
                      %s, %s, %s,
                      %s, %s, %s,
                      %s, %s,
                      %s, %s,
                      %s, %s, %s, %s,
                      %s, %s, %s,
                      %s, %s,
                      %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            data['user_id'],
            data['name'],
            data.get('race_id'),
            data.get('subrace_id'),
            data.get('class_id'),
            data.get('background_id'),
            data.get('level', 1),
            data.get('experience', 0),
            stats.get('STR', 10),
            stats.get('DEX', 10),
            stats.get('CON', 10),
            stats.get('INT', 10),
            stats.get('WIS', 10),
            stats.get('CHA', 10),
            data.get('hp', 0),
            data.get('ac', 10),
            data.get('speed', 30),
            Json(data.get('selected_skills', [])),
            Json(data.get('selected_masteries', [])),
            data.get('selected_fighting_style'),
            Json(data.get('selected_invocations', [])),
            Json(data.get('selected_spells', [])),
            data.get('selected_weapon'),
            data.get('selected_armor'),
            data.get('backstory', ''),
            data.get('image_file_id'),
            data.get('origin_feat', ''),
            data.get('alignment', 'Нейтральный'),
            data.get('druid_order'),
            data.get('cleric_order'),
            data.get('warlock_pact'),
            Json(data.get('rogue_expertise', [])),
            data.get('rogue_extra_language'),
            Json(data.get('auto_spells', [])),
            Json(data.get('pact_tome_cantrips', [])),
            Json(data.get('pact_tome_rituals', [])),
            data.get('pact_blade_weapon')
        )
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()
                if result:
                    return result[0]
                else:
                    raise Exception("Failed to insert character, no ID returned")

    def get_by_id(self, character_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                query = """
                    SELECT
                        c.id, c.user_id, c.name, c.level, c.experience,
                        c.str, c.dex, c.con, c.int, c.wis, c.cha,
                        c.hp, c.ac, c.speed,
                        c.selected_skills, c.selected_masteries, c.selected_fighting_style,
                        c.selected_invocations, c.selected_spells,
                        c.selected_weapon, c.selected_armor,
                        c.backstory, c.image_file_id, c.origin_feat, c.alignment,
                        c.druid_order, c.cleric_order, c.warlock_pact,
                        c.rogue_expertise, c.rogue_extra_language,
                        c.auto_spells, c.pact_tome_cantrips, c.pact_tome_rituals, c.pact_blade_weapon,
                        r.name as race_name,
                        s.name as subrace_name,
                        cl.name as class_name,
                        b.name as background_name
                    FROM characters c
                    LEFT JOIN races r ON c.race_id = r.id
                    LEFT JOIN subraces s ON c.subrace_id = s.id
                    LEFT JOIN classes cl ON c.class_id = cl.id
                    LEFT JOIN backgrounds b ON c.background_id = b.id
                    WHERE c.id = %s
                """
                params = [character_id]
                if user_id is not None:
                    query += " AND c.user_id = %s"
                    params.append(user_id)
                cur.execute(query, params)
                row = cur.fetchone()
                if not row:
                    return None
                return self._deserialize_character(row)

    def get_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT
                        c.id, c.user_id, c.name, c.level, c.experience,
                        c.str, c.dex, c.con, c.int, c.wis, c.cha,
                        c.hp, c.ac, c.speed,
                        c.selected_skills, c.selected_masteries, c.selected_fighting_style,
                        c.selected_invocations, c.selected_spells,
                        c.selected_weapon, c.selected_armor,
                        c.backstory, c.image_file_id, c.origin_feat, c.alignment,
                        c.druid_order, c.cleric_order, c.warlock_pact,
                        c.rogue_expertise, c.rogue_extra_language,
                        c.auto_spells, c.pact_tome_cantrips, c.pact_tome_rituals, c.pact_blade_weapon,
                        r.name as race_name,
                        s.name as subrace_name,
                        cl.name as class_name,
                        b.name as background_name
                    FROM characters c
                    LEFT JOIN races r ON c.race_id = r.id
                    LEFT JOIN subraces s ON c.subrace_id = s.id
                    LEFT JOIN classes cl ON c.class_id = cl.id
                    LEFT JOIN backgrounds b ON c.background_id = b.id
                    WHERE c.user_id = %s
                    ORDER BY c.id DESC
                """, (user_id,))
                rows = cur.fetchall()
                return [self._deserialize_character(row) for row in rows]

    def update(self, character_id: int, user_id: int, data: Dict[str, Any]) -> bool:
        set_clauses = []
        params = []
        allowed_fields = [
            'name', 'level', 'experience', 'hp', 'ac', 'speed',
            'selected_skills', 'selected_masteries', 'selected_fighting_style',
            'selected_invocations', 'selected_spells', 'selected_weapon', 'selected_armor',
            'backstory', 'image_file_id', 'origin_feat', 'alignment',
            'druid_order', 'cleric_order', 'warlock_pact',
            'rogue_extra_language', 'pact_blade_weapon'
        ]
        for field in allowed_fields:
            if field in data:
                set_clauses.append(f"{field} = %s")
                if field in ('selected_skills', 'selected_masteries', 'selected_invocations', 'selected_spells',
                             'rogue_expertise', 'auto_spells', 'pact_tome_cantrips', 'pact_tome_rituals'):
                    params.append(Json(data[field] if data[field] is not None else []))
                else:
                    params.append(data[field])
        if not set_clauses:
            return False
        stat_fields = ['str', 'dex', 'con', 'int', 'wis', 'cha']
        for stat in stat_fields:
            if stat in data:
                set_clauses.append(f"{stat} = %s")
                params.append(data[stat])
        query = f"UPDATE characters SET {', '.join(set_clauses)} WHERE id = %s AND user_id = %s"
        params.extend([character_id, user_id])
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount > 0

    def delete(self, character_id: int, user_id: int) -> bool:
        query = "DELETE FROM characters WHERE id = %s AND user_id = %s"
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (character_id, user_id))
                return cur.rowcount > 0

    def _deserialize_character(self, row: Dict[str, Any]) -> Dict[str, Any]:
        # Для jsonb-полей данные уже будут десериализованы в Python-объекты
        # (psycopg2 автоматически преобразует jsonb в dict/list)
        jsonb_fields = ['selected_skills', 'selected_masteries', 'selected_invocations', 'selected_spells',
                        'rogue_expertise', 'auto_spells', 'pact_tome_cantrips', 'pact_tome_rituals']
        for field in jsonb_fields:
            if row.get(field) is None:
                row[field] = []
            # Если это строка (вдруг), можно распарсить, но обычно нет
            elif isinstance(row[field], str):
                try:
                    row[field] = json.loads(row[field])
                except:
                    row[field] = []
        return row