"""
PDF Generator Module for D&D Character Sheets
Модуль для генерации PDF листов персонажей D&D
"""

import os
import logging
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, TemplateError
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTML шаблон для персонажа (встроенный на случай отсутствия файла)
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
            font-family: 'Arial', 'Helvetica', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px;
            min-height: 100vh;
        }

        .sheet {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .header p {
            font-size: 18px;
            opacity: 0.9;
        }

        .content {
            padding: 30px;
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .info-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 15px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .info-card h3 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 16px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .info-card .value {
            font-size: 28px;
            font-weight: bold;
            color: #3498db;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }

        .stat {
            background: #ecf0f1;
            padding: 15px;
            text-align: center;
            border-radius: 15px;
            transition: transform 0.3s;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .stat:hover {
            transform: translateY(-5px);
        }

        .stat h3 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 14px;
            text-transform: uppercase;
        }

        .stat .score {
            font-size: 32px;
            font-weight: bold;
            color: #3498db;
            margin: 10px 0;
        }

        .stat .mod {
            font-size: 18px;
            color: #7f8c8d;
            font-weight: bold;
        }

        .section {
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .section h2 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 24px;
        }

        .skills-list, .equipment-list, .spells-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
        }

        .skill-item, .equipment-item, .spell-item {
            background: white;
            padding: 10px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }

        .footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 12px;
        }

        @media print {
            body {
                background: white;
                padding: 0;
            }
            .stat:hover {
                transform: none;
            }
        }
    </style>
</head>
<body>
    <div class="sheet">
        <div class="header">
            <h1>📖 {{ name }}</h1>
            <p>{{ class_name }} • {{ race }} • Уровень {{ level }}</p>
        </div>

        <div class="content">
            <div class="info-grid">
                <div class="info-card">
                    <h3>❤️ Здоровье (HP)</h3>
                    <div class="value">{{ hp }}</div>
                </div>
                <div class="info-card">
                    <h3>🛡️ Класс брони (AC)</h3>
                    <div class="value">{{ ac }}</div>
                </div>
                <div class="info-card">
                    <h3>📊 Уровень</h3>
                    <div class="value">{{ level }}</div>
                </div>
            </div>

            <h2 style="margin-bottom: 15px;">📊 Характеристики</h2>
            <div class="stats-grid">
                <div class="stat">
                    <h3>💪 Сила (STR)</h3>
                    <div class="score">{{ stats.STR }}</div>
                    <div class="mod">({{ (stats.STR - 10) // 2 }})</div>
                </div>
                <div class="stat">
                    <h3>🤸 Ловкость (DEX)</h3>
                    <div class="score">{{ stats.DEX }}</div>
                    <div class="mod">({{ (stats.DEX - 10) // 2 }})</div>
                </div>
                <div class="stat">
                    <h3>🏋️ Телосложение (CON)</h3>
                    <div class="score">{{ stats.CON }}</div>
                    <div class="mod">({{ (stats.CON - 10) // 2 }})</div>
                </div>
                <div class="stat">
                    <h3>🧠 Интеллект (INT)</h3>
                    <div class="score">{{ stats.INT }}</div>
                    <div class="mod">({{ (stats.INT - 10) // 2 }})</div>
                </div>
                <div class="stat">
                    <h3>🧙 Мудрость (WIS)</h3>
                    <div class="score">{{ stats.WIS }}</div>
                    <div class="mod">({{ (stats.WIS - 10) // 2 }})</div>
                </div>
                <div class="stat">
                    <h3>✨ Харизма (CHA)</h3>
                    <div class="score">{{ stats.CHA }}</div>
                    <div class="mod">({{ (stats.CHA - 10) // 2 }})</div>
                </div>
            </div>

            {% if skills %}
            <div class="section">
                <h2>⚔️ Навыки</h2>
                <div class="skills-list">
                    {% for skill in skills %}
                    <div class="skill-item">• {{ skill }}</div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            {% if equipment %}
            <div class="section">
                <h2>🎒 Снаряжение</h2>
                <div class="equipment-list">
                    {% for item in equipment %}
                    <div class="equipment-item">• {{ item }}</div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            {% if spells %}
            <div class="section">
                <h2>🔮 Заклинания</h2>
                <div class="spells-list">
                    {% for spell in spells %}
                    <div class="spell-item">✨ {{ spell }}</div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>

        <div class="footer">
            <p>D&D Character Sheet • Generated by D&D Bot</p>
        </div>
    </div>
</body>
</html>
'''


# Инициализация окружения Jinja2
def get_jinja_env():
    """Создает и возвращает окружение Jinja2"""
    # Создаем папку templates если её нет
    if not os.path.exists("templates"):
        os.makedirs("templates")
        logger.info("✅ Создана папка templates")

    # Проверяем наличие файла шаблона
    template_path = "templates/character.html"
    if not os.path.exists(template_path):
        # Создаем файл шаблона с содержимым по умолчанию
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(DEFAULT_HTML_TEMPLATE)
        logger.info("✅ Создан файл шаблона character.html")

    return Environment(loader=FileSystemLoader("templates"), autoescape=True)


def ensure_template_exists() -> bool:
    """
    Проверяет существование шаблона и создает его при необходимости

    Returns:
        bool: True если шаблон существует или создан
    """
    try:
        template_path = "templates/character.html"

        # Создаем папку если нет
        if not os.path.exists("templates"):
            os.makedirs("templates")
            logger.info("📁 Создана папка templates")

        # Создаем файл если нет
        if not os.path.exists(template_path):
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(DEFAULT_HTML_TEMPLATE)
            logger.info("📄 Создан файл шаблона character.html")
            return True

        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при создании шаблона: {e}")
        return False


def generate_pdf(data: Dict[str, Any], filename: str) -> Optional[str]:
    """
    Генерирует PDF файл с листом персонажа

    Args:
        data: словарь с данными персонажа
        filename: имя файла для сохранения PDF

    Returns:
        str: путь к созданному файлу или None при ошибке
    """
    try:
        # Проверяем наличие шаблона
        if not ensure_template_exists():
            logger.error("❌ Не удалось создать/найти шаблон")
            return None

        # Валидация входных данных
        required_fields = ['name', 'class_name', 'race', 'level', 'stats', 'hp', 'ac']
        for field in required_fields:
            if field not in data:
                logger.error(f"❌ Отсутствует обязательное поле: {field}")
                return None

        # Проверяем, что stats содержит все характеристики
        required_stats = ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']
        for stat in required_stats:
            if stat not in data['stats']:
                logger.error(f"❌ Отсутствует характеристика: {stat}")
                return None

        # Загружаем шаблон
        env = get_jinja_env()
        template = env.get_template("character.html")

        # Подготавливаем данные для шаблона
        template_data = {
            'name': data['name'],
            'class_name': data['class_name'],
            'race': data['race'],
            'level': data['level'],
            'stats': data['stats'],
            'hp': data['hp'],
            'ac': data['ac'],
            'skills': data.get('skills', []),
            'equipment': data.get('equipment', []),
            'spells': data.get('spells', [])
        }

        # Рендерим HTML
        try:
            html_content = template.render(**template_data)
            logger.info(f"✅ HTML сгенерирован для {data['name']}")
        except TemplateError as e:
            logger.error(f"❌ Ошибка рендеринга шаблона: {e}")
            return None

        # Генерируем PDF
        try:
            # Настройка шрифтов для корректного отображения
            font_config = FontConfiguration()

            # Создаем PDF
            html = HTML(string=html_content)
            html.write_pdf(filename, font_config=font_config)

            # Проверяем, что файл создан
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
        max_age_hours: максимальный возраст файлов в часах
    """
    import time

    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        for filename in os.listdir(directory):
            if filename.startswith("temp_") and filename.endswith(".pdf"):
                filepath = os.path.join(directory, filename)
                file_age = current_time - os.path.getmtime(filepath)

                if file_age > max_age_seconds:
                    os.remove(filepath)
                    logger.info(f"🗑️ Удален старый PDF: {filename}")

    except Exception as e:
        logger.error(f"❌ Ошибка при очистке PDF: {e}")


# Тестирование модуля
if __name__ == "__main__":
    print("=== Тестирование PDF Generator ===\n")

    # Тестовые данные
    test_data = {
        "name": "Тестовый Персонаж",
        "class_name": "Воин",
        "race": "Человек",
        "level": 1,
        "stats": {
            "STR": 15,
            "DEX": 14,
            "CON": 13,
            "INT": 12,
            "WIS": 10,
            "CHA": 8
        },
        "hp": 12,
        "ac": 15,
        "skills": ["Athletics", "Intimidation"],
        "equipment": ["Longsword", "Shield", "Chain Mail"],
        "spells": []
    }

    # Генерация PDF
    result = generate_pdf(test_data, "test_character.pdf")

    if result:
        print(f"✅ PDF успешно создан: {result}")

        # Проверка размера файла
        file_size = os.path.getsize(result)
        print(f"📄 Размер файла: {file_size} байт")

        # Очистка тестового файла
        # os.remove(result)
        # print("🗑️ Тестовый файл удален")
    else:
        print("❌ Ошибка при создании PDF")

    print("\n✅ Модуль pdf_generator.py готов к использованию!")