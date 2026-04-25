# races_data.py
"""
D&D 5e Races Data Module
Модуль с данными о расах для D&D 5 редакции
Поддерживает 16 рас и их подрасы
"""

from typing import Dict, Any, List, Optional

RACES_DATA: Dict[str, Dict[str, Any]] = {
    "Аасимар": {
        "ability_bonuses": {"CHA": 2},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий", "Небесный"],
        "traits": [
            "Тёмное зрение",
            "Небесное наследие",
            "Исцеляющие руки",
            "Светоносный",
            "Сопротивление некротической и лучевой энергии"
        ],
        "subraces": {
            "Протектор": {
                "ability_bonuses": {"WIS": 1},
                "trait": "Сияющая душа",
                "description": "Протекторы используют силу света для защиты"
            },
            "Разоритель": {
                "ability_bonuses": {"CON": 1},
                "trait": "Пожирающий свет",
                "description": "Разорители черпают силу из разрушения"
            },
            "Несущий скорбь": {
                "ability_bonuses": {"STR": 1},
                "trait": "Некротический гнев",
                "description": "Несущие скорбь связаны с некротической энергией"
            }
        },
        "description": "Существа с небесной кровью, несущие свет и справедливость"
    },
    "Гном": {
        "ability_bonuses": {"INT": 2},
        "speed": 25,
        "size": "Маленький",
        "languages": ["Общий", "Гномий"],
        "traits": [
            "Тёмное зрение",
            "Гномья хитрость",
            "Искусный ремесленник"
        ],
        "subraces": {
            "Лесной гном": {
                "ability_bonuses": {"DEX": 1},
                "trait": "Разговор с мелкими зверями",
                "description": "Лесные гномы умеют общаться с животными"
            },
            "Скальный гном": {
                "ability_bonuses": {"CON": 1},
                "trait": "Сведущий в механизмах",
                "description": "Скальные гномы искусны в работе с механизмами"
            }
        },
        "description": "Маленькие, но изобретательные создания с любовью к знаниям"
    },
    "Голиаф": {
        "ability_bonuses": {"STR": 2, "CON": 1},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий", "Голиаф"],
        "traits": [
            "Природный атлет",
            "Каменное телосложение",
            "Рождённый для холода",
            "Мощное телосложение"
        ],
        "description": "Гигантоподобные существа, живущие в горах"
    },
    "Дампир": {
        "ability_bonuses": {"CON": 2, "CHA": 1},
        "speed": 35,
        "size": "Средний",
        "languages": ["Общий"],
        "traits": [
            "Тёмное зрение",
            "Смертельный укус",
            "Паучье лазание",
            "Кровопийца",
            "Неживая природа"
        ],
        "resistances": ["Некротическая"],
        "description": "Полувампиры, потомки вампиров или заражённые вампиризмом"
    },
    "Дварф": {
        "ability_bonuses": {"CON": 2},
        "speed": 25,
        "size": "Средний",
        "languages": ["Общий", "Дварфийский"],
        "traits": [
            "Тёмное зрение",
            "Дварфийская стойкость",
            "Боевое мастерство",
            "Знание камня"
        ],
        "subraces": {
            "Горный дварф": {
                "ability_bonuses": {"STR": 2},
                "trait": "Мастерство в лёгких и средних доспехах",
                "description": "Горные дварфы сильны и выносливы"
            },
            "Холмовой дварф": {
                "ability_bonuses": {"WIS": 1},
                "trait": "Дварфийская живучесть",
                "description": "Холмовые дварфы мудры и жизнерадостны"
            }
        },
        "description": "Коренастые, сильные и выносливые подгорные жители"
    },
    "Драконорожденный": {
        "ability_bonuses": {"STR": 2, "CHA": 1},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий", "Драконий"],
        "traits": [
            "Оружие дыхания",
            "Сопротивление урону",
            "Драконья внешность"
        ],
        "draconic_ancestry": [
            "Чёрный (кислота)",
            "Синий (молния)",
            "Латунный (огонь)",
            "Бронзовый (молния)",
            "Медный (кислота)",
            "Золотой (огонь)",
            "Зелёный (яд)",
            "Красный (огонь)",
            "Серебряный (холод)",
            "Белый (холод)"
        ],
        "description": "Гуманоиды с драконьей кровью, гордые и сильные"
    },
    "Калаштар": {
        "ability_bonuses": {"WIS": 2, "CHA": 1},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий", "Небесный"],
        "traits": [
            "Псионический разум",
            "Стойкость к психике",
            "Сновидение",
            "Псионическое чутьё"
        ],
        "description": "Гуманоиды с психическими способностями, потомки беженцев из Ксориата"
    },
    "Кованный": {
        "ability_bonuses": {"CON": 2, "STR": 1},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий"],
        "traits": [
            "Конструированная стойкость",
            "Специализированный дизайн",
            "Сенсорный интерфейс",
            "Восстановление",
            "Живая броня"
        ],
        "resistances": ["Яд"],
        "immunities": ["Болезнь"],
        "description": "Искусственные существа, созданные для войны"
    },
    "Кхоравар": {
        "ability_bonuses": {"DEX": 2, "CHA": 1},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий"],
        "traits": [
            "Изменчивая природа",
            "Кхораварская ловкость",
            "Язык тела",
            "Адаптивная внешность"
        ],
        "description": "Оборотни с ограниченной способностью к смене формы"
    },
    "Орк": {
        "ability_bonuses": {"STR": 2, "CON": 1},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий", "Орочий"],
        "traits": [
            "Тёмное зрение",
            "Агрессивный",
            "Мощное телосложение",
            "Резвый отдых"
        ],
        "description": "Сильные и свирепые воины с обострёнными чувствами"
    },
    "Полурослик": {
        "ability_bonuses": {"DEX": 2},
        "speed": 25,
        "size": "Маленький",
        "languages": ["Общий", "Полурослий"],
        "traits": [
            "Везучий",
            "Храбрый",
            "Полуросливая ловкость"
        ],
        "subraces": {
            "Легконогий": {
                "ability_bonuses": {"CHA": 1},
                "trait": "Природно-незаметный",
                "description": "Легконогие полурослики умеют прятаться"
            },
            "Крепкостоп": {
                "ability_bonuses": {"CON": 1},
                "trait": "Стойкость крепкостопа",
                "description": "Крепкостопы выносливы и стойки"
            }
        },
        "description": "Маленькие, удачливые и жизнерадостные создания"
    },
    "Тифлинг": {
        "ability_bonuses": {"CHA": 2, "INT": 1},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий", "Адский"],
        "traits": [
            "Тёмное зрение",
            "Адское сопротивление",
            "Наследие ада",
            "Дьявольский язык"
        ],
        "resistances": ["Огонь"],
        "description": "Потомки людей и демонов с дьявольской внешностью"
    },
    "Человек": {
        "ability_bonuses": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий"],
        "traits": [
            "Универсальность человечества"
        ],
        "variant": {
            "ability_bonuses": {"STR": 1, "DEX": 1},
            "skill": "Любой на выбор",
            "feat": "Любая черта на выбор",
            "description": "Альтернативный вариант человека с чертой и навыком"
        },
        "description": "Амбициозные и разносторонние создания, заселившие все земли"
    },
    "Ченжлинг": {
        "ability_bonuses": {"CHA": 2, "DEX": 1},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий"],
        "traits": [
            "Изменчивая природа",
            "Двойник",
            "Раздельный разум"
        ],
        "description": "Оборотни, способные менять свою внешность"
    },
    "Шифтер": {
        "ability_bonuses": {"DEX": 2},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий"],
        "traits": [
            "Тёмное зрение",
            "Звериное чутьё",
            "Сдвиг"
        ],
        "subraces": {
            "Медвежий": {
                "ability_bonuses": {"CON": 1},
                "trait": "Медвежья выносливость",
                "description": "Медвежьи шифтеры сильны и выносливы"
            },
            "Кошачий": {
                "ability_bonuses": {"DEX": 1},
                "trait": "Кошачья ловкость",
                "description": "Кошачьи шифтеры быстры и ловки"
            },
            "Крысиный": {
                "ability_bonuses": {"INT": 1},
                "trait": "Крысиная хитрость",
                "description": "Крысиные шифтеры умны и хитры"
            },
            "Волчий": {
                "ability_bonuses": {"WIS": 1},
                "trait": "Волчье чутьё",
                "description": "Волчьи шифтеры обладают острым чутьём"
            }
        },
        "description": "Ликантропы с контролируемой способностью к превращению"
    },
    "Эльф": {
        "ability_bonuses": {"DEX": 2},
        "speed": 30,
        "size": "Средний",
        "languages": ["Общий", "Эльфийский"],
        "traits": [
            "Тёмное зрение",
            "Заточение фей",
            "Транс",
            "Чувство стрелы"
        ],
        "subraces": {
            "Высший эльф": {
                "ability_bonuses": {"INT": 1},
                "trait": "Дополнительный кантрип",
                "description": "Высшие эльфы искусны в магии"
            },
            "Лесной эльф": {
                "ability_bonuses": {"WIS": 1},
                "trait": "Быстрые ноги",
                "description": "Лесные эльфы быстры и скрытны"
            },
            "Тёмный эльф (Дроу)": {
                "ability_bonuses": {"CHA": 1},
                "trait": "Фейский огонёк",
                "sunlight_sensitivity": True,
                "description": "Дроу живут в подземельях и чувствительны к свету"
            }
        },
        "description": "Изящные, долгоживущие существа, связанные с магией и природой"
    }
}


