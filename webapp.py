# webapp.py
"""
Веб-сервер для отображения листа персонажа (Telegram Mini App)
Адаптирован под новый премиальный HTML-шаблон.
Гарантирует, что все числовые значения передаются как int.
"""
 
import os
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Template, Environment, FileSystemLoader
from dotenv import load_dotenv
 
# Репозитории
from repositories.character_repository import CharacterRepository
from repositories.class_repository import ClassRepository
from repositories.background_repository import BackgroundRepository
from repositories.race_repository import RaceRepository
 
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
    "Чернокнижник": "⛧",
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
    "Чернокнижник": "warlock",
    "Волшебник":    "mage",
    "Артефактор":   "default",
}
 
 
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
    proficiency_bonus = 2
 
    background_info = _bg_repo.get_by_name(background_name) or {}
    background_trait = background_info.get("trait", "")
    background_description = background_info.get("description", "")
    origin_feat = background_info.get("origin_feat", "")
 
    selected_spells = char.get("selected_spells", []) or []
    auto_spells = char.get("auto_spells", []) or []
    all_spells = list(set(selected_spells + auto_spells))
 
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
 
    skill_mods = {}
    for skill in skills_list:
        base_stat = "DEX"
        if skill == "Атлетика":
            base_stat = "STR"
        elif skill in ["Анализ", "Знание магии", "История", "Исследование", "Природа", "Религия"]:
            base_stat = "INT"
        elif skill in ["Внимательность", "Выживание", "Медицина", "Обращение с животными", "Проницательность"]:
            base_stat = "WIS"
        elif skill in ["Выступление", "Запугивание", "Обман", "Убеждение"]:
            base_stat = "CHA"
        mod = (stats[base_stat] - 10) // 2
        if skill in skills_list:
            mod += proficiency_bonus
        skill_mods[skill] = f"{mod:+d}"
 
    initiative = (stats['DEX'] - 10) // 2
    hp = int(char.get("hp", 0))
    ac = int(char.get("ac", 10))
    speed = int(char.get("speed", 30))
    level = int(char.get("level", 1))
    experience = int(char.get("experience", 0))
 
    return {
        "name":                   char["name"],
        "class":                  class_name_ru,
        "class_key":              class_key,
        "class_color":            class_color,
        "class_color_rgb":        f"{int(class_color[1:3],16)},{int(class_color[3:5],16)},{int(class_color[5:7],16)}",
        "class_symbol":           CLASS_SYMBOLS.get(class_name_ru, "✦"),   # ← Вариант 2
        "class_pattern":          CLASS_PATTERNS.get(class_name_ru, "default"),  # ← Вариант 3
        "race":                   race_name,
        "level":                  level,
        "alignment":              alignment,
        "background":             background_name,
        "background_trait":       background_trait,
        "background_description": background_description,
        "origin_feat":            origin_feat,
        "backstory":              char.get("backstory", ""),
        "stats":                  stats,
        "mods":                   mods,
        "hp":                     hp,
        "ac":                     ac,
        "speed":                  speed,
        "experience":             experience,
        "proficiency_bonus":      proficiency_bonus,
        "prof_saves":             saving_throws,
        "prof_skills":            skills_list,
        "skills":                 skill_mods,
        "initiative":             initiative,
        "equipment":              equipment,
        "spells":                 all_spells,
        "order_features":         categorized['order'],
        "pact_features":          categorized['pact'],
        "rogue_features":         categorized['rogue'],
        "class_specific_features": categorized['class'],
        "attacks":                "",
        "created_date":           "недавно",
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
