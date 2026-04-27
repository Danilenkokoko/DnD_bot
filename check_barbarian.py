# check_warrior_data.py
from db import get_connection


def check():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, masteries_count FROM classes WHERE name IN ('Воин', 'Варвар', 'Плут')")
            for row in cur.fetchall():
                print(f"{row[0]}: masteries_count={row[1]}")

            cur.execute(
                "SELECT c.name, COUNT(fs.id) FROM class_fighting_styles cfs JOIN classes c ON cfs.class_id = c.id JOIN fighting_styles fs ON cfs.style_id = fs.id WHERE c.name IN ('Воин', 'Варвар') GROUP BY c.name")
            for row in cur.fetchall():
                print(f"{row[0]}: {row[1]} боевых стилей")


if __name__ == "__main__":
    check()