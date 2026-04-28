#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Поиск неправильного импорта create_category_keyboard
"""

import os
import re


def find_wrong_imports(root_dir="."):
    wrong_import_pattern = r"from\s+keyboards\.character_keyboards\s+import\s+.*create_category_keyboard"
    wrong_import_pattern2 = r"import\s+.*create_category_keyboard.*from\s+keyboards\.character_keyboards"

    found = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Пропускаем виртуальные окружения и кэш
        if '.venv' in dirpath or 'venv' in dirpath or '__pycache__' in dirpath:
            continue
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(dirpath, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if re.search(wrong_import_pattern, content) or re.search(wrong_import_pattern2, content):
                            found.append(filepath)
                except Exception as e:
                    print(f"⚠️ Ошибка чтения {filepath}: {e}")

    return found


if __name__ == "__main__":
    files = find_wrong_imports(".")
    if files:
        print("❌ Найдены файлы с неправильным импортом create_category_keyboard из keyboards.character_keyboards:")
        for f in files:
            print(f"   - {f}")
        print("\n🔧 Исправление: замените 'from keyboards.character_keyboards import create_category_keyboard'")
        print(
            "   на 'from keyboards.spell_keyboards import create_category_keyboard' или 'from keyboards import create_category_keyboard'")
    else:
        print("✅ Неправильный импорт не найден.")