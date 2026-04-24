import asyncio
import os
import re
import logging
import signal
import sys
import tempfile

PID_FILE = "bot.pid"


def check_pid_file():
    """Проверяет, не запущен ли уже бот"""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = int(f.read().strip())

            # Проверяем, существует ли процесс с таким PID
            try:
                os.kill(old_pid, 0)
                print(f"❌ Бот уже запущен с PID {old_pid}")
                print(f"Убейте процесс командой: kill -9 {old_pid} или удалите файл {PID_FILE}")
                sys.exit(1)
            except OSError:
                # Процесс не существует, можно удалить файл
                os.remove(PID_FILE)
        except:
            pass

    # Записываем текущий PID
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))


def cleanup_pid_file():
    """Удаляет файл PID при выходе"""
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except:
        pass


from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramNetworkError
from aiogram.types import (
    Message, FSInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    CallbackQuery
)
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

from db import (
    init_database,
    save_character,
    get_user_characters,
    get_character_by_id,
    delete_character
)
from dnd_logic import calc_hp, calc_ac, CLASS_DATA
from pdf_generator import generate_pdf

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден в .env")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

STANDARD_STATS = [15, 14, 13, 12, 10, 8]


# ---------- FSM ----------
class Char(StatesGroup):
    name = State()
    class_name = State()
    race = State()


# ---------- MENU ----------
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Создать персонажа")],
            [KeyboardButton(text="📜 Мои персонажи")]
        ],
        resize_keyboard=True
    )


# ---------- INLINE KEYBOARDS ----------
def class_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚔️ Воин", callback_data="class_Воин"),
            InlineKeyboardButton(text="🧙 Маг", callback_data="class_Маг"),
            InlineKeyboardButton(text="🗡 Плут", callback_data="class_Плут"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_name")
        ]
    ])


def race_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🧑 Человек", callback_data="race_Человек"),
            InlineKeyboardButton(text="🧝 Эльф", callback_data="race_Эльф"),
        ],
        [
            InlineKeyboardButton(text="⛏ Дварф", callback_data="race_Дварф"),
            InlineKeyboardButton(text="🍀 Полурослик", callback_data="race_Полурослик"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_class")
        ]
    ])


