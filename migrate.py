# migrate.py
from db import migrate_database

print("🔄 Запуск миграции базы данных...")
migrate_database()
print("✅ Миграция завершена!")