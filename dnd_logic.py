#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dnd_logic.py - D&D 5.5e (2024) Character Logic Module
Модуль с игровой логикой для создания персонажей
Все данные берутся из PostgreSQL
"""

import psycopg2
import json
import os
import logging
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация базы данных
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "DND_DB"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "").strip(),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}


def get_connection():
    """Создаёт подключение к базе данных"""
    return psycopg2.connect(**DB_CONFIG)


# =========================================================
# 1. БАЗОВЫЕ РАСЧЁТЫ
# =========================================================

def modifier(stat: int) -> int:
    """
    Расчёт модификатора характеристики

    Args:
        stat: значение характеристики (от 1 до 30)

    Returns:
        int: модификатор характеристики
    """
    return (stat - 10) // 2


def calculate_proficiency_bonus(level: int) -> int:
    """
    Расчёт бонуса мастерства в зависимости от уровня

    Args:
        level: уровень персонажа (1-20)

    Returns:
        int: бонус мастерства
    """
    if level < 1:
        raise ValueError("Уровень должен быть >= 1")

    if level <= 4:
        return 2
    elif level <= 8:
        return 3
    elif level <= 12:
        return 4
    elif level <= 16:
        return 5
    else:
        return 6


def calc_hp(class_id: int, constitution: int, level: int = 1) -> int:
    """
    Расчёт HP персонажа

    Args:
        class_id: ID класса
        constitution: значение телосложения
        level: уровень персонажа

    Returns:
        int: максимальное HP
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT hit_die FROM classes WHERE id = %s", (class_id,))
            result = cur.fetchone()
            if not result:
                raise ValueError(f"Класс с ID {class_id} не найден")
            hit_die = result[0]

    con_mod = modifier(constitution)

    if level == 1:
        return hit_die + max(1, con_mod)
    else:
        avg_roll = (hit_die // 2) + 1
        return hit_die + max(1, con_mod) + (level - 1) * (avg_roll + max(1, con_mod))


def calc_ac(dexterity: int, armor_type: str = "none", has_shield: bool = False) -> int:
    """
    Расчёт Класса Брони (AC)

    Args:
        dexterity: значение ловкости
        armor_type: тип брони ("none", "light", "medium", "heavy")
        has_shield: есть ли щит

    Returns:
        int: Класс Брони
    """
    dex_mod = modifier(dexterity)

    armor_base = {
        "none": 10 + dex_mod,
        "light": 11 + dex_mod,
        "medium": 14 + min(2, dex_mod),
        "heavy": 16
    }

    base_ac = armor_base.get(armor_type, 10 + dex_mod)

    if has_shield:
        base_ac += 2

    return base_ac


# =========================================================
# 2. РАБОТА С РАСАМИ (из БД)
# =========================================================

def get_all_races() -> List[Dict[str, Any]]:
    """Возвращает список всех рас"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, speed, size, description FROM races ORDER BY name")
            columns = ['id', 'name', 'speed', 'size', 'description']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_race_list() -> List[str]:
    """Возвращает список названий рас"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM races ORDER BY name")
            return [row[0] for row in cur.fetchall()]


def get_race_by_name(race_name: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о расе по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, speed, size, description 
                FROM races WHERE name = %s
            """, (race_name,))
            row = cur.fetchone()
            if row:
                return {'id': row[0], 'name': row[1], 'speed': row[2], 'size': row[3], 'description': row[4]}
    return None


def get_race_info(race_name: str) -> Dict[str, Any]:
    """Возвращает полную информацию о расе (для совместимости со старым кодом)"""
    race = get_race_by_name(race_name)
    if not race:
        return {}

    # Получаем подрасы
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT name, trait, description FROM subraces 
                WHERE race_id = %s
            """, (race['id'],))
            subraces = {}
            for row in cur.fetchall():
                subraces[row[0]] = {'trait': row[1], 'description': row[2]}

    return {
        'name': race_name,
        'speed': race['speed'],
        'size': race['size'],
        'description': race['description'],
        'traits': [],  # В новой версии особенности расы будут в отдельной таблице
        'subraces': subraces
    }