def characters_keyboard(chars):
    if not chars:
        return None

    buttons = []
    for c in chars:
        buttons.append([InlineKeyboardButton(
            text=f"{c[1]} ({c[2]})",
            callback_data=f"char_{c[0]}"
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ---------- START ----------
@dp.message(Command("start"))
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("🎮 Добро пожаловать в D&D Character Creator!\n\nВыбери действие:", reply_markup=main_menu())


# ---------- CREATE CHARACTER ----------
@dp.message(F.text == "➕ Создать персонажа")
async def create_character(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("✍️ Введи имя своего персонажа:", reply_markup=None)
    await state.set_state(Char.name)


@dp.message(Char.name)
async def get_name(m: Message, state: FSMContext):
    if not m.text or len(m.text.strip()) < 1:
        await m.answer("❌ Имя не может быть пустым. Введи имя:")
        return

    if len(m.text.strip()) > 50:
        await m.answer("❌ Имя слишком длинное (максимум 50 символов). Введи другое имя:")
        return

    await state.update_data(name=m.text.strip())
    await m.answer("🎭 Выбери класс:", reply_markup=class_keyboard())
    await state.set_state(Char.class_name)


@dp.callback_query(lambda c: c.data.startswith("class_"))
async def class_chosen(call: CallbackQuery, state: FSMContext):
    try:
        class_name = call.data.split("_")[1]

        # Проверяем, существует ли такой класс
        if class_name not in CLASS_DATA:
            await call.answer("❌ Такого класса нет", show_alert=True)
            return

        await state.update_data(class_name=class_name)
        await call.answer()

        await call.message.edit_text(
            f"📖 Выбран класс: *{class_name}*\n\nТеперь выбери расу:",
            parse_mode="Markdown",
            reply_markup=race_keyboard()
        )
        await state.set_state(Char.race)
    except Exception as e:
        logger.error(f"Error in class_chosen: {e}")
        await call.answer("❌ Ошибка, попробуй еще раз", show_alert=True)


@dp.callback_query(lambda c: c.data.startswith("race_"))
async def race_chosen(call: CallbackQuery, state: FSMContext):
    temp_pdf_file = None

    try:
        race = call.data.split("_")[1]
        await state.update_data(race=race)
        await call.answer("⏳ Создаю персонажа...")

        data = await state.get_data()

        # Валидация данных
        required_fields = ["name", "class_name", "race"]
        for field in required_fields:
            if field not in data:
                await call.message.answer(f"❌ Ошибка: поле {field} отсутствует. Начни заново /start")
                await state.clear()
                return

        # Базовые характеристики
        stats = {
            "STR": 15, "DEX": 14, "CON": 13,
            "INT": 12, "WIS": 10, "CHA": 8
        }

        # Расчет HP и AC
        hp = calc_hp(data["class_name"], stats["CON"])
        ac = calc_ac(stats["DEX"])
        class_data = CLASS_DATA[data["class_name"]]

        # Сохраняем в базу данных
        try:
            save_character(
                call.from_user.id,
                data,
                stats,
                hp,
                ac,
                class_data["skills"],
                class_data["equipment"],
                class_data["spells"]
            )
            logger.info(f"Персонаж {data['name']} сохранен для user {call.from_user.id}")
        except Exception as e:
            logger.error(f"DB save error: {e}")
            await call.message.answer("❌ Ошибка при сохранении в базу данных. Попробуй еще раз.")
            await state.clear()
            return

        # Генерируем PDF
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", data["name"])

        # Используем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf',
                                         prefix=f"{call.from_user.id}_{safe_name}_") as tmp_file:
            temp_pdf_file = tmp_file.name

        try:
            pdf_file = generate_pdf({
                "name": data["name"],
                "class_name": data["class_name"],
                "race": race,
                "level": 1,
                "stats": stats,
                "hp": hp,
                "ac": ac,
                "skills": class_data["skills"],
                "equipment": class_data["equipment"],
                "spells": class_data["spells"]
            }, temp_pdf_file)

            if pdf_file and os.path.exists(pdf_file):
                await call.message.answer_document(
                    FSInputFile(pdf_file),
                    caption=f"✅ Персонаж *{data['name']}* успешно создан!\n\n🎭 Класс: {data['class_name']}\n🧝 Раса: {race}\n❤️ HP: {hp} | 🛡️ AC: {ac}",
                    parse_mode="Markdown"
                )
            else:
                await call.message.answer(
                    f"✅ Персонаж *{data['name']}* создан!\n\n"
                    f"🎭 Класс: {data['class_name']}\n"
                    f"🧝 Раса: {race}\n"
                    f"❤️ HP: {hp} | 🛡️ AC: {ac}\n\n"
                    f"⚠️ PDF не сгенерирован (проверь шаблон)",
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            await call.message.answer(
                f"✅ Персонаж *{data['name']}* создан!\n\n"
                f"🎭 Класс: {data['class_name']}\n"
                f"🧝 Раса: {race}\n"
                f"❤️ HP: {hp} | 🛡️ AC: {ac}",
                parse_mode="Markdown"
            )

        await call.message.answer("🎮 Главное меню", reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.error(f"Error in race_chosen: {e}")
        await call.message.answer(f"❌ Произошла ошибка: {str(e)}\nНачни заново /start")
        await state.clear()

    finally:
        # Удаляем временный PDF файл
        if temp_pdf_file and os.path.exists(temp_pdf_file):
            try:
                os.remove(temp_pdf_file)
            except Exception as e:
                logger.error(f"Error deleting temp file: {e}")


# ---------- BACK BUTTONS ----------
@dp.callback_query(lambda c: c.data == "back_name")
async def back_to_name(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("✍️ Введи имя персонажа:")
    await state.set_state(Char.name)


@dp.callback_query(lambda c: c.data == "back_class")
async def back_to_class(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("🎭 Выбери класс:", reply_markup=class_keyboard())
    await state.set_state(Char.class_name)


# ---------- MY CHARACTERS ----------
@dp.message(F.text == "📜 Мои персонажи")
async def show_my_characters(m: Message):
    try:
        chars = get_user_characters(m.from_user.id)

        if not chars:
            await m.answer("📭 У тебя пока нет персонажей. Создай первого с помощью кнопки '➕ Создать персонажа'!")
            return

        keyboard = characters_keyboard(chars)
        if keyboard:
            await m.answer(f"📜 У тебя {len(chars)} персонаж(ей):", reply_markup=keyboard)
        else:
            await m.answer("📭 У тебя пока нет персонажей.")

    except Exception as e:
        logger.error(f"Error in show_my_characters: {e}")
        await m.answer("❌ Ошибка при загрузке персонажей. Попробуй позже.")


# ---------- CHARACTER DETAILS ----------
@dp.callback_query(lambda c: c.data.startswith("char_"))
async def show_character_details(call: CallbackQuery):
    try:
        char_id = int(call.data.split("_")[1])
        char = get_character_by_id(char_id)

        if not char:
            await call.message.edit_text("❌ Персонаж не найден")
            await call.answer()
            return

        # Формируем сообщение с данными персонажа
        message_text = (
            f"📖 *{char['name']}*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🎭 *Класс:* {char['class_name']}\n"
            f"🧝 *Раса:* {char['race']}\n"
            f"📊 *Уровень:* {char['level']}\n"
            f"❤️ *HP:* {char['hp']}\n"
            f"🛡️ *AC:* {char['ac']}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Характеристики*\n"
            f"💪 СИЛ: {char['str']}\n"
            f"🤸 ЛОВ: {char['dex']}\n"
            f"🏋️ ТЕЛ: {char['con']}\n"
            f"🧠 ИНТ: {char['int']}\n"
            f"🧙 МУД: {char['wis']}\n"
            f"✨ ХАР: {char['cha']}"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 Скачать PDF", callback_data=f"pdf_{char_id}")],
            [InlineKeyboardButton(text="🗑 Удалить персонажа", callback_data=f"delete_{char_id}")]
        ])

        await call.message.edit_text(message_text, parse_mode="Markdown", reply_markup=keyboard)
        await call.answer()

    except Exception as e:
        logger.error(f"Error in show_character_details: {e}")
        await call.answer("❌ Ошибка при загрузке персонажа", show_alert=True)


# ---------- GENERATE PDF ----------
@dp.callback_query(lambda c: c.data.startswith("pdf_"))
async def generate_character_pdf(call: CallbackQuery):
    temp_pdf_file = None

    try:
        char_id = int(call.data.split("_")[1])
        char = get_character_by_id(char_id)

        if not char:
            await call.answer("❌ Персонаж не найден", show_alert=True)
            return

        await call.answer("⏳ Генерирую PDF...")

        # Подготавливаем данные для PDF
        stats = {
            "STR": char['str'],
            "DEX": char['dex'],
            "CON": char['con'],
            "INT": char['int'],
            "WIS": char['wis'],
            "CHA": char['cha']
        }

        # Создаем временный файл
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", char['name'])
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf',
                                         prefix=f"{call.from_user.id}_{safe_name}_") as tmp_file:
            temp_pdf_file = tmp_file.name

        # Генерируем PDF
        pdf_file = generate_pdf({
            "name": char['name'],
            "class_name": char['class_name'],
            "race": char['race'],
            "level": char['level'],
            "stats": stats,
            "hp": char['hp'],
            "ac": char['ac'],
            "skills": char['skills'] if char['skills'] else [],
            "equipment": char['equipment'] if char['equipment'] else [],
            "spells": char['spells'] if char['spells'] else []
        }, temp_pdf_file)

        if pdf_file and os.path.exists(pdf_file):
            await call.message.answer_document(
                FSInputFile(pdf_file),
                caption=f"📄 Лист персонажа *{char['name']}*",
                parse_mode="Markdown"
            )
        else:
            await call.message.answer("❌ Не удалось создать PDF. Проверь наличие шаблона character.html")

        await call.answer()

    except Exception as e:
        logger.error(f"Error in generate_character_pdf: {e}")
        await call.answer("❌ Ошибка при создании PDF", show_alert=True)

    finally:
        # Удаляем временный файл
        if temp_pdf_file and os.path.exists(temp_pdf_file):
            try:
                os.remove(temp_pdf_file)
            except Exception as e:
                logger.error(f"Error deleting temp file: {e}")


# ---------- DELETE CHARACTER ----------
@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def confirm_character_deletion(call: CallbackQuery):
    try:
        char_id = int(call.data.split("_")[1])
        char = get_character_by_id(char_id)

        if not char:
            await call.answer("❌ Персонаж не найден", show_alert=True)
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"char_{char_id}"),
                InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete_confirm_{char_id}")
            ]
        ])

        await call.message.edit_text(
            f"⚠️ *Удалить персонажа {char['name']}?*\n\nЭто действие необратимо!",
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        await call.answer()

    except Exception as e:
        logger.error(f"Error in confirm_character_deletion: {e}")
        await call.answer("❌ Ошибка", show_alert=True)


@dp.callback_query(lambda c: c.data.startswith("delete_confirm_"))
async def delete_character_from_db(call: CallbackQuery):
    try:
        char_id = int(call.data.split("_")[2])

        success = delete_character(char_id, call.from_user.id)

        if success:
            await call.message.edit_text("🗑️ Персонаж успешно удален!")
            await call.message.answer("🎮 Главное меню", reply_markup=main_menu())
            logger.info(f"Character {char_id} deleted by user {call.from_user.id}")
        else:
            await call.message.edit_text("❌ Не удалось удалить персонажа или он не принадлежит тебе")

        await call.answer()

    except Exception as e:
        logger.error(f"Error in delete_character_from_db: {e}")
        await call.message.edit_text("❌ Ошибка при удалении")
        await call.answer()


# ---------- CANCEL COMMAND ----------
@dp.message(Command("cancel"))
async def cancel_command(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("❌ Действие отменено", reply_markup=main_menu())


# ---------- HELP COMMAND ----------
@dp.message(Command("help"))
async def help_command(m: Message):
    help_text = (
        "📚 *D&D Character Creator - Помощь*\n\n"
        "🔹 *Создать персонажа* - создай нового персонажа\n"
        "🔹 *Мои персонажи* - посмотреть список твоих персонажей\n"
        "🔹 /cancel - отменить текущее действие\n"
        "🔹 /start - вернуться в главное меню\n"
        "🔹 /help - показать эту справку\n\n"
        "После создания персонажа ты можешь:\n"
        "• Скачать PDF с листом персонажа\n"
        "• Просмотреть характеристики\n"
        "• Удалить персонажа"
    )
    await m.answer(help_text, parse_mode="Markdown", reply_markup=main_menu())


# ---------- GLOBAL ERROR HANDLER ----------
@dp.errors()
async def global_error_handler(update, exception):
    """Глобальный обработчик ошибок"""
    logger.error(f"Global error - Update: {update}, Exception: {exception}")
    return True  # Не позволяем ошибке остановить бота


# ---------- RUN BOT ----------
async def main():
    """Запуск бота"""
    check_pid_file()
    signal.signal(signal.SIGTERM, lambda *args: cleanup_pid_file())
    signal.signal(signal.SIGINT, lambda *args: cleanup_pid_file())
    # Инициализируем базу данных
    try:
        init_database()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        return

    # Информация о боте
    try:
        bot_info = await bot.get_me()
        logger.info(f"🚀 Бот {bot_info.username} запущен!")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к Telegram API: {e}")
        return

    # Запускаем поллинг
    try:
        await dp.start_polling(bot)
    except TelegramNetworkError as e:
        logger.error(f"Network error in polling: {e}")
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
    finally:
        await bot.session.close()
        logger.info("Бот завершил работу")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        cleanup_pid_file())