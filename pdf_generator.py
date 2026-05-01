# pdf_generator.py
"""
HTML Generator Module for D&D Character Sheets
Генерирует красивый HTML-лист персонажа в стиле D&D 5e,
а также умеет конвертировать HTML в PDF через WeasyPrint.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, TemplateError
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# HTML-шаблон (ваш лист.html, адаптированный для Jinja2)
# ----------------------------------------------------------------------
DEFAULT_HTML_TEMPLATE = '''<!DOCTYPE html>
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
        /* Навыки теперь в две колонки */
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
        /* Печатная версия — логические разрывы страниц */
        @media print {
            body {
                background: white;
                padding: 0;
                margin: 0;
            }
            .sheet {
                background: white;
                box-shadow: none;
                padding: 0.6in;
                margin: 0;
            }
            /* Запрет разрыва внутри коротких блоков */
            .stats-grid, .combat-stats, .basic-info, .saves-section, .skills-section {
                break-inside: avoid;
                page-break-inside: avoid;
            }
            /* Длинные списки могут разрываться между элементами */
            .traits-list, .equipment-list, .spells-list {
                break-inside: auto;
            }
            .traits-list li, .equipment-list li, .spell-item {
                break-inside: avoid;
                page-break-inside: avoid;
            }
            /* Заголовок блока не отрывать от содержимого */
            .detail-title {
                break-after: avoid;
                page-break-after: avoid;
            }
            .skill-row {
                break-inside: avoid;
            }
            @page {
                size: A4;
                margin: 1.5cm;
            }
        }
    </style>
</head>
<body class="theme-{{ class_name | lower | replace(' ', '-') | replace('ё', 'е') }}">
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
        <div class="stat-card">
            <div class="stat-name">{{ stat }}</div>
            <div class="stat-score">{{ stats[stat] }}</div>
            <div class="stat-mod">{{ (stats[stat] - 10) // 2 }}</div>
        </div>
        {% endfor %}
    </div>
    <div class="saves-skills">
        <div class="saves-section">
            <div class="section-title"><i class="fas fa-brain"></i> СПАСБРОСКИ</div>
            {% for save in ["STR", "DEX", "CON", "INT", "WIS", "CHA"] %}
            <div class="save-row">
                <span>{% if save in saving_throws %}✓{% else %}•{% endif %} {{ save }}</span>
                <span>{% if save in saving_throws %}{{ (stats[save] - 10) // 2 + proficiency_bonus }}{% else %}{{ (stats[save] - 10) // 2 }}{% endif %}</span>
            </div>
            {% endfor %}
        </div>
        <div class="skills-section">
            <div class="section-title"><i class="fas fa-feather-alt"></i> НАВЫКИ</div>
            <div class="skills-list">
                {% for skill in all_skills %}
                <div class="skill-row">
                    <span>{% if skill in skills %}✓{% else %}•{% endif %} {{ skill }}</span>
                    <span>{{ skill_mods[skill] }}</span>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
    <div class="combat-stats">
        <div class="combat-card"><div class="combat-label"><i class="fas fa-shield-halbed"></i> КЛАСС БРОНИ</div><div class="combat-value">{{ ac }}</div></div>
        <div class="combat-card">
            <div class="combat-label"><i class="fas fa-heartbeat"></i> ХИТЫ (HP)</div>
            <div class="combat-value">{{ hp }}</div>
            <div class="hp-bar"><div class="hp-fill"></div></div>
        </div>
        <div class="combat-card"><div class="combat-label"><i class="fas fa-wind"></i> СКОРОСТЬ</div><div class="combat-value">{{ speed }} фт.</div></div>
    </div>
    {% if race_traits or class_features or background_trait or origin_feat %}
    <div class="detail-section">
        <div class="detail-title"><i class="fas fa-gem"></i> ОСОБЕННОСТИ И УМЕНИЯ</div>
        <div class="detail-content">
            <ul class="traits-list">
                {% for trait in race_traits %}<li><strong>Раса:</strong> {{ trait }}</li>{% endfor %}
                {% for feature in class_features %}<li><strong>Класс:</strong> {{ feature }}</li>{% endfor %}
                {% if background_trait %}<li><strong>Предыстория:</strong> {{ background_trait }}</li>{% endif %}
                {% if origin_feat %}<li><strong>Черта происхождения:</strong> {{ origin_feat }}</li>{% endif %}
            </ul>
        </div>
    </div>
    {% endif %}
    <div class="detail-section">
        <div class="detail-title"><i class="fas fa-backpack"></i> СНАРЯЖЕНИЕ</div>
        <div class="detail-content">
            <ul class="equipment-list">
                {% for item in equipment %}<li>{{ item }}</li>{% else %}<li>Нет снаряжения</li>{% endfor %}
            </ul>
            {% if coins %}<div style="margin-top: 12px;"><i class="fas fa-coins"></i> <strong>Монеты:</strong> {{ coins }}</div>{% endif %}
        </div>
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
        <div class="spell-slots">
            <div class="slot-level">1 уровень: {{ spell_slots_1 }} ячейки</div>
            <div class="slot-level">2 уровень: {{ spell_slots_2 }} ячеек</div>
        </div>
        <div class="spells-list">
            {% for spell in spells %}<div class="spell-item"><i class="fas fa-star-of-life"></i> {{ spell }}</div>{% endfor %}
        </div>
    </div>
    {% endif %}
    <div class="notes-section">
        <div class="detail-title"><i class="fas fa-pen-fancy"></i> ЗАМЕТКИ</div>
        <div class="detail-content">{{ notes if notes else "—" }}</div>
    </div>
    <div class="footer">
        <i class="fas fa-dice-d20"></i> D&D Character Sheet • {{ created_date }}
    </div>
</div>
</body>
</html>'''

# ----------------------------------------------------------------------
# Утилиты для шаблона
# ----------------------------------------------------------------------
def get_skill_ability(skill_name: str) -> str:
    skill_map = {
        "Акробатика": "DEX", "Атлетика": "STR", "Аркана": "INT",
        "Восприятие": "WIS", "Выживание": "WIS", "Выступление": "CHA",
        "Запугивание": "CHA", "История": "INT", "Ловкость рук": "DEX",
        "Медицина": "WIS", "Обман": "CHA", "Обращение с животными": "WIS",
        "Природа": "INT", "Проницательность": "WIS", "Расследование": "INT",
        "Религия": "INT", "Скрытность": "DEX", "Тайная магия": "INT",
        "Убеждение": "CHA"
    }
    return skill_map.get(skill_name, "WIS")

def calculate_modifier(stat_value: int) -> int:
    return (stat_value - 10) // 2

def prepare_template_data(character_data: Dict[str, Any]) -> Dict[str, Any]:
    all_skills = [
        "Акробатика", "Атлетика", "Аркана", "Восприятие", "Выживание",
        "Выступление", "Запугивание", "История", "Ловкость рук", "Медицина",
        "Обман", "Обращение с животными", "Природа", "Проницательность",
        "Расследование", "Религия", "Скрытность", "Тайная магия", "Убеждение"
    ]
    stats = character_data.get('stats', {})
    proficiency = character_data.get('proficiency_bonus', 2)
    skills_list = character_data.get('skills', [])

    skill_mods = {}
    for skill in all_skills:
        ability = get_skill_ability(skill)
        mod = calculate_modifier(stats.get(ability, 10))
        if skill in skills_list:
            mod += proficiency
        skill_mods[skill] = mod

    return {
        'name': character_data.get('name', 'Безымянный'),
        'class_name': character_data.get('class_name', 'Без класса'),
        'race': character_data.get('race', 'Неизвестно'),
        'level': character_data.get('level', 1),
        'background': character_data.get('background', 'Нет'),
        'background_trait': character_data.get('background_trait', ''),
        'background_description': character_data.get('background_description', ''),
        'origin_feat': character_data.get('origin_feat', ''),
        'backstory': character_data.get('backstory', 'Нет истории'),
        'stats': stats,
        'hp': character_data.get('hp', 0),
        'ac': character_data.get('ac', 10),
        'speed': character_data.get('speed', 30),
        'alignment': character_data.get('alignment', 'Нейтральное'),
        'player_name': character_data.get('player_name', ''),
        'appearance': character_data.get('appearance', ''),
        'experience': character_data.get('experience', 0),
        'proficiency_bonus': proficiency,
        'saving_throws': character_data.get('saving_throws', []),
        'skills': skills_list,
        'all_skills': all_skills,
        'skill_mods': skill_mods,
        'race_traits': character_data.get('race_traits', []),
        'class_features': character_data.get('class_features', []),
        'equipment': character_data.get('equipment', []),
        'coins': character_data.get('coins', ''),
        'spells': character_data.get('spells', []),
        'spell_slots_1': character_data.get('spell_slots_1', 0),
        'spell_slots_2': character_data.get('spell_slots_2', 0),
        'notes': character_data.get('notes', ''),
        'created_date': datetime.now().strftime("%d.%m.%Y")
    }

# ----------------------------------------------------------------------
# Работа с шаблоном
# ----------------------------------------------------------------------
def ensure_template_exists() -> bool:
    try:
        if not os.path.exists("templates"):
            os.makedirs("templates")
            logger.info("📁 Создана папка templates")
        template_path = "templates/character_sheet.html"
        if not os.path.exists(template_path):
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(DEFAULT_HTML_TEMPLATE)
            logger.info("📄 Создан файл шаблона character_sheet.html")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при создании шаблона: {e}")
        return False

def generate_character_html(character_data: Dict[str, Any]) -> str:
    if not ensure_template_exists():
        raise RuntimeError("Не удалось создать шаблон")
    env = Environment(loader=FileSystemLoader("templates"), autoescape=True)
    template = env.get_template("character_sheet.html")
    data = prepare_template_data(character_data)
    try:
        html = template.render(**data)
        logger.info(f"✅ HTML сгенерирован для {character_data.get('name', 'Unknown')}")
        return html
    except TemplateError as e:
        logger.error(f"❌ Ошибка рендеринга шаблона: {e}")
        raise

def generate_pdf(data: Dict[str, Any], filename: str) -> Optional[str]:
    try:
        html_content = generate_character_html(data)
        if filename.endswith('.pdf'):
            filename = filename[:-4] + '.html'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"✅ HTML сохранён: {filename}")
        return filename
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении HTML: {e}")
        return None

# ----------------------------------------------------------------------
# Конвертация HTML -> PDF
# ----------------------------------------------------------------------
def convert_html_to_pdf(html_path: str, pdf_path: str) -> bool:
    """
    Конвертирует HTML-файл в PDF с помощью WeasyPrint.
    Возвращает True при успехе.
    """
    try:
        font_config = FontConfiguration()
        css = CSS(string='@page { size: A4; margin: 1.5cm; }')
        HTML(filename=html_path).write_pdf(pdf_path, stylesheets=[css], font_config=font_config)
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            logger.info(f"✅ PDF успешно создан: {pdf_path}")
            return True
        else:
            logger.error(f"❌ PDF не создан или пуст: {pdf_path}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка конвертации HTML в PDF: {e}")
        return False

def cleanup_old_pdfs(directory: str = ".", max_age_hours: int = 24):
    import time
    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        for filename in os.listdir(directory):
            if (filename.startswith("temp_") or filename.endswith("_character_sheet")) and (filename.endswith(".html") or filename.endswith(".pdf")):
                filepath = os.path.join(directory, filename)
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    os.remove(filepath)
                    logger.info(f"🗑️ Удален старый файл: {filename}")
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке: {e}")

if __name__ == "__main__":
    # Тестовый запуск
    test_data = {
        "name": "Тестовый Герой",
        "class_name": "Воин",
        "race": "Человек",
        "level": 1,
        "background": "Солдат",
        "stats": {"STR": 16, "DEX": 14, "CON": 14, "INT": 10, "WIS": 12, "CHA": 10},
        "hp": 12,
        "ac": 16,
        "speed": 30,
        "skills": ["Атлетика", "Восприятие"],
        "equipment": ["Длинный меч", "Кольчуга"],
        "spells": [],
        "proficiency_bonus": 2,
        "saving_throws": ["STR", "CON"],
        "race_traits": ["Универсальность человечества"],
        "class_features": ["Второе дыхание", "Боевой стиль"],
        "backstory": "Родился в семье солдата...",
        "alignment": "Нейтральное",
        "player_name": "Тестер",
        "experience": 0,
        "notes": "",
        "coins": "50 ЗМ",
        "spell_slots_1": 0,
        "spell_slots_2": 0,
        "appearance": ""
    }
    html_file = generate_pdf(test_data, "test_character.html")
    if html_file:
        print(f"✅ HTML создан: {html_file}")
        pdf_file = html_file.replace('.html', '.pdf')
        if convert_html_to_pdf(html_file, pdf_file):
            print(f"✅ PDF создан: {pdf_file}")
        else:
            print("❌ Не удалось создать PDF")
    else:
        print("❌ Ошибка создания HTML")