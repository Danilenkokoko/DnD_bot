import asyncio
import os
import re
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError

from aiogram import Bot, Dispatcher, F
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
    save_character,
    get_user_characters,
    get_character_by_id,
    delete_character
)
from dnd_logic import calc_hp, calc_ac, CLASS_DATA
from pdf_generator import generate_pdf

logging.basicConfig(level=logging.INFO)
load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
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


# ---------- INLINE ----------
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
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{c[1]} ({c[2]})",
                callback_data=f"char_{c[0]}"
            )] for c in chars
        ]
    )


# ---------- START ----------
@dp.message(Command("start"))
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("🎮 Главное меню", reply_markup=main_menu())


# ---------- CREATE ----------
@dp.message(F.text == "➕ Создать персонажа")
async def create_character(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("✍️ Введи имя:", reply_markup=None)
    await state.set_state(Char.name)


@dp.message(Char.name)
async def name(m: Message, state: FSMContext):
    await state.update_data(name=m.text)
    await m.answer("🎭 Выбери класс:", reply_markup=class_keyboard())
    await state.set_state(Char.class_name)


@dp.callback_query(lambda c: c.data.startswith("class_"))
async def class_chosen(call: CallbackQuery, state: FSMContext):
    class_name = call.data.split("_")[1]
    await state.update_data(class_name=class_name)
    await call.answer()

    await call.message.edit_text(
        f"Класс: {class_name}\nВыбери расу:",
        reply_markup=race_keyboard()
    )
    await state.set_state(Char.race)


@dp.callback_query(lambda c: c.data.startswith("race_"))
async def race_chosen(call: CallbackQuery, state: FSMContext):
    race = call.data.split("_")[1]
    await state.update_data(race=race)
    await call.answer()

    data = await state.get_data()

    stats = {
        "STR": 15, "DEX": 14, "CON": 13,
        "INT": 12, "WIS": 10, "CHA": 8
    }

    hp = calc_hp(data["class_name"], stats["CON"])
    ac = calc_ac(stats["DEX"])
    class_data = CLASS_DATA[data["class_name"]]

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

    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", data["name"])

    file = generate_pdf({
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
    }, f"{safe_name}.pdf")

    await call.message.answer_document(FSInputFile(file))
    await call.message.answer("🎮 Главное меню", reply_markup=main_menu())

    await state.clear()


# ---------- BACK ----------
@dp.callback_query(lambda c: c.data == "back_name")
async def back_name(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("✍️ Введи имя:")
    await state.set_state(Char.name)


@dp.callback_query(lambda c: c.data == "back_class")
async def back_class(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.edit_text("🎭 Выбери класс:", reply_markup=class_keyboard())
    await state.set_state(Char.class_name)


# ---------- MY CHARACTERS ----------
@dp.message(F.text == "📜 Мои персонажи")
async def my_chars(m: Message):
    chars = get_user_characters(m.from_user.id)

    if not chars:
        return await m.answer("Нет персонажей")

    await m.answer("📜 Твои персонажи:", reply_markup=characters_keyboard(chars))


@dp.callback_query(lambda c: c.data.startswith("char_"))
async def show_char(call: CallbackQuery):
    char_id = int(call.data.split("_")[1])
    char = get_character_by_id(char_id)

    await call.message.edit_text(
        f"{char[2]}\n{char[3]} {char[4]}\nHP:{char[12]} AC:{char[13]}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 PDF", callback_data=f"pdf_{char_id}")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{char_id}")]
        ])
    )
    await call.answer()


# ---------- PDF ----------
@dp.callback_query(lambda c: c.data.startswith("pdf_"))
async def send_pdf(call: CallbackQuery):
    char_id = int(call.data.split("_")[1])
    char = get_character_by_id(char_id)

    stats = {
        "STR": char[6], "DEX": char[7], "CON": char[8],
        "INT": char[9], "WIS": char[10], "CHA": char[11],
    }

    file = generate_pdf({
        "name": char[2],
        "class_name": char[3],
        "race": char[4],
        "level": char[5],
        "stats": stats,
        "hp": char[12],
        "ac": char[13],
        "skills": char[14],
        "equipment": char[15],
        "spells": char[16]
    }, f"{char[2]}.pdf")

    await call.message.answer_document(FSInputFile(file))
    await call.answer()


# ---------- DELETE ----------
@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def confirm_delete(call: CallbackQuery):
    char_id = int(call.data.split("_")[1])

    await call.message.edit_text(
        "Удалить персонажа?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Нет", callback_data=f"char_{char_id}"),
                InlineKeyboardButton(text="✅ Да", callback_data=f"delete_confirm_{char_id}")
            ]
        ])
    )
    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("delete_confirm_"))
async def delete_char(call: CallbackQuery):
    char_id = int(call.data.split("_")[2])

    delete_character(char_id, call.from_user.id)

    await call.message.edit_text("Удалено")
    await call.message.answer("🎮 Главное меню", reply_markup=main_menu())

    await call.answer()


# ---------- RUN ----------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