def get_all_races() -> List[str]:
    """Возвращает список всех рас"""
    return list(RACES_DATA.keys())


def get_race_data(race_name: str) -> Dict[str, Any]:
    """Возвращает данные о расе по имени"""
    return dict(RACES_DATA.get(race_name, {}))


def get_race_ability_bonuses(race_name: str, subrace: Optional[str] = None) -> Dict[str, int]:
    """
    Возвращает бонусы к характеристикам расы

    Args:
        race_name: название расы
        subrace: название подрасы (опционально)

    Returns:
        Dict[str, int]: бонусы к характеристикам
    """
    race = RACES_DATA.get(race_name, {})
    bonuses = dict(race.get("ability_bonuses", {}))

    if subrace and "subraces" in race and subrace in race["subraces"]:
        subrace_bonuses = race["subraces"][subrace]
        # Обновляем только бонусы к характеристикам
        for key in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]:
            if key in subrace_bonuses:
                bonuses[key] = bonuses.get(key, 0) + subrace_bonuses[key]

    return bonuses


def get_race_traits(race_name: str, subrace: Optional[str] = None) -> List[str]:
    """
    Возвращает особенности расы

    Args:
        race_name: название расы
        subrace: название подрасы (опционально)

    Returns:
        List[str]: список особенностей
    """
    race = RACES_DATA.get(race_name, {})
    traits = list(race.get("traits", []))

    if subrace and "subraces" in race and subrace in race["subraces"]:
        subrace_trait = race["subraces"][subrace].get("trait")
        if subrace_trait:
            traits.append(subrace_trait)

    return traits


