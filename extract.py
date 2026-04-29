import os
import re
import ast
from pathlib import Path

# Проектные папки, которые нужно обойти (можно указать корень)
ROOT_DIR = Path(__file__).parent  # или укажите абсолютный путь к проекту
EXCLUDE_DIRS = {'venv', '__pycache__', '.git', 'env', 'venv', '.venv', 'logs'}

# Регулярные выражения для поиска строковых литералов в разных контекстах
PATTERNS = [
    # Прямые вызовы answer и edit_text
    r'await\s+(?:message|callback\.message|m|call\.message)\.(?:answer|edit_text|answer_photo)\([^,)]*?(["\'])(.*?)\1',
    r'await\s+callback\.answer\((["\'])(.*?)\1',
    # Кнопки
    r'InlineKeyboardButton\(text=(["\'])(.*?)\1',
    r'KeyboardButton\(text=(["\'])(.*?)\1',
    # caption в answer_photo
    r'caption=(["\'])(.*?)\1',
]


def extract_strings_from_file(filepath):
    """Извлекает строки из файла с помощью регулярных выражений (простой метод)."""
    strings = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            for pattern in PATTERNS:
                for match in re.finditer(pattern, content, re.DOTALL):
                    # Группа 2 – это сама строка (без кавычек)
                    text = match.group(2).strip()
                    if text and len(text) > 1 and not text.startswith('http') and not text.startswith('/'):
                        strings.add(text)
    except Exception as e:
        print(f"Ошибка при чтении {filepath}: {e}")
    return strings


def is_relevant_file(filepath):
    """Проверяет, нужно ли обрабатывать файл."""
    # Пропускаем служебные и тестовые файлы, а также сам скрипт
    if filepath.name == 'extract_texts.py':
        return False
    # Можно добавить другие исключения
    return True


def main():
    all_texts = set()
    for root, dirs, files in os.walk(ROOT_DIR):
        # Исключаем ненужные директории
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith('.py'):
                filepath = Path(root) / file
                if is_relevant_file(filepath):
                    texts = extract_strings_from_file(filepath)
                    all_texts.update(texts)

    # Сортируем для удобства
    sorted_texts = sorted(all_texts)

    # Выводим в консоль и сохраняем в файл
    output_file = ROOT_DIR / 'all_bot_texts.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=== ПОЛЬЗОВАТЕЛЬСКИЕ ТЕКСТЫ БОТА ===\n\n")
        for i, text in enumerate(sorted_texts, 1):
            f.write(f"{i}. {text}\n")

    print(f"Найдено {len(sorted_texts)} уникальных текстов. Сохранено в {output_file}")
    # Также выведем в консоль для быстрого просмотра
    for text in sorted_texts[:20]:  # первые 20
        print(f"- {text}")
    if len(sorted_texts) > 20:
        print(f"... и ещё {len(sorted_texts) - 20}")


if __name__ == "__main__":
    main()