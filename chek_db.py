#!/usr/bin/env python3
"""
diagnose_skills.py - Диагностика проблемы выбора навыков класса
Запуск: python diagnose_skills.py
"""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN не найден в .env")
    sys.exit(1)

# Настройка логирования для диагностики
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from repositories.class_repository import ClassRepository
from repositories.character_repository import CharacterRepository
from states.character_states import CreateCharacter
from keyboards.character_keyboards import create_skills_keyboard

async def main():
    print("=" * 60)
    print("ДИАГНОСТИКА ВЫБОРА НАВЫКОВ")
    print("=" * 60)

    # 1. Проверка наличия данных в БД
    print("\n1. ПРОВЕРКА БАЗЫ ДАННЫХ")
    repo = ClassRepository()
    class_data = repo.get_by_name("Воин")
    if class_data:
        skills = class_data.get('skills')
        choices = class_data.get('skill_choices')
        print(f"   Класс 'Воин': навыки = {skills} (тип: {type(skills)}), выборов = {choices}")
        if not skills or not isinstance(skills, list):
            print("   ❌ Нет списка навыков или это не список. Проверьте содержимое БД.")
    else:
        print("   ❌ Класс 'Воин' не найден в БД")

    # 2. Проверка импорта и состояния FSM
    print("\n2. ПРОВЕРКА FSM СОСТОЯНИЙ")
    states = [attr for attr in dir(CreateCharacter) if not attr.startswith('_')]
    if 'skills_select' in states:
        print("   ✅ Состояние skills_select присутствует")
    else:
        print("   ❌ Отсутствует состояние skills_select")

    # 3. Проверка создания клавиатуры
    print("\n3. ПРОВЕРКА КЛАВИАТУРЫ")
    test_skills = ["Акробатика", "Атлетика", "Восприятие"]
    keyboard = create_skills_keyboard(test_skills, 2, [])
    buttons = keyboard.inline_keyboard
    print(f"   Клавиатура создана, кнопок: {len(buttons)}")
    for row in buttons:
        for btn in row:
            print(f"     {btn.text} -> {btn.callback_data}")

    # 4. Проверка регистрации роутеров (имитация)
    print("\n4. ПРОВЕРКА РОУТЕРОВ В bot.py")
    # Читаем bot.py, чтобы убедиться, что оба роутера подключены
    try:
        with open("bot.py", "r", encoding="utf-8") as f:
            bot_content = f.read()
        if "from handlers.spell_handlers import router as spell_router" in bot_content:
            print("   ✅ spell_router импортирован")
        else:
            print("   ❌ spell_router не импортирован в bot.py")
        if "from handlers.character_handlers import router as character_router" in bot_content:
            print("   ✅ character_router импортирован")
        else:
            print("   ❌ character_router не импортирован")
        if "dp.include_router(spell_router)" in bot_content and "dp.include_router(character_router)" in bot_content:
            print("   ✅ Оба роутера подключены в bot.py")
        else:
            print("   ❌ Один или оба роутера не подключены")
    except FileNotFoundError:
        print("   ❌ bot.py не найден")

    # 5. Проверка наличия обработчика в character_handlers.py
    print("\n5. ПРОВЕРКА ОБРАБОТЧИКА handle_skills_selection")
    try:
        with open("handlers/character_handlers.py", "r", encoding="utf-8") as f:
            ch_content = f.read()
        if "async def handle_skills_selection" in ch_content:
            print("   ✅ Функция handle_skills_selection присутствует")
        else:
            print("   ❌ handle_skills_selection не найдена")
        if "@router.callback_query(lambda c: c.data.startswith(\"skills_\"))" in ch_content:
            print("   ✅ Декоратор для skills_ зарегистрирован")
        else:
            print("   ❌ Декоратор для skills_ отсутствует")
    except FileNotFoundError:
        print("   ❌ handlers/character_handlers.py не найден")

    # 6. Проверка конфликта роутеров (список всех callback-обработчиков в character_handlers)
    print("\n6. ПОИСК КОНФЛИКТУЮЩИХ ОБРАБОТЧИКОВ")
    import re
    callbacks = re.findall(r"@router\.callback_query\(lambda c: c\.data\.startswith\([\"'](.*?)[\"']\)\)", ch_content)
    print(f"   Зарегистрированные префиксы callback-data в character_handlers: {callbacks}")

    # 7. Проверка импорта клавиатуры в character_handlers
    if "from keyboards.character_keyboards import create_skills_keyboard" in ch_content:
        print("   ✅ create_skills_keyboard импортирована в character_handlers")
    else:
        print("   ❌ create_skills_keyboard не импортирована")

    # 8. Проверка, что бот запускается с правильным порядком роутеров
    print("\n7. РЕКОМЕНДАЦИИ")
    print("   - Убедитесь, что в таблице classes заполнены поля skills (JSONB) и skill_choices.")
    print("   - Проверьте, что в bot.py порядок подключения: сначала spell_router, затем character_router.")
    print("   - Перезапустите бота и нажмите на любой навык. В логах должно появиться сообщение 'DEBUG: вызван handle_skills_selection'.")
    print("   - Если этого сообщения нет, значит обработчик не вызывается – возможно, проблема в регистрации роутера.")
    print("   - Проверьте, что файл handlers/__init__.py не пустой и экспортирует роутеры.")
    print("   - Удалите папки __pycache__ командой: find . -type d -name __pycache__ -exec rm -rf {} +")

    # Дополнительно: симуляция callback, чтобы проверить, вызовется ли он, если запустить бота в тестовом режиме
    # (требует запуска бота, пропустим)

if __name__ == "__main__":
    asyncio.run(main())
