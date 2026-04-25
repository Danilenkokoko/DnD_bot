# races_data.py
"""
D&D 5e Races Data Module
Модуль с данными о расах для D&D 5 редакции
Поддерживает 16 рас и их подрасы
"""

from typing import Dict, Any, List, Optional
import os

# Словарь с путями к картинкам рас
RACE_IMAGES = {
    "Аасимар": "images/races/aasimar.jpg",
    "Гном": "images/races/gnom.jpg",
    "Голиаф": "images/races/goliaf.jpg",
    "Дампир": "images/races/dampir.jpg",
    "Дварф": "images/races/dwarf.jpg",
    "Драконорожденный": "images/races/dragonborn.jpg",
    "Калаштар": "images/races/kalashtar.jpg",
    "Кованный": "images/races/kowanniy.jpg",
    "Кхоравар": "images/races/khorawar.jpg",
    "Орк": "images/races/ork.jpg",
    "Полурослик": "images/races/halfman.jpg",
    "Тифлинг": "images/races/tifling.jpg",
    "Человек": "images/races/man.jpg",
    "Ченжлинг": "images/races/changaling.jpg",
    "Шифтер": "images/races/shifter.jpg",
    "Эльф": "images/races/elf.jpg"
}

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
                "description": "Протекторы используют силу света для защиты своих союзников."
            },
            "Разоритель": {
                "ability_bonuses": {"CON": 1},
                "trait": "Пожирающий свет",
                "description": "Разорители черпают силу из разрушения и несут возмездие."
            },
            "Несущий скорбь": {
                "ability_bonuses": {"STR": 1},
                "trait": "Некротический гнев",
                "description": "Несущие скорбь связаны с некротической энергией и тайнами смерти."
            }
        },
        "description": "Аасимары — это смертные, которые несут в своих душах искру Верхних Планов. Независимо от того, произошли они от ангельского существа или наделены силой небожителя, они могут раздуть эту искру, чтобы нести свет, исцеление и небесную ярость."
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
                "description": "Лесные гномы умеют общаться с животными и прятаться в природе."
            },
            "Скальный гном": {
                "ability_bonuses": {"CON": 1},
                "trait": "Сведущий в механизмах",
                "description": "Скальные гномы искусны в работе с механизмами и алхимией."
            }
        },
        "description": "Гномы — миниатюрный народец с большими глазами и заострёнными ушами, который живет порядка 425 лет. Многим гномам нравится ощущение крыши над головой, даже если эта 'крыша' - всего лишь шляпа."
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
        "description": "Возвышающиеся над большинством народов голиафы — отдалённые потомки великанов. Каждый голиаф обладает благоволением первых великанов. Оно проявляется в различных сверхъестественных дарах, включая способность быстро увеличиваться в размерах, временно приближаясь к росту гигантских сородичей голиафов."
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
        "description": "Дампиры живы, но обладают как способностями вампиров, так и их ужасным голодом. Большинство дампиров жаждут крови, но некоторые питаются снами, жизненной энергией или из других источников. Каждый дампир должен выбрать, будет ли он пытаться держать свой голод под контролем — или поддаться хищническим желаниям."
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
                "description": "Горные дварфы сильны и выносливы, они искусны в бою."
            },
            "Холмовой дварф": {
                "ability_bonuses": {"WIS": 1},
                "trait": "Дварфийская живучесть",
                "description": "Холмовые дварфы мудры и жизнерадостны, обладают повышенной выносливостью."
            }
        },
        "description": "В древние времена дварфы были подняты из земли божеством кузни. В разных мирах называемое по-разному — Морадин, Реоркс и другие — это божество наделило дварфов сродством к камню и металлу и к жизни под землёй. Оно также сделало их устойчивыми, как горы; дварфы живут около 350 лет."
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
        "description": "Драконорождённые выглядят как бескрылые двуногие драконы — чешуйчатые, ясноглазые, ширококостные, с рожками на головах — а их окраска и другие особенности напоминают их драконьих предков."
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
        "description": "Калаштары происходят от союза человечества и мятежных духов с плана снов, называемых куори. Калаштары выглядят как люди, но их духовная связь различными способами влияет на них. У них симметричные, слегка угловатые черты лица, а их глаза часто светятся, когда они концентрируются или выражают сильные эмоции."
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
        "description": "Кованые — это механические существа, созданные как оружие для Последней войны. В результате совершенно неожиданного следствия изменения технологии вместо бездумных автоматонов появились разумные существа, созданные из дерева и металла, но тем не менее способные испытывать боль и эмоции."
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
        "description": "На протяжении столетий потомки союзов людей и эльфов создавали в Кхорваире свои отдельные сообщества и традиции. Эта культура особо развилась с возвышением Дома Лирандар и Дома Медани. Членам этих сообществ не нравится название 'полуэльфы', поэтому они называют себя кхораварами, что в переводе с эльфийского означает 'дети Кхорваира'."
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
        "description": "Орки ведут своё сотворение от Груумша, могущественного бога, который бродил по широким просторам Материального плана. Груумш снабдил своих детей дарами, помогающими им бродить по великим равнинам, обширным пещерам и бурлящим морям, и выживать во встречах с чудовищами, там обитающими. Даже когда орки обращают свою преданность к другим богам, они сохраняют дары Груумша: выносливость, решительность, способность видеть в темноте."
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
                "description": "Легконогие полурослики умеют прятаться за другими существами."
            },
            "Крепкостоп": {
                "ability_bonuses": {"CON": 1},
                "trait": "Стойкость крепкостопа",
                "description": "Крепкостопы выносливы и стойки к ядам."
            }
        },
        "description": "Общины полуросликов бывают самых разных видов. На каждое поселение, спрятанное в нетронутой части мира, приходится криминальный синдикат, подобный клану Боромар в сеттинге Эберрон, или местная банда полуросликов, как в сеттинге Тёмного солнца."
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
        "description": "Тифлинги либо рождаются на Нижних планах, либо происходят от живущих там исчадий. Каждый тифлинг связан кровными узами с дьяволом, демоном или каким-либо другим Исчадием. Эта связь с Нижними планами — наследие тифлинга, которое сулит могущество, но не оказывает влияния на моральный компас тифлинга."
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
        "description": "Встречающиеся по всей мультивселенной люди столь же разнообразны, сколь и многочисленны, и они стремятся достичь как можно большего за отведенные им годы жизни. Их честолюбие и находчивость вызывают похвалу, уважение и ужас во многих мирах."
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
        "description": "Благодаря своей способности менять облик, ченжлинги незаметно живут во многих обществах. Каждый ченжлинг может сверхъестественным образом принять любой облик, который ему нравится. Принятие нового облика может раскрыть некий новый аспект души ченжлинга."
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
                "description": "Медвежьи шифтеры получают временные хиты при сдвиге."
            },
            "Кошачий": {
                "ability_bonuses": {"DEX": 1},
                "trait": "Кошачья ловкость",
                "description": "Кошачьи шифтеры получают бонус к скорости и ловкости."
            },
            "Крысиный": {
                "ability_bonuses": {"INT": 1},
                "trait": "Крысиная хитрость",
                "description": "Крысиные шифтеры получают бонус к интеллектуальным проверкам."
            },
            "Волчий": {
                "ability_bonuses": {"WIS": 1},
                "trait": "Волчье чутьё",
                "description": "Волчьи шифтеры получают бонус к восприятию и выслеживанию."
            }
        },
        "description": "Шифтер — иногда называемые 'переворотнями' - происходят от людей, заразившихся полной или частичной ликантропией. Шифтеры — гуманоиды с явно заметным животными чертами, они не могут полностью изменить свою форму, но могут временно усилить свои животные черты в процессе, который они называют 'переворотом'."
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
                "description": "Высшие эльфы искусны в магии и получают дополнительное заклинание."
            },
            "Лесной эльф": {
                "ability_bonuses": {"WIS": 1},
                "trait": "Быстрые ноги",
                "description": "Лесные эльфы быстры и скрытны, они чувствуют себя в лесу как дома."
            },
            "Тёмный эльф (Дроу)": {
                "ability_bonuses": {"CHA": 1},
                "trait": "Фейский огонёк",
                "sunlight_sensitivity": True,
                "description": "Дроу живут в подземельях, они чувствительны к свету, но могут использовать магию."
            }
        },
        "description": "Созданные богом Кореллоном, первые эльфы могли неограниченно менять свой облик. Они утратили эту способность, когда Кореллон проклял их за сговор с божеством Лолс, пытавшейся узурпировать власть Кореллона и потерпевшей неудачу. После изгнания Лолс в Бездну большинство эльфов отреклись от неё и заслужили прощение Кореллона, но то, что Кореллон отнял у них, было потеряно навсегда."
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


