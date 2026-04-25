# classes_data.py
"""
D&D 5e Classes Data Module
Модуль с данными о классах для D&D 5 редакции
Поддерживает 13 классов с их умениями по уровням
"""

from typing import Dict, Any, List, Optional

CLASSES_DATA: Dict[str, Dict[str, Any]] = {
    "Артефактор": {
        "hit_die": 8,
        "primary_stats": ["INT"],
        "saving_throws": ["CON", "INT"],
        "skills": ["Arcana", "History", "Investigation", "Medicine", "Perception", "Sleight of Hand"],
        "skill_choices": 2,
        "equipment": ["Light Crossbow", "Leather Armor", "Thieves' Tools", "Simple Weapon"],
        "spellcasting": True,
        "spellcasting_ability": "INT",
        "description": "Мастер магических изобретений и артефактов",
        "features": {
            1: ["Владение инструментами", "Магия артефактов"],
            2: ["Инфузия предметов"],
            3: ["Специализация артефактора", "Черта"],
            4: ["Увеличение характеристик"],
            5: ["Дополнительная атака"],
            6: ["Инфузия предметов (2)"],
            10: ["Магический предмет"],
            20: ["Душа артефакта"]
        }
    },
    "Бард": {
        "hit_die": 8,
        "primary_stats": ["CHA"],
        "saving_throws": ["DEX", "CHA"],
        "skills": ["Acrobatics", "Animal Handling", "Arcana", "Athletics", "Deception", "History",
                   "Insight", "Intimidation", "Investigation", "Medicine", "Nature", "Perception",
                   "Performance", "Persuasion", "Religion", "Sleight of Hand", "Stealth", "Survival"],
        "skill_choices": 3,
        "equipment": ["Rapier", "Dagger", "Entertainer's Pack", "Leather Armor", "Lute"],
        "spellcasting": True,
        "spellcasting_ability": "CHA",
        "description": "Вдохновляющий исполнитель, черпающий силу из музыки и историй",
        "features": {
            1: ["Вдохновение барда", "Заклинания"],
            2: ["Песнь отдыха", "Черта"],
            3: ["Колледж барда", "Специализация"],
            4: ["Увеличение характеристик"],
            5: ["Источник вдохновения", "Кости вдохновения (d8)"],
            6: ["Контрчары", "Колледж барда (2)"],
            10: ["Кости вдохновения (d10)", "Песнь отдыха (2)"],
            20: ["Эпическое вдохновение"]
        }
    },
    "Варвар": {
        "hit_die": 12,
        "primary_stats": ["STR", "CON"],
        "saving_throws": ["STR", "CON"],
        "skills": ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"],
        "skill_choices": 2,
        "equipment": ["Greataxe", "Two Handaxes", "Explorer's Pack", "Javelins"],
        "spellcasting": False,
        "description": "Дикий воин, питающийся яростью в бою",
        "features": {
            1: ["Ярость", "Бездоспешная защита"],
            2: ["Свирепая атака", "Чувство опасности"],
            3: ["Путь варвара"],
            4: ["Увеличение характеристик"],
            5: ["Быстрое передвижение", "Дополнительная атака"],
            7: ["Звериное чутьё"],
            9: ["Брутальный критический урон"],
            11: ["Неистовая ярость"],
            15: ["Постоянная ярость"],
            20: ["Беспредельная ярость"]
        }
    },
    "Воин": {
        "hit_die": 10,
        "primary_stats": ["STR", "DEX"],
        "saving_throws": ["STR", "CON"],
        "skills": ["Acrobatics", "Animal Handling", "Athletics", "History", "Insight",
                   "Intimidation", "Perception", "Survival"],
        "skill_choices": 2,
        "equipment": ["Chain Mail", "Longsword", "Shield", "Light Crossbow"],
        "spellcasting": False,
        "description": "Мастер боя, владеющий всеми видами оружия и доспехов",
        "features": {
            1: ["Боевой стиль", "Второе дыхание"],
            2: ["Порыв действия"],
            3: ["Архетип воина"],
            4: ["Увеличение характеристик"],
            5: ["Дополнительная атака"],
            6: ["Увеличение характеристик (2)"],
            9: ["Непоколебимость"],
            11: ["Дополнительная атака (2)"],
            15: ["Порыв действия (2)"],
            20: ["Дополнительная атака (3)"]
        }
    },
    "Волшебник": {
        "hit_die": 6,
        "primary_stats": ["INT"],
        "saving_throws": ["INT", "WIS"],
        "skills": ["Arcana", "History", "Insight", "Investigation", "Medicine", "Religion"],
        "skill_choices": 2,
        "equipment": ["Quarterstaff", "Spellbook", "Component Pouch", "Explorer's Pack"],
        "spellcasting": True,
        "spellcasting_ability": "INT",
        "description": "Таинственный заклинатель, черпающий силу из магии",
        "features": {
            1: ["Книга заклинаний", "Восстановление магии"],
            2: ["Магическая традиция"],
            3: ["Магическая традиция (2)"],
            4: ["Увеличение характеристик"],
            6: ["Магическая традиция (3)"],
            10: ["Магическая традиция (4)"],
            14: ["Магическая традиция (5)"],
            18: ["Мастер заклинаний"],
            20: ["Великий волшебник"]
        }
    },
    "Друид": {
        "hit_die": 8,
        "primary_stats": ["WIS"],
        "saving_throws": ["INT", "WIS"],
        "skills": ["Arcana", "Animal Handling", "Insight", "Medicine", "Nature", "Perception",
                   "Religion", "Survival"],
        "skill_choices": 2,
        "equipment": ["Wooden Shield", "Scimitar", "Druidic Focus", "Explorer's Pack"],
        "spellcasting": True,
        "spellcasting_ability": "WIS",
        "description": "Хранитель природы, черпающий силу из диких земель",
        "features": {
            1: ["Друидийский язык", "Заклинания"],
            2: ["Дикая форма", "Круг друидов"],
            4: ["Увеличение характеристик"],
            6: ["Дикая форма (2)", "Круг друидов (2)"],
            8: ["Дикая форма (3)"],
            10: ["Круг друидов (3)"],
            14: ["Дикая форма (4)"],
            18: ["Вечное тело"],
            20: ["Великий друид"]
        }
    },
    "Жрец": {
        "hit_die": 8,
        "primary_stats": ["WIS"],
        "saving_throws": ["WIS", "CHA"],
        "skills": ["History", "Insight", "Medicine", "Persuasion", "Religion"],
        "skill_choices": 2,
        "equipment": ["Mace", "Chain Shirt", "Holy Symbol", "Priest's Pack"],
        "spellcasting": True,
        "spellcasting_ability": "WIS",
        "description": "Служитель богов, направляющий божественную силу",
        "features": {
            1: ["Божественное вдохновение", "Заклинания"],
            2: ["Канал божественной энергии"],
            3: ["Божественный домен"],
            4: ["Увеличение характеристик"],
            5: ["Уничтожение нежити"],
            6: ["Канал божественной энергии (2)", "Божественный домен (2)"],
            8: ["Уничтожение нежити (2)", "Божественный домен (3)"],
            10: ["Божественное вмешательство"],
            14: ["Уничтожение нежити (3)"],
            20: ["Великое божественное вмешательство"]
        }
    },
    "Колдун": {
        "hit_die": 8,
        "primary_stats": ["CHA"],
        "saving_throws": ["WIS", "CHA"],
        "skills": ["Arcana", "Deception", "History", "Intimidation", "Investigation", "Nature", "Religion"],
        "skill_choices": 2,
        "equipment": ["Light Crossbow", "Arcane Focus", "Scholar's Pack", "Leather Armor"],
        "spellcasting": True,
        "spellcasting_ability": "CHA",
        "description": "Заклинатель, заключивший сделку с потусторонним существом",
        "features": {
            1: ["Потусторонний покровитель", "Магия договора"],
            2: ["Эльдричное заклинание", "Мистические тайны"],
            3: ["Дар покровителя"],
            4: ["Увеличение характеристик"],
            5: ["Мистические тайны (2)"],
            6: ["Дар покровителя (2)"],
            10: ["Дар покровителя (3)"],
            11: ["Мистические тайны (3)"],
            14: ["Дар покровителя (4)"],
            20: ["Великий колдун"]
        }
    },
    "Монах": {
        "hit_die": 8,
        "primary_stats": ["DEX", "WIS"],
        "saving_throws": ["STR", "DEX"],
        "skills": ["Acrobatics", "Athletics", "History", "Insight", "Religion", "Stealth"],
        "skill_choices": 2,
        "equipment": ["Shortsword", "Dart", "Dungeoneer's Pack"],
        "spellcasting": False,
        "description": "Мастер боевых искусств, использующий дисциплину и силу духа",
        "features": {
            1: ["Боевые искусства", "Бездоспешная защита"],
            2: ["Очки ки", "Стремительный удар"],
            3: ["Монашеская традиция", "Отражение снарядов"],
            4: ["Увеличение характеристик", "Замедленное падение"],
            5: ["Лавина ударов", "Ошеломляющий удар"],
            6: ["Магический кулак", "Монашеская традиция (2)"],
            14: ["Алмазная душа"],
            18: ["Пустота"],
            20: ["Совершенная душа"]
        }
    },
    "Паладин": {
        "hit_die": 10,
        "primary_stats": ["STR", "CHA"],
        "saving_throws": ["WIS", "CHA"],
        "skills": ["Athletics", "Insight", "Intimidation", "Medicine", "Persuasion", "Religion"],
        "skill_choices": 2,
        "equipment": ["Chain Mail", "Longsword", "Shield", "Holy Symbol"],
        "spellcasting": True,
        "spellcasting_ability": "CHA",
        "description": "Священный воин, объединяющий боевые навыки и божественную магию",
        "features": {
            1: ["Божественное чутьё", "Наложение рук"],
            2: ["Боевой стиль", "Божественная кара", "Заклинания"],
            3: ["Божественное здоровье", "Клятва паладина"],
            4: ["Увеличение характеристик"],
            5: ["Дополнительная атака"],
            6: ["Аура защиты"],
            10: ["Аура храбрости"],
            14: ["Очищающее касание"],
            18: ["Аура улучшений"],
            20: ["Святой"]
        }
    },
    "Плут": {
        "hit_die": 8,
        "primary_stats": ["DEX"],
        "saving_throws": ["DEX", "INT"],
        "skills": ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation",
                   "Perception", "Performance", "Persuasion", "Sleight of Hand", "Stealth"],
        "skill_choices": 4,
        "equipment": ["Two Daggers", "Shortsword", "Thieves' Tools", "Burglar's Pack"],
        "spellcasting": False,
        "description": "Ловкий и скрытный искатель приключений",
        "features": {
            1: ["Скрытая атака", "Взломщик", "Воровской жаргон"],
            2: ["Ловкие действия"],
            3: ["Архетип плута"],
            4: ["Увеличение характеристик"],
            5: ["Уклонение"],
            6: ["Экспертиза"],
            7: ["Чутьё"],
            11: ["Надёжный талант"],
            14: ["Ослепительное уклонение"],
            18: ["Неуловимый"],
            20: ["Удача вора"]
        }
    },
    "Следопыт": {
        "hit_die": 10,
        "primary_stats": ["DEX", "WIS"],
        "saving_throws": ["STR", "DEX"],
        "skills": ["Animal Handling", "Athletics", "Insight", "Investigation", "Nature",
                   "Perception", "Stealth", "Survival"],
        "skill_choices": 3,
        "equipment": ["Longbow", "Scale Mail", "Two Handaxes", "Explorer's Pack"],
        "spellcasting": True,
        "spellcasting_ability": "WIS",
        "description": "Охотник и следопыт, защищающий границы цивилизации",
        "features": {
            1: ["Избранный враг", "Следопыт"],
            2: ["Боевой стиль", "Заклинания"],
            3: ["Архетип следопыта", "Первобытное чутьё"],
            4: ["Увеличение характеристик"],
            5: ["Дополнительная атака"],
            6: ["Избранный враг (2)", "Следопыт (2)"],
            10: ["Скрытность в природе"],
            14: ["Уклонение"],
            18: ["Улучшенное чутьё"],
            20: ["Первобытный мститель"]
        }
    },
    "Чародей": {
        "hit_die": 6,
        "primary_stats": ["CHA"],
        "saving_throws": ["CON", "CHA"],
        "skills": ["Arcana", "Deception", "Insight", "Intimidation", "Persuasion", "Religion"],
        "skill_choices": 2,
        "equipment": ["Light Crossbow", "Arcane Focus", "Dungeoneer's Pack", "Two Daggers"],
        "spellcasting": True,
        "spellcasting_ability": "CHA",
        "description": "Заклинатель с врождённым магическим даром",
        "features": {
            1: ["Магия крови", "Происхождение чародея"],
            2: ["Источник магии"],
            3: ["Метаморфия"],
            4: ["Увеличение характеристик"],
            5: ["Источник магии (2)"],
            6: ["Происхождение чародея (2)"],
            10: ["Происхождение чародея (3)"],
            14: ["Происхождение чародея (4)"],
            18: ["Происхождение чародея (5)"],
            20: ["Чарующее восстановление"]
        }
    }
}


