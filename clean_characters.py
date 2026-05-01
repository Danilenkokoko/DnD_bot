# clean_characters.py
"""
Удаляет всех персонажей из базы данных.
Запускать перед первым запуском обновлённого бота, чтобы избежать конфликтов.
"""

import os
import sys
from dotenv import load_dotenv
from repositories.character_repository import CharacterRepository

load_dotenv()

def clear_all_characters():
    repo = CharacterRepository()
    # Получаем список всех пользователей, у которых есть персонажи
    # Для простоты удалим всех персонажей напрямую (можно через SQL)
    # Или используем метод get_all и удаляем каждого.
    # В репозитории нет готового метода delete_all, поэтому напишем прямой запрос.
    from db import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM characters")
            deleted = cur.rowcount
            conn.commit()
            print(f"✅ Удалено {deleted} персонажей.")
    # Также можно удалить старые временные файлы, если нужно
    import tempfile
    # (опционально)

if __name__ == "__main__":
    confirm = input("⚠️ ВНИМАНИЕ! Это удалит ВСЕХ персонажей. Продолжить? (yes/no): ")
    if confirm.lower() == "yes":
        clear_all_characters()
    else:
        print("Операция отменена.")