# webapp.py
"""
Веб-сервер для отображения листа персонажа (Telegram Mini App)
Обновлён для отображения всех новых классовых особенностей с разделением по категориям.
"""

import os
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Template
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


def format_features_by_category(char: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Формирует словарь с особенностями персонажа, разделёнными по категориям.
    Возвращает {'order': [], 'pact': [], 'rogue': [], 'class': []}
    """
    result = {
        'order': [],   # орден друида / жреца
        'pact': [],    # договор колдуна (возвания)
        'rogue': [],   # экспертиза и язык плута
        'class': []    # все остальные классовые особенности
    }

    # 1. Орден друида
    druid_order = char.get("druid_order")
    if druid_order:
        if druid_order == "guide":
            result['order'].append(DRUID_ORDER_GUIDE_DESC)
        elif druid_order == "guardian":
            result['order'].append(DRUID_ORDER_GUARDIAN_DESC)

    # 2. Орден жреца
    cleric_order = char.get("cleric_order")
    if cleric_order:
        if cleric_order == "protector":
            result['order'].append(CLERIC_ORDER_PROTECTOR_DESC)
        elif cleric_order == "miracle":
            result['order'].append(CLERIC_ORDER_MIRACLE_DESC)

    # 3. Договор колдуна
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

    # 4. Плут: экспертиза и язык
    rogue_expertise = char.get("rogue_expertise", [])
    if rogue_expertise:
        result['rogue'].append(ROGUE_EXPERTISE.format(skills=", ".join(rogue_expertise)))
    rogue_lang = char.get("rogue_extra_language")
    if rogue_lang:
        result['rogue'].append(ROGUE_EXTRA_LANGUAGE.format(language=rogue_lang))

    # 5. Классовые особенности (из strings.py)
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
        "STR": char.get("str", 10),
        "DEX": char.get("dex", 10),
        "CON": char.get("con", 10),
        "INT": char.get("int", 10),
        "WIS": char.get("wis", 10),
        "CHA": char.get("cha", 10),
    }

    skills = char.get("selected_skills", [])
    class_name = char.get("class_name") or "Без класса"
    race_name = char.get("race_name") or "Неизвестно"
    background_name = char.get("background_name") or "Нет"

    class_info = _class_repo.get_by_name(class_name) or {}
    saving_throws = class_info.get("saving_throws", [])
    background_info = _bg_repo.get_by_name(background_name) or {}
    background_trait = background_info.get("trait", "")
    background_description = background_info.get("description", "")
    origin_feat = background_info.get("origin_feat", "")

    # Собираем все заклинания: выбранные + автоматические
    selected_spells = char.get("selected_spells", [])
    auto_spells = char.get("auto_spells", [])
    all_spells = list(set(selected_spells + auto_spells))

    # Категоризированные особенности
    categorized_features = format_features_by_category(char)

    # Снаряжение: от класса и от предыстории
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

    # Модификаторы навыков
    skill_mods = {}
    for skill in skills:
        base_stat = "DEX"
        if skill in ["Атлетика"]:
            base_stat = "STR"
        elif skill in ["Анализ", "Знание магии", "История", "Исследование", "Природа", "Религия"]:
            base_stat = "INT"
        elif skill in ["Внимательность", "Выживание", "Медицина", "Обращение с животными", "Проницательность"]:
            base_stat = "WIS"
        elif skill in ["Выступление", "Запугивание", "Обман", "Убеждение"]:
            base_stat = "CHA"
        mod = (stats[base_stat] - 10) // 2
        if skill in saving_throws:
            mod += 2
        skill_mods[skill] = f"{mod:+d}"

    return {
        "name": char["name"],
        "class_name": class_name,
        "race": race_name,
        "level": char.get("level", 1),
        "background": background_name,
        "background_trait": background_trait,
        "background_description": background_description,
        "origin_feat": origin_feat,
        "backstory": char.get("backstory", ""),
        "stats": stats,
        "hp": char.get("hp", 0),
        "ac": char.get("ac", 10),
        "speed": char.get("speed", 30),
        "alignment": char.get("alignment", "Нейтральное"),
        "experience": char.get("experience", 0),
        "proficiency_bonus": 2,
        "saving_throws": saving_throws,
        "skills": skills,
        "equipment": equipment,
        "spells": all_spells,
        "order_features": categorized_features['order'],
        "pact_features": categorized_features['pact'],
        "rogue_features": categorized_features['rogue'],
        "class_specific_features": categorized_features['class'],
        "skill_mods": skill_mods,
        "all_skills": skills,
        "race_traits": [],          # можно заполнить из репозитория рас
        "class_features": [],       # можно заполнить из репозитория классов
        "appearance": "",
        "created_date": "недавно",
    }

# ------------------------------------------------------------------
# HTML-шаблон (можно вынести в отдельный файл, но для простоты здесь)
# ------------------------------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">

<style>
@page {
  size: A4;
  margin: 0;
}

body {
  margin: 0;
  font-family: 'Inter', sans-serif;
  background: #0f172a;
  color: white;
}

/* ===== CONTAINER ===== */

.container {
  padding: 40px;
}

/* ===== HERO BLOCK (ВАЖНО ДЛЯ PREVIEW) ===== */

.hero {
  background: linear-gradient(135deg, #7c3aed, #4f46e5);
  border-radius: 20px;
  padding: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.name {
  font-size: 42px;
  font-weight: 700;
}

.meta {
  font-size: 16px;
  opacity: 0.9;
}

.level-badge {
  background: rgba(255,255,255,0.2);
  padding: 10px 16px;
  border-radius: 12px;
  font-weight: bold;
}

/* ===== STATS STRIP ===== */

.stats {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}

.stat {
  background: rgba(255,255,255,0.05);
  border-radius: 14px;
  padding: 14px;
  text-align: center;
  width: 15%;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
}

.stat-label {
  font-size: 11px;
  opacity: 0.7;
}

/* ===== MAIN GRID ===== */

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 30px;
}

.card {
  background: rgba(255,255,255,0.05);
  border-radius: 16px;
  padding: 16px;
}

.title {
  font-weight: 600;
  margin-bottom: 10px;
  font-size: 14px;
  opacity: 0.8;
}

.content {
  font-size: 13px;
  white-space: pre-line;
}

/* ===== COMBAT BADGES ===== */

.combat {
  display: flex;
  gap: 15px;
  margin-top: 20px;
}

.badge {
  flex: 1;
  background: rgba(255,255,255,0.08);
  border-radius: 14px;
  padding: 12px;
  text-align: center;
}

.badge-value {
  font-size: 22px;
  font-weight: bold;
}

.badge-label {
  font-size: 11px;
  opacity: 0.6;
}

/* ===== FOOTER ===== */

.footer {
  text-align: center;
  margin-top: 40px;
  font-size: 11px;
  opacity: 0.5;
}

.brand {
  color: #a78bfa;
}

</style>
</head>

<body>

<div class="container">

  <!-- 🔥 HERO (ЭТО ВИДИТ TELEGRAM) -->
  <div class="hero">
    <div>
      <div class="name">{{ name }}</div>
      <div class="meta">
        {{ class }} • {{ race }}
      </div>
    </div>

    <div class="level-badge">
      LVL {{ level }}
    </div>
  </div>

  <!-- STATS -->
  <div class="stats">
    {% for key, value in stats.items() %}
    <div class="stat">
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ key }}</div>
    </div>
    {% endfor %}
  </div>

  <!-- COMBAT -->
  <div class="combat">
    <div class="badge">
      <div class="badge-value">🛡 {{ ac }}</div>
      <div class="badge-label">AC</div>
    </div>

    <div class="badge">
      <div class="badge-value">❤️ {{ hp }}</div>
      <div class="badge-label">HP</div>
    </div>

    <div class="badge">
      <div class="badge-value">⚡ {{ initiative }}</div>
      <div class="badge-label">INIT</div>
    </div>

    <div class="badge">
      <div class="badge-value">🏃 {{ speed }}</div>
      <div class="badge-label">SPEED</div>
    </div>
  </div>

  <!-- MAIN -->
  <div class="grid">

    <div class="card">
      <div class="title">Навыки</div>
      <div class="content">
{% for skill, value in skills.items() %}
{{ skill }}: {{ value }}
{% endfor %}
      </div>
    </div>

    <div class="card">
      <div class="title">Особенности</div>
      <div class="content">{{ features }}</div>
    </div>

    <div class="card">
      <div class="title">Снаряжение</div>
      <div class="content">{{ equipment }}</div>
    </div>

    <div class="card">
      <div class="title">Атаки</div>
      <div class="content">{{ attacks }}</div>
    </div>

  </div>

  <!-- FOOTER -->
  <div class="footer">
    Создано в <span class="brand">Кузнице героев ⚔️</span>
  </div>

</div>

</body>
</html>
"""


def get_template() -> Template:
    """Загружает HTML-шаблон из файла (если он есть) или возвращает встроенный."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "character_sheet.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return Template(f.read())
    else:
        # fallback – минимальный шаблон с предупреждением (обычно такого не должно быть)
        return Template("<h1>Ошибка: шаблон не найден</h1><p>{{ error }}</p>")


@app.get("/character/{char_id}", response_class=HTMLResponse)
async def character_sheet(char_id: int = Path(..., title="ID персонажа")):
    try:
        data = get_character_data(char_id)
        template = get_template()
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