def get_all_classes() -> List[str]:
    """Возвращает список всех классов"""
    return list(CLASSES_DATA.keys())


def get_class_data(class_name: str) -> Dict[str, Any]:
    """Возвращает данные о классе по имени"""
    return dict(CLASSES_DATA.get(class_name, {}))


def get_class_hit_die(class_name: str) -> int:
    """Возвращает хитовый кубик класса"""
    class_data = CLASSES_DATA.get(class_name, {})
    return class_data.get("hit_die", 6)


def get_class_primary_stats(class_name: str) -> List[str]:
    """Возвращает основные характеристики класса"""
    class_data = CLASSES_DATA.get(class_name, {})
    return class_data.get("primary_stats", [])


def get_class_saving_throws(class_name: str) -> List[str]:
    """Возвращает спасброски класса"""
    class_data = CLASSES_DATA.get(class_name, {})
    return class_data.get("saving_throws", [])


def get_class_skill_choices(class_name: str) -> List[str]:
    """Возвращает список доступных навыков для выбора"""
    class_data = CLASSES_DATA.get(class_name, {})
    return class_data.get("skills", [])


def get_class_skill_count(class_name: str) -> int:
    """Возвращает количество навыков, которые может выбрать класс"""
    class_data = CLASSES_DATA.get(class_name, {})
    return class_data.get("skill_choices", 2)


