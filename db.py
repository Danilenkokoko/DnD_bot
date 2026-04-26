# db.py
"""
D&D 5.5e (2024) Database Module
Модуль для работы с PostgreSQL базой данных
Поддерживает все таблицы для D&D 5.5e, включая оружие, заклинания, броню и снаряжение классов
"""

import psycopg2
import os
import logging
import json
from dotenv import load_dotenv
from psycopg2.extras import Json, RealDictCursor
from contextlib import contextmanager
from typing import Dict, Any, List, Optional

# ---------------- CONFIG ----------------
load_dotenv(encoding="utf-8")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "DND_DB"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": (os.getenv("DB_PASSWORD") or "").strip(),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "connect_timeout": 5
}

# Проверка env
for key, value in DB_CONFIG.items():
    if key == "connect_timeout":
        continue
    if not value:
        raise ValueError(f"❌ Не задана переменная окружения: {key}")

logger.info(f"📊 Настройки БД: host={DB_CONFIG['host']}, dbname={DB_CONFIG['dbname']}, user={DB_CONFIG['user']}")


# ---------------- CONNECTION ----------------
@contextmanager
def get_connection():
    """Создаёт подключение к базе данных"""
    conn = None
    try:
        logger.debug("🔄 Попытка подключения к БД...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        logger.debug("✅ Подключение к БД установлено")
        yield conn
        conn.commit()
    except psycopg2.OperationalError as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Ошибка подключения к БД: {e}")
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"❌ Ошибка БД: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()
            logger.debug("🔌 Соединение с БД закрыто")


# ---------------- INIT DATABASE ----------------
def init_database():
    """Создаёт все таблицы если они не существуют (D&D 5.5e)"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # ===== 1. ТАБЛИЦА РАС (без бонусов к характеристикам в 5.5e!) =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS races (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) UNIQUE NOT NULL,
                        speed INTEGER DEFAULT 30,
                        size VARCHAR(20) DEFAULT 'Средний',
                        description TEXT,
                        image_path VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица races готова")

                # ===== 2. ТАБЛИЦА ПОДРАС =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS subraces (
                        id SERIAL PRIMARY KEY,
                        race_id INTEGER NOT NULL REFERENCES races(id) ON DELETE CASCADE,
                        name VARCHAR(50) NOT NULL,
                        trait VARCHAR(255),
                        description TEXT,
                        extra_speed INTEGER DEFAULT 0,
                        extra_traits JSONB DEFAULT '[]',
                        UNIQUE(race_id, name)
                    )
                """)
                logger.info("✅ Таблица subraces готова")

                # ===== 3. ТАБЛИЦА КЛАССОВ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS classes (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) UNIQUE NOT NULL,
                        hit_die INTEGER NOT NULL CHECK (hit_die IN (6, 8, 10, 12)),
                        primary_stats JSONB NOT NULL,
                        saving_throws JSONB NOT NULL,
                        skill_choices INTEGER DEFAULT 2,
                        description TEXT,
                        image_path VARCHAR(255),
                        is_spellcaster BOOLEAN DEFAULT FALSE,
                        spellcasting_ability VARCHAR(3),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица classes готова")

                # ===== 4. ТАБЛИЦА ПОДКЛАССОВ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS subclasses (
                        id SERIAL PRIMARY KEY,
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        name VARCHAR(50) NOT NULL,
                        level_acquired INTEGER DEFAULT 1,
                        description TEXT,
                        features JSONB DEFAULT '[]',
                        UNIQUE(class_id, name)
                    )
                """)
                logger.info("✅ Таблица subclasses готова")

                # ===== 5. ТАБЛИЦА ПРЕДЫСТОРИЙ (В 5.5e ОНИ ДАЮТ БОНУСЫ К ХАРАКТЕРИСТИКАМ!) =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS backgrounds (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) UNIQUE NOT NULL,
                        characteristic1 VARCHAR(3) NOT NULL,
                        characteristic2 VARCHAR(3) NOT NULL,
                        characteristic3 VARCHAR(3) NOT NULL,
                        trait VARCHAR(255) NOT NULL,
                        skills JSONB NOT NULL,
                        tools VARCHAR(255),
                        equipment_a TEXT NOT NULL,
                        equipment_b TEXT NOT NULL,
                        description TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица backgrounds готова")

                # ===== 6. ТАБЛИЦА ЗАКЛИНАНИЙ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS spells (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        level INTEGER DEFAULT 0,
                        school VARCHAR(50),
                        casting_time VARCHAR(50),
                        range VARCHAR(50),
                        components VARCHAR(50),
                        duration VARCHAR(100),
                        description TEXT,
                        is_cantrip BOOLEAN DEFAULT FALSE,
                        is_ritual BOOLEAN DEFAULT FALSE,
                        requires_concentration BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица spells готова")

                # ===== 7. СВЯЗЬ КЛАССОВ С ЗАКЛИНАНИЯМИ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS class_spells (
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        spell_id INTEGER NOT NULL REFERENCES spells(id) ON DELETE CASCADE,
                        is_available BOOLEAN DEFAULT TRUE,
                        PRIMARY KEY (class_id, spell_id)
                    )
                """)
                logger.info("✅ Таблица class_spells готова")

                # ===== 8. ТАБЛИЦА РЕКОМЕНДОВАННЫХ ЗАКЛИНАНИЙ (для новичков) =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS recommended_spells (
                        id SERIAL PRIMARY KEY,
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        spell_id INTEGER NOT NULL REFERENCES spells(id) ON DELETE CASCADE,
                        is_cantrip BOOLEAN DEFAULT FALSE,
                        priority INTEGER DEFAULT 1,
                        UNIQUE(class_id, spell_id)
                    )
                """)
                logger.info("✅ Таблица recommended_spells готова")

                # ===== 9. ТАБЛИЦА ОРУЖИЯ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS weapons (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL UNIQUE,
                        category VARCHAR(20) NOT NULL, -- simple, martial
                        damage_dice VARCHAR(10), -- 1d6, 1d8
                        damage_type VARCHAR(20), -- slashing, piercing, bludgeoning
                        properties JSONB DEFAULT '[]', -- ["light", "finesse"]
                        suitable_masteries JSONB DEFAULT '[]', -- ["Выпад", "Подавление"]
                        detailed_masteries JSONB DEFAULT '[]', -- детальные приёмы из файла
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица weapons готова")

                # ===== 10. ДОСТУПНОЕ ОРУЖИЕ ПО КЛАССАМ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS class_weapons (
                        id SERIAL PRIMARY KEY,
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        weapon_category VARCHAR(20), -- simple, martial, all
                        weapon_id INTEGER REFERENCES weapons(id) ON DELETE CASCADE,
                        UNIQUE(class_id, weapon_id)
                    )
                """)
                logger.info("✅ Таблица class_weapons готова")

                # ===== 11. ТАБЛИЦА ОРУЖЕЙНЫХ ПРИЁМОВ (Weapon Mastery) =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS weapon_masteries (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL UNIQUE,
                        trigger_condition TEXT NOT NULL,
                        effect TEXT NOT NULL,
                        weapons TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица weapon_masteries готова")

                # ===== 12. ТАБЛИЦА БРОНИ (НОВАЯ!) =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS armor (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL UNIQUE,
                        ac_base INTEGER NOT NULL,
                        ac_modifier VARCHAR(10) DEFAULT 'dex',
                        has_shield BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица armor готова")

                # ===== 13. ТАБЛИЦА СНАРЯЖЕНИЯ ПО КЛАССАМ (НОВАЯ!) =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS class_equipment (
                        id SERIAL PRIMARY KEY,
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        choice VARCHAR(1),
                        armor VARCHAR(50),
                        weapon VARCHAR(50),
                        secondary_weapon VARCHAR(50),
                        other_items TEXT,
                        coins INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(class_id, choice)
                    )
                """)
                logger.info("✅ Таблица class_equipment готова")

                # ===== 14. ТАБЛИЦА БОЕВЫХ СТИЛЕЙ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS fighting_styles (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(50) NOT NULL UNIQUE,
                        description TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица fighting_styles готова")

                # ===== 15. ДОСТУПНЫЕ БОЕВЫЕ СТИЛИ ПО КЛАССАМ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS class_fighting_styles (
                        id SERIAL PRIMARY KEY,
                        class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                        style_id INTEGER NOT NULL REFERENCES fighting_styles(id) ON DELETE CASCADE,
                        UNIQUE(class_id, style_id)
                    )
                """)
                logger.info("✅ Таблица class_fighting_styles готова")

                # ===== 16. ТАБЛИЦА ТАИНСТВЕННЫХ ВОЗВАНИЙ =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS invocations (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        level_required INTEGER DEFAULT 1,
                        effect TEXT NOT NULL,
                        requires_pact_boon BOOLEAN DEFAULT FALSE,
                        pact_boon_type VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица invocations готова")

                # ===== 17. ТАБЛИЦА ПЕРСОНАЖЕЙ (обновлённая структура для 5.5e) =====
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS characters (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        race_id INTEGER REFERENCES races(id),
                        subrace_id INTEGER REFERENCES subraces(id),
                        class_id INTEGER REFERENCES classes(id),
                        subclass_id INTEGER REFERENCES subclasses(id),
                        background_id INTEGER REFERENCES backgrounds(id),
                        level INTEGER DEFAULT 1,
                        experience INTEGER DEFAULT 0,
                        str INTEGER DEFAULT 10,
                        dex INTEGER DEFAULT 10,
                        con INTEGER DEFAULT 10,
                        int INTEGER DEFAULT 10,
                        wis INTEGER DEFAULT 10,
                        cha INTEGER DEFAULT 10,
                        hp INTEGER DEFAULT 0,
                        ac INTEGER DEFAULT 10,
                        speed INTEGER DEFAULT 30,
                        selected_skills JSONB DEFAULT '[]',
                        selected_masteries JSONB DEFAULT '[]',
                        selected_fighting_style VARCHAR(50),
                        selected_invocations JSONB DEFAULT '[]',
                        selected_spells JSONB DEFAULT '[]',
                        selected_weapon VARCHAR(50),
                        selected_armor VARCHAR(50),
                        selected_equipment_choice VARCHAR(1),
                        backstory TEXT,
                        image_file_id VARCHAR(255),
                        alignment VARCHAR(20) DEFAULT 'Нейтральное',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                logger.info("✅ Таблица characters готова")

                # ===== ИНДЕКСЫ =====
                cur.execute("CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_characters_class_id ON characters(class_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_characters_race_id ON characters(race_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_characters_background_id ON characters(background_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_class_spells_class_id ON class_spells(class_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_class_spells_spell_id ON class_spells(spell_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_subraces_race_id ON subraces(race_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_subclasses_class_id ON subclasses(class_id)")
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_recommended_spells_class_id ON recommended_spells(class_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_weapons_name ON weapons(name)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_class_weapons_class_id ON class_weapons(class_id)")
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_class_fighting_styles_class_id ON class_fighting_styles(class_id)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_armor_name ON armor(name)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_class_equipment_class_id ON class_equipment(class_id)")
                logger.info("✅ Все индексы созданы")

                conn.commit()

    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации таблиц: {e}")
        raise


# =========================================================
# 1. СОХРАНЕНИЕ ПЕРСОНАЖА (ОБНОВЛЁННАЯ ВЕРСИЯ)
# =========================================================

def save_character(
        user_id: int,
        name: str,
        race_id: Optional[int] = None,
        subrace_id: Optional[int] = None,
        class_id: Optional[int] = None,
        subclass_id: Optional[int] = None,
        background_id: Optional[int] = None,
        level: int = 1,
        experience: int = 0,
        stats: Optional[Dict[str, int]] = None,
        hp: int = 0,
        ac: int = 10,
        speed: int = 30,
        selected_skills: Optional[List[str]] = None,
        selected_masteries: Optional[List[str]] = None,
        selected_fighting_style: Optional[str] = None,
        selected_invocations: Optional[List[str]] = None,
        selected_spells: Optional[List[str]] = None,
        selected_weapon: Optional[str] = None,
        selected_armor: Optional[str] = None,
        selected_equipment_choice: str = "A",
        backstory: str = "",
        image_file_id: Optional[str] = None,
        alignment: str = "Нейтральное"
) -> int:
    """
    Сохраняет персонажа в базу данных (обновлённая версия для 5.5e)
    """
    if stats is None:
        stats = {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10}
    if selected_skills is None:
        selected_skills = []
    if selected_masteries is None:
        selected_masteries = []
    if selected_invocations is None:
        selected_invocations = []
    if selected_spells is None:
        selected_spells = []

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO characters (
                    user_id, name, race_id, subrace_id, class_id, subclass_id,
                    background_id, level, experience, str, dex, con, int, wis, cha,
                    hp, ac, speed, selected_skills, selected_masteries,
                    selected_fighting_style, selected_invocations, selected_spells,
                    selected_weapon, selected_armor, selected_equipment_choice, backstory, image_file_id, alignment
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id, name, race_id, subrace_id, class_id, subclass_id,
                background_id, level, experience,
                stats.get("STR", 10), stats.get("DEX", 10), stats.get("CON", 10),
                stats.get("INT", 10), stats.get("WIS", 10), stats.get("CHA", 10),
                hp, ac, speed,
                Json(selected_skills), Json(selected_masteries),
                selected_fighting_style, Json(selected_invocations), Json(selected_spells),
                selected_weapon, selected_armor, selected_equipment_choice, backstory, image_file_id, alignment
            ))

            char_id = cur.fetchone()[0]
            logger.info(f"✅ Персонаж сохранён: ID={char_id}, Name={name}")
            return char_id


# =========================================================
# 2. ПОЛУЧЕНИЕ ПЕРСОНАЖЕЙ
# =========================================================

def get_user_characters(user_id: int) -> List[Dict[str, Any]]:
    """Возвращает всех персонажей пользователя"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT c.id, c.name, c.level, c.hp, c.ac, c.created_at,
                       cls.name as class_name, r.name as race_name, bg.name as background_name
                FROM characters c
                LEFT JOIN classes cls ON c.class_id = cls.id
                LEFT JOIN races r ON c.race_id = r.id
                LEFT JOIN backgrounds bg ON c.background_id = bg.id
                WHERE c.user_id = %s
                ORDER BY c.id DESC
            """, (user_id,))
            return cur.fetchall()


