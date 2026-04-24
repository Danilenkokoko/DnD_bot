import asyncio
import logging
import os
import re
import tempfile

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery, FSInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from dotenv import load_dotenv

from db import save_character
from dnd_logic import calc_hp, calc_ac, CLASS_DATA
from pdf_generator import generate_pdf

# ---------------- CONFIG ----------------
load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- FSM ----------------
class Char(StatesGroup):
    name = State()
    class_name = State()
    race = State()

# ---------------- MENU ----------------
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎲 Создать персонажа")],
            [KeyboardButton(text="🗑 Удалить персонажа")]
        ],
        resize_keyboard=True
    )

# ---------------- KEYBOARDS ----------------
def class_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Воин", callback_data="class_Воин")],
        [InlineKeyboardButton(text="🧙 Маг", callback_data="class_Маг")],
        [InlineKeyboardButton(text="🗡 Плут", callback_data="class_Плут")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_name")]
    ])

def race_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Человек", callback_data="race_Человек")],
        [InlineKeyboardButton(text="🧝 Эльф", callback_data="race_Эльф")],
        [InlineKeyboardButton(text="⛏ Дварф", callback_data="race_Дварф")],
        [InlineKeyboardButton(text="🍀 Полурослик", callback_data="race_Полурослик")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_class")]
    ])

# ---------------- START ----------------
@dp.message(Command("start"))
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("🎮 Главное меню", reply_markup=main_menu())

# ---------------- CREATE ----------------
@dp.message(F.text == "🎲 Создать персонажа")
async def create_char(m: Message, state: FSMContext):
    await state.set_state(Char.name)
    await m.answer("✏️ Введи имя персонажа:")

# ---------------- NAME ----------------
@dp.message(Char.name)
async def set_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text)
    await state.set_state(Char.class_name)
    await m.answer("🎭 Выбери класс:", reply_markup=class_kb())

# ---------------- CLASS ----------------
@dp.callback_query(lambda c: c.data.startswith("class_"))
async def class_chosen(call: CallbackQuery, state: FSMContext):
    class_name = call.data.split("_", 1)[1]
    await state.update_data(class_name=class_name)
    await state.set_state(Char.race)

    await call.answer()
    await call.message.edit_text("🧝 Выбери расу:", reply_markup=race_kb())

# ---------------- BACK ----------------
@dp.callback_query(lambda c: c.data == "back_name")
async def back_name(call: CallbackQuery, state: FSMContext):
    await state.set_state(Char.name)
    await call.answer()
    await call.message.edit_text("✏️ Введи имя персонажа:")

@dp.callback_query(lambda c: c.data == "back_class")
async def back_class(call: CallbackQuery, state: FSMContext):
    await state.set_state(Char.class_name)
    await call.answer()
    await call.message.edit_text("🎭 Выбери класс:", reply_markup=class_kb())

# ---------------- RACE + CREATE ----------------
@dp.callback_query(lambda c: c.data.startswith("race_"))
async def race_chosen(call: CallbackQuery, state: FSMContext):
    temp_pdf_file = None

    try:
        parts = call.data.split("_", 1)
        if len(parts) < 2:
            await call.answer()
            return

        race = parts[1]
        await state.update_data(race=race)

        await call.answer()
        await call.message.answer("⏳ Создаю персонажа...")

        data = await state.get_data()

        if not data.get("name") or not data.get("class_name"):
            await call.message.answer("❌ Ошибка. Начни заново /start")
            await state.clear()
            return

        class_name = data["class_name"]

        if class_name not in CLASS_DATA:
            await call.message.answer("❌ Ошибка класса")
            await state.clear()
            return

        stats = {
            "STR": 15, "DEX": 14, "CON": 13,
            "INT": 12, "WIS": 10, "CHA": 8
        }

        hp = calc_hp(class_name, stats["CON"])
        ac = calc_ac(stats["DEX"])
        class_data = CLASS_DATA[class_name]

        # SAVE DB
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

        # PDF
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", data["name"])

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_pdf_file = tmp.name
        tmp.close()

        pdf_file = generate_pdf({
            "name": data["name"],
            "class": class_name,
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
                caption=(
                    f"✅ Персонаж *{data['name']}* создан!\n\n"
                    f"🎭 Класс: {class_name}\n"
                    f"🧝 Раса: {race}\n"
                    f"❤️ HP: {hp} | 🛡️ AC: {ac}"
                ),
                parse_mode=ParseMode.MARKDOWN
            )
            await asyncio.sleep(1)
        else:
            await call.message.answer("⚠️ PDF не создан, но персонаж сохранён")

        await call.message.answer("🎮 Главное меню", reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.error(e, exc_info=True)
        await call.message.answer("❌ Ошибка при создании персонажа")
        await state.clear()

    finally:
        if temp_pdf_file and os.path.exists(temp_pdf_file):
            os.remove(temp_pdf_file)

# ---------------- DELETE ----------------
@dp.message(F.text == "🗑 Удалить персонажа")
async def delete_char(m: Message):
    # заглушка (можешь расширить)
    await m.answer("❌ Функция удаления пока простая (добавим позже)")

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())