def get_race_speed(race_name: str) -> int:
    """Возвращает скорость расы"""
    race = RACES_DATA.get(race_name, {})
    return race.get("speed", 30)


def get_race_size(race_name: str) -> str:
    """Возвращает размер расы"""
    race = RACES_DATA.get(race_name, {})
    return race.get("size", "Средний")


def get_race_languages(race_name: str) -> List[str]:
    """Возвращает языки расы"""
    race = RACES_DATA.get(race_name, {})
    return race.get("languages", ["Общий"])


def get_race_description(race_name: str) -> str:
    """Возвращает описание расы"""
    race = RACES_DATA.get(race_name, {})
    return race.get("description", "Нет описания")


def get_race_subraces(race_name: str) -> Dict[str, Dict[str, Any]]:
    """Возвращает подрасы расы"""
    race = RACES_DATA.get(race_name, {})
    return race.get("subraces", {})


def has_subraces(race_name: str) -> bool:
    """Проверяет, есть ли у расы подрасы"""
    return len(get_race_subraces(race_name)) > 0


def get_race_traits_full_list(race_name: str, subrace: Optional[str] = None) -> Dict[str, Any]:
    """
    Возвращает полную информацию о расе для отображения

    Returns:
        Dict с полями: name, speed, size, languages, traits, description
    """
    race = RACES_DATA.get(race_name, {})

    return {
        "name": race_name,
        "speed": race.get("speed", 30),
        "size": race.get("size", "Средний"),
        "languages": race.get("languages", ["Общий"]),
        "traits": get_race_traits(race_name, subrace),
        "description": race.get("description", "Нет описания"),
        "subrace": subrace,
        "has_subraces": has_subraces(race_name)
    }


