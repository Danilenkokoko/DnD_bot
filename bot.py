#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot.py - D&D Character Creator Bot for D&D 5.5e (2024)
Обновлённая версия с многослойной архитектурой и веб-сервером для Mini App.
"""

import asyncio
import logging
import os
import threading

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from dotenv import load_dotenv

from db import init_database, migrate_database_v2

# Импортируем роутеры обработчиков
from handlers.character_handlers import router as character_router
from handlers.spell_handlers import router as spell_router

# Импортируем функцию запуска веб-сервера
from webapp import run_webapp

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def main():
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК БОТА D&D CHARACTER CREATOR 5.5e (МНОГОСЛОЙНАЯ АРХИТЕКТУРА)")
    logger.info("=" * 50)

    try:
        # Инициализация БД
        init_database()
        migrate_database_v2()
        logger.info("✅ База данных готова")

        # Подключение роутеров (сначала spell_router, чтобы его обработчики имели приоритет)
        dp.include_router(spell_router)
        dp.include_router(character_router)

        # Удаляем webhook (для polling режима)
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook удалён")

        bot_info = await bot.get_me()
        logger.info(f"✅ Бот: @{bot_info.username}")

        # Запускаем веб-сервер для Mini App в отдельном потоке
        web_thread = threading.Thread(target=run_webapp, daemon=True)
        web_thread.start()
        logger.info("✅ Веб-сервер для Mini App запущен на порту 8000")

        logger.info("🎲 БОТ ГОТОВ К РАБОТЕ!")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())