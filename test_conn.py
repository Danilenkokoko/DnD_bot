# test_conn.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

print(f"Пытаюсь подключиться к БД: {os.getenv('DB_NAME')}")

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
    cur.execute("SELECT current_database()")
    db_name = cur.fetchone()[0]
    print(f"Текущая БД: {db_name}")

    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchall()
    print(f"Таблицы: {[t[0] for t in tables]}")

    conn.close()

except psycopg2.OperationalError as e:
    print(f"❌ ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
    print("\nВозможные причины:")
    print("1. PostgreSQL не запущен")
    print("2. Неправильный пароль")
    print("3. База данных не существует")
    print("4. Пользователь не имеет прав")

except Exception as e:
    print(f"❌ ДРУГАЯ ОШИБКА: {e}")