def validate_race(race_name: str) -> bool:
    """Проверяет существование расы"""
    return race_name in RACES_DATA


def validate_subrace(race_name: str, subrace_name: str) -> bool:
    """Проверяет существование подрасы"""
    subraces = get_race_subraces(race_name)
    return subrace_name in subraces


def format_race_info(race_name: str, subrace: Optional[str] = None) -> str:
    """
    Форматирует информацию о расе для отображения пользователю

    Args:
        race_name: название расы
        subrace: название подрасы (опционально)

    Returns:
        str: отформатированный текст
    """
    race = RACES_DATA.get(race_name, {})
    if not race:
        return f"❌ Раса '{race_name}' не найдена"

    info = f"🧝 **{race_name}**"
    if subrace:
        info += f" ({subrace})"
    info += "\n\n"

    info += f"**Описание:** {race.get('description', 'Нет описания')}\n\n"
    info += f"**Скорость:** {race.get('speed', 30)} футов\n"
    info += f"**Размер:** {race.get('size', 'Средний')}\n"
    info += f"**Языки:** {', '.join(race.get('languages', ['Общий']))}\n\n"

    # Бонусы к характеристикам
    bonuses = get_race_ability_bonuses(race_name, subrace)
    if bonuses:
        info += "**Бонусы к характеристикам:**\n"
        for stat, bonus in bonuses.items():
            info += f"  • {stat}: +{bonus}\n"
        info += "\n"

    # Особенности
    traits = get_race_traits(race_name, subrace)
    if traits:
        info += "**Особенности:**\n"
        for trait in traits:
            info += f"  • {trait}\n"

    return info


# ---------------- ТЕСТИРОВАНИЕ ----------------
if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТ МОДУЛЯ RACES_DATA")
    print("=" * 60)

    # 1. Список всех рас
    print("\n1. Список всех рас:")
    races = get_all_races()
    print(f"   Всего рас: {len(races)}")
    print(f"   {', '.join(races)}")

    # 2. Проверка каждой расы
    print("\n2. Детальная информация о расах:")
    for race_name in races[:5]:  # Первые 5 для примера
        print(f"\n   --- {race_name} ---")
        print(f"   Скорость: {get_race_speed(race_name)}")
        print(f"   Размер: {get_race_size(race_name)}")
        print(f"   Языки: {', '.join(get_race_languages(race_name))}")
        print(f"   Бонусы: {get_race_ability_bonuses(race_name)}")

        # Особенности
        traits = get_race_traits(race_name)
        if traits:
            print(f"   Особенности: {', '.join(traits[:3])}")
            if len(traits) > 3:
                print(f"      ... и {len(traits) - 3} других")

    # 3. Тест подрас
    print("\n3. Тест подрас:")
    races_with_subraces = [r for r in races if has_subraces(r)]
    print(f"   Расы с подрасами: {', '.join(races_with_subraces)}")

    for race_name in races_with_subraces[:3]:
        subraces = get_race_subraces(race_name)
        print(f"\n   {race_name}:")
        for subrace_name, subrace_data in subraces.items():
            bonuses = get_race_ability_bonuses(race_name, subrace_name)
            print(f"      • {subrace_name}: {subrace_data.get('trait')[:50]}...")
            print(f"        Бонусы: {bonuses}")

    # 4. Тест функции format_race_info
    print("\n4. Тест форматирования информации:")
    print(format_race_info("Эльф", "Лесной эльф"))

    # 5. Тест валидации
    print("\n5. Тест валидации:")
    print(f"   validate_race('Эльф'): {validate_race('Эльф')}")
    print(f"   validate_race('НесуществующаяРаса'): {validate_race('НесуществующаяРаса')}")
    print(f"   validate_subrace('Эльф', 'Лесной эльф'): {validate_subrace('Эльф', 'Лесной эльф')}")

    # 6. Статистика
    print("\n6. Статистика:")
    total_traits = sum(len(get_race_traits(race)) for race in races)
    total_subraces = sum(len(get_race_subraces(race)) for race in races)
    print(f"   Всего особенностей рас: {total_traits}")
    print(f"   Всего подрас: {total_subraces}")

    print("\n" + "=" * 60)
    print("✅ МОДУЛЬ RACES_DATA УСПЕШНО ЗАГРУЖЕН!")
    print("=" * 60)