def get_character_by_id(char_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает полную информацию о персонаже по ID"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT c.*, 
                       cls.name as class_name, cls.hit_die, cls.primary_stats, cls.saving_throws,
                       r.name as race_name, r.speed as race_speed, r.size as race_size,
                       bg.name as background_name, bg.trait as background_trait
                FROM characters c
                LEFT JOIN classes cls ON c.class_id = cls.id
                LEFT JOIN races r ON c.race_id = r.id
                LEFT JOIN backgrounds bg ON c.background_id = bg.id
                WHERE c.id = %s
            """, (char_id,))
            return cur.fetchone()


def get_character_by_id_and_user(char_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает персонажа по ID и ID пользователя (для проверки прав)"""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT c.*, 
                       cls.name as class_name,
                       r.name as race_name,
                       bg.name as background_name
                FROM characters c
                LEFT JOIN classes cls ON c.class_id = cls.id
                LEFT JOIN races r ON c.race_id = r.id
                LEFT JOIN backgrounds bg ON c.background_id = bg.id
                WHERE c.id = %s AND c.user_id = %s
            """, (char_id, user_id))
            return cur.fetchone()


# =========================================================
# 3. ОБНОВЛЕНИЕ ПЕРСОНАЖА
# =========================================================

def update_character_level(char_id: int, new_level: int) -> bool:
    """Обновляет уровень персонажа"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE characters 
                SET level = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_level, char_id))
            return cur.rowcount > 0


