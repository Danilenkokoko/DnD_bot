# migrate_fix_ranger_spells.py
"""
Миграция для исправления следопыта (Ranger):
- Установить is_spellcaster = TRUE
- Установить spells_count_level1 = 2
- Привязать список заклинаний следопыта к классу
"""

import logging
from dotenv import load_dotenv
from db import get_connection

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RANGER_SPELLS = [
    'Град шипов', 'Добряника', 'Дружба с животными', 'Лечение ран',
    'Метка охотника', 'Обнаружение болезней и ядов', 'Обнаружение магии',
    'Опутывание', 'Опутывающий удар', 'Прыжок', 'Разговор с животными',
    'Сигнал тревоги', 'Скороход', 'Туманное облако'
]

def run_migration():
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Проверить наличие колонки class_list в таблице spells, добавить если нет
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='spells' AND column_name='class_list'
            """)
            if not cur.fetchone():
                cur.execute("ALTER TABLE spells ADD COLUMN class_list TEXT[]")
                logger.info("✅ Добавлена колонка class_list в таблицу spells")

            # 2. Обновить класс Следопыт
            cur.execute("""
                UPDATE classes 
                SET is_spellcaster = TRUE, 
                    spells_count_level1 = 2 
                WHERE name = 'Следопыт'
            """)
            logger.info("✅ Следопыт: is_spellcaster = TRUE, spells_count_level1 = 2")

            # 3. Привязать заклинания к классу (добавить 'Следопыт' в class_list)
            for spell in RANGER_SPELLS:
                cur.execute("""
                    UPDATE spells 
                    SET class_list = array_append(class_list, %s)
                    WHERE name = %s AND NOT (%s = ANY(class_list))
                """, ('Следопыт', spell, 'Следопыт'))
            logger.info(f"✅ Привязано {len(RANGER_SPELLS)} заклинаний к классу Следопыт")

            # 4. Убедиться, что заклинание "Метка охотника" существует и имеет уровень 1
            cur.execute("SELECT id FROM spells WHERE name = 'Метка охотника'")
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO spells (name, level, description, is_cantrip, class_list)
                    VALUES ('Метка охотника', 1, 'Вы выбираете существо, которое можете видеть в пределах дистанции, и мистическим образом метите его. Пока заклинание активно, каждый раз, когда вы попадаете по отмеченной цели атакой оружием, вы наносите дополнительный урон 1к6 того же типа, что и оружие.', FALSE, ARRAY['Следопыт'])
                """)
                logger.info("✅ Добавлено заклинание 'Метка охотника'")

            conn.commit()
            logger.info("🎉 Миграция для следопыта завершена")

if __name__ == "__main__":
    run_migration()