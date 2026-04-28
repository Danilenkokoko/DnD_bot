#!/usr/bin/env python3
import os
import re

patterns = [
    r"from\s+keyboards\.character_keyboards\s+import",
    r"from\s+\.character_keyboards\s+import",
    r"import\s+.*create_category_keyboard",
]

found_files = []

for root, dirs, files in os.walk("."):
    if ".venv" in root or "venv" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    for pat in patterns:
                        if re.search(pat, content):
                            found_files.append(path)
                            break
            except Exception:
                pass

if found_files:
    print("Файлы, содержащие подозрительные импорты:")
    for f in found_files:
        print(f"  - {f}")
else:
    print("Ничего не найдено.")