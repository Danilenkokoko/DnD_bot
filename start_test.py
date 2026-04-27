# diagnose_bot_startup.py
"""
Диагностика запуска бота с детальным логированием каждого шага
Запуск: python diagnose_bot_startup.py
"""

import asyncio
import sys
import os
import signal
import time
import traceback
from datetime import datetime


# Цвета для вывода
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{'=' * 70}{Colors.END}")
    print(f"{Colors.HEADER}{text}{Colors.END}")
    print(f"{Colors.HEADER}{'=' * 70}{Colors.END}")


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


def print_exception(e: Exception):
    print(f"{Colors.RED}Ошибка: {type(e).__name__}: {e}{Colors.END}")
    traceback.print_exc()


# ============================================================
# ДИАГНОСТИЧЕСКИЙ ЗАПУСК
# ============================================================

async def diagnose_startup():
    """Диагностика каждого шага запуска бота"""
    print_header("🐉 ДИАГНОСТИКА ЗАПУСКА БОТА")

    # === ШАГ 1: ИМПОРТ МОДУЛЕЙ ===
    print_step("ШАГ 1: Импорт модулей...")

    modules_to_import = [
        ("db", ["init_database", "migrate_database_v2", "get_connection"]),
        ("dnd_logic", ["get_class_list", "modifier"]),
        ("spell_selector", ["SpellSelector"]),
        ("pdf_generator", ["generate_pdf"]),
        ("aiogram", ["Bot", "Dispatcher", "F"]),
    ]

    imported_modules = {}
    for module_name, functions in modules_to_import:
        try:
            module = __import__(module_name)
            imported_modules[module_name] = module
            for func in functions:
                if hasattr(module, func):
                    print_step(f"  ✅ {module_name}.{func} импортирован", "success")
                else:
                    print_step(f"  ❌ {module_name}.{func} отсутствует", "error")
                    return False
        except Exception as e:
            print_step(f"  ❌ Ошибка импорта {module_name}: {e}", "error")
            print_exception(e)
            return False

    print_step("Импорт модулей завершён успешно", "success")

    # === ШАГ 2: ЗАГРУЗКА .env ===
    print_step("ШАГ 2: Загрузка переменных окружения...")

    try:
        from dotenv import load_dotenv
        load_dotenv()

        required_vars = ["BOT_TOKEN", "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]
        for var in required_vars:
            value = os.getenv(var)
            if value:
                if var == "BOT_TOKEN":
                    print_step(f"  ✅ {var} = {value[:10]}...{value[-5:]}", "success")
                else:
                    print_step(f"  ✅ {var} = {value}", "success")
            else:
                print_step(f"  ❌ {var} не найден", "error")
                return False
    except Exception as e:
        print_step(f"Ошибка загрузки .env: {e}", "error")
        print_exception(e)
        return False

    # === ШАГ 3: ИНИЦИАЛИЗАЦИЯ БД ===
    print_step("ШАГ 3: Инициализация базы данных...")

    try:
        from db import init_database, migrate_database_v2

        print_step("  Вызов init_database()...")
        init_database()
        print_step("  init_database() выполнен", "success")

        print_step("  Вызов migrate_database_v2()...")
        migrate_database_v2()
        print_step("  migrate_database_v2() выполнен", "success")

    except Exception as e:
        print_step(f"Ошибка инициализации БД: {e}", "error")
        print_exception(e)
        return False

    # === ШАГ 4: СОЗДАНИЕ БОТА ===
    print_step("ШАГ 4: Создание экземпляра бота...")

    try:
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage

        BOT_TOKEN = os.getenv("BOT_TOKEN")

        print_step("  Создание Bot...")
        bot = Bot(token=BOT_TOKEN)
        print_step("  Bot создан", "success")

        print_step("  Создание Dispatcher с MemoryStorage...")
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        print_step("  Dispatcher создан", "success")

    except Exception as e:
        print_step(f"Ошибка создания бота: {e}", "error")
        print_exception(e)
        return False

    # === ШАГ 5: УДАЛЕНИЕ WEBHOOK ===
    print_step("ШАГ 5: Удаление webhook...")

    try:
        print_step("  Вызов bot.delete_webhook()...")
        await bot.delete_webhook(drop_pending_updates=True)
        print_step("  Webhook удалён", "success")
    except Exception as e:
        print_step(f"Ошибка удаления webhook: {e}", "error")
        print_exception(e)
        return False

    # === ШАГ 6: ПОЛУЧЕНИЕ ИНФОРМАЦИИ О БОТЕ ===
    print_step("ШАГ 6: Получение информации о боте...")

    try:
        bot_info = await bot.get_me()
        print_step(f"  Бот: @{bot_info.username}", "success")
        print_step(f"  ID: {bot_info.id}", "success")
        print_step(f"  Имя: {bot_info.full_name}", "success")
    except Exception as e:
        print_step(f"Ошибка получения информации: {e}", "error")
        print_exception(e)
        return False

    # === ШАГ 7: РЕГИСТРАЦИЯ ОБРАБОТЧИКОВ ===
    print_step("ШАГ 7: Проверка регистрации обработчиков...")

    try:
        # Импортируем обработчики из bot.py (это зарегистрирует их)
        print_step("  Импорт обработчиков из bot.py...")
        from bot import dp as bot_dp

        # Проверяем количество зарегистрированных обработчиков
        msg_handlers = len(bot_dp.observers["message"].handlers)
        cb_handlers = len(bot_dp.observers["callback_query"].handlers)

        print_step(f"  Message handlers: {msg_handlers}", "success")
        print_step(f"  Callback handlers: {cb_handlers}", "success")

        if msg_handlers == 0 and cb_handlers == 0:
            print_step("  ВНИМАНИЕ: Нет зарегистрированных обработчиков!", "warning")

    except Exception as e:
        print_step(f"Ошибка регистрации обработчиков: {e}", "error")
        print_exception(e)
        # Не возвращаем False, так как это может быть не критично

    # === ШАГ 8: ПРОВЕРКА ДОПОЛНИТЕЛЬНЫХ ФАЙЛОВ ===
    print_step("ШАГ 8: Проверка наличия дополнительных файлов...")

    required_files = [
        "races_data.py",
        "classes_data.py",
        "backgrounds_data.py",
        "images/races/",
        "images/classes/",
        "templates/"
    ]

    for file_path in required_files:
        if os.path.exists(file_path):
            print_step(f"  ✅ {file_path}", "success")
        else:
            print_step(f"  ⚠️ {file_path} не найден", "warning")

    # === ШАГ 9: ПРОВЕРКА ПОРТОВ ===
    print_step("ШАГ 9: Проверка сетевых портов...")

    import socket
    db_port = int(os.getenv("DB_PORT", 5432))

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', db_port))
        sock.close()

        if result == 0:
            print_step(f"  ✅ PostgreSQL порт {db_port} открыт", "success")
        else:
            print_step(f"  ⚠️ PostgreSQL порт {db_port} не отвечает (код: {result})", "warning")
    except Exception as e:
        print_step(f"  ⚠️ Не удалось проверить порт: {e}", "warning")

    # === ШАГ 10: ПРОВЕРКА ПАМЯТИ И РЕСУРСОВ ===
    print_step("ШАГ 10: Проверка системных ресурсов...")

    import resource
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        print_step(f"  Максимальное количество открытых файлов: {soft}", "success")
        if soft < 1024:
            print_step(f"  ⚠️ Рекомендуется увеличить лимит (ulimit -n 4096)", "warning")
    except:
        pass

    # === ШАГ 11: ПРОВЕРКА ПУТИ ===
    print_step("ШАГ 11: Проверка рабочей директории...")

    print_step(f"  Текущая директория: {os.getcwd()}", "success")
    print_step(f"  Python путь: {sys.path[:3]}...", "success")

    # === ШАГ 12: ПРОВЕРКА ЦИКЛИЧЕСКИХ ИМПОРТОВ ===
    print_step("ШАГ 12: Проверка на циклические импорты...")

    try:
        import bot
        print_step("  bot.py успешно импортирован", "success")
    except ImportError as e:
        print_step(f"  ❌ Ошибка импорта bot.py: {e}", "error")
        if "circular import" in str(e).lower():
            print_step("  Обнаружен циклический импорт!", "error")
        print_exception(e)

    # === ШАГ 13: ЗАПУСК ПОЛЛИНГА С ТАЙМАУТОМ ===
    print_step("ШАГ 13: Пробный запуск polling (на 3 секунды)...")

    try:
        # Создаём задачу для запуска polling
        polling_task = asyncio.create_task(dp.start_polling(bot))

        # Даём боту поработать 3 секунды
        print_step("  Бот работает... (3 секунды)")
        await asyncio.sleep(3)

        # Останавливаем polling
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

        print_step("  Polling успешно запущен и остановлен", "success")

    except asyncio.CancelledError:
        print_step("  Polling был отменён", "warning")
    except Exception as e:
        print_step(f"  ❌ Ошибка при запуске polling: {e}", "error")
        print_exception(e)
        return False

    # === ИТОГ ===
    print_header("✨ ДИАГНОСТИКА ЗАВЕРШЕНА ✨")
    print_step("Все проверки пройдены! Бот должен работать.", "success")
    print_step("Теперь можно запустить бота командой: python bot.py", "info")

    # Закрываем сессию бота
    await bot.session.close()

    return True


# ============================================================
# ОТДЕЛЬНЫЙ ТЕСТ - ЗАПУСК БОТА С КОНКРЕТНОЙ ОШИБКОЙ
# ============================================================

async def test_bot_import_only():
    """Проверяет только импорт bot.py без запуска"""
    print_header("ТЕСТ ИМПОРТА BOT.PY")

    try:
        print_step("Импорт bot.py...")
        import bot
        print_step("✅ bot.py успешно импортирован", "success")

        # Проверяем наличие основных объектов
        if hasattr(bot, 'dp'):
            print_step("  ✅ dp (Dispatcher) найден", "success")
        if hasattr(bot, 'bot'):
            print_step("  ✅ bot (Bot) найден", "success")
        if hasattr(bot, 'CreateCharacter'):
            print_step("  ✅ CreateCharacter (FSM) найден", "success")

        return True
    except ImportError as e:
        print_step(f"❌ Ошибка импорта: {e}", "error")
        traceback.print_exc()
        return False
    except Exception as e:
        print_step(f"❌ Другая ошибка: {e}", "error")
        traceback.print_exc()
        return False


# ============================================================
# ОСНОВНОЙ ЗАПУСК
# ============================================================

async def main():
    """Основная функция диагностики"""
    print_header("Запуск диагностики...")

    # Сначала проверяем импорт bot.py отдельно
    import_success = await test_bot_import_only()

    if not import_success:
        print_step("Импорт bot.py не удался. Полная диагностика не требуется.", "error")
        return 1

    # Затем полная диагностика
    success = await diagnose_startup()

    if success:
        print_header("🎉 ГОТОВО! БОТ ДОЛЖЕН ЗАПУСТИТЬСЯ")
        print_step("Запустите бота командой:", "info")
        print(f"{Colors.GREEN}python bot.py{Colors.END}")
    else:
        print_header("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
        print_step("Исправьте ошибки выше и повторите запуск", "error")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)