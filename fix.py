# fix_all_missing_data.py
from db import get_connection


def fix_all():
    with get_connection() as conn:
        with conn.cursor() as cur:
            print("1. Добавление боевых стилей...")
            styles = [
                ("Дуэлянт", "Когда вы атакуете оружием в одной руке и не используете щит, вы добавляете +2 к урону."),
                ("Защита",
                 "Когда существо, которое вы видите, атакует цель, отличную от вас, вы можете реакцией дать помеху на эту атаку."),
                ("Оборона", "Вы получаете +1 к Классу Брони, если носите броню."),
                ("Перехват",
                 "Когда существо атакует цель в пределах 5 футов от вас, вы можете реакцией уменьшить урон на 1d10 + бонус мастерства."),
                ("Сражение без оружия", "Ваши безоружные удары наносят 1d6 + модификатор силы урона."),
                ("Сражение большим оружием",
                 "При атаке двуручным оружием вы можете перебросить единицы и двойки на кубиках урона."),
                ("Сражение вслепую", "Вы получаете слепое зрение в радиусе 10 футов."),
                ("Сражение двумя оружиями",
                 "При атаке лёгким оружием вы можете добавить модификатор характеристики к урону бонусной атаки."),
                ("Сражение метательным оружием", "Вы можете выхватить метательное оружие как часть атаки им."),
                ("Стрельба", "Вы получаете +2 к броскам атаки дальнобойным оружием.")
            ]

            for name, desc in styles:
                cur.execute("""
                    INSERT INTO fighting_styles (name, description)
                    VALUES (%s, %s)
                    ON CONFLICT (name) DO NOTHING
                """, (name, desc))
            print("   ✅ Боевые стили добавлены")

            print("2. Настройка количества оружейных приёмов для классов...")
            masteries_data = [
                ("Воин", 3),
                ("Варвар", 2),
                ("Паладин", 2),
                ("Следопыт", 2),
                ("Плут", 1),
            ]

            for class_name, count in masteries_data:
                cur.execute("UPDATE classes SET masteries_count = %s WHERE name = %s", (count, class_name))
                print(f"   ✅ {class_name}: {count} приёма(ов)")

            print("3. Связывание боевых стилей с классами...")

            # Получаем ID классов
            cur.execute("SELECT id, name FROM classes WHERE name IN ('Воин', 'Паладин', 'Следопыт', 'Варвар')")
            classes = {row[1]: row[0] for row in cur.fetchall()}

            # Получаем ID стилей
            cur.execute("SELECT id, name FROM fighting_styles")
            styles_dict = {row[1]: row[0] for row in cur.fetchall()}

            # Воин - все стили
            warrior_styles = ["Дуэлянт", "Защита", "Оборона", "Перехват", "Сражение без оружия",
                              "Сражение большим оружием", "Сражение вслепую", "Сражение двумя оружиями",
                              "Сражение метательным оружием", "Стрельба"]

            # Паладин
            paladin_styles = ["Дуэлянт", "Защита", "Оборона", "Перехват", "Сражение без оружия",
                              "Сражение большим оружием", "Сражение вслепую"]

            # Следопыт
            ranger_styles = ["Дуэлянт", "Защита", "Оборона", "Сражение вслепую",
                             "Сражение двумя оружиями", "Сражение метательным оружием", "Стрельба"]

            # Варвар - ограниченный набор
            barbarian_styles = ["Оборона", "Сражение без оружия", "Сражение большим оружием",
                                "Сражение вслепую", "Сражение двумя оружиями"]

            class_styles = {
                "Воин": warrior_styles,
                "Паладин": paladin_styles,
                "Следопыт": ranger_styles,
                "Варвар": barbarian_styles
            }

            for class_name, style_list in class_styles.items():
                if class_name in classes:
                    for style_name in style_list:
                        if style_name in styles_dict:
                            cur.execute("""
                                INSERT INTO class_fighting_styles (class_id, style_id)
                                VALUES (%s, %s)
                                ON CONFLICT (class_id, style_id) DO NOTHING
                            """, (classes[class_name], styles_dict[style_name]))
                    print(f"   ✅ {class_name}: {len([s for s in style_list if s in styles_dict])} стилей")

            conn.commit()
            print("\n✅ Все данные успешно добавлены!")


if __name__ == "__main__":
    fix_all()