def update_character_hp(char_id: int, new_hp: int) -> bool:
    """Обновляет HP персонажа"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE characters 
                SET hp = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_hp, char_id))
            return cur.rowcount > 0


def update_character_stats(char_id: int, stats: Dict[str, int]) -> bool:
    """Обновляет характеристики персонажа"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE characters 
                SET str = %s, dex = %s, con = %s, int = %s, wis = %s, cha = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                stats.get("STR", 10), stats.get("DEX", 10), stats.get("CON", 10),
                stats.get("INT", 10), stats.get("WIS", 10), stats.get("CHA", 10),
                char_id
            ))
            return cur.rowcount > 0


def update_character_backstory(char_id: int, backstory: str) -> bool:
    """Обновляет историю персонажа"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE characters 
                SET backstory = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (backstory, char_id))
            return cur.rowcount > 0


def update_character_image(char_id: int, image_file_id: str) -> bool:
    """Обновляет картинку персонажа"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE characters 
                SET image_file_id = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (image_file_id, char_id))
            return cur.rowcount > 0


def update_character_experience(char_id: int, experience: int) -> bool:
    """Обновляет опыт персонажа и автоматически повышает уровень при необходимости"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT level FROM characters WHERE id = %s", (char_id,))
            result = cur.fetchone()
            if not result:
                return False
            current_level = result[0]

            exp_thresholds = {1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500}
            new_level = current_level
            for lvl, exp_needed in exp_thresholds.items():
                if experience >= exp_needed and lvl > new_level:
                    new_level = lvl

            cur.execute("""
                UPDATE characters 
                SET experience = %s, level = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (experience, new_level, char_id))
            return cur.rowcount > 0


