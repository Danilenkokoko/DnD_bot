# repositories/character_repository.py
import json
import psycopg2
from typing import List, Dict, Any, Optional
from psycopg2.extras import RealDictCursor
from repositories.base_repository import BaseRepository
from db import get_connection

class CharacterRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self._table_name = "characters"

    def create(self, data: Dict[str, Any]) -> int:
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
                selected_equipment_choice,
                druid_order, cleric_order, warlock_pact,
                rogue_expertise, rogue_extra_language,
                auto_spells, pact_tome_cantrips, pact_tome_rituals, pact_blade_weapon,
                languages, selected_tools,
                selected_secondary_weapon, selected_other_items, coins,
                draconic_ancestry, warlock_invocation, favored_enemy,
                sorcerer_origin, trinket,
                inspiration,
                max_hp, current_hp, temp_hp, hit_dice_used, exhaustion, conditions
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                      %s, %s, %s, %s, %s, %s,
                      %s, %s, %s,
                      %s, %s, %s,
                      %s, %s,
                      %s, %s,
                      %s, %s, %s, %s,
                      %s,
                      %s, %s, %s,
                      %s, %s,
                      %s, %s, %s, %s,
                      %s, %s,
                      %s, %s, %s,
                      %s, %s, %s,
                      %s, %s,
                      %s,
                      %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        # Для jsonb-полей -> преобразуем в JSON-строку
        selected_skills = json.dumps(data.get('selected_skills', []))
        selected_masteries = json.dumps(data.get('selected_masteries', []))
        selected_invocations = json.dumps(data.get('selected_invocations', []))
        selected_spells = json.dumps(data.get('selected_spells', []))
        # Новые JSONB-поля 2024 PHB: языки и владение инструментами
        languages = json.dumps(data.get('languages', []))
        selected_tools = json.dumps(data.get('selected_tools', []))
        # Снаряжение и стартовые монеты (2024 PHB).
        # coins хранится JSONB с пятью ключами; неуказанные слитки = 0.
        coins_default = {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0}
        coins_value = data.get('coins')
        if not isinstance(coins_value, dict):
            coins_value = coins_default
        else:
            coins_value = {**coins_default, **coins_value}
        coins = json.dumps(coins_value)
        # Для полей типа ARRAY -> передаём список (psycopg2 преобразует в массив)
        rogue_expertise = data.get('rogue_expertise', [])
        auto_spells = data.get('auto_spells', [])
        pact_tome_cantrips = data.get('pact_tome_cantrips', [])
        pact_tome_rituals = data.get('pact_tome_rituals', [])

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
            selected_skills,
            selected_masteries,
            data.get('selected_fighting_style'),
            selected_invocations,
            selected_spells,
            data.get('selected_weapon'),
            data.get('selected_armor'),
            data.get('backstory', ''),
            data.get('image_file_id'),
            data.get('origin_feat', ''),
            data.get('alignment', 'Нейтральный'),
            data.get('selected_equipment_choice', 'A'),   # новое поле
            data.get('druid_order'),
            data.get('cleric_order'),
            data.get('warlock_pact'),
            rogue_expertise,
            data.get('rogue_extra_language'),
            auto_spells,
            pact_tome_cantrips,
            pact_tome_rituals,
            data.get('pact_blade_weapon'),
            languages,
            selected_tools,
            data.get('selected_secondary_weapon'),
            data.get('selected_other_items'),
            coins,
            data.get('draconic_ancestry'),
            data.get('warlock_invocation'),
            data.get('favored_enemy'),
            # Этап 3.5/3.2: новые PHB 2024 поля.
            data.get('sorcerer_origin'),
            data.get('trinket'),
            # NOTE (этап 1): personality_trait/ideal/bond/flaw удалены.
            bool(data.get('inspiration', False)),
            # PHB 2024 — расширенный HP/state-трекинг.
            data.get('max_hp', data.get('hp', 0)),
            data.get('current_hp', data.get('hp', 0)),
            int(data.get('temp_hp', 0) or 0),
            int(data.get('hit_dice_used', 0) or 0),
            int(data.get('exhaustion', 0) or 0),
            data.get('conditions', []) or [],
        )
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()
                if result:
                    return result[0]
                raise Exception("Failed to insert character, no ID returned")

    def get_by_id(self, character_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
                        c.languages, c.selected_tools,
                        c.selected_secondary_weapon, c.selected_other_items, c.coins,
                        c.draconic_ancestry, c.warlock_invocation, c.favored_enemy,
                        c.sorcerer_origin, c.trinket,
                        c.inspiration,
                        c.max_hp, c.current_hp, c.temp_hp,
                        c.hit_dice_used, c.exhaustion, c.conditions,
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
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
                        c.languages, c.selected_tools,
                        c.selected_secondary_weapon, c.selected_other_items, c.coins,
                        c.draconic_ancestry, c.warlock_invocation, c.favored_enemy,
                        c.sorcerer_origin, c.trinket,
                        c.inspiration,
                        c.max_hp, c.current_hp, c.temp_hp,
                        c.hit_dice_used, c.exhaustion, c.conditions,
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
            'selected_equipment_choice',
            'backstory', 'image_file_id', 'origin_feat', 'alignment',
            'druid_order', 'cleric_order', 'warlock_pact',
            'rogue_extra_language', 'pact_blade_weapon',
            'languages', 'selected_tools',
            'selected_secondary_weapon', 'selected_other_items', 'coins',
            'draconic_ancestry', 'warlock_invocation', 'favored_enemy',
            'sorcerer_origin', 'trinket',
            'inspiration',
            # PHB 2024 — HP/state-трекинг.
            'max_hp', 'current_hp', 'temp_hp', 'hit_dice_used',
            'exhaustion', 'conditions',
        ]
        for field in allowed_fields:
            if field in data:
                set_clauses.append(f"{field} = %s")
                # Для jsonb-полей
                if field in ('selected_skills', 'selected_masteries',
                             'selected_invocations', 'selected_spells',
                             'languages', 'selected_tools'):
                    params.append(json.dumps(data[field] if data[field] is not None else []))
                # Монеты — JSONB-объект (5 ключей).
                elif field == 'coins':
                    coins_default = {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0}
                    val = data[field] if isinstance(data[field], dict) else {}
                    params.append(json.dumps({**coins_default, **val}))
                # Для полей типа ARRAY
                elif field in ('rogue_expertise', 'auto_spells',
                               'pact_tome_cantrips', 'pact_tome_rituals',
                               'conditions'):
                    params.append(data[field] if data[field] is not None else [])
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
        """Преобразует JSONB-поля из строк в списки, если они ещё не распарсены."""
        jsonb_fields = [
            'selected_skills', 'selected_masteries', 'selected_invocations', 'selected_spells',
            'languages', 'selected_tools', 'coins',
        ]
        for field in jsonb_fields:
            val = row.get(field)
            if isinstance(val, str):
                try:
                    row[field] = json.loads(val)
                except:
                    row[field] = [] if field != 'coins' else {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0}
            elif val is None:
                row[field] = [] if field != 'coins' else {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0}
        array_fields = [
            'rogue_expertise', 'auto_spells',
            'pact_tome_cantrips', 'pact_tome_rituals',
            'conditions',
        ]
        for field in array_fields:
            if row.get(field) is None:
                row[field] = []
        return row
