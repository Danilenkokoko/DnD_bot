# check_env.py
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

print("=== ПРОВЕРКА .env ===")
print(f"DB_NAME = '{os.getenv('DB_NAME')}'")
print(f"DB_USER = '{os.getenv('DB_USER')}'")
print(f"DB_HOST = '{os.getenv('DB_HOST')}'")

print("\n=== ПРОВЕРКА ПОДКЛЮЧЕНИЯ ===")
try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=5432,
        connect_timeout=5
    )
    print("✅ ПОДКЛЮЧЕНИЕ УСПЕШНО!")

    cur = conn.cursor()
    cur.execute("SELECT current_database();")
    print(f"✅ Текущая БД: {cur.fetchone()[0]}")

    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public';")
    tables = [t[0] for t in cur.fetchall()]
    print(f"✅ Таблицы: {tables}")

    conn.close()

except psycopg2.OperationalError as e:
    print(f"❌ ОШИБКА: {e}")
    print("\nВозможные причины:")
    print("1. PostgreSQL не запущен")
    print("2. Неверное имя БД в .env")
    print("3. Неверный пароль")
    print("4. Хост указан неверно")

print("\n=== РЕШЕНИЕ ===")
print("Если имена не совпадают - исправьте .env или создайте БД вручную:")
print("sudo -u postgres createdb " + os.getenv("DB_NAME", "dnd_db"))