# =========================================================
# 4. УДАЛЕНИЕ ПЕРСОНАЖА
# =========================================================

def delete_character(char_id: int, user_id: int) -> bool:
    """Удаляет персонажа (только если он принадлежит пользователю)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM characters
                WHERE id = %s AND user_id = %s
            """, (char_id, user_id))

            deleted = cur.rowcount > 0
            if deleted:
                logger.info(f"🗑️ Персонаж удалён: ID={char_id}, User={user_id}")
            return deleted


# =========================================================
# 5. СТАТИСТИКА
# =========================================================

def get_user_characters_count(user_id: int) -> int:
    """Возвращает количество персонажей пользователя"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM characters WHERE user_id = %s", (user_id,))
            return cur.fetchone()[0]


def get_total_characters_count() -> int:
    """Возвращает общее количество персонажей в базе"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM characters")
            return cur.fetchone()[0]


# =========================================================
# 6. РАБОТА С ПРЕДЫСТОРИЯМИ (ИЗ БД)
# =========================================================

def get_all_backgrounds_from_db() -> List[Dict[str, Any]]:
    """Получает все предыстории из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name, description FROM backgrounds ORDER BY name")
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить предыстории: {e}")
        return []


def get_background_from_db(background_name: str) -> Optional[Dict[str, Any]]:
    """Получает предысторию по имени из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, characteristic1, characteristic2, characteristic3,
                           trait, skills, tools, equipment_a, equipment_b, description
                    FROM backgrounds WHERE name = %s
                """, (background_name,))
                return cur.fetchone()
    except Exception as e:
        logger.warning(f"Не удалось загрузить предысторию {background_name}: {e}")
        return None


def get_background_names() -> List[str]:
    """Возвращает список названий предысторий"""
    backgrounds = get_all_backgrounds_from_db()
    return [bg["name"] for bg in backgrounds]


# =========================================================
# 7. РАБОТА С РАСАМИ (ИЗ БД)
# =========================================================

def get_all_races_from_db() -> List[Dict[str, Any]]:
    """Получает все расы из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name, speed, size, description, image_path FROM races ORDER BY name")
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить расы: {e}")
        return []


