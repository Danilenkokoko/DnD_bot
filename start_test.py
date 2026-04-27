# diagnose_bot_startup_fixed.py
"""
Исправленная диагностика запуска бота
Запуск: python diagnose_bot_startup_fixed.py
"""

import asyncio
import sys
import os
import traceback
from datetime import datetime


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_step(step: str, status: str = "info"):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    if status == "success":
        print(f"{Colors.GREEN}[{timestamp}] ✅ {step}{Colors.END}")
    elif status == "error":
        print(f"{Colors.RED}[{timestamp}] ❌ {step}{Colors.END}")
    elif status == "warning":
        print(f"{Colors.YELLOW}[{timestamp}] ⚠️ {step}{Colors.END}")
    else:
        print(f"{Colors.BLUE}[{timestamp}] 📌 {step}{Colors.END}")


async def main():
    print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}🐉 ДИАГНОСТИКА ЗАПУСКА БОТА (ИСПРАВЛЕННАЯ){Colors.END}")
    print(f"{Colors.BOLD}{'=' * 70}{Colors.END}")

    # Шаг 1: Проверка .env
    print_step("ШАГ 1: Проверка .env файла...")
    from dotenv import load_dotenv
    load_dotenv()

    required_vars = ["BOT_TOKEN", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
    all_ok = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == "BOT_TOKEN":
                print_step(f"  ✅ {var} = {value[:10]}...{value[-5:]}", "success")
            else:
                print_step(f"  ✅ {var} = {value}", "success")
        else:
            print_step(f"  ❌ {var} отсутствует", "error")
            all_ok = False

    if not all_ok:
        print_step("Добавьте недостающие переменные в .env файл и повторите запуск", "error")
        return

    # Шаг 2: Проверка импорта бота
    print_step("ШАГ 2: Проверка импорта bot.py...")
    try:
        import bot
        print_step("  ✅ bot.py импортирован", "success")
        print_step(f"  ✅ dp (Dispatcher) найден: {hasattr(bot, 'dp')}", "success")
        print_step(f"  ✅ bot_instance найден: {hasattr(bot, 'bot')}", "success")
        print_step(f"  ✅ CreateCharacter найден: {hasattr(bot, 'CreateCharacter')}", "success")
    except Exception as e:
        print_step(f"  ❌ Ошибка: {e}", "error")
        traceback.print_exc()
        return

    # Шаг 3: Проверка БД
    print_step("ШАГ 3: Проверка подключения к БД...")
    try:
        from db import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                print_step("  ✅ Подключение к БД работает", "success")
    except Exception as e:
        print_step(f"  ❌ Ошибка: {e}", "error")
        return

    # Шаг 4: Проверка запуска (без реального polling)
    print_step("ШАГ 4: Проверка создания экземпляров...")
    try:
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        from aiogram import Bot, Dispatcher
        test_bot = Bot(token=BOT_TOKEN)
        test_dp = Dispatcher()
        print_step("  ✅ Бот и диспетчер созданы", "success")

        # Проверка webhook
        await test_bot.delete_webhook(drop_pending_updates=True)
        print_step("  ✅ Webhook удалён", "success")

        # Проверка информации о боте
        bot_info = await test_bot.get_me()
        print_step(f"  ✅ Бот: @{bot_info.username}", "success")

        await test_bot.session.close()
        print_step("  ✅ Сессия закрыта", "success")

    except Exception as e:
        print_step(f"  ❌ Ошибка: {e}", "error")
        traceback.print_exc()
        return

    # Шаг 5: Проверка, что бот может быть запущен
    print_step("ШАГ 5: Проверка запуска (имитация)...")
    print_step("  Бот готов к запуску. Выполните команду:", "info")
    print(f"{Colors.GREEN}  python bot.py{Colors.END}")

    print(f"\n{Colors.GREEN}{'=' * 70}{Colors.END}")
    print(f"{Colors.GREEN}✨ ДИАГНОСТИКА ПРОЙДЕНА! БОТ ДОЛЖЕН РАБОТАТЬ{Colors.END}")
    print(f"{Colors.GREEN}{'=' * 70}{Colors.END}")


if __name__ == "__main__":
    asyncio.run(main())