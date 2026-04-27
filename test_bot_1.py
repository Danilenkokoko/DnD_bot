# test_bot_start.py
import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


async def test_imports():
    print("1. Проверка импортов...")
    try:
        from db import init_database, migrate_database_v2
        print("   ✅ db импортирован")
    except Exception as e:
        print(f"   ❌ Ошибка импорта db: {e}")
        return False

    try:
        from dnd_logic import get_class_list
        print("   ✅ dnd_logic импортирован")
    except Exception as e:
        print(f"   ❌ Ошибка импорта dnd_logic: {e}")
        return False

    try:
        from spell_selector import SpellSelector
        print("   ✅ spell_selector импортирован")
    except Exception as e:
        print(f"   ❌ Ошибка импорта spell_selector: {e}")
        return False

    try:
        from pdf_generator import generate_pdf
        print("   ✅ pdf_generator импортирован")
    except Exception as e:
        print(f"   ❌ Ошибка импорта pdf_generator: {e}")
        return False

    return True


async def test_db_init():
    print("\n2. Проверка инициализации БД...")
    try:
        from db import init_database, migrate_database_v2
        print("   Вызов init_database()...")
        init_database()
        print("   ✅ init_database() выполнен")

        print("   Вызов migrate_database_v2()...")
        migrate_database_v2()
        print("   ✅ migrate_database_v2() выполнен")

        return True
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bot_creation():
    print("\n3. Проверка создания бота...")
    try:
        from aiogram import Bot, Dispatcher
        import os
        from dotenv import load_dotenv

        load_dotenv()
        BOT_TOKEN = os.getenv("BOT_TOKEN")

        if not BOT_TOKEN:
            print("   ❌ BOT_TOKEN не найден")
            return False

        bot = Bot(token=BOT_TOKEN)
        dispatcher = Dispatcher()
        print("   ✅ Бот и диспетчер созданы")

        await bot.delete_webhook(drop_pending_updates=True)
        print("   ✅ Webhook удалён")

        bot_info = await bot.get_me()
        print(f"   ✅ Бот: @{bot_info.username}")

        return True
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 50)
    print("ТЕСТ ЗАПУСКА БОТА")
    print("=" * 50)

    # Тест 1: импорты
    if not await test_imports():
        print("\n❌ Ошибка на этапе импортов")
        return

    # Тест 2: инициализация БД
    if not await test_db_init():
        print("\n❌ Ошибка на этапе инициализации БД")
        return

    # Тест 3: создание бота
    if not await test_bot_creation():
        print("\n❌ Ошибка на этапе создания бота")
        return

    print("\n" + "=" * 50)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    print("Бот должен запускаться корректно")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())