def get_race_from_db(race_name: str) -> Optional[Dict[str, Any]]:
    """Получает расу по имени из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name, speed, size, description, image_path FROM races WHERE name = %s",
                            (race_name,))
                return cur.fetchone()
    except Exception as e:
        logger.warning(f"Не удалось загрузить расу {race_name}: {e}")
        return None


def get_subraces_from_db(race_name: str) -> List[Dict[str, Any]]:
    """Получает подрасы для указанной расы"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT s.id, s.name, s.trait, s.description, s.extra_speed
                    FROM subraces s
                    JOIN races r ON s.race_id = r.id
                    WHERE r.name = %s
                    ORDER BY s.name
                """, (race_name,))
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить подрасы для {race_name}: {e}")
        return []


# =========================================================
# 8. РАБОТА С КЛАССАМИ (ИЗ БД)
# =========================================================

def get_all_classes_from_db() -> List[Dict[str, Any]]:
    """Получает все классы из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, hit_die, primary_stats, saving_throws, 
                           skill_choices, description, image_path, is_spellcaster, spellcasting_ability
                    FROM classes ORDER BY name
                """)
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить классы: {e}")
        return []


def get_class_from_db(class_name: str) -> Optional[Dict[str, Any]]:
    """Получает класс по имени из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, hit_die, primary_stats, saving_throws, 
                           skill_choices, description, image_path, is_spellcaster, spellcasting_ability
                    FROM classes WHERE name = %s
                """, (class_name,))
                return cur.fetchone()
    except Exception as e:
        logger.warning(f"Не удалось загрузить класс {class_name}: {e}")
        return None


# =========================================================
# 9. РАБОТА С БРОНЁЙ
# =========================================================

def get_armor_by_name(armor_name: str) -> Optional[Dict[str, Any]]:
    """Получает броню по названию"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name, ac_base, ac_modifier, has_shield FROM armor WHERE name = %s",
                            (armor_name,))
                return cur.fetchone()
    except Exception as e:
        logger.warning(f"Не удалось загрузить броню {armor_name}: {e}")
        return None