def get_race_description(race_name: str) -> str:
    """Возвращает описание расы"""
    race = get_race_by_name(race_name)
    return race['description'] if race else "Нет описания"


def get_race_speed(race_name: str) -> int:
    """Возвращает скорость расы"""
    race = get_race_by_name(race_name)
    return race['speed'] if race else 30


def has_subraces(race_name: str) -> bool:
    """Проверяет, есть ли у расы подрасы"""
    race = get_race_by_name(race_name)
    if not race:
        return False

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM subraces WHERE race_id = %s", (race['id'],))
            return cur.fetchone()[0] > 0


def get_subraces(race_name: str) -> List[str]:
    """Возвращает список подрас для указанной расы"""
    race = get_race_by_name(race_name)
    if not race:
        return []

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM subraces WHERE race_id = %s", (race['id'],))
            return [row[0] for row in cur.fetchall()]


# =========================================================
# 3. РАБОТА С КЛАССАМИ (из БД)
# =========================================================

def get_all_classes() -> List[Dict[str, Any]]:
    """Возвращает список всех классов"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, hit_die, primary_stats, saving_throws, 
                       skill_choices, description, is_spellcaster, spellcasting_ability
                FROM classes ORDER BY name
            """)
            columns = ['id', 'name', 'hit_die', 'primary_stats', 'saving_throws',
                       'skill_choices', 'description', 'is_spellcaster', 'spellcasting_ability']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_class_list() -> List[str]:
    """Возвращает список названий классов"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM classes ORDER BY name")
            return [row[0] for row in cur.fetchall()]


def get_class_by_name(class_name: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о классе по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, hit_die, primary_stats, saving_throws, 
                       skill_choices, description, is_spellcaster, spellcasting_ability
                FROM classes WHERE name = %s
            """, (class_name,))
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0], 'name': row[1], 'hit_die': row[2],
                    'primary_stats': row[3], 'saving_throws': row[4],
                    'skill_choices': row[5], 'description': row[6],
                    'is_spellcaster': row[7], 'spellcasting_ability': row[8]
                }
    return None


def get_class_info(class_name: str) -> Dict[str, Any]:
    """Возвращает информацию о классе (для совместимости)"""
    class_data = get_class_by_name(class_name)
    if not class_data:
        return {}

    return {
        'hit_die': class_data['hit_die'],
        'primary_stats': class_data['primary_stats'],
        'saving_throws': class_data['saving_throws'],
        'skill_choices': class_data['skill_choices'],
        'description': class_data['description'],
        'spellcasting': class_data['is_spellcaster'],
        'spellcasting_ability': class_data['spellcasting_ability']
    }


def get_class_description(class_name: str) -> str:
    """Возвращает описание класса"""
    class_data = get_class_by_name(class_name)
    return class_data['description'] if class_data else "Нет описания"


def get_class_hit_die(class_name: str) -> int:
    """Возвращает хитовый кубик класса"""
    class_data = get_class_by_name(class_name)
    return class_data['hit_die'] if class_data else 6


# =========================================================
# 4. РАБОТА С ПРЕДЫСТОРИЯМИ (из БД) - КЛЮЧЕВОЕ ДЛЯ 5.5e!
# =========================================================

