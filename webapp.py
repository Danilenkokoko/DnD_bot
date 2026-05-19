# webapp.py
"""
Веб-сервер для отображения листа персонажа (Telegram Mini App)
Адаптирован под новый премиальный HTML-шаблон.
Гарантирует, что все числовые значения передаются как int.
"""

import os
import re
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment
from dotenv import load_dotenv

# Репозитории
from repositories.character_repository import CharacterRepository
from repositories.class_repository import ClassRepository
from repositories.background_repository import BackgroundRepository
from repositories.race_repository import RaceRepository
from repositories.spell_repository import SpellRepository

from engine.proficiency import calculate_proficiency_bonus
from engine.spell_slots import get_spell_slots, is_pact_magic

from strings import (
    DRUID_ORDER_GUIDE_DESC, DRUID_ORDER_GUARDIAN_DESC,
    CLERIC_ORDER_PROTECTOR_DESC, CLERIC_ORDER_MIRACLE_DESC,
    WARLOCK_PACT_TOME_DESC, WARLOCK_PACT_BLADE_DESC, WARLOCK_PACT_CHAIN_DESC,
    WARLOCK_PACT_SHADOW_ARMOR_DESC, WARLOCK_PACT_ARCANE_MIND_DESC,
    FEATURE_MENDING, FEATURE_BARDIC_INSPIRATION, FEATURE_RAGE,
    FEATURE_UNARMORED_DEFENSE_BARBARIAN, FEATURE_SECOND_WIND,
    FEATURE_WIZARD_SPELLS, FEATURE_RITUAL_CASTER, FEATURE_ARCANE_RECOVERY,
    FEATURE_DRUIDIC_LANGUAGE, FEATURE_SPEAK_WITH_ANIMALS,
    MONK_MARTIAL_ARTS, PALADIN_LAY_ON_HANDS,
    ROGUE_SNEAK_ATTACK, ROGUE_THIEVES_CANT, ROGUE_EXPERTISE, ROGUE_EXTRA_LANGUAGE,
    RANGER_HUNTERS_MARK, SORCERER_MAGIC_RELEASE
)

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(title="D&D Character Sheet Viewer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_char_repo = CharacterRepository()
_class_repo = ClassRepository()
_bg_repo = BackgroundRepository()
_race_repo = RaceRepository()
_spell_repo = SpellRepository()

# Цвета классов для PDF/HTML (в шестнадцатеричном формате)
CLASS_COLORS = {
    "artificer": "#14b8a6",
    "barbarian": "#f97316",
    "bard":      "#ec4899",
    "cleric":    "#fbbf24",
    "druid":     "#10b981",
    "fighter":   "#ef4444",
    "monk":      "#6b7280",
    "paladin":   "#eab308",
    "ranger":    "#84cc16",
    "rogue":     "#8b5cf6",
    "sorcerer":  "#f43f5e",
    "warlock":   "#a855f7",
    "wizard":    "#3b82f6",
}

# Символы классов для угловых орнаментов (Вариант 2)
CLASS_SYMBOLS = {
    "Варвар":       "⛉",
    "Бард":         "♪",
    "Жрец":         "✙",
    "Друид":        "❁",
    "Воин":         "⚔",
    "Монах":        "☯",
    "Паладин":      "⚜",
    "Следопыт":     "⊕",
    "Плут":         "◈",
    "Чародей":      "✦",
    "Колдун":       "⛧",
    "Волшебник":    "✦",
    "Артефактор":   "⚙",
}

# Паттерны фона по классу (Вариант 3)
CLASS_PATTERNS = {
    "Варвар":       "barbarian",
    "Бард":         "bard",
    "Жрец":         "cleric",
    "Друид":        "druid",
    "Воин":         "warrior",
    "Монах":        "monk",
    "Паладин":      "paladin",
    "Следопыт":     "ranger",
    "Плут":         "rogue",
    "Чародей":      "mage",
    "Колдун":       "warlock",
    "Волшебник":    "mage",
    "Артефактор":   "default",
}


# ── Кость хитов по классу ──────────────────────────────────────────────────
HIT_DICE = {
    "Варвар":     "к12",
    "Бард":       "к8",
    "Жрец":       "к8",
    "Друид":      "к8",
    "Воин":       "к10",
    "Монах":      "к8",
    "Паладин":    "к10",
    "Следопыт":   "к10",
    "Плут":       "к8",
    "Чародей":    "к6",
    "Колдун":     "к8",
    "Волшебник":  "к6",
    "Артефактор": "к8",
}

# ── Ресурсы класса: иконка FA + название + формула расчёта ─────────────────
def build_class_resources(class_name: str, level: int, mods: Dict[str, int]) -> List[Dict]:
    """Возвращает список ресурсов класса для отображения в шаблоне."""
    resources = []

    if class_name == "Монах":
        # PHB 2024: Focus Points (бывшие Ki) у Монаха появляются с L2.
        # На L1 ресурса нет — раньше блок показывался с total=1.
        if level >= 2:
            resources.append({"name": "Очки фокуса", "icon": "fas fa-yin-yang", "total": level, "used": 0})

    elif class_name == "Варвар":
        rages = 2 if level < 3 else (3 if level < 6 else 4)
        resources.append({"name": "Ярость", "icon": "fas fa-fire", "total": rages, "used": 0})

    elif class_name == "Бард":
        # PHB 2024: Bardic Inspiration кость растёт по уровню барда —
        # L1: d6, L5: d8, L10: d10, L15: d12. Количество = max(1, CHA_mod).
        insp = max(1, mods.get("CHA", 0))
        if   level >= 15: die = "d12"
        elif level >= 10: die = "d10"
        elif level >= 5:  die = "d8"
        else:             die = "d6"
        resources.append({
            "name": f"Вдохновение барда ({die})",
            "icon": "fas fa-music",
            "total": insp, "used": 0,
        })

    elif class_name == "Паладин":
        hp_reserve = level * 5
        resources.append({"name": f"Возложение рук ({hp_reserve} хп)", "icon": "fas fa-hand-holding-heart", "total": min(hp_reserve, 20), "used": 0})

    # NB: для Колдуна Pact Magic слоты идут в блоке «Ячейки заклинаний»;
    # отдельный ресурс «Ячейки договора» был удалён как дубль. Класса
    # «Чернокнижник» в seed_data.py нет — мёртвая ветка тоже удалена.

    elif class_name == "Волшебник":
        recovery = max(1, level // 2)
        resources.append({"name": f"Арканное восстановление (ур.{recovery})", "icon": "fas fa-hat-wizard", "total": 1, "used": 0})

    elif class_name == "Друид":
        # PHB 2024: Wild Shape с L2 (на L1 у друида ресурса нет).
        if level >= 2:
            resources.append({"name": "Облик зверя", "icon": "fas fa-paw", "total": 2, "used": 0})

    elif class_name == "Воин":
        # PHB 2024: Second Wind использований по уровню — L1-3: 2, L4-9: 3,
        # L10-14: 4, L15+: 5. Раньше было захардкожено 1.
        if level >= 15:   sw = 5
        elif level >= 10: sw = 4
        elif level >= 4:  sw = 3
        else:             sw = 2
        resources.append({"name": "Второе дыхание", "icon": "fas fa-wind", "total": sw, "used": 0})

    elif class_name == "Чародей":
        # PHB 2024: Sorcery Points появляются на L2 (= level). На L1 ресурса
        # нет вообще — не добавляем (раньше показывался блок 0/0).
        if level >= 2:
            resources.append({"name": "Очки чародейства", "icon": "fas fa-star", "total": level, "used": 0})

    return resources


# ── Блок атак из снаряжения персонажа ──────────────────────────────────────
def build_attacks(char: Dict[str, Any], stats: Dict[str, int], proficiency_bonus: int) -> List[Dict]:
    """Формирует список атак: выбранное оружие (если есть) + безоружный удар.

    PHB 2024: Unarmed Strike доступен ЛЮБОМУ персонажу (включая безоружных).
    Поэтому ранний return при отсутствии оружия убран — мы всегда возвращаем
    хотя бы один безоружный удар.
    """
    attacks = []
    weapon = char.get("selected_weapon")

    str_mod = (stats["STR"] - 10) // 2
    dex_mod = (stats["DEX"] - 10) // 2

    # Справочник оружия по PHB 2024:
    # (dice, тип урона, тип характеристики, дистанция, [finesse]).
    # Ключ stat_key="DEX_OR_STR" означает Finesse — берётся max(STR, DEX).
    WEAPON_DATA = {
        # ── Простое рукопашное ──────────────────────────────────────
        "Кинжал":         ("1к4",  "колющий",   "DEX_OR_STR", "Ближн. 5 / Метат. 20/60"),
        "Посох":          ("1к6",  "дробящий",  "STR",        "5 фут."),
        "Булава":         ("1к6",  "дробящий",  "STR",        "5 фут."),
        "Копьё":          ("1к6",  "колющий",   "STR",        "5 / 20/60 фут."),
        "Лёгкий молот":   ("1к4",  "дробящий",  "STR",        "5 / 20/60 фут."),
        "Серп":           ("1к4",  "рубящий",   "STR",        "5 фут."),
        "Большая дубина": ("1к8",  "дробящий",  "STR",        "5 фут."),
        # ── Простое дальнобойное ────────────────────────────────────
        "Лук":            ("1к8",  "колющий",   "DEX",        "80/320 фут."),
        "Лёгкий арбалет": ("1к8",  "колющий",   "DEX",        "80/320 фут."),
        # ── Воинское рукопашное ─────────────────────────────────────
        "Короткий меч":   ("1к6",  "колющий",   "DEX_OR_STR", "5 фут."),
        "Рапира":         ("1к8",  "колющий",   "DEX_OR_STR", "5 фут."),
        "Ятаган":         ("1к6",  "рубящий",   "DEX_OR_STR", "5 фут."),
        "Длинный меч":    ("1к8",  "рубящий",   "STR",        "5 фут."),
        "Двуручный меч":  ("2к6",  "рубящий",   "STR",        "5 фут."),
        "Боевой топор":   ("1к8",  "рубящий",   "STR",        "5 фут."),
        "Секира":         ("1к12", "рубящий",   "STR",        "5 фут."),
        "Цеп":            ("1к8",  "дробящий",  "STR",        "5 фут."),
        "Боевой молот":   ("1к8",  "дробящий",  "STR",        "5 фут."),
        "Двуручный молот":("2к6",  "дробящий",  "STR",        "5 фут."),
        "Глефа":          ("1к10", "рубящий",   "STR",        "10 фут."),
        "Алебарда":       ("1к10", "рубящий",   "STR",        "10 фут."),
        "Пика":           ("1к10", "колющий",   "STR",        "10 фут."),
        # ── Воинское дальнобойное ───────────────────────────────────
        "Длинный лук":    ("1к8",  "колющий",   "DEX",        "150/600 фут."),
        "Тяжёлый арбалет":("1к10", "колющий",   "DEX",        "100/400 фут."),
        "Ручной арбалет": ("1к6",  "колющий",   "DEX",        "30/120 фут."),
        # Generic fallback для устаревшего имени:
        "Арбалет":        ("1к10", "колющий",   "DEX",        "100/400 фут."),
    }

    # Атака оружием — только если оно выбрано.
    if weapon:
        data = WEAPON_DATA.get(weapon)
        if data:
            dice, dmg_type, stat_key, rng = data
            # 2024 PHB: Finesse — игрок выбирает STR или DEX (берём max).
            if stat_key == "DEX_OR_STR":
                mod = max(str_mod, dex_mod)
            elif stat_key == "STR":
                mod = str_mod
            else:  # "DEX"
                mod = dex_mod
            bonus = mod + proficiency_bonus
            sign = "+" if bonus >= 0 else ""
            attacks.append({
                "name":        weapon,
                "bonus":       f"{sign}{bonus}",
                "damage":      f"{dice}{'+' if mod >= 0 else ''}{mod}",
                "damage_type": dmg_type,
                "range":       rng,
            })
        else:
            # Неизвестное оружие — базовый расчёт без кубика
            bonus = str_mod + proficiency_bonus
            sign = "+" if bonus >= 0 else ""
            attacks.append({
                "name":        weapon,
                "bonus":       f"{sign}{bonus}",
                "damage":      "—",
                "damage_type": "—",
                "range":       "5 фут.",
            })

    # PHB 2024: Unarmed Strike доступен ЛЮБОМУ персонажу.
    # Базовый урон = 1 + STR_mod (дробящий, ближний 5 фт.).
    # Монах с Martial Arts (L1: d6) использует max(STR, DEX) — отдельная запись.
    class_name = char.get("class_name")
    if class_name == "Монах":
        unarmed_mod = max(str_mod, dex_mod)
        unarmed_bonus = unarmed_mod + proficiency_bonus
        unarmed_sign = "+" if unarmed_bonus >= 0 else ""
        unarmed_dmg_sign = "+" if unarmed_mod >= 0 else ""
        attacks.append({
            "name":        "Безоружный удар (Боевые искусства)",
            "bonus":       f"{unarmed_sign}{unarmed_bonus}",
            "damage":      f"1к6{unarmed_dmg_sign}{unarmed_mod}",
            "damage_type": "дробящий",
            "range":       "5 фут.",
        })
    else:
        # Стандартный безоружный удар: 1 + STR_mod.
        u_bonus = str_mod + proficiency_bonus
        u_sign  = "+" if u_bonus >= 0 else ""
        d_sign  = "+" if str_mod >= 0 else ""
        attacks.append({
            "name":        "Безоружный удар",
            "bonus":       f"{u_sign}{u_bonus}",
            "damage":      f"1{d_sign}{str_mod}",
            "damage_type": "дробящий",
            "range":       "5 фут.",
        })

    return attacks


def format_features_by_category(char: Dict[str, Any]) -> Dict[str, List[str]]:
    """Формирует словарь с особенностями персонажа, разделёнными по категориям."""
    result = {
        'order': [],
        'pact': [],
        'rogue': [],
        'class': []
    }

    # Орден друида
    druid_order = char.get("druid_order")
    if druid_order:
        if druid_order == "guide":
            result['order'].append(DRUID_ORDER_GUIDE_DESC)
        elif druid_order == "guardian":
            result['order'].append(DRUID_ORDER_GUARDIAN_DESC)

    # Орден жреца
    cleric_order = char.get("cleric_order")
    if cleric_order:
        if cleric_order == "protector":
            result['order'].append(CLERIC_ORDER_PROTECTOR_DESC)
        elif cleric_order == "miracle":
            result['order'].append(CLERIC_ORDER_MIRACLE_DESC)

    # Договор колдуна
    warlock_pact = char.get("warlock_pact")
    if warlock_pact == "tome":
        result['pact'].append(WARLOCK_PACT_TOME_DESC)
        pact_cantrips = char.get("pact_tome_cantrips", [])
        pact_rituals = char.get("pact_tome_rituals", [])
        if pact_cantrips:
            result['pact'].append(f"• Заговоры Книги теней: {', '.join(pact_cantrips)}")
        if pact_rituals:
            result['pact'].append(f"• Ритуалы Книги теней: {', '.join(pact_rituals)}")
    elif warlock_pact == "blade":
        result['pact'].append(WARLOCK_PACT_BLADE_DESC)
        blade_weapon = char.get("pact_blade_weapon")
        if blade_weapon:
            result['pact'].append(f"• Оружие договора: {blade_weapon}")
    elif warlock_pact == "chain":
        result['pact'].append(WARLOCK_PACT_CHAIN_DESC)
    elif warlock_pact == "shadow_armor":
        result['pact'].append(WARLOCK_PACT_SHADOW_ARMOR_DESC)
    elif warlock_pact == "arcane_mind":
        result['pact'].append(WARLOCK_PACT_ARCANE_MIND_DESC)

    # Плут: экспертиза и язык
    rogue_expertise = char.get("rogue_expertise", [])
    if rogue_expertise:
        result['rogue'].append(ROGUE_EXPERTISE.format(skills=", ".join(rogue_expertise)))
    rogue_lang = char.get("rogue_extra_language")
    if rogue_lang:
        result['rogue'].append(ROGUE_EXTRA_LANGUAGE.format(language=rogue_lang))

    # Классовые особенности
    class_name = char.get("class_name")
    if class_name == "Артефактор":
        result['class'].append(FEATURE_MENDING)
    elif class_name == "Бард":
        result['class'].append(FEATURE_BARDIC_INSPIRATION)
    elif class_name == "Варвар":
        result['class'].append(FEATURE_RAGE)
        result['class'].append(FEATURE_UNARMORED_DEFENSE_BARBARIAN)
    elif class_name == "Воин":
        result['class'].append(FEATURE_SECOND_WIND)
    elif class_name == "Волшебник":
        result['class'].append(FEATURE_WIZARD_SPELLS)
        result['class'].append(FEATURE_RITUAL_CASTER)
        result['class'].append(FEATURE_ARCANE_RECOVERY)
    elif class_name == "Друид":
        result['class'].append(FEATURE_DRUIDIC_LANGUAGE)
        result['class'].append(FEATURE_SPEAK_WITH_ANIMALS)
    elif class_name == "Монах":
        result['class'].append(MONK_MARTIAL_ARTS)
    elif class_name == "Паладин":
        hp_reserve = char.get("level", 1) * 5
        result['class'].append(PALADIN_LAY_ON_HANDS.format(hp_reserve=hp_reserve))
    elif class_name == "Плут":
        result['class'].append(ROGUE_SNEAK_ATTACK.format(damage_dice="1к6"))
        result['class'].append(ROGUE_THIEVES_CANT)
    elif class_name == "Следопыт":
        result['class'].append(RANGER_HUNTERS_MARK)
    elif class_name == "Чародей":
        result['class'].append(SORCERER_MAGIC_RELEASE)

    return result


def get_character_data(char_id: int) -> Dict[str, Any]:
    char = _char_repo.get_by_id(char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Персонаж не найден")

    # Уровень — используется во многих местах ниже; читаем один раз.
    level = int(char.get("level", 1))

    stats = {
        "STR": int(char.get("str", 10)),
        "DEX": int(char.get("dex", 10)),
        "CON": int(char.get("con", 10)),
        "INT": int(char.get("int", 10)),
        "WIS": int(char.get("wis", 10)),
        "CHA": int(char.get("cha", 10)),
    }

    # Вычисляем модификаторы один раз
    mods = {stat: (stats[stat] - 10) // 2 for stat in stats}

    skills_list = char.get("selected_skills", []) or []
    class_name_ru = char.get("class_name") or "Без класса"
    race_name = char.get("race_name") or "Неизвестно"
    background_name = char.get("background_name") or "Нет"
    alignment = char.get("alignment", "Нейтральное")

    class_mapping = {
        "Варвар":       "barbarian",
        "Бард":         "bard",
        "Жрец":         "cleric",
        "Друид":        "druid",
        "Воин":         "fighter",
        "Монах":        "monk",
        "Паладин":      "paladin",
        "Следопыт":     "ranger",
        "Плут":         "rogue",
        "Чародей":      "sorcerer",
        "Колдун":       "warlock",
        "Волшебник":    "wizard",
        "Артефактор":   "artificer",
    }
    class_key = class_mapping.get(class_name_ru, "fighter")
    class_color = CLASS_COLORS.get(class_key, "#ef4444")

    class_info = _class_repo.get_by_name(class_name_ru) or {}
    saving_throws = class_info.get("saving_throws", [])
    # Бонус мастерства считается из уровня (D&D 5.5e таблица: 1-4 → +2, 5-8 → +3, ...)
    proficiency_bonus = calculate_proficiency_bonus(level)

    background_info = _bg_repo.get_by_name(background_name) or {}
    background_trait = background_info.get("trait", "")
    background_description = background_info.get("description", "")
    origin_feat = background_info.get("origin_feat", "")

    selected_spells = char.get("selected_spells", []) or []
    auto_spells = char.get("auto_spells", []) or []
    all_spells = list(set(selected_spells + auto_spells))

    # PHB 2024 — для раскрытия описания на листе персонажа: подтягиваем полную
    # информацию о каждом заклинании (имя, уровень, категория, описание).
    # Группируем по категории, чтобы шаблон вывел блоками.
    spells_full = []
    for sp_name in all_spells:
        sp_data = _spell_repo.get_by_name(sp_name) if hasattr(_spell_repo, 'get_by_name') else None
        if sp_data:
            spells_full.append({
                "name":        sp_data.get("name", sp_name),
                "level":       sp_data.get("level", 0),
                "is_cantrip":  bool(sp_data.get("is_cantrip", False)),
                "category":    sp_data.get("category") or "Прочее",
                "description": sp_data.get("description") or "Описание отсутствует.",
            })
        else:
            spells_full.append({
                "name": sp_name, "level": 0, "is_cantrip": True,
                "category": "Прочее", "description": "Описание отсутствует.",
            })
    # Сортировка: сначала заговоры (level 0), потом 1-й уровень; внутри — по категории.
    _cat_order = ["Урон", "Лечение", "Защита", "Контроль", "Утилита", "Иллюзии", "Природа", "Прочее"]
    spells_full.sort(key=lambda s: (s["level"], _cat_order.index(s["category"]) if s["category"] in _cat_order else 99, s["name"]))

    # 2024 PHB: языки (Общий + 2 от предыстории) и владение инструментами
    languages = char.get("languages", []) or []
    selected_tools = char.get("selected_tools", []) or []

    # 2024 PHB: ячейки заклинаний по уровню класса (для блока «Слоты заклинаний»).
    spell_slots_dict = get_spell_slots(class_name_ru, level)
    # Превращаем в список словарей для шаблона: [{level, total, used}, …].
    # Без отслеживания «использовано» в БД — пока used=0 везде.
    spell_slots_list = [
        {"level": lvl, "total": total, "used": 0}
        for lvl, total in sorted(spell_slots_dict.items())
    ]
    pact_magic = is_pact_magic(class_name_ru)

    # Weapon Mastery: список приёмов оружия (#15 на лист).
    weapon_masteries = char.get("selected_masteries", []) or []

    # Монеты (2024 PHB: cp/sp/ep/gp/pp); если в БД пока нет — все нули.
    coins = char.get("coins") or {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0}

    # Heroic Inspiration (PHB 2024) — целочисленный счётчик. БД сейчас хранит
    # BOOLEAN (наследие); приводим к int (0 или 1) — позже в схеме можно
    # заменить на INTEGER без поломки шаблона.
    raw_inspiration = char.get("inspiration", 0)
    if isinstance(raw_inspiration, bool):
        inspiration = int(raw_inspiration)
    else:
        try:
            inspiration = max(0, int(raw_inspiration))
        except (TypeError, ValueError):
            inspiration = 0

    # NOTE (этап 1): блок «4 черты личности» удалён по запросу владельца
    # проекта. Шаблон character_sheet.html больше не отрисовывает этот блок.

    # Расовые черты (2024 PHB) — список из репозитория расы.
    race_traits = []
    try:
        race_data = _race_repo.get_by_name(race_name) if race_name else None
        if race_data:
            race_traits = race_data.get("traits") or []
            # Поддержим dict (pg-jsonb) и list-форму
            if isinstance(race_traits, dict):
                race_traits = list(race_traits.values())
        subrace_name_db = char.get("subrace_name")
        if subrace_name_db and race_name:
            sub = _race_repo.get_subrace_by_name(race_name, subrace_name_db)
            if sub:
                sub_trait = sub.get("trait")
                if sub_trait:
                    race_traits = list(race_traits) + [sub_trait]
    except Exception as e:
        logger.warning(f"Не удалось получить расовые черты: {e}")

    categorized = format_features_by_category(char)

    equipment = []
    if char.get("selected_weapon"):
        equipment.append(char["selected_weapon"])
    if char.get("selected_armor"):
        equipment.append(char["selected_armor"])
    equip_choice = char.get("selected_equipment_choice")
    if equip_choice and background_info:
        equip_desc = background_info.get(f"equipment_{equip_choice.lower()}", "")
        if equip_desc:
            equipment.append(f"Снаряжение предыстории ({equip_choice}): {equip_desc}")

    # D&D 5.5e (2024) PHB — каноническая привязка навыка к характеристике.
    # Используем точные русские имена из БД (см. db.init_db и handlers).
    SKILL_TO_STAT = {
        # STR
        "Атлетика": "STR",
        # DEX
        "Акробатика": "DEX",
        "Ловкость рук": "DEX",
        "Скрытность": "DEX",
        # INT
        "История": "INT",
        "Природа": "INT",
        "Расследование": "INT",
        "Религия": "INT",
        "Тайная магия": "INT",
        # WIS
        "Восприятие": "WIS",
        "Выживание": "WIS",
        "Медицина": "WIS",
        "Обращение с животными": "WIS",
        "Проницательность": "WIS",
        # CHA
        "Выступление": "CHA",
        "Запугивание": "CHA",
        "Обман": "CHA",
        "Убеждение": "CHA",
    }

    # Экспертиза (Плут L1 / Бард L1, 2024 PHB) — удвоенный бонус мастерства.
    # Поле в БД называется `rogue_expertise` исторически, но фактически хранит
    # экспертизу любого класса с этой фичей.
    expertise_set = set(char.get("rogue_expertise", []) or [])

    # PHB 2024: на офиц. листе всегда показаны ВСЕ 18 навыков с галочкой
    # proficiency. Поэтому идём по полному словарю SKILL_TO_STAT, а не только
    # по выбранным `skills_list`.
    proficient_skills = set(skills_list)
    skill_mods = {}
    for skill, base_stat in SKILL_TO_STAT.items():
        mod = (stats[base_stat] - 10) // 2
        if skill in proficient_skills:
            mod += proficiency_bonus
            # Если экспертиза — добавляем бонус ещё раз (всего ×2 от proficiency).
            if skill in expertise_set:
                mod += proficiency_bonus
        skill_mods[skill] = f"{mod:+d}"

    # PHB 2024: Пассивные значения = 10 + бонус навыка.
    # На лист идут: Внимание (Восприятие), Расследование, Проницательность.
    def _passive(skill_name: str, base_stat: str) -> int:
        m = (stats[base_stat] - 10) // 2
        if skill_name in proficient_skills:
            m += proficiency_bonus
            if skill_name in expertise_set:
                m += proficiency_bonus
        return 10 + m

    passive_perception    = _passive("Восприятие",      "WIS")
    passive_investigation = _passive("Расследование",   "INT")
    passive_insight       = _passive("Проницательность", "WIS")

    # PHB 2024 Spellcasting: считаем DC и бонус атаки заклинаниями.
    # Spell Save DC      = 8 + proficiency_bonus + spellcasting_ability_mod
    # Spell Attack Bonus =     proficiency_bonus + spellcasting_ability_mod
    is_spellcaster = bool(class_info.get("is_spellcaster", False))
    spell_ability_key = class_info.get("spellcasting_ability")
    spellcasting = None
    if is_spellcaster and spell_ability_key in stats:
        sp_mod = mods[spell_ability_key]
        ability_name_ru = {
            "INT": "Интеллект",
            "WIS": "Мудрость",
            "CHA": "Харизма",
        }.get(spell_ability_key, spell_ability_key)
        spellcasting = {
            "ability":      spell_ability_key,
            "ability_name": ability_name_ru,
            "ability_mod":  f"{sp_mod:+d}",
            "save_dc":      8 + proficiency_bonus + sp_mod,
            "attack_bonus": f"{proficiency_bonus + sp_mod:+d}",
        }

    initiative = (stats['DEX'] - 10) // 2
    hp = int(char.get("hp", 0))
    ac = int(char.get("ac", 10))
    speed = int(char.get("speed", 30))

    # PHB 2024 — AC breakdown текстом под значением.
    # Если есть выбранная броня — указываем её имя; иначе формула "10 + DEX".
    # Щит читаем из selected_secondary_weapon или selected_other_items.
    _armor_name = char.get("selected_armor") or ""
    _sec  = (char.get("selected_secondary_weapon") or "").lower()
    _oth  = (char.get("selected_other_items") or "").lower()
    _has_shield = ("щит" in _sec) or ("щит" in _oth)
    _ac_parts = []
    if _armor_name:
        _ac_parts.append(_armor_name)
    else:
        _ac_parts.append(f"10 + DEX {mods['DEX']:+d}")
    if _has_shield:
        _ac_parts.append("Щит +2")
    ac_breakdown = " + ".join(_ac_parts)

    # PHB 2024 — Senses (Тёмное зрение N футов) и Movement modes (полёт/лазание/
    # плавание) парсим из расовых черт. Не нашли — 0 (на лист не выводим).
    def _parse_trait_value(traits, pattern):
        for t in traits or []:
            m = re.search(pattern, str(t))
            if m:
                try:
                    return int(m.group(1))
                except ValueError:
                    continue
        return 0

    darkvision_ft = _parse_trait_value(race_traits, r"[Тт]ёмн\w*\s+зрени\w*\s+(\d+)")
    fly_speed     = _parse_trait_value(race_traits, r"[Сс]корост\w*\s+полёт\w*\s+(\d+)")
    climb_speed   = _parse_trait_value(race_traits, r"[Сс]корост\w*\s+лазани\w*\s+(\d+)")
    swim_speed    = _parse_trait_value(race_traits, r"[Сс]корост\w*\s+плавани\w*\s+(\d+)")
    extra_speeds = []
    if fly_speed:   extra_speeds.append({"label": "Полёт",   "value": fly_speed,   "icon": "fas fa-feather"})
    if climb_speed: extra_speeds.append({"label": "Лазание", "value": climb_speed, "icon": "fas fa-mountain"})
    if swim_speed:  extra_speeds.append({"label": "Плавание","value": swim_speed,  "icon": "fas fa-water"})

    # `level` уже определён в начале функции — не пересчитываем.
    experience = int(char.get("experience", 0))

    # ── НОВЫЕ ПОЛЯ: кость хитов ────────────────────────────────────────────
    hit_die = HIT_DICE.get(class_name_ru, "к8")
    hit_dice_total = level          # на 1 уровне = 1, растёт с уровнем
    hit_dice_used  = int(char.get("hit_dice_used", 0))

    # PHB 2024: HP/state-трекинг. После миграции БД эти колонки заполняются;
    # для совместимости со старыми записями — fallback на hp.
    max_hp     = int(char.get("max_hp")     if char.get("max_hp")     is not None else hp)
    current_hp = int(char.get("current_hp") if char.get("current_hp") is not None else hp)
    temp_hp    = int(char.get("temp_hp")    if char.get("temp_hp")    is not None else 0)
    exhaustion = int(char.get("exhaustion") if char.get("exhaustion") is not None else 0)
    conditions = char.get("conditions") or []
    # Encumbrance / Carry Capacity (PHB 2024): носимая нагрузка = STR × 15 фунтов.
    carry_capacity = stats["STR"] * 15

    # ── НОВЫЕ ПОЛЯ: ресурсы класса ─────────────────────────────────────────
    class_resources = build_class_resources(class_name_ru, level, mods)

    # ── НОВЫЕ ПОЛЯ: атаки ──────────────────────────────────────────────────
    attacks = build_attacks(char, stats, proficiency_bonus)

    return {
        "name":                    char["name"],
        "class":                   class_name_ru,
        "class_key":               class_key,
        "class_color":             class_color,
        "class_color_rgb":         f"{int(class_color[1:3],16)},{int(class_color[3:5],16)},{int(class_color[5:7],16)}",
        "class_symbol":            CLASS_SYMBOLS.get(class_name_ru, "✦"),
        "class_pattern":           CLASS_PATTERNS.get(class_name_ru, "default"),
        "race":                    race_name,
        "subrace_name":            char.get("subrace_name") or "",
        "level":                   level,
        "alignment":               alignment,
        "background":              background_name,
        "background_trait":        background_trait,
        "background_description":  background_description,
        "origin_feat":             origin_feat,
        "backstory":               char.get("backstory", ""),
        "stats":                   stats,
        "mods":                    mods,
        # ── Хиты ──────────────────────────────────────────────────────────
        "hp":                      hp,
        "max_hp":                  max_hp,
        "current_hp":              current_hp,
        "temp_hp":                 temp_hp,
        # ── PHB 2024 state ─────────────────────────────────────────────────
        "exhaustion":              exhaustion,
        "conditions":              conditions,
        "carry_capacity":          carry_capacity,
        # ── Кость хитов ───────────────────────────────────────────────────
        "hit_die":                 hit_die,
        "hit_dice_total":          hit_dice_total,
        "hit_dice_used":           hit_dice_used,
        # ── Боевые ────────────────────────────────────────────────────────
        "ac":                      ac,
        "ac_breakdown":            ac_breakdown,
        "speed":                   speed,
        "extra_speeds":            extra_speeds,
        "darkvision_ft":           darkvision_ft,
        "initiative":              initiative,
        "experience":              experience,
        "proficiency_bonus":       proficiency_bonus,
        "prof_saves":              saving_throws,
        "prof_skills":             skills_list,
        "skills":                  skill_mods,
        # ── Пассивные значения (PHB 2024) ─────────────────────────────────
        "passive_perception":      passive_perception,
        "passive_investigation":   passive_investigation,
        "passive_insight":         passive_insight,
        # ── Spellcasting (PHB 2024) ───────────────────────────────────────
        "spellcasting":            spellcasting,
        # ── Атаки и ресурсы ───────────────────────────────────────────────
        "attacks":                 attacks,
        "class_resources":         class_resources,
        # ── Снаряжение и заклинания ───────────────────────────────────────
        "equipment":               equipment,
        "spells":                  all_spells,
        "spells_full":             spells_full,
        # ── Языки и инструменты (2024 PHB) ────────────────────────────────
        "languages":               languages,
        "tools":                   selected_tools,
        # ── Слоты заклинаний / Pact Magic (2024 PHB) ──────────────────────
        "spell_slots":             spell_slots_list,
        "pact_magic":              pact_magic,
        # ── Weapon Mastery, монеты ────────────────────────────────────────
        "weapon_masteries":        weapon_masteries,
        "coins":                   coins,
        # ── Inspiration и расовые черты (2024 PHB) ────────────────────────
        "inspiration":             inspiration,
        "race_traits":             race_traits,
        # NOTE (этап 1): ключ "personality" удалён — блока больше нет в шаблоне.
        # ── Особенности ───────────────────────────────────────────────────
        "order_features":          categorized['order'],
        "pact_features":           categorized['pact'],
        "rogue_features":          categorized['rogue'],
        "class_specific_features": categorized['class'],
        "created_date":            "недавно",
    }


# Настройка Jinja2 с пользовательским фильтром
def modifier_filter(value):
    """Возвращает модификатор характеристики со знаком."""
    try:
        val = int(value)
    except (TypeError, ValueError):
        return "0"
    mod = (val - 10) // 2
    return f"{mod:+d}" if mod != 0 else "0"


# Загружаем шаблон из файла
template_path = os.path.join(os.path.dirname(__file__), "templates", "character_sheet.html")
if os.path.exists(template_path):
    with open(template_path, "r", encoding="utf-8") as f:
        html_template = f.read()
    env = Environment()
    env.filters['modifier'] = modifier_filter
    template = env.from_string(html_template)
else:
    template = None
    logger.error(f"HTML шаблон не найден по пути: {template_path}")


@app.get("/character/{char_id}", response_class=HTMLResponse)
async def character_sheet(char_id: int = Path(..., title="ID персонажа")):
    try:
        data = get_character_data(char_id)
        if template is None:
            return HTMLResponse(content="<h1>Ошибка: шаблон не загружен</h1>", status_code=500)
        html = template.render(**data)
        return HTMLResponse(content=html)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка рендеринга страницы: {e}", exc_info=True)
        return HTMLResponse(content=f"<h1>Ошибка</h1><p>{str(e)}</p>", status_code=500)


def run_webapp():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