def get_all_armor() -> List[Dict[str, Any]]:
    """Получает все виды брони"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name, ac_base, ac_modifier, has_shield FROM armor ORDER BY name")
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить броню: {e}")
        return []


# =========================================================
# 10. РАБОТА СО СНАРЯЖЕНИЕМ КЛАССОВ
# =========================================================

def get_class_equipment_from_db(class_name: str, choice: Optional[str] = None) -> List[Dict[str, Any]]:
    """Получает снаряжение для класса"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return []
                class_id = class_result["id"]

                if choice:
                    cur.execute("""
                        SELECT class_id, choice, armor, weapon, secondary_weapon, other_items, coins
                        FROM class_equipment 
                        WHERE class_id = %s AND choice = %s
                    """, (class_id, choice))
                else:
                    cur.execute("""
                        SELECT class_id, choice, armor, weapon, secondary_weapon, other_items, coins
                        FROM class_equipment 
                        WHERE class_id = %s
                        ORDER BY choice
                    """, (class_id,))
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить снаряжение для класса {class_name}: {e}")
        return []


# =========================================================
# 11. РАБОТА С ОРУЖИЕМ
# =========================================================

def get_weapons_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Возвращает список оружия, доступного для класса"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return []
                class_id = class_result["id"]

                cur.execute("""
                    SELECT w.id, w.name, w.category, w.damage_dice, w.damage_type, w.properties, w.suitable_masteries
                    FROM weapons w
                    JOIN class_weapons cw ON w.id = cw.weapon_id
                    WHERE cw.class_id = %s
                    ORDER BY w.category, w.name
                """, (class_id,))
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить оружие для класса {class_name}: {e}")
        return []