def get_all_backgrounds() -> List[Dict[str, Any]]:
    """Возвращает список всех предысторий"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, characteristic1, characteristic2, characteristic3,
                       trait, skills, tools, equipment_a, equipment_b, description
                FROM backgrounds ORDER BY name
            """)
            columns = ['id', 'name', 'characteristic1', 'characteristic2', 'characteristic3',
                       'trait', 'skills', 'tools', 'equipment_a', 'equipment_b', 'description']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_background_list() -> List[str]:
    """Возвращает список названий предысторий"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM backgrounds ORDER BY name")
            return [row[0] for row in cur.fetchall()]


def get_background_by_name(background_name: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о предыстории по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, characteristic1, characteristic2, characteristic3,
                       trait, skills, tools, equipment_a, equipment_b, description
                FROM backgrounds WHERE name = %s
            """, (background_name,))
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0], 'name': row[1],
                    'characteristics': [row[2], row[3], row[4]],
                    'trait': row[5],
                    'skills': row[6] if isinstance(row[6], list) else json.loads(row[6]),
                    'tools': row[7],
                    'equipment_a': row[8],
                    'equipment_b': row[9],
                    'description': row[10]
                }
    return None


def get_background_data(background_name: str) -> Dict[str, Any]:
    """Возвращает данные предыстории (для совместимости)"""
    bg = get_background_by_name(background_name)
    if not bg:
        return {}

    return {
        'characteristics': bg['characteristics'],
        'trait': bg['trait'],
        'skills': bg['skills'],
        'tools': bg['tools'],
        'equipment_a': bg['equipment_a'],
        'equipment_b': bg['equipment_b'],
        'description': bg['description']
    }


def get_background_characteristics(background_name: str) -> List[str]:
    """Возвращает бонусы к характеристикам от предыстории (КЛЮЧЕВО ДЛЯ 5.5e!)"""
    bg = get_background_by_name(background_name)
    return bg['characteristics'] if bg else ["Ловкость", "Ловкость", "Ловкость"]


def get_background_trait(background_name: str) -> str:
    """Возвращает черту предыстории"""
    bg = get_background_by_name(background_name)
    return bg['trait'] if bg else ""


def get_background_skills(background_name: str) -> List[str]:
    """Возвращает навыки от предыстории"""
    bg = get_background_by_name(background_name)
    return bg['skills'] if bg else []


def get_background_tools(background_name: str) -> str:
    """Возвращает инструменты от предыстории"""
    bg = get_background_by_name(background_name)
    return bg['tools'] if bg else ""


def get_background_description(background_name: str) -> str:
    """Возвращает описание предыстории"""
    bg = get_background_by_name(background_name)
    return bg['description'] if bg else ""


def get_equipment_choice(background_name: str, choice: str = "A") -> str:
    """Возвращает снаряжение предыстории по выбору А или Б"""
    bg = get_background_by_name(background_name)
    if not bg:
        return ""
    return bg['equipment_a'] if choice.upper() == "A" else bg['equipment_b']


# =========================================================
# 5. РАСЧЁТ ХАРАКТЕРИСТИК (с бонусами от предыстории!)
# =========================================================

def get_standard_stats() -> Dict[str, int]:
    """
    Возвращает стандартный набор характеристик (15, 14, 13, 12, 10, 8)
    """
    return {
        "STR": 15,
        "DEX": 14,
        "CON": 13,
        "INT": 12,
        "WIS": 10,
        "CHA": 8
    }


def apply_background_bonuses(stats: Dict[str, int], background_name: str) -> Dict[str, int]:
    """
    Применяет бонусы к характеристикам от предыстории (D&D 5.5e!)

    В 5.5e бонусы даёт ПРЕДЫСТОРИЯ, а не раса!
    """
    result = stats.copy()

    bg = get_background_by_name(background_name)
    if not bg:
        return result

    # Карта перевода русских названий в коды статов
    stat_map = {
        "Сила": "STR", "Ловкость": "DEX", "Телосложение": "CON",
        "Интеллект": "INT", "Мудрость": "WIS", "Харизма": "CHA"
    }

    characteristics = bg['characteristics']

    # +2 к первой характеристике
    stat1 = stat_map.get(characteristics[0], "DEX")
    result[stat1] += 2

    # +1 ко второй характеристике
    stat2 = stat_map.get(characteristics[1], "DEX")
    result[stat2] += 1

    # Третья характеристика остаётся без бонуса (только для опционального правила)

    # Ограничиваем значения
    for stat in result:
        result[stat] = min(20, result[stat])

    return result