def get_class_equipment(class_name: str) -> List[str]:
    """Возвращает стартовое снаряжение класса"""
    class_data = CLASSES_DATA.get(class_name, {})
    return class_data.get("equipment", [])


def get_class_spellcasting(class_name: str) -> bool:
    """Возвращает, может ли класс использовать заклинания"""
    class_data = CLASSES_DATA.get(class_name, {})
    return class_data.get("spellcasting", False)


def get_class_spellcasting_ability(class_name: str) -> Optional[str]:
    """Возвращает характеристику для колдовства"""
    class_data = CLASSES_DATA.get(class_name, {})
    return class_data.get("spellcasting_ability")


def get_class_description(class_name: str) -> str:
    """Возвращает описание класса"""
    class_data = CLASSES_DATA.get(class_name, {})
    return class_data.get("description", "Нет описания")


def get_class_features(class_name: str, level: int) -> List[str]:
    """Возвращает умения класса на определённом уровне"""
    class_data = CLASSES_DATA.get(class_name, {})
    features = class_data.get("features", {})

    # Собираем все умения до указанного уровня
    result = []
    for lvl in range(1, level + 1):
        if lvl in features:
            result.extend(features[lvl])

    return result


def get_class_features_at_level(class_name: str, level: int) -> List[str]:
    """Возвращает умения класса на конкретном уровне"""
    class_data = CLASSES_DATA.get(class_name, {})
    features = class_data.get("features", {})
    return features.get(level, [])


