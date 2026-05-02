# webapp.py
"""
Веб-сервер для отображения листа персонажа (Telegram Mini App)
Обновлён для отображения всех новых классовых особенностей.
"""

import os
import logging
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Path
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
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


def format_extra_features(char: Dict[str, Any]) -> List[str]:
    """Формирует список дополнительных особенностей персонажа."""
    features = []

    # 1. Орден друида
    druid_order = char.get("druid_order")
    if druid_order:
        if druid_order == "guide":
            features.append(DRUID_ORDER_GUIDE_DESC)
        elif druid_order == "guardian":
            features.append(DRUID_ORDER_GUARDIAN_DESC)

    # 2. Орден жреца
    cleric_order = char.get("cleric_order")
    if cleric_order:
        if cleric_order == "protector":
            features.append(CLERIC_ORDER_PROTECTOR_DESC)
        elif cleric_order == "miracle":
            features.append(CLERIC_ORDER_MIRACLE_DESC)

    # 3. Договор колдуна
    warlock_pact = char.get("warlock_pact")
    if warlock_pact == "tome":
        features.append(WARLOCK_PACT_TOME_DESC)
        pact_cantrips = char.get("pact_tome_cantrips", [])
        pact_rituals = char.get("pact_tome_rituals", [])
        if pact_cantrips:
            features.append(f"• Заговоры Книги теней: {', '.join(pact_cantrips)}")
        if pact_rituals:
            features.append(f"• Ритуалы Книги теней: {', '.join(pact_rituals)}")
    elif warlock_pact == "blade":
        features.append(WARLOCK_PACT_BLADE_DESC)
        blade_weapon = char.get("pact_blade_weapon")
        if blade_weapon:
            features.append(f"• Оружие договора: {blade_weapon}")
    elif warlock_pact == "chain":
        features.append(WARLOCK_PACT_CHAIN_DESC)
    elif warlock_pact == "shadow_armor":
        features.append(WARLOCK_PACT_SHADOW_ARMOR_DESC)
    elif warlock_pact == "arcane_mind":
        features.append(WARLOCK_PACT_ARCANE_MIND_DESC)

    # 4. Плут: экспертиза и язык
    rogue_expertise = char.get("rogue_expertise", [])
    if rogue_expertise:
        features.append(ROGUE_EXPERTISE.format(skills=", ".join(rogue_expertise)))
    rogue_lang = char.get("rogue_extra_language")
    if rogue_lang:
        features.append(ROGUE_EXTRA_LANGUAGE.format(language=rogue_lang))

    # 5. Особенности из strings.py (добавляем по классу)
    class_name = char.get("class_name")
    if class_name == "Артефактор":
        features.append(FEATURE_MENDING)
    elif class_name == "Бард":
        features.append(FEATURE_BARDIC_INSPIRATION)
    elif class_name == "Варвар":
        features.append(FEATURE_RAGE)
        features.append(FEATURE_UNARMORED_DEFENSE_BARBARIAN)
    elif class_name == "Воин":
        features.append(FEATURE_SECOND_WIND)
    elif class_name == "Волшебник":
        features.append(FEATURE_WIZARD_SPELLS)
        features.append(FEATURE_RITUAL_CASTER)
        features.append(FEATURE_ARCANE_RECOVERY)
    elif class_name == "Друид":
        features.append(FEATURE_DRUIDIC_LANGUAGE)
        features.append(FEATURE_SPEAK_WITH_ANIMALS)
    elif class_name == "Монах":
        features.append(MONK_MARTIAL_ARTS)
    elif class_name == "Паладин":
        hp_reserve = char.get("level", 1) * 5
        features.append(PALADIN_LAY_ON_HANDS.format(hp_reserve=hp_reserve))
    elif class_name == "Плут":
        # Урон коварной атаки для 1 уровня – 1к6, растёт с уровнем (можно динамически)
        features.append(ROGUE_SNEAK_ATTACK.format(damage_dice="1к6"))
        features.append(ROGUE_THIEVES_CANT)
    elif class_name == "Следопыт":
        features.append(RANGER_HUNTERS_MARK)
    elif class_name == "Чародей":
        features.append(SORCERER_MAGIC_RELEASE)

    return features


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

    # Дополнительные особенности (ордены, договоры, экспертиза и т.д.)
    extra_features = format_extra_features(char)

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
        "proficiency_bonus": 2,  # можно вычислить по уровню, но для 1-го уровня 2
        "saving_throws": saving_throws,
        "skills": skills,
        "equipment": [char.get("selected_weapon"), char.get("selected_armor")] if char.get("selected_weapon") or char.get("selected_armor") else [],
        "spells": all_spells,
        "extra_features": extra_features,
    }