def get_initial_stats(background_name: str) -> Dict[str, int]:
    """
    Получает начальные характеристики с учётом предыстории (D&D 5.5e!)

    ВАЖНО: В 5.5e бонусы даёт ПРЕДЫСТОРИЯ, а не раса!
    """
    base_stats = get_standard_stats()
    return apply_background_bonuses(base_stats, background_name)


# =========================================================
# 6. РАБОТА С ОРУЖЕЙНЫМИ ПРИЁМАМИ
# =========================================================

def get_all_weapon_masteries() -> List[Dict[str, Any]]:
    """Возвращает список всех оружейных приёмов"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, trigger_condition, effect, weapons FROM weapon_masteries ORDER BY name")
            columns = ['id', 'name', 'trigger_condition', 'effect', 'weapons']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_weapon_mastery_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о приёме по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, trigger_condition, effect, weapons 
                FROM weapon_masteries WHERE name = %s
            """, (name,))
            row = cur.fetchone()
            if row:
                return {'id': row[0], 'name': row[1], 'trigger_condition': row[2], 'effect': row[3], 'weapons': row[4]}
    return None


# =========================================================
# 7. РАБОТА С БОЕВЫМИ СТИЛЯМИ
# =========================================================

def get_all_fighting_styles() -> List[Dict[str, Any]]:
    """Возвращает список всех боевых стилей"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM fighting_styles ORDER BY name")
            columns = ['id', 'name', 'description']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_fighting_style_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о стиле по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, description FROM fighting_styles WHERE name = %s", (name,))
            row = cur.fetchone()
            if row:
                return {'id': row[0], 'name': row[1], 'description': row[2]}
    return None


# =========================================================
# 8. РАБОТА С ТАИНСТВЕННЫМИ ВОЗВАНИЯМИ
# =========================================================

def get_all_invocations(level: int = 1) -> List[Dict[str, Any]]:
    """Возвращает список доступных возваний для колдуна"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, level_required, effect, requires_pact_boon, pact_boon_type
                FROM invocations 
                WHERE level_required <= %s
                ORDER BY level_required, name
            """, (level,))
            columns = ['id', 'name', 'level_required', 'effect', 'requires_pact_boon', 'pact_boon_type']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_invocation_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Получает информацию о возвании по названию"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, level_required, effect, requires_pact_boon, pact_boon_type 
                FROM invocations WHERE name = %s
            """, (name,))
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0], 'name': row[1], 'level_required': row[2],
                    'effect': row[3], 'requires_pact_boon': row[4], 'pact_boon_type': row[5]
                }
    return None


# =========================================================
# 9. РАБОТА С ЗАКЛИНАНИЯМИ
# =========================================================

def get_spells_for_class(class_name: str, level: int = 1, is_cantrip: bool = None) -> List[Dict[str, Any]]:
    """Возвращает заклинания для указанного класса"""
    class_data = get_class_by_name(class_name)
    if not class_data:
        return []

    with get_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT s.id, s.name, s.level, s.is_cantrip, s.description
                FROM spells s
                JOIN class_spells cs ON s.id = cs.spell_id
                WHERE cs.class_id = %s AND cs.is_available = TRUE
            """
            params = [class_data['id']]

            if is_cantrip is not None:
                query += " AND s.is_cantrip = %s"
                params.append(is_cantrip)

            if not is_cantrip:
                query += " AND s.level <= %s"
                params.append(level)

            query += " ORDER BY s.level, s.name"

            cur.execute(query, params)
            columns = ['id', 'name', 'level', 'is_cantrip', 'description']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


def get_cantrips_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Возвращает заговоры для указанного класса"""
    return get_spells_for_class(class_name, is_cantrip=True)