def get_masteries_for_weapon(weapon_name: str) -> List[str]:
    """Возвращает список подходящих оружейных приёмов для указанного оружия"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT suitable_masteries FROM weapons WHERE name = %s", (weapon_name,))
                result = cur.fetchone()
                if result and result[0]:
                    if isinstance(result[0], list):
                        return result[0]
                    try:
                        return json.loads(result[0])
                    except:
                        return []
                return []
    except Exception as e:
        logger.warning(f"Не удалось загрузить приёмы для оружия {weapon_name}: {e}")
        return []


def get_detailed_masteries_for_weapon(weapon_name: str) -> List[Dict[str, Any]]:
    """Возвращает детальные оружейные приёмы для указанного оружия из поля detailed_masteries"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT detailed_masteries FROM weapons WHERE name = %s", (weapon_name,))
                result = cur.fetchone()
                if result and result[0]:
                    if isinstance(result[0], list):
                        return result[0]
                    try:
                        return json.loads(result[0])
                    except:
                        return []
                return []
    except Exception as e:
        logger.warning(f"Не удалось загрузить детальные приёмы для оружия {weapon_name}: {e}")
        return []


def get_all_weapon_masteries_from_db() -> List[Dict[str, Any]]:
    """Получает все базовые оружейные приёмы из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name, trigger_condition, effect, weapons FROM weapon_masteries ORDER BY name")
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить оружейные приёмы: {e}")
        return []


# =========================================================
# 12. РАБОТА С БОЕВЫМИ СТИЛЯМИ
# =========================================================

def get_fighting_styles_for_class(class_name: str) -> List[Dict[str, Any]]:
    """Возвращает боевые стили, доступные для класса (с фильтрацией)"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return []
                class_id = class_result["id"]

                cur.execute("""
                    SELECT fs.id, fs.name, fs.description
                    FROM fighting_styles fs
                    JOIN class_fighting_styles cfs ON fs.id = cfs.style_id
                    WHERE cfs.class_id = %s
                    ORDER BY fs.name
                """, (class_id,))
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить боевые стили для класса {class_name}: {e}")
        return []


def get_all_fighting_styles_from_db() -> List[Dict[str, Any]]:
    """Получает все боевые стили из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id, name, description FROM fighting_styles ORDER BY name")
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить боевые стили: {e}")
        return []


# =========================================================
# 13. РАБОТА С ВОЗВАНИЯМИ
# =========================================================

def get_all_invocations_from_db(level: int = 1) -> List[Dict[str, Any]]:
    """Получает доступные возвания для колдуна из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, level_required, effect, requires_pact_boon, pact_boon_type
                    FROM invocations 
                    WHERE level_required <= %s
                    ORDER BY level_required, name
                """, (level,))
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить возвания: {e}")
        return []


# =========================================================
# 14. РАБОТА С ЗАКЛИНАНИЯМИ
# =========================================================

def get_spells_for_class_from_db(class_name: str, level: int = 1, is_cantrip: bool = None) -> List[Dict[str, Any]]:
    """Получает заклинания для указанного класса из БД"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return []
                class_id = class_result["id"]

                query = """
                    SELECT s.id, s.name, s.level, s.is_cantrip, s.description, s.school
                    FROM spells s
                    JOIN class_spells cs ON s.id = cs.spell_id
                    WHERE cs.class_id = %s AND cs.is_available = TRUE
                """
                params = [class_id]

                if is_cantrip is not None:
                    query += " AND s.is_cantrip = %s"
                    params.append(is_cantrip)

                if not is_cantrip:
                    query += " AND s.level <= %s"
                    params.append(level)

                query += " ORDER BY s.level, s.name"

                cur.execute(query, params)
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить заклинания для {class_name}: {e}")
        return []