def get_class_max_level(class_name: str) -> int:
    """Возвращает максимальный уровень с описанными умениями"""
    class_data = CLASSES_DATA.get(class_name, {})
    features = class_data.get("features", {})
    if features:
        return max(features.keys())
    return 20


def get_classes_by_spellcasting(spellcasting: bool = True) -> List[str]:
    """Возвращает классы, которые могут использовать магию"""
    result = []
    for class_name, data in CLASSES_DATA.items():
        if data.get("spellcasting", False) == spellcasting:
            result.append(class_name)
    return result


def get_classes_by_hit_die(min_hit_die: int = 1, max_hit_die: int = 20) -> List[str]:
    """Возвращает классы с хитовым кубиком в заданном диапазоне"""
    result = []
    for class_name, data in CLASSES_DATA.items():
        hit_die = data.get("hit_die", 6)
        if min_hit_die <= hit_die <= max_hit_die:
            result.append(class_name)
    return result


def validate_class(class_name: str) -> bool:
    """Проверяет существование класса"""
    return class_name in CLASSES_DATA


def format_class_info(class_name: str) -> str:
    """
    Форматирует информацию о классе для отображения пользователю

    Args:
        class_name: название класса

    Returns:
        str: отформатированный текст
    """
    class_data = CLASSES_DATA.get(class_name, {})
    if not class_data:
        return f"❌ Класс '{class_name}' не найден"

    info = f"⚔️ **{class_name}**\n\n"
    info += f"**Описание:** {class_data.get('description', 'Нет описания')}\n\n"
    info += f"**Хитовый кубик:** d{class_data.get('hit_die', 6)}\n"
    info += f"**Основные характеристики:** {', '.join(class_data.get('primary_stats', []))}\n"
    info += f"**Спасброски:** {', '.join(class_data.get('saving_throws', []))}\n"
    info += f"**Количество навыков:** {class_data.get('skill_choices', 2)}\n"

    # Заклинания
    if class_data.get('spellcasting', False):
        spell_ability = class_data.get('spellcasting_ability', '')
        info += f"**Колдовство:** Да (характеристика: {spell_ability})\n"
    else:
        info += "**Колдовство:** Нет\n"

    # Навыки (показываем первые 8)
    skills = class_data.get('skills', [])
    if skills:
        info += f"\n**Доступные навыки ({len(skills)}):**\n"
        for skill in skills[:8]:
            info += f"  • {skill}\n"
        if len(skills) > 8:
            info += f"  • ... и {len(skills) - 8} других\n"

    return info


