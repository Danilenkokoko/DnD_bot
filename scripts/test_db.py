# test_db_connection.py
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "DND_DB"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "").strip(),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}

print("=" * 50)
print("ДИАГНОСТИКА ПОДКЛЮЧЕНИЯ К БД")
print("=" * 50)
print(f"Host: {DB_CONFIG['host']}")
print(f"Port: {DB_CONFIG['port']}")
print(f"Database: {DB_CONFIG['dbname']}")
print(f"User: {DB_CONFIG['user']}")
print(f"Password: {'***' if DB_CONFIG['password'] else 'Empty'}")
print("=" * 50)

try:
    print("\n1. Пробуем подключиться...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("   ✅ Подключение успешно!")

    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"   ✅ PostgreSQL версия: {version[:50]}...")

    cur.execute("SELECT current_database();")
    db_name = cur.fetchone()[0]
    print(f"   ✅ Текущая БД: {db_name}")

    conn.close()
    print("\n✅ БД готова к работе!")

except psycopg2.OperationalError as e:
    print(f"\n❌ ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
    print("\n🔧 РЕШЕНИЯ:")
    print("   1. Запустите PostgreSQL: sudo service postgresql start (Linux) или через службы Windows")
    print("   2. Проверьте .env файл - убедитесь что пароль правильный")
    print("   3. Создайте базу данных: sudo -u postgres createdb DND_DB")
    print("   4. Проверьте что PostgreSQL слушает порт 5432")

except Exception as e:
    print(f"\n❌ ДРУГАЯ ОШИБКА: {e}")