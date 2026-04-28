# pdf_generator.py
"""
PDF Generator Module for D&D Character Sheets
Модуль для генерации PDF листов персонажей D&D в стиле официальных листов
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, TemplateError
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML шаблон для персонажа в стиле D&D
DEFAULT_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ name }} - D&D Character Sheet</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Times New Roman', 'Georgia', 'Arial', serif;
            background: #f5f0e8;
            padding: 20px;
        }

        .sheet {
            max-width: 1100px;
            margin: 0 auto;
            background: #faf8f0;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            padding: 20px;
        }

        .header {
            border-bottom: 2px solid #8b4513;
            margin-bottom: 20px;
            padding-bottom: 10px;
        }

        .header h1 {
            font-size: 28px;
            color: #2c1810;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .basic-info {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
            background: #f0ebdf;
            padding: 15px;
            border-radius: 5px;
        }

        .info-row {
            margin-bottom: 8px;
        }

        .info-label {
            font-weight: bold;
            font-size: 10px;
            text-transform: uppercase;
            color: #8b4513;
            letter-spacing: 1px;
        }

        .info-value {
            font-size: 14px;
            border-bottom: 1px solid #c4b89c;
            padding: 4px;
            font-weight: bold;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: #f0ebdf;
            text-align: center;
            padding: 10px;
            border: 1px solid #c4b89c;
            border-radius: 5px;
        }

        .stat-name {
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            color: #8b4513;
        }

        .stat-score {
            font-size: 28px;
            font-weight: bold;
            margin: 5px 0;
        }

        .stat-mod {
            font-size: 14px;
            color: #555;
        }

        .saves-skills {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .saves-section, .skills-section {
            background: #f0ebdf;
            padding: 15px;
            border-radius: 5px;
        }

        .section-title {
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            border-bottom: 2px solid #8b4513;
            padding-bottom: 5px;
            margin-bottom: 10px;
            color: #2c1810;
        }

        .save-row, .skill-row {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            border-bottom: 1px dotted #c4b89c;
            font-size: 12px;
        }

        .combat-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }

        .combat-card {
            background: #f0ebdf;
            text-align: center;
            padding: 10px;
            border-radius: 5px;
        }

        .combat-label {
            font-size: 10px;
            text-transform: uppercase;
            color: #8b4513;
        }

        .combat-value {
            font-size: 24px;
            font-weight: bold;
        }

        .detail-section {
            margin-bottom: 20px;
        }

        .detail-title {
            font-size: 14px;
            font-weight: bold;
            text-transform: uppercase;
            background: #2c1810;
            color: #faf8f0;
            padding: 5px 10px;
            margin-bottom: 10px;
        }

        .detail-content {
            background: #f0ebdf;
            padding: 15px;
            border-radius: 5px;
            font-size: 12px;
            line-height: 1.5;
        }

        .equipment-list, .traits-list {
            list-style: none;
            padding: 0;
        }

        .equipment-list li, .traits-list li {
            padding: 4px 0;
            border-bottom: 1px dotted #c4b89c;
        }

        .notes-section {
            background: #f0ebdf;
            padding: 15px;
            border-radius: 5px;
            min-height: 100px;
            margin-bottom: 20px;
        }

        .spells-section {
            margin-bottom: 20px;
        }

        .spell-slots {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }

        .slot-level {
            background: #2c1810;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
        }

        .spells-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 5px;
        }

        .spell-item {
            background: #e8e0d0;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 11px;
        }

        .footer {
            text-align: center;
            font-size: 10px;
            color: #999;
            margin-top: 20px;
            padding-top: 10px;
            border-top: 1px solid #c4b89c;
        }

        @media print {
            body {
                background: white;
                padding: 0;
            }
            .sheet {
                box-shadow: none;
                padding: 0;
            }
        }
    </style>
</head>
<body>
    <div class="sheet">
        <div class="header">
            <h1>{{ name }}</h1>
        </div>

        <div class="basic-info">
            <div>
                <div class="info-row">
                    <div class="info-label">КЛАСС И УРОВЕНЬ</div>
                    <div class="info-value">{{ class_name }} • Уровень {{ level }}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">ПРЕДЫСТОРИЯ</div>
                    <div class="info-value">{{ background }}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">МИРОВОЗЗРЕНИЕ</div>
                    <div class="info-value">{{ alignment }}</div>
                </div>
            </div>
            <div>
                <div class="info-row">
                    <div class="info-label">РАСА</div>
                    <div class="info-value">{{ race }}</div>
                </div>
                <div class="info-row">
                    <div class="info-label">ОПЫТ</div>
                    <div class="info-value">{{ experience }} / 300 XP</div>
                </div>
            </div>
            <div>
                <div class="info-row">
                    <div class="info-label">ВНЕШНОСТЬ</div>
                    <div class="info-value">{{ appearance if appearance else "—" }}</div>
                </div>
            </div>
        </div>

        <div class="stats-grid">
            {% set stat_names = ["STR", "DEX", "CON", "INT", "WIS", "CHA"] %}
            {% for stat in stat_names %}
            <div class="stat-card">
                <div class="stat-name">{{ stat }}</div>
                <div class="stat-score">{{ stats[stat] }}</div>
                <div class="stat-mod">({{ (stats[stat] - 10) // 2 }})</div>
            </div>
            {% endfor %}
        </div>

        <div class="saves-skills">
            <div class="saves-section">
                <div class="section-title">СПАСБРОСКИ</div>
                {% for save in ["STR", "DEX", "CON", "INT", "WIS", "CHA"] %}
                <div class="save-row">
                    <span>{% if save in saving_throws %}✓{% else %}•{% endif %} {{ save }}</span>
                    <span>{% if save in saving_throws %}{{ (stats[save] - 10) // 2 + proficiency_bonus }}{% else %}{{ (stats[save] - 10) // 2 }}{% endif %}</span>
                </div>
                {% endfor %}
            </div>
            <div class="skills-section">
                <div class="section-title">НАВЫКИ</div>
                {% for skill in all_skills %}
                <div class="skill-row">
                    <span>{% if skill in skills %}✓{% else %}•{% endif %} {{ skill }}</span>
                    <span>{{ calculate_skill_mod(skill, stats, proficiency_bonus if skill in skills else 0) }}</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="combat-stats">
            <div class="combat-card">
                <div class="combat-label">КЛАСС БРОНИ (AC)</div>
                <div class="combat-value">{{ ac }}</div>
            </div>
            <div class="combat-card">
                <div class="combat-label">ХИТЫ (HP)</div>
                <div class="combat-value">{{ hp }}</div>
            </div>
            <div class="combat-card">
                <div class="combat-label">СКОРОСТЬ</div>
                <div class="combat-value">{{ speed }} фт.</div>
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-title">ОСОБЕННОСТИ И УМЕНИЯ</div>
            <div class="detail-content">
                <ul class="traits-list">
                    {% for trait in race_traits %}
                    <li><strong>Раса:</strong> {{ trait }}</li>
                    {% endfor %}
                    {% for feature in class_features %}
                    <li><strong>Класс:</strong> {{ feature }}</li>
                    {% endfor %}
                    {% if background_trait %}
                    <li><strong>Предыстория:</strong> {{ background_trait }}</li>
                    {% endif %}
                </ul>
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-title">СНАРЯЖЕНИЕ</div>
            <div class="detail-content">
                <ul class="equipment-list">
                    {% for item in equipment %}
                    <li>{{ item }}</li>
                    {% else %}
                    <li>Нет снаряжения</li>
                    {% endfor %}
                </ul>
                {% if coins %}
                <div style="margin-top: 10px;">
                    <strong>Монеты:</strong> {{ coins }}
                </div>
                {% endif %}
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-title">ПРЕДЫСТОРИЯ И ЛИЧНЫЕ КАЧЕСТВА</div>
            <div class="detail-content">
                {% if background_description %}
                <p><strong>Описание предыстории:</strong></p>
                <p>{{ background_description }}</p>
                {% endif %}
                <p><strong>История персонажа:</strong></p>
                <p>{{ backstory }}</p>
            </div>
        </div>

        {% if spells and spells|length > 0 %}
        <div class="spells-section">
            <div class="detail-title">ЗАКЛИНАНИЯ</div>
            <div class="spell-slots">
                <div class="slot-level">1-й уровень: {{ spell_slots_1 }} ячейки</div>
                <div class="slot-level">2-й уровень: {{ spell_slots_2 }} ячеек</div>
            </div>
            <div class="spells-list">
                {% for spell in spells %}
                <div class="spell-item">✨ {{ spell }}</div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <div class="notes-section">
            <div class="detail-title">ЗАМЕТКИ</div>
            <div class="detail-content">
                {{ notes if notes else "—" }}
            </div>
        </div>

        <div class="footer">
            <p>D&D Character Sheet • Создано в D&D Character Creator • {{ created_date }}</p>
        </div>
    </div>
</body>
</html>
'''


def get_jinja_env():
    """Создает и возвращает окружение Jinja2"""
    if not os.path.exists("templates"):
        os.makedirs("templates")
        logger.info("✅ Создана папка templates")

    template_path = "templates/character.html"
    if not os.path.exists(template_path):
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(DEFAULT_HTML_TEMPLATE)
        logger.info("✅ Создан файл шаблона character.html")

    return Environment(loader=FileSystemLoader("templates"), autoescape=True)


def ensure_template_exists() -> bool:
    """Проверяет существование шаблона и создает его при необходимости"""
    try:
        template_path = "templates/character.html"

        if not os.path.exists("templates"):
            os.makedirs("templates")
            logger.info("📁 Создана папка templates")

        if not os.path.exists(template_path):
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(DEFAULT_HTML_TEMPLATE)
            logger.info("📄 Создан файл шаблона character.html")
            return True

        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при создании шаблона: {e}")
        return False


def get_skill_ability(skill_name: str) -> str:
    """
    Определяет, какая характеристика отвечает за навык

    Args:
        skill_name: название навыка на русском

    Returns:
        str: название характеристики (STR, DEX, CON, INT, WIS, CHA)
    """
    skill_map = {
        "Акробатика": "DEX",
        "Атлетика": "STR",
        "Аркана": "INT",
        "Восприятие": "WIS",
        "Выживание": "WIS",
        "Выступление": "CHA",
        "Запугивание": "CHA",
        "История": "INT",
        "Ловкость рук": "DEX",
        "Медицина": "WIS",
        "Обман": "CHA",
        "Обращение с животными": "WIS",
        "Природа": "INT",
        "Проницательность": "WIS",
        "Расследование": "INT",
        "Религия": "INT",
        "Скрытность": "DEX",
        "Тайная магия": "INT",
        "Убеждение": "CHA"
    }
    return skill_map.get(skill_name, "WIS")


def calculate_modifier(stat_value: int) -> int:
    """
    Рассчитывает модификатор характеристики

    Args:
        stat_value: значение характеристики (например, 15)

    Returns:
        int: модификатор (например, 2)
    """
    return (stat_value - 10) // 2


def prepare_pdf_data(character_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Подготавливает данные для PDF шаблона с значениями по умолчанию

    Args:
        character_data: сырые данные персонажа

    Returns:
        Dict[str, Any]: подготовленные данные для шаблона
    """
    # Полный список навыков для отображения
    all_skills = [
        "Акробатика", "Атлетика", "Аркана", "Восприятие", "Выживание",
        "Выступление", "Запугивание", "История", "Ловкость рук", "Медицина",
        "Обман", "Обращение с животными", "Природа", "Проницательность",
        "Расследование", "Религия", "Скрытность", "Тайная магия", "Убеждение"
    ]

    def calculate_skill_mod(skill: str, stats: Dict[str, int], prof_bonus: int) -> int:
        """Вспомогательная функция для расчёта модификатора навыка"""
        ability = get_skill_ability(skill)
        mod = calculate_modifier(stats.get(ability, 10))
        if prof_bonus > 0:
            mod += prof_bonus
        return mod

    # Подготавливаем данные с значениями по умолчанию
    stats = character_data.get('stats', {})
    if not stats:
        stats = {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10}

    return {
        'name': character_data.get('name', 'Безымянный'),
        'class_name': character_data.get('class_name', 'Без класса'),
        'race': character_data.get('race', 'Неизвестно'),
        'level': character_data.get('level', 1),
        'background': character_data.get('background', 'Нет'),
        'background_trait': character_data.get('background_trait', 'Нет'),
        'background_description': character_data.get('background_description', ''),
        'backstory': character_data.get('backstory', 'Нет истории'),
        'stats': stats,
        'hp': character_data.get('hp', 0),
        'ac': character_data.get('ac', 10),
        'speed': character_data.get('speed', 30),
        'alignment': character_data.get('alignment', 'Нейтральное'),
        'player_name': character_data.get('player_name', ''),
        'appearance': character_data.get('appearance', ''),
        'experience': character_data.get('experience', 0),
        'proficiency_bonus': character_data.get('proficiency_bonus', 2),
        'saving_throws': character_data.get('saving_throws', []),
        'skills': character_data.get('skills', []),
        'all_skills': all_skills,
        'calculate_skill_mod': calculate_skill_mod,
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


def generate_pdf(data: Dict[str, Any], filename: str) -> Optional[str]:
    """
    Генерирует PDF файл с листом персонажа в стиле D&D

    Args:
        data: словарь с данными персонажа
        filename: имя файла для сохранения PDF

    Returns:
        str: путь к созданному файлу или None при ошибке
    """
    try:
        if not ensure_template_exists():
            logger.error("❌ Не удалось создать/найти шаблон")
            return None

        # Валидация входных данных
        required_fields = ['name', 'class_name', 'race', 'level', 'stats', 'hp', 'ac']
        for field in required_fields:
            if field not in data:
                logger.error(f"❌ Отсутствует обязательное поле: {field}")
                return None

        required_stats = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
        for stat in required_stats:
            if stat not in data['stats']:
                logger.error(f"❌ Отсутствует характеристика: {stat}")
                return None

        env = get_jinja_env()
        template = env.get_template("character.html")

        # Подготавливаем данные для шаблона
        template_data = prepare_pdf_data(data)

        try:
            html_content = template.render(**template_data)
            logger.info(f"✅ HTML сгенерирован для {data['name']}")
        except TemplateError as e:
            logger.error(f"❌ Ошибка рендеринга шаблона: {e}")
            return None

        try:
            font_config = FontConfiguration()
            html = HTML(string=html_content)

            # CSS для печати
            css = CSS(string='''
                @page {
                    size: A4;
                    margin: 1.5cm;
                }
                body {
                    margin: 0;
                    padding: 0;
                }
            ''')

            html.write_pdf(filename, stylesheets=[css], font_config=font_config)

            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                logger.info(f"✅ PDF создан: {filename} (размер: {os.path.getsize(filename)} байт)")
                return filename
            else:
                logger.error(f"❌ Файл PDF не создан или пуст: {filename}")
                return None

        except Exception as e:
            logger.error(f"❌ Ошибка при создании PDF: {e}")
            return None

    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка в generate_pdf: {e}")
        return None


def generate_pdf_from_template(template_name: str, data: Dict[str, Any], filename: str) -> Optional[str]:
    """
    Генерирует PDF используя указанный шаблон

    Args:
        template_name: имя файла шаблона
        data: данные для шаблона
        filename: имя выходного файла

    Returns:
        str: путь к файлу или None при ошибке
    """
    try:
        if not ensure_template_exists():
            return None

        env = get_jinja_env()
        template = env.get_template(template_name)
        html_content = template.render(**data)

        HTML(string=html_content).write_pdf(filename)

        if os.path.exists(filename):
            return filename
        return None

    except Exception as e:
        logger.error(f"❌ Ошибка в generate_pdf_from_template: {e}")
        return None


def cleanup_old_pdfs(directory: str = ".", max_age_hours: int = 24):
    """
    Очищает старые PDF файлы

    Args:
        directory: директория для очистки
        max_age_hours: максимальный возраст файла в часах
    """
    import time

    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        for filename in os.listdir(directory):
            if (filename.startswith("temp_") or filename.endswith("_character_sheet.pdf")) and filename.endswith(
                    ".pdf"):
                filepath = os.path.join(directory, filename)
                file_age = current_time - os.path.getmtime(filepath)

                if file_age > max_age_seconds:
                    os.remove(filepath)
                    logger.info(f"🗑️ Удален старый PDF: {filename}")

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке PDF: {e}")


# =========================================================
# ТЕСТИРОВАНИЕ
# =========================================================

if __name__ == "__main__":
    print("=== Тестирование PDF Generator ===\n")

    test_data = {
        "name": "Арагорн",
        "class_name": "Следопыт",
        "race": "Человек",
        "level": 3,
        "background": "Стражник",
        "background_trait": "Бдительный",
        "background_description": "Вы прошли через множество сражений и научились выживать в самых опасных условиях.",
        "backstory": "Родился в семье лесничих, с детства учился выживать в дикой природе. После нападения орков на деревню поклялся защищать невинных.",
        "stats": {
            "STR": 16,
            "DEX": 14,
            "CON": 15,
            "INT": 12,
            "WIS": 13,
            "CHA": 11
        },
        "hp": 32,
        "ac": 16,
        "speed": 30,
        "alignment": "Добрый",
        "player_name": "Иван",
        "experience": 900,
        "proficiency_bonus": 2,
        "saving_throws": ["STR", "DEX"],
        "skills": ["Атлетика", "Выживание", "Восприятие"],
        "race_traits": ["Универсальность человечества", "+1 ко всем характеристикам"],
        "class_features": ["Боевой стиль: Стрельба", "Первобытное чутьё", "Избранный враг: Звери"],
        "equipment": ["Длинный лук", "20 стрел", "Кожаная броня", "Два кинжала"],
        "coins": "50 ЗМ",
        "notes": "Ищет доказательства существования древнего пророчества.",
        "spells": [],
        "spell_slots_1": 0,
        "spell_slots_2": 0
    }

    result = generate_pdf(test_data, "test_character.pdf")

    if result:
        print(f"✅ PDF успешно создан: {result}")
        file_size = os.path.getsize(result)
        print(f"📄 Размер файла: {file_size} байт")
    else:
        print("❌ Ошибка при создании PDF")

    print("\n✅ Модуль pdf_generator.py готов к использованию!")