def get_race_description(race_name: str, subrace: Optional[str] = None) -> str:
    """Возвращает полное описание расы (с учётом подрасы)"""
    race = RACES_DATA.get(race_name, {})
    description = race.get("description", "Нет описания")

    if subrace and "subraces" in race and subrace in race["subraces"]:
        subrace_desc = race["subraces"][subrace].get("description")
        if subrace_desc:
            description += f"\n\n**{subrace}:** {subrace_desc}"

    return description


def get_race_image_path(race_name: str) -> Optional[str]:
    """Возвращает путь к картинке расы"""
    return RACE_IMAGES.get(race_name)


def get_race_image_exists(race_name: str) -> bool:
    """Проверяет, существует ли файл картинки расы"""
    image_path = get_race_image_path(race_name)
    return image_path is not None and os.path.exists(image_path)


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
        "description": get_race_description(race_name, subrace),
        "subrace": subrace,
        "has_subraces": has_subraces(race_name),
        "image_path": get_race_image_path(race_name)
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

    info += f"📖 {get_race_description(race_name, subrace)}\n\n"
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
    for race_name in races[:5]:
        print(f"\n   --- {race_name} ---")
        print(f"   Скорость: {get_race_speed(race_name)}")
        print(f"   Размер: {get_race_size(race_name)}")
        print(f"   Языки: {', '.join(get_race_languages(race_name))}")
        print(f"   Бонусы: {get_race_ability_bonuses(race_name)}")

        # Проверка картинки
        image_path = get_race_image_path(race_name)
        print(f"   Картинка: {image_path} ({'✅ существует' if get_race_image_exists(race_name) else '❌ не найдена'})")

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
    print(format_race_info("Эльф", "Лесной эльф")[:200] + "...")

    # 5. Тест валидации
    print("\n5. Тест валидации:")
    print(f"   validate_race('Эльф'): {validate_race('Эльф')}")
    print(f"   validate_race('НесуществующаяРаса'): {validate_race('НесуществующаяРаса')}")
    print(f"   validate_subrace('Эльф', 'Лесной эльф'): {validate_subrace('Эльф', 'Лесной эльф')}")

    # 6. Статистика
    print("\n6. Статистика:")
    total_traits = sum(len(get_race_traits(race)) for race in races)
    total_subraces = sum(len(get_race_subraces(race)) for race in races)
    total_images = sum(1 for race in races if get_race_image_exists(race))
    print(f"   Всего особенностей рас: {total_traits}")
    print(f"   Всего подрас: {total_subraces}")
    print(f"   Картинок рас: {total_images}/{len(races)}")

    print("\n" + "=" * 60)
    print("✅ МОДУЛЬ RACES_DATA УСПЕШНО ЗАГРУЖЕН!")
    print("=" * 60)