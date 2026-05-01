# migrate_character_fields.py
"""
Migration script to add origin_feat and alignment columns to characters table,
and remove deprecated selected_equipment_choice column.
Run this script once after updating the code.
"""

import logging
from db import get_connection, return_connection

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_migration():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Add origin_feat column if not exists
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'characters' AND column_name = 'origin_feat'
            """)
            if not cur.fetchone():
                cur.execute("ALTER TABLE characters ADD COLUMN origin_feat VARCHAR(100) DEFAULT ''")
                logger.info("✅ Added column 'origin_feat' to characters table")
            else:
                logger.info("⏩ Column 'origin_feat' already exists, skipping")

            # 2. Add alignment column if not exists
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'characters' AND column_name = 'alignment'
            """)
            if not cur.fetchone():
                cur.execute("ALTER TABLE characters ADD COLUMN alignment VARCHAR(30) DEFAULT 'Нейтральный'")
                logger.info("✅ Added column 'alignment' to characters table")
            else:
                logger.info("⏩ Column 'alignment' already exists, skipping")

            # 3. Drop selected_equipment_choice column if it exists
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'characters' AND column_name = 'selected_equipment_choice'
            """)
            if cur.fetchone():
                cur.execute("ALTER TABLE characters DROP COLUMN selected_equipment_choice")
                logger.info("✅ Dropped deprecated column 'selected_equipment_choice'")
            else:
                logger.info("⏩ Column 'selected_equipment_choice' does not exist, nothing to drop")

            conn.commit()
            logger.info("🎉 Migration completed successfully")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        return_connection(conn)


if __name__ == "__main__":
    run_migration()