def get_level1_spells_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Возвращает заклинания 1 уровня для указанного класса"""
    return get_spells_for_class(class_name, level=1, is_cantrip=False)


# =========================================================
# 10. ВАЛИДАЦИЯ
# =========================================================

def validate_name(name: str) -> Tuple[bool, str]:
    """Проверяет имя персонажа"""
    if not name or len(name.strip()) == 0:
        return False, "❌ Имя не может быть пустым"
    if len(name) > 50:
        return False, "❌ Имя слишком длинное (максимум 50 символов)"
    if len(name) < 2:
        return False, "❌ Имя слишком короткое (минимум 2 символа)"
    return True, "✅ Имя корректно"


def validate_race(race: str) -> Tuple[bool, str]:
    """Проверяет расу"""
    races = get_race_list()
    if race not in races:
        return False, f"❌ Раса '{race}' не существует"
    return True, "✅ Раса корректна"


def validate_class(class_name: str) -> Tuple[bool, str]:
    """Проверяет класс"""
    classes = get_class_list()
    if class_name not in classes:
        return False, f"❌ Класс '{class_name}' не существует"
    return True, "✅ Класс корректен"


def validate_background(background: str) -> Tuple[bool, str]:
    """Проверяет предысторию"""
    backgrounds = get_background_list()
    if background not in backgrounds:
        return False, f"❌ Предыстория '{background}' не существует"
    return True, "✅ Предыстория корректна"


def validate_stats(stats: Dict[str, int]) -> Tuple[bool, str]:
    """Проверяет характеристики"""
    required_stats = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]

    for stat in required_stats:
        if stat not in stats:
            return False, f"❌ Характеристика {stat} отсутствует"
        if not (1 <= stats[stat] <= 30):
            return False, f"❌ {stat} должно быть от 1 до 30"

    total = sum(stats.values())
    if total > 90:
        return False, f"⚠️ Сумма характеристик ({total}) очень высокая"

    return True, "✅ Характеристики корректны"


def validate_character(name: str, class_name: str, race: str, background: str, stats: Dict[str, int]) -> Tuple[
    bool, str]:
    """Полная валидация персонажа"""
    valid, msg = validate_name(name)
    if not valid:
        return False, msg
    valid, msg = validate_race(race)
    if not valid:
        return False, msg
    valid, msg = validate_class(class_name)
    if not valid:
        return False, msg
    valid, msg = validate_background(background)
    if not valid:
        return False, msg
    valid, msg = validate_stats(stats)
    if not valid:
        return False, msg
    return True, "✅ Персонаж валиден"


# =========================================================
# 11. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (для совместимости)
# =========================================================

def get_race_traits_list(race: str, subrace: Optional[str] = None) -> List[str]:
    """Возвращает особенности расы (заглушка для совместимости)"""
    traits = []
    race_info = get_race_info(race)
    traits.extend(race_info.get('traits', []))
    if subrace and 'subraces' in race_info and subrace in race_info['subraces']:
        trait = race_info['subraces'][subrace].get('trait')
        if trait:
            traits.append(trait)
    return traits


def get_class_features(class_name: str, level: int = 1) -> List[str]:
    """Возвращает особенности класса на уровне (заглушка)"""
    class_data = get_class_by_name(class_name)
    if not class_data:
        return []

    # Базовые особенности для 1 уровня
    features = []
    if class_data['is_spellcaster']:
        features.append("Заклинания")

    # Специфические для класса
    class_specific = {
        "Бард": ["Вдохновение барда"],
        "Варвар": ["Ярость", "Бездоспешная защита"],
        "Воин": ["Второе дыхание"],
        "Волшебник": ["Книга заклинаний", "Восстановление магии"],
        "Друид": ["Друидийский язык"],
        "Жрец": ["Божественное вдохновение"],
        "Колдун": ["Потусторонний покровитель", "Магия договора"],
        "Монах": ["Боевые искусства", "Бездоспешная защита"],
        "Паладин": ["Божественное чутьё", "Наложение рук"],
        "Плут": ["Скрытая атака", "Взломщик"],
        "Следопыт": ["Избранный враг", "Следопыт"],
        "Чародей": ["Магия крови"],
        "Артефактор": ["Магия артефактов"]
    }

    return features + class_specific.get(class_name, [])


def format_background_for_display(background: str) -> str:
    """Форматирует информацию о предыстории для отображения"""
    bg = get_background_by_name(background)
    if not bg:
        return f"❌ Предыстория '{background}' не найдена"

    info = f"📜 **{bg['name']}**\n\n"
    info += f"**Описание:** {bg['description'][:200]}...\n\n"
    info += f"**Черта:** {bg['trait']}\n"
    info += f"**Характеристики:** +2 к {bg['characteristics'][0]}, +1 к {bg['characteristics'][1]}\n"
    info += f"**Навыки:** {', '.join(bg['skills'])}\n"
    info += f"**Инструменты:** {bg['tools']}\n\n"
    info += f"**Снаряжение А:** {bg['equipment_a'][:100]}...\n"
    info += f"**Снаряжение Б:** {bg['equipment_b'][:100]}..."
    return info


# =========================================================
# 12. ФУНКЦИИ ДЛЯ ОБНОВЛЁННОГО ПОРЯДКА СОЗДАНИЯ
# =========================================================

def get_class_skill_choices(class_name: str) -> List[str]:
    """Возвращает список доступных навыков для класса"""
    skills_map = {
        "Бард": ["Акробатика", "Выступление", "Обман", "Убеждение", "Проницательность", "Скрытность"],
        "Воин": ["Атлетика", "Запугивание", "Восприятие", "Выживание"],
        "Волшебник": ["Тайная магия", "История", "Религия", "Расследование"],
        "Жрец": ["Религия", "Медицина", "Убеждение", "Проницательность"],
        "Плут": ["Ловкость рук", "Скрытность", "Обман", "Восприятие", "Расследование"],
    }
    return skills_map.get(class_name, ["Восприятие", "Скрытность"])


def get_subclasses_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Возвращает подклассы для указанного класса"""
    class_data = get_class_by_name(class_name)
    if not class_data:
        return []

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, level_acquired, description, features
                FROM subclasses 
                WHERE class_id = %s
                ORDER BY level_acquired, name
            """, (class_data['id'],))
            columns = ['id', 'name', 'level_acquired', 'description', 'features']
            return [dict(zip(columns, row)) for row in cur.fetchall()]


# =========================================================
# ТЕСТИРОВАНИЕ
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ D&D LOGIC MODULE (PostgreSQL версия)")
    print("=" * 60)

    # 1. Тест рас
    print("\n1. Список рас:")
    for race in get_race_list()[:5]:
        print(f"   • {race}")

    # 2. Тест классов
    print("\n2. Список классов:")
    for cls in get_class_list():
        print(f"   • {cls}")

    # 3. Тест предысторий
    print("\n3. Список предысторий:")
    for bg in get_background_list()[:5]:
        print(f"   • {bg}")

    # 4. Тест характеристик с бонусами от предыстории
    print("\n4. Тест характеристик (5.5e):")
    stats = get_initial_stats("Солдат")
    print(f"   Солдат (бонусы: +2 Сила, +1 Ловкость): {stats}")

    stats = get_initial_stats("Мудрец")
    print(f"   Мудрец (бонусы: +2 Телосложение, +1 Интеллект): {stats}")

    # 5. Тест заклинаний
    print("\n5. Тест заклинаний:")
    spells = get_level1_spells_for_class("Волшебник")
    for spell in spells[:5]:
        print(f"   • {spell['name']}")

    print("\n✅ Модуль dnd_logic.py готов к работе!")