def format_class_level_up(class_name: str, new_level: int) -> str:
    """
    Форматирует информацию о повышении уровня

    Args:
        class_name: название класса
        new_level: новый уровень

    Returns:
        str: отформатированный текст
    """
    features = get_class_features_at_level(class_name, new_level)
    if not features:
        return f"На {new_level} уровне нет новых умений."

    info = f"**Новые умения {class_name} на {new_level} уровне:**\n"
    for feature in features:
        info += f"  • {feature}\n"

    return info


# ---------------- ТЕСТИРОВАНИЕ ----------------
if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ МОДУЛЯ CLASSES_DATA")
    print("=" * 60)

    # 1. Список всех классов
    print("\n1. Список всех классов:")
    classes = get_all_classes()
    print(f"   Всего классов: {len(classes)}")
    print(f"   {', '.join(classes)}")

    # 2. Детальная информация о каждом классе
    print("\n2. Детальная информация о классах:")
    for class_name in classes[:5]:  # Первые 5 для примера
        print(f"\n   --- {class_name} ---")
        print(f"   Хитовый кубик: d{get_class_hit_die(class_name)}")
        print(f"   Основные статы: {', '.join(get_class_primary_stats(class_name))}")
        print(f"   Спасброски: {', '.join(get_class_saving_throws(class_name))}")
        print(f"   Навыков можно выбрать: {get_class_skill_count(class_name)}")
        print(f"   Магия: {get_class_spellcasting(class_name)}")

        if get_class_spellcasting(class_name):
            print(f"   Характеристика магии: {get_class_spellcasting_ability(class_name)}")

    # 3. Тест умений по уровням
    print("\n3. Умения классов по уровням:")
    for class_name in ["Воин", "Волшебник", "Плут"]:
        print(f"\n   {class_name}:")
        for level in [1, 3, 5, 10, 20]:
            features = get_class_features_at_level(class_name, level)
            if features:
                print(f"      Уровень {level}: {', '.join(features)}")

    # 4. Тест фильтрации
    print("\n4. Фильтрация классов:")
    spellcasters = get_classes_by_spellcasting(True)
    print(f"   Классы с магией ({len(spellcasters)}): {', '.join(spellcasters[:8])}...")

    martial = get_classes_by_spellcasting(False)
    print(f"   Классы без магии ({len(martial)}): {', '.join(martial)}")

    high_hp = get_classes_by_hit_die(10, 12)
    print(f"   Классы с высоким HP (d10-d12): {', '.join(high_hp)}")

    # 5. Тест функции format_class_info
    print("\n5. Тест форматирования информации:")
    print(format_class_info("Паладин"))

    # 6. Тест валидации
    print("\n6. Тест валидации:")
    print(f"   validate_class('Воин'): {validate_class('Воин')}")
    print(f"   validate_class('НесуществующийКласс'): {validate_class('НесуществующийКласс')}")

    # 7. Статистика
    print("\n7. Статистика:")
    total_skills = sum(len(get_class_skill_choices(cls)) for cls in classes)
    total_features = sum(len(data.get("features", {})) for data in CLASSES_DATA.values())
    print(f"   Всего уникальных навыков: {total_skills}")
    print(f"   Всего умений по уровням: {total_features}")

    print("\n" + "=" * 60)
    print("✅ МОДУЛЬ CLASSES_DATA УСПЕШНО ЗАГРУЖЕН!")
    print("=" * 60)