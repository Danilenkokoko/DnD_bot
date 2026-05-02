# check_updates.py
"""
Скрипт для проверки всех выполненных изменений в боте D&D.
Проверяет базу данных, наличие новых файлов и корректность импортов.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_db():
    """Проверяет наличие новых таблиц и колонок в БД"""
    logger.info("🔍 Проверка базы данных...")
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Проверка таблицы languages
                cur.execute("SELECT to_regclass('public.languages')")
                if cur.fetchone()[0]:
                    cur.execute("SELECT COUNT(*) FROM languages")
                    cnt = cur.fetchone()[0]
                    logger.info(f"✅ Таблица languages существует, записей: {cnt}")
                else:
                    logger.warning("❌ Таблица languages не найдена")

                # Проверка таблицы warlock_pacts
                cur.execute("SELECT to_regclass('public.warlock_pacts')")
                if cur.fetchone()[0]:
                    logger.info("✅ Таблица warlock_pacts существует")
                else:
                    logger.warning("❌ Таблица warlock_pacts не найдена")

                # Проверка наличия новых колонок в characters
                cur.execute("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'characters'
                """)
                columns = {row[0] for row in cur.fetchall()}
                required_columns = [
                    'druid_order', 'cleric_order', 'warlock_pact',
                    'rogue_expertise', 'rogue_extra_language', 'auto_spells',
                    'pact_tome_cantrips', 'pact_tome_rituals', 'pact_blade_weapon',
                    'origin_feat', 'alignment'
                ]
                missing = [col for col in required_columns if col not in columns]
                if missing:
                    logger.warning(f"❌ Отсутствуют колонки: {missing}")
                else:
                    logger.info("✅ Все необходимые колонки в characters присутствуют")

                # Проверка на устаревшую колонку
                if 'selected_equipment_choice' in columns:
                    logger.warning("⚠️ Устаревшая колонка selected_equipment_choice всё ещё существует")
                else:
                    logger.info("✅ Устаревшая колонка удалена или отсутствует")

    except Exception as e:
        logger.error(f"Ошибка при проверке БД: {e}")


def check_files():
    """Проверяет наличие ключевых файлов с обновлениями"""
    logger.info("\n🔍 Проверка файлов проекта...")
    required_files = [
        'strings.py',
        'states/character_states.py',
        'handlers/character_handlers.py',
        'keyboards/character_keyboards.py',
        'services/character_service.py',
        'services/spell_service.py',
        'repositories/character_repository.py',
        'utils/message_utils.py'
    ]
    for file in required_files:
        if os.path.exists(file):
            logger.info(f"✅ {file} найден")
        else:
            logger.warning(f"❌ {file} не найден")


def check_imports():
    """Проверяет, что новые импорты работают (без запуска бота)"""
    logger.info("\n🔍 Проверка импортов...")
    try:
        from strings import (
            DRUID_ORDER_GUIDE, CLERIC_ORDER_PROTECTOR, WARLOCK_PACT_TOME,
            FEATURE_MENDING, FEATURE_BARDIC_INSPIRATION
        )
        logger.info("✅ strings.py импортируется корректно")
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта из strings.py: {e}")

    try:
        from states.character_states import CreateCharacter
        # Проверяем наличие новых состояний
        attrs = dir(CreateCharacter)
        required_states = ['druid_order_select', 'cleric_order_select', 'warlock_pact_select']
        missing_states = [s for s in required_states if s not in attrs]
        if missing_states:
            logger.warning(f"❌ В character_states отсутствуют: {missing_states}")
        else:
            logger.info("✅ Все новые состояния в character_states присутствуют")
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта states: {e}")

    try:
        from services.spell_service import SpellSelectionService
        # Проверяем наличие метода _ensure_selector (приватный)
        if hasattr(SpellSelectionService, '_ensure_selector'):
            logger.info("✅ SpellSelectionService содержит _ensure_selector")
        else:
            logger.warning("❌ SpellSelectionService не имеет _ensure_selector")
    except ImportError as e:
        logger.error(f"❌ Ошибка импорта spell_service: {e}")


def check_env():
    """Проверяет переменные окружения"""
    logger.info("\n🔍 Проверка .env...")
    required_vars = ['BOT_TOKEN', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    for var in required_vars:
        val = os.getenv(var)
        if val:
            logger.info(f"✅ {var} задан")
        else:
            logger.warning(f"❌ {var} не задан или пуст")
    # Дополнительная проверка пароля
    if os.getenv('DB_PASSWORD'):
        logger.info("✅ Пароль БД не пустой")
    else:
        logger.warning("❌ DB_PASSWORD отсутствует или пуст")


if __name__ == "__main__":
    logger.info("🚀 Запуск проверки обновлений D&D бота")
    check_env()
    check_db()
    check_files()
    check_imports()
    logger.info("\n✅ Проверка завершена")