import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432))
}

class_images = {
    "Артефактор": "artifactor.jpg",
    "Бард": "bard.jpg",
    "Варвар": "barbarian.jpg",
    "Воин": "fighter.jpg",
    "Волшебник": "wizard.jpg",
    "Друид": "druid.jpg",
    "Жрец": "cleric.jpg",
    "Колдун": "warlock.jpg",
    "Монах": "monk.jpg",
    "Паладин": "paladin.jpg",
    "Плут": "rogue.jpg",
    "Следопыт": "ranger.jpg",
    "Чародей": "socerer.jpg"
}

race_images = {
    "Аасимар": "aasimar.jpg",
    "Гном": "gnom.jpg",
    "Голиаф": "goliaf.jpg",
    "Дампир": "dampir.jpg",
    "Дварф": "dwarf.jpg",
    "Драконорожденный": "dragonborn.jpg",
    "Калаштар": "kalashtar.jpg",
    "Кованный": "kowanniy.jpg",
    "Кхоравар": "khorawar.jpg",
    "Орк": "ork.jpg",
    "Полурослик": "halfman.jpg",
    "Тифлинг": "tifling.jpg",
    "Человек": "man.jpg",
    "Ченжлинг": "changaling.jpg",
    "Шифтер": "shifter.jpg",
    "Эльф": "elf.jpg"
}


def update_paths():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    for name, filename in class_images.items():
        path = f"images/classes/{filename}"
        cur.execute("UPDATE classes SET image_path = %s WHERE name = %s", (path, name))
        print(f"✅ Class {name} -> {path}")

    for name, filename in race_images.items():
        path = f"images/races/{filename}"
        cur.execute("UPDATE races SET image_path = %s WHERE name = %s", (path, name))
        print(f"✅ Race {name} -> {path}")

    conn.commit()
    cur.close()
    conn.close()
    print("\n🎉 Все пути к картинкам успешно обновлены!")


if __name__ == "__main__":
    update_paths()