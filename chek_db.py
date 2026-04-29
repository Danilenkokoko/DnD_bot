# fill_class_skills.py
import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "DND_DB"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "").strip(),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432))
}

# Данные о навыках классов
skills_data = {
    "Артефактор": {
        "skills": ["Восприятие", "История", "Ловкость рук", "Медицина", "Природа", "Расследование", "Тайная магия"],
        "choices": 2
    },
    "Бард": {
        "skills": None,
        "choices": 3
    },
    "Варвар": {
        "skills": ["Атлетика", "Восприятие", "Выживание", "Запугивание", "Обращение с животными", "Природа"],
        "choices": 2
    },
    "Воин": {
        "skills": ["Акробатика", "Атлетика", "Восприятие", "Выживание", "Запугивание", "История", "Обращение с животными", "Проницательность", "Убеждение"],
        "choices": 2
    },
    "Волшебник": {
        "skills": ["История", "Медицина", "Природа", "Проницательность", "Расследование", "Религия", "Тайная магия"],
        "choices": 2
    },
    "Друид": {
        "skills": ["Восприятие", "Выживание", "Медицина", "Обращение с животными", "Природа", "Проницательность", "Религия", "Тайная магия"],
        "choices": 2
    },
    "Жрец": {
        "skills": ["История", "Медицина", "Проницательность", "Религия", "Убеждение"],
        "choices": 2
    },
    "Колдун": {
        "skills": ["Запугивание", "История", "Обман", "Природа", "Расследование", "Религия", "Тайная магия"],
        "choices": 2
    },
    "Монах": {
        "skills": ["Акробатика", "Атлетика", "История", "Проницательность", "Религия", "Скрытность"],
        "choices": 2
    },
    "Паладин": {
        "skills": ["Атлетика", "Запугивание", "Медицина", "Проницательность", "Религия", "Убеждение"],
        "choices": 2
    },
    "Плут": {
        "skills": ["Акробатика", "Атлетика", "Восприятие", "Запугивание", "Ловкость рук", "Обман", "Проницательность", "Расследование", "Скрытность", "Убеждение"],
        "choices": 4
    },
    "Следопыт": {
        "skills": ["Атлетика", "Восприятие", "Выживание", "Обращение с животными", "Природа", "Проницательность", "Расследование", "Скрытность"],
        "choices": 3
    },
    "Чародей": {
        "skills": ["Запугивание", "Обман", "Проницательность", "Религия", "Тайная магия", "Убеждение"],
        "choices": 2
    },
}

def add_columns_if_not_exists(conn):
    """Добавляет колонки skills и skill_choices, если их нет"""
    with conn.cursor() as cur:
        # Проверяем колонку skills
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'classes' AND column_name = 'skills'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE classes ADD COLUMN skills JSONB DEFAULT '[]'")
            print("✅ Добавлена колонка skills")
        else:
            print("ℹ️ Колонка skills уже существует")
        
        # Проверяем колонку skill_choices
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'classes' AND column_name = 'skill_choices'
        """)
        if not cur.fetchone():
            cur.execute("ALTER TABLE classes ADD COLUMN skill_choices INTEGER DEFAULT 2")
            print("✅ Добавлена колонка skill_choices")
        else:
            print("ℹ️ Колонка skill_choices уже существует")
        conn.commit()

def update_class_skills():
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        
        # Добавляем колонки
        add_columns_if_not_exists(conn)
        
        # Заполняем данные
        with conn.cursor() as cur:
            for class_name, data in skills_data.items():
                skills_json = json.dumps(data["skills"]) if data["skills"] else '[]'
                cur.execute(
                    "UPDATE classes SET skills = %s, skill_choices = %s WHERE name = %s",
                    (skills_json, data["choices"], class_name)
                )
                print(f"Обновлён {class_name}: выборов={data['choices']}")
            conn.commit()
        print("✅ Данные успешно загружены!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_class_skills()