def get_recommended_spells_from_db(class_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """Получает рекомендованные заклинания для класса (кантрипы и 1 уровень)"""
    result = {"cantrips": [], "level1": []}

    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return result
                class_id = class_result["id"]

                cur.execute("""
                    SELECT s.id, s.name, s.level, s.is_cantrip, s.description
                    FROM spells s
                    JOIN recommended_spells rs ON s.id = rs.spell_id
                    WHERE rs.class_id = %s
                    ORDER BY rs.priority, s.name
                """, (class_id,))

                spells = cur.fetchall()
                for spell in spells:
                    if spell.get("is_cantrip"):
                        result["cantrips"].append(spell)
                    else:
                        result["level1"].append(spell)

                return result
    except Exception as e:
        logger.warning(f"Не удалось загрузить рекомендованные заклинания для {class_name}: {e}")
        return result


# =========================================================
# 15. РАБОТА С ПОДКЛАССАМИ
# =========================================================

def get_subclasses_for_class_from_db(class_name: str, level: int = 1) -> List[Dict[str, Any]]:
    """Возвращает подклассы для указанного класса, доступные на определённом уровне"""
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT id FROM classes WHERE name = %s", (class_name,))
                class_result = cur.fetchone()
                if not class_result:
                    return []
                class_id = class_result["id"]

                cur.execute("""
                    SELECT id, name, level_acquired, description, features
                    FROM subclasses 
                    WHERE class_id = %s AND level_acquired <= %s
                    ORDER BY level_acquired, name
                """, (class_id, level))
                return cur.fetchall()
    except Exception as e:
        logger.warning(f"Не удалось загрузить подклассы для класса {class_name}: {e}")
        return []


# =========================================================
# 16. БЭКАП И ВОССТАНОВЛЕНИЕ
# =========================================================

def backup_all_characters():
    """Копирует всех персонажей из characters в characters_backup"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS characters_backup (LIKE characters INCLUDING ALL)
                """)

                cur.execute("TRUNCATE TABLE characters_backup")

                cur.execute("""
                    INSERT INTO characters_backup 
                    SELECT * FROM characters
                """)

                logger.info(f"✅ Создана резервная копия {cur.rowcount} персонажей")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании резервной копии: {e}")


def restore_from_backup():
    """Восстанавливает персонажей из резервной копии"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'characters_backup'
                    )
                """)
                if not cur.fetchone()[0]:
                    logger.warning("⚠️ Таблица characters_backup не существует")
                    return

                cur.execute("TRUNCATE TABLE characters")

                cur.execute("""
                    INSERT INTO characters 
                    SELECT * FROM characters_backup
                """)

                logger.info(f"✅ Восстановлено {cur.rowcount} персонажей из резервной копии")
    except Exception as e:
        logger.error(f"❌ Ошибка при восстановлении из резервной копии: {e}")


# =========================================================
# 17. МИГРАЦИЯ
# =========================================================

def migrate_database():
    """Миграция существующей базы данных (добавление новых полей для 5.5e)"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                new_columns = [
                    ("selected_armor", "VARCHAR(50)"),
                ]

                for col_name, col_type in new_columns:
                    try:
                        cur.execute(f"""
                            ALTER TABLE characters 
                            ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                        """)
                        logger.info(f"✅ Добавлена колонка: {col_name}")
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось добавить {col_name}: {e}")

                conn.commit()
                logger.info("✅ Миграция базы данных завершена")
    except Exception as e:
        logger.warning(f"⚠️ Ошибка миграции: {e}")


# =========================================================
# ТЕСТИРОВАНИЕ
# =========================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🐉 ТЕСТ МОДУЛЯ DB.PY (D&D 5.5e)")
    print("=" * 60)

    try:
        init_database()
        migrate_database()

        with get_connection() as conn:
            with conn.cursor() as cur:
                tables = ["races", "subraces", "classes", "subclasses", "backgrounds",
                          "spells", "class_spells", "recommended_spells", "weapons",
                          "class_weapons", "weapon_masteries", "armor", "class_equipment",
                          "fighting_styles", "class_fighting_styles", "invocations", "characters"]

                print("\n📋 СУЩЕСТВУЮЩИЕ ТАБЛИЦЫ:")
                for table in tables:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cur.fetchone()[0]
                        print(f"   • {table}: {count} записей")
                    except Exception:
                        print(f"   • {table}: таблица не создана")

        print("\n✅ Модуль db.py готов к использованию!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")