# ------------------------------------------------------------------
# HTML-шаблон (можно вынести в отдельный файл, но для простоты здесь)
# ------------------------------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>{{ name }} — D&D Character Sheet</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700;800;900&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap" rel="stylesheet">
    <style>
        :root {
            --accent: #b57c48;
            --accent-dark: #7a4c2a;
            --accent-bg: rgba(181, 124, 72, 0.15);
            --paper: #fef7e8;
            --paper-dark: #f0e2cf;
            --text-dark: #2c1a0e;
            --text-muted: #6b4c34;
        }
        body.theme-warrior { --accent: #9b2e2e; --accent-dark: #631c1c; }
        body.theme-wizard { --accent: #2c5f8a; --accent-dark: #1a3d5a; }
        body.theme-cleric { --accent: #dbb42c; --accent-dark: #a07f1a; }
        body.theme-rogue  { --accent: #4e6a5e; --accent-dark: #2e423a; }
        body.theme-druid  { --accent: #4f7942; --accent-dark: #2e4a24; }
        body.theme-barbarian { --accent: #c97e3a; --accent-dark: #8a521f; }
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Cormorant Garamond', 'Georgia', serif;
            background: #1c1610;
            background-image: radial-gradient(circle at 25% 40%, rgba(150, 110, 70, 0.25) 2%, transparent 2.5%);
            background-size: 48px 48px;
            padding: 24px 16px;
            min-height: 100vh;
        }
        .sheet {
            max-width: 1100px;
            margin: 0 auto;
            background: linear-gradient(145deg, var(--paper) 0%, var(--paper-dark) 100%);
            border-radius: 28px;
            position: relative;
            box-shadow: 0 25px 40px -12px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,245,225,0.7);
            padding: 28px 24px;
            isolation: isolate;
        }
        .print-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--accent-dark);
            color: white;
            border: none;
            border-radius: 50px;
            padding: 12px 24px;
            font-family: 'Cinzel', serif;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: transform 0.2s;
        }
        .print-btn:hover { transform: scale(1.05); }
        @media print { .print-btn { display: none; } }
        .sheet::after {
            content: "🎲";
            font-size: 200px;
            position: absolute;
            bottom: 10px;
            right: 10px;
            opacity: 0.06;
            pointer-events: none;
            font-family: 'Segoe UI', system-ui;
            transform: rotate(-12deg);
            z-index: 0;
        }
        .corner {
            position: absolute;
            width: 50px;
            height: 50px;
            border-style: solid;
            border-color: var(--accent);
            opacity: 0.5;
            pointer-events: none;
            z-index: 2;
        }
        .corner-tl { top: 16px; left: 16px; border-top-width: 3px; border-left-width: 3px; }
        .corner-tr { top: 16px; right: 16px; border-top-width: 3px; border-right-width: 3px; }
        .corner-bl { bottom: 16px; left: 16px; border-bottom-width: 3px; border-left-width: 3px; }
        .corner-br { bottom: 16px; right: 16px; border-bottom-width: 3px; border-right-width: 3px; }
        .header {
            border-bottom: 3px solid var(--accent);
            margin-bottom: 28px;
            padding-bottom: 12px;
            position: relative;
            z-index: 2;
        }
        .header h1 {
            font-family: 'Cinzel', serif;
            font-size: 38px;
            font-weight: 800;
            color: var(--text-dark);
            text-transform: uppercase;
            letter-spacing: 4px;
            text-shadow: 2px 2px 0 rgba(110, 70, 30, 0.15);
            word-break: break-word;
        }
        .basic-info {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 32px;
            background: var(--accent-bg);
            backdrop-filter: blur(2px);
            padding: 18px;
            border-radius: 24px;
            border: 1px solid rgba(220, 200, 160, 0.6);
            position: relative;
            z-index: 2;
        }
        .info-row { margin-bottom: 12px; }
        .info-label {
            font-family: 'Cinzel', serif;
            font-weight: 700;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--accent-dark);
        }
        .info-label i { margin-right: 6px; font-size: 10px; }
        .info-value {
            font-size: 16px;
            border-bottom: 1px solid #cfb991;
            padding: 5px 4px;
            font-weight: 600;
            color: var(--text-dark);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 14px;
            margin-bottom: 32px;
            position: relative;
            z-index: 2;
        }
        .stat-card {
            background: rgba(250, 240, 225, 0.9);
            text-align: center;
            padding: 12px 5px;
            border-radius: 32px;
            border-bottom: 4px solid var(--accent);
            box-shadow: 0 5px 10px rgba(0,0,0,0.1);
            transition: transform 0.15s;
        }
        .stat-card:hover { transform: translateY(-3px); }
        .stat-name {
            font-family: 'Cinzel', serif;
            font-size: 14px;
            font-weight: bold;
            color: var(--accent-dark);
        }
        .stat-score {
            font-size: 34px;
            font-weight: 800;
            margin: 5px 0;
            color: var(--text-dark);
        }
        .stat-mod {
            background: var(--accent-dark);
            color: #fef0df;
            display: inline-block;
            width: 36px;
            height: 36px;
            line-height: 36px;
            clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
            font-size: 18px;
            font-weight: bold;
            margin-top: 4px;
            box-shadow: inset 0 1px 0 rgba(255,255,200,0.3), 0 2px 4px rgba(0,0,0,0.2);
        }
        .saves-skills {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 24px;
            margin-bottom: 32px;
            position: relative;
            z-index: 2;
        }
        .saves-section, .skills-section {
            background: rgba(255, 250, 240, 0.8);
            backdrop-filter: blur(2px);
            padding: 18px;
            border-radius: 24px;
            border: 1px solid #e2cfb0;
            box-shadow: 0 5px 12px rgba(0,0,0,0.05);
        }
        .section-title {
            font-family: 'Cinzel', serif;
            font-size: 15px;
            font-weight: bold;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 8px;
            margin-bottom: 16px;
            letter-spacing: 1px;
            color: var(--text-dark);
        }
        .section-title i { margin-right: 8px; color: var(--accent); }
        .save-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px dotted #cfbc9a;
            font-size: 15px;
            font-weight: 500;
        }
        .skills-list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 4px 12px;
        }
        .skill-row {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            break-inside: avoid;
            page-break-inside: avoid;
            border-bottom: 1px dotted #cfbc9a;
            font-size: 15px;
            font-weight: 500;
        }
        .combat-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 32px;
            position: relative;
            z-index: 2;
        }
        .combat-card {
            background: linear-gradient(145deg, #f7eedc, #efe2ce);
            text-align: center;
            padding: 16px 12px;
            border-radius: 48px;
            border-bottom: 4px solid var(--accent);
            box-shadow: 0 8px 12px rgba(0,0,0,0.1);
        }
        .combat-label {
            font-family: 'Cinzel', serif;
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--accent-dark);
        }
        .combat-value {
            font-size: 40px;
            font-weight: 800;
            color: var(--text-dark);
            line-height: 1.2;
        }
        .hp-bar {
            margin-top: 8px;
            height: 8px;
            background: #d9c29e;
            border-radius: 20px;
            overflow: hidden;
            width: 85%;
            margin-left: auto;
            margin-right: auto;
        }
        .hp-fill {
            width: 70%;
            height: 100%;
            background: #b3432c;
            border-radius: 20px;
            box-shadow: inset 0 1px 1px rgba(0,0,0,0.2);
        }
        .detail-section { margin-bottom: 28px; position: relative; z-index: 2; }
        .detail-title {
            font-family: 'Cinzel', serif;
            font-size: 16px;
            font-weight: bold;
            background: var(--accent-dark);
            color: #fef0dd;
            padding: 6px 20px 6px 24px;
            border-radius: 40px;
            display: inline-block;
            letter-spacing: 1.5px;
            margin-bottom: 14px;
            box-shadow: 0 3px 6px rgba(0,0,0,0.2);
        }
        .detail-title i { margin-right: 10px; }
        .detail-content {
            background: rgba(255, 250, 240, 0.85);
            padding: 18px;
            border-radius: 24px;
            border: 1px solid #e2cfb0;
        }
        .traits-list, .equipment-list {
            list-style: none;
            padding-left: 0;
        }
        .traits-list li, .equipment-list li {
            padding: 6px 0 6px 20px;
            border-bottom: 1px dotted #cfbc9a;
            position: relative;
        }
        .traits-list li::before, .equipment-list li::before {
            content: "✧";
            color: var(--accent);
            position: absolute;
            left: 0;
        }
        .spells-section { margin-bottom: 28px; position: relative; z-index: 2; }
        .spell-slots {
            display: flex;
            gap: 18px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        .slot-level {
            background: var(--accent-dark);
            color: #fff0e0;
            padding: 5px 16px;
            border-radius: 60px;
            font-size: 14px;
            font-weight: 600;
        }
        .spells-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 8px;
        }
        .spell-item {
            background: #e7dbc8;
            padding: 6px 14px;
            border-radius: 28px;
            font-size: 13px;
            border-left: 5px solid var(--accent);
        }
        .notes-section {
            background: rgba(255, 250, 240, 0.85);
            padding: 8px 18px 18px 18px;
            border-radius: 24px;
            margin-bottom: 24px;
            border: 1px solid #e2cfb0;
            position: relative;
            z-index: 2;
        }
        .footer {
            text-align: center;
            font-size: 11px;
            color: #b5916a;
            margin-top: 28px;
            padding-top: 14px;
            border-top: 1px solid #dccaa8;
            font-style: italic;
            position: relative;
            z-index: 2;
        }
        @media (max-width: 750px) {
            body { padding: 12px; }
            .sheet { padding: 18px 16px; }
            .stats-grid { grid-template-columns: repeat(3, 1fr); gap: 10px; }
            .saves-skills { grid-template-columns: 1fr; gap: 18px; }
            .skills-list { grid-template-columns: 1fr; }
            .combat-stats { grid-template-columns: 1fr; gap: 12px; }
            .basic-info { grid-template-columns: 1fr; gap: 12px; }
            .stat-score { font-size: 28px; }
            .combat-value { font-size: 32px; }
            .header h1 { font-size: 28px; }
            .corner { width: 35px; height: 35px; }
            .sheet::after { font-size: 130px; bottom: 0; right: 0; }
        }
        @media print {
            body { background: white; padding: 0; margin: 0; }
            .sheet { background: white; box-shadow: none; padding: 0.6in; margin: 0; }
            .stats-grid, .combat-stats, .basic-info, .saves-section, .skills-section {
                break-inside: avoid; page-break-inside: avoid;
            }
            .traits-list, .equipment-list, .spells-list { break-inside: auto; }
            .traits-list li, .equipment-list li, .spell-item {
                break-inside: avoid; page-break-inside: avoid;
            }
            .detail-title { break-after: avoid; page-break-after: avoid; }
            .skill-row { break-inside: avoid; }
            @page { size: A4; margin: 1.5cm; }
        }
    </style>
</head>
<body class="theme-{{ class_name | lower | replace(' ', '-') | replace('ё', 'е') }}">
<div style="position: fixed; bottom: 20px; right: 20px; z-index: 1000; display: flex; flex-direction: column; align-items: flex-end; gap: 8px;">
    <button class="print-btn" type="button" onclick="window.print();">
        <i class="fas fa-print"></i> Сохранить как PDF
    </button>
    <div style="background: rgba(0,0,0,0.7); color: #ffdd99; padding: 6px 12px; border-radius: 20px; font-size: 12px; text-align: right; max-width: 260px;">
        📱 На телефоне: откройте файл → меню (три точки) → «Печать» → «Сохранить как PDF»<br>
        💻 На компьютере: Ctrl+P → «Сохранить как PDF»
    </div>
</div>
<div class="sheet">
    <div class="corner corner-tl"></div>
    <div class="corner corner-tr"></div>
    <div class="corner corner-bl"></div>
    <div class="corner corner-br"></div>
    <div class="header"><h1>{{ name }}</h1></div>
    <div class="basic-info">
        <div><div class="info-row"><div class="info-label"><i class="fas fa-shield-alt"></i> КЛАСС И УРОВЕНЬ</div><div class="info-value">{{ class_name }} • Уровень {{ level }}</div></div>
        <div class="info-row"><div class="info-label"><i class="fas fa-scroll"></i> ПРЕДЫСТОРИЯ</div><div class="info-value">{{ background }}</div></div>
        <div class="info-row"><div class="info-label"><i class="fas fa-balance-scale"></i> МИРОВОЗЗРЕНИЕ</div><div class="info-value">{{ alignment }}</div></div></div>
        <div><div class="info-row"><div class="info-label"><i class="fas fa-dragon"></i> РАСА</div><div class="info-value">{{ race }}</div></div>
        <div class="info-row"><div class="info-label"><i class="fas fa-chart-line"></i> ОПЫТ</div><div class="info-value">{{ experience }} XP</div></div></div>
        <div><div class="info-row"><div class="info-label"><i class="fas fa-user-circle"></i> ВНЕШНОСТЬ</div><div class="info-value">{{ appearance if appearance else "—" }}</div></div></div>
    </div>
    <div class="stats-grid">
        {% set stat_names = ["STR", "DEX", "CON", "INT", "WIS", "CHA"] %}
        {% for stat in stat_names %}
        <div class="stat-card"><div class="stat-name">{{ stat }}</div><div class="stat-score">{{ stats[stat] }}</div><div class="stat-mod">{{ (stats[stat] - 10) // 2 }}</div></div>
        {% endfor %}
    </div>
    <div class="saves-skills">
        <div class="saves-section">
            <div class="section-title"><i class="fas fa-brain"></i> СПАСБРОСКИ</div>
            {% for save in ["STR", "DEX", "CON", "INT", "WIS", "CHA"] %}
            <div class="save-row"><span>{% if save in saving_throws %}✓{% else %}•{% endif %} {{ save }}</span><span>{% if save in saving_throws %}{{ (stats[save] - 10) // 2 + proficiency_bonus }}{% else %}{{ (stats[save] - 10) // 2 }}{% endif %}</span></div>
            {% endfor %}
        </div>
        <div class="skills-section">
            <div class="section-title"><i class="fas fa-feather-alt"></i> НАВЫКИ</div>
            <div class="skills-list">
                {% for skill in all_skills %}
                <div class="skill-row"><span>{% if skill in skills %}✓{% else %}•{% endif %} {{ skill }}</span><span>{{ skill_mods[skill] }}</span></div>
                {% endfor %}
            </div>
        </div>
    </div>
    <div class="combat-stats">
        <div class="combat-card"><div class="combat-label"><i class="fas fa-shield-halbed"></i> КЛАСС БРОНИ</div><div class="combat-value">{{ ac }}</div></div>
        <div class="combat-card"><div class="combat-label"><i class="fas fa-heartbeat"></i> ХИТЫ (HP)</div><div class="combat-value">{{ hp }}</div><div class="hp-bar"><div class="hp-fill"></div></div></div>
        <div class="combat-card"><div class="combat-label"><i class="fas fa-wind"></i> СКОРОСТЬ</div><div class="combat-value">{{ speed }} фт.</div></div>
    </div>
    {% if race_traits or class_features or background_trait or origin_feat %}
    <div class="detail-section">
        <div class="detail-title"><i class="fas fa-gem"></i> ОСОБЕННОСТИ И УМЕНИЯ</div>
        <div class="detail-content"><ul class="traits-list">
            {% for trait in race_traits %}<li><strong>Раса:</strong> {{ trait }}</li>{% endfor %}
            {% for feature in class_features %}<li><strong>Класс:</strong> {{ feature }}</li>{% endfor %}
            {% if background_trait %}<li><strong>Предыстория:</strong> {{ background_trait }}</li>{% endif %}
            {% if origin_feat %}<li><strong>Черта происхождения:</strong> {{ origin_feat }}</li>{% endif %}
        </ul></div>
    </div>
    {% endif %}
    <div class="detail-section">
        <div class="detail-title"><i class="fas fa-backpack"></i> СНАРЯЖЕНИЕ</div>
        <div class="detail-content"><ul class="equipment-list">
            {% for item in equipment %}<li>{{ item }}</li>{% else %}<li>Нет снаряжения</li>{% endfor %}
        </ul>{% if coins %}<div style="margin-top: 12px;"><i class="fas fa-coins"></i> <strong>Монеты:</strong> {{ coins }}</div>{% endif %}</div>
    </div>
    <div class="detail-section">
        <div class="detail-title"><i class="fas fa-history"></i> ПРЕДЫСТОРИЯ</div>
        <div class="detail-content">
            {% if background_description %}<p><strong>Описание:</strong> {{ background_description }}</p>{% endif %}
            <p><strong>История:</strong> {{ backstory }}</p>
        </div>
    </div>
    {% if spells and spells|length > 0 %}
    <div class="spells-section">
        <div class="detail-title"><i class="fas fa-magic"></i> ЗАКЛИНАНИЯ</div>
        <div class="spell-slots"><div class="slot-level">1 уровень: {{ spell_slots_1 }} ячейки</div><div class="slot-level">2 уровень: {{ spell_slots_2 }} ячеек</div></div>
        <div class="spells-list">{% for spell in spells %}<div class="spell-item"><i class="fas fa-star-of-life"></i> {{ spell }}</div>{% endfor %}</div>
    </div>
    {% endif %}
    <div class="notes-section"><div class="detail-title"><i class="fas fa-pen-fancy"></i> ЗАМЕТКИ</div><div class="detail-content">{{ notes if notes else "—" }}</div></div>
    <div class="footer"><i class="fas fa-dice-d20"></i> D&D Character Sheet • {{ created_date }}</div>
</div>
</body>
</html>
"""

from pdf_generator import generate_character_html


@app.get("/character/{char_id}", response_class=HTMLResponse)
async def character_sheet(char_id: int = Path(..., title="ID персонажа")):
    try:
        data = get_character_data(char_id)
        # Передаём в шаблон дополнительные переменные для совместимости
        data["all_skills"] = data["skills"]  # для цикла в шаблоне
        data["skill_mods"] = {skill: f"{((data['stats'][skill[:3]] - 10)//2) + (2 if skill in data['saving_throws'] else 0)}" for skill in data["skills"]}  # упрощённо
        data["race_traits"] = []  # можно добавить из репозитория рас
        data["class_features"] = []
        data["appearance"] = ""
        data["created_date"] = "недавно"
        html = generate_character_html(data)  # можно заменить на рендеринг через Jinja2, но пока оставим как есть
        return HTMLResponse(content=html)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка рендеринга страницы: {e}")
        return HTMLResponse(content=f"<h1>Ошибка</h1><p>{str(e)}</p>", status_code=500)


def run_webapp():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")