# bot.py
import asyncio
import logging
import os
import re
import tempfile
from typing import Dict, Any, Optional

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

from db import (
    save_character, get_user_characters, get_character_by_id,
    delete_character, get_user_characters_count
)
from dnd_logic import (
    get_initial_stats, calc_hp, calc_ac, validate_character,
    get_race_list, get_class_list, get_background_list,
    get_race_info, get_class_info, get_background_data,
    get_race_traits_list, get_class_skill_choices,
    calculate_proficiency_bonus, format_background_for_display,
    get_equipment_choice, get_race_description, get_race_ability_bonuses,
    get_class_description
)
from pdf_generator import generate_pdf

# Импортируем функции для работы с картинками рас
from races_data import get_race_image_path, get_race_image_exists, RACE_IMAGES

# ---------------- CONFIG ----------------
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env файле")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ---------------- FSM STATES ----------------
class CreateCharacter(StatesGroup):
    race = State()  # 1. Выбор расы
    subrace = State()  # 1а. Выбор подрасы (если есть)
    char_class = State()  # 2. Выбор класса
    name = State()  # 3. Ввод имени
    background = State()  # 4. Выбор предыстории
    equipment = State()  # 5. Выбор снаряжения А или Б
    backstory = State()  # 6. Ввод истории
    image = State()  # 7. Загрузка картинки


# ---------------- MENU ----------------
def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню"""
    keyboard = [
        [KeyboardButton(text="🎲 Создать персонажа")],
        [KeyboardButton(text="📋 Мои персонажи")],
        [KeyboardButton(text="🗑 Удалить персонажа")],
        [KeyboardButton(text="ℹ️ О боте"), KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def cancel_kb() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )


@dp.message(Command("info"))
async def info_command(m: Message):
    """Обработчик команды /info"""
    info_text = (
        "ℹ️ **О боте D&D Character Creator**\n\n"
        "**Описание:**\n"
        "Этот бот помогает создавать персонажей для игры в Dungeons & Dragons 5-й редакции.\n\n"
        "**Возможности:**\n"
        "• 16 рас с подробным описанием и изображениями\n"
        "• 13 классов с характеристиками и умениями\n"
        "• 17 предысторий с выбором снаряжения\n"
        "• Генерация PDF-листа персонажа\n"
        "• Сохранение истории персонажа\n"
        "• Загрузка портрета персонажа\n\n"
        "**Технологии:**\n"
        "• Python + aiogram\n"
        "• PostgreSQL\n"
        "• WeasyPrint для генерации PDF\n\n"
        "**Планы на будущее:**\n"
        "• Система уровней и опыта\n"
        "• Боевая система\n"
        "• Инвентарь и экипировка\n"
        "• Броски кубиков 🎲\n\n"
        "Приятной игры! 🎮"
    )
    await m.answer(info_text, parse_mode=ParseMode.MARKDOWN)


@dp.message(F.text == "ℹ️ О боте")
async def info_button(m: Message):
    """Кнопка информации о боте"""
    await info_command(m)


@dp.message(F.text == "❓ Помощь")
async def help_button(m: Message):
    """Кнопка помощи"""
    await help_command(m)

# ---------------- HELP & INFO ----------------
@dp.message(Command("help"))
async def help_command(m: Message):
    """Обработчик команды /help"""
    help_text = (
        "❓ **Помощь по использованию бота**\n\n"
        "**Доступные команды:**\n"
        "• `/start` - Запустить бота и показать главное меню\n"
        "• `/help` - Показать это сообщение\n"
        "• `/info` - Информация о боте\n"
        "• `/skip` - Пропустить загрузку картинки персонажа\n\n"
        "**Как создать персонажа:**\n"
        "1️⃣ Нажмите кнопку «🎲 Создать персонажа»\n"
        "2️⃣ Выберите расу из предложенных\n"
        "3️⃣ Выберите класс\n"
        "4️⃣ Введите имя персонажа\n"
        "5️⃣ Выберите предысторию\n"
        "6️⃣ Выберите стартовое снаряжение\n"
        "7️⃣ Напишите историю персонажа\n"
        "8️⃣ Загрузите портрет (или пропустите)\n\n"
        "**Другие возможности:**\n"
        "• 📋 Мои персонажи - посмотреть список всех персонажей\n"
        "• 🗑 Удалить персонажа - удалить ненужного персонажа\n\n"
        "Есть идеи или нашли ошибку? Пишите @danilenkokoko007_official"
    )
    await m.answer(help_text, parse_mode=ParseMode.MARKDOWN)


@dp.message(Command("info"))
async def info_command(m: Message):
    """Обработчик команды /info"""
    info_text = (
        "ℹ️ **О боте D&D Character Creator**\n\n"
        "**Версия:** 2.0.0\n\n"
        "**Описание:**\n"
        "Этот бот помогает создавать персонажей для игры в Dungeons & Dragons 5-й редакции.\n\n"
        "**Возможности:**\n"
        "• 16 рас с подробным описанием и изображениями\n"
        "• 13 классов с характеристиками и умениями\n"
        "• 17 предысторий с выбором снаряжения\n"
        "• Генерация PDF-листа персонажа\n"
        "• Сохранение истории персонажа\n"
        "• Загрузка портрета персонажа\n\n"
        "**Технологии:**\n"
        "• Python + aiogram\n"
        "• PostgreSQL\n"
        "• WeasyPrint для генерации PDF\n\n"
        "Приятной игры! 🎮"
    )
    await m.answer(info_text, parse_mode=ParseMode.MARKDOWN)


# ↓↓↓ ВОТ ЭТОТ ОБРАБОТЧИК ОТСУТСТВУЕТ! ↓↓↓

@dp.message(F.text == "❓ Помощь")
async def help_button(m: Message):
    """Кнопка помощи в главном меню"""
    await help_command(m)


@dp.message(F.text == "ℹ️ О боте")
async def info_button(m: Message):
    """Кнопка информации о боте в главном меню"""
    await info_command(m)


# ---------------- INLINE KEYBOARDS ----------------
def create_race_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора расы (2 колонки)"""
    races = get_race_list()
    buttons = []
    row = []

    for i, race in enumerate(races):
        row.append(InlineKeyboardButton(text=race, callback_data=f"race_{race}"))
        if len(row) == 2 or i == len(races) - 1:
            buttons.append(row)
            row = []

    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_creation")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_subrace_keyboard(race: str) -> Optional[InlineKeyboardMarkup]:
    """Создаёт клавиатуру выбора подрасы (если есть)"""
    race_info = get_race_info(race)
    subraces = race_info.get("subraces", {})

    if not subraces:
        return None

    buttons = []
    for subrace_name, subrace_data in subraces.items():
        desc = subrace_data.get("trait", "")
        text = f"{subrace_name} ({desc[:30]})" if desc else subrace_name
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"subrace_{subrace_name}")])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_races")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_class_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора класса (2 колонки)"""
    classes = get_class_list()
    buttons = []
    row = []

    for i, class_name in enumerate(classes):
        row.append(InlineKeyboardButton(text=class_name, callback_data=f"class_{class_name}"))
        if len(row) == 2 or i == len(classes) - 1:
            buttons.append(row)
            row = []

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_races")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_background_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора предыстории"""
    backgrounds = get_background_list()
    buttons = []
    row = []

    for i, bg in enumerate(backgrounds):
        row.append(InlineKeyboardButton(text=bg, callback_data=f"bg_{bg}"))
        if len(row) == 2 or i == len(backgrounds) - 1:
            buttons.append(row)
            row = []

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_class")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_equipment_keyboard(background: str) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру выбора снаряжения А или Б"""
    bg_info = get_background_data(background)
    equipment_a = bg_info.get("equipment_a", "Нет описания")[:60]
    equipment_b = bg_info.get("equipment_b", "Нет описания")[:60]

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📦 Вариант А: {equipment_a}...", callback_data="equip_A")],
        [InlineKeyboardButton(text=f"🎒 Вариант Б: {equipment_b}...", callback_data="equip_B")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_background")]
    ])


def create_character_list_keyboard(user_id: int) -> Optional[InlineKeyboardMarkup]:
    """Создаёт клавиатуру со списком персонажей пользователя"""
    characters = get_user_characters(user_id)

    if not characters:
        return None

    buttons = []
    for char in characters:
        text = f"{char['name']} - {char['class_name']} ур.{char['level']}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"view_{char['id']}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_delete_keyboard(characters: list) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для удаления персонажей"""
    buttons = []
    for char in characters:
        text = f"🗑 {char['name']} ({char['class_name']})"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"delete_{char['id']}")])

    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ---------------- START ----------------
@dp.message(Command("start"))
async def start(m: Message, state: FSMContext):
    await state.clear()

    # Приветственное сообщение с описанием
    welcome_text = (
        "🎮 **Добро пожаловать в D&D Character Creator!**\n\n"
        "Я помогу тебе создать персонажа для Dungeons & Dragons 5-й редакции.\n\n"
        "**Что я умею:**\n"
        "• Создавать персонажей с нуля 🎲\n"
        "• Показывать информацию о расах и классах 📖\n"
        "• Генерировать красивый PDF-лист персонажа 📄\n"
        "• Сохранять историю и портрет персонажа 🖼️\n\n"
        "**Как начать:**\n"
        "Нажми кнопку «🎲 Создать персонажа» и следуй инструкциям!\n\n"
        "В любое время можешь нажать «❓ Помощь» для подсказок."
    )

    try:
        count = get_user_characters_count(m.from_user.id)
        await m.answer(
            f"{welcome_text}\n\n"
            f"📊 У вас создано персонажей: {count}",
            reply_markup=main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Ошибка при старте: {e}")
        await m.answer(
            welcome_text,
            reply_markup=main_menu(),
            parse_mode=ParseMode.MARKDOWN
        )

@dp.message(Command("menu"))
async def menu_command(m: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await m.answer(
        "🎮 Возвращаемся в главное меню",
        reply_markup=main_menu()
    )

@dp.message(F.text == "❌ Отмена")
async def cancel_creation(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(
        "❌ Создание персонажа отменено.\n\n"
        "Чтобы начать заново, нажмите «🎲 Создать персонажа»",
        reply_markup=main_menu()
    )


@dp.message()
async def unknown_command(m: Message, state: FSMContext):
    """Обработчик неизвестных команд"""
    current_state = await state.get_state()

    if current_state:
        # Если пользователь в процессе создания персонажа
        await m.answer(
            "⏳ Вы находитесь в процессе создания персонажа.\n\n"
            "Пожалуйста, следуйте инструкциям или нажмите «❌ Отмена» чтобы начать заново.",
            reply_markup=cancel_kb()
        )
    else:
        # Если пользователь не в процессе
        await m.answer(
            "❓ Я не понимаю эту команду.\n\n"
            "Используйте кнопки меню или команду /help для получения справки.",
            reply_markup=main_menu()
        )


@dp.message(F.text == "❌ Отмена")
async def cancel_creation(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("❌ Создание персонажа отменено", reply_markup=main_menu())


# ---------------- CREATE CHARACTER ----------------
@dp.message(F.text == "🎲 Создать персонажа")
async def create_char_start(m: Message, state: FSMContext):
    await state.set_state(CreateCharacter.race)
    await m.answer(
        "🏰 **Создание нового персонажа**\n\n"
        "**Шаг 1/7: Выберите расу**\n\n"
        "Раса определяет ваши врождённые способности и внешность.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_race_keyboard()
    )


# ---------------- RACE SELECTION ----------------
@dp.callback_query(lambda c: c.data.startswith("race_"))
async def select_race(call: CallbackQuery, state: FSMContext):
    race = call.data.replace("race_", "")
    await state.update_data(race=race)

    race_info = get_race_info(race)
    subraces = race_info.get("subraces", {})

    # Получаем полное описание расы
    from races_data import get_race_description
    race_description = get_race_description(race)

    # Получаем путь к картинке расы
    image_path = get_race_image_path(race)
    image_exists = image_path and os.path.exists(image_path)

    # Формируем текст
    text = f"🧝 **{race}**\n\n"
    text += f"📖 {race_description}\n\n"
    text += f"**Скорость:** {race_info.get('speed', 30)} футов\n"
    text += f"**Размер:** {race_info.get('size', 'Средний')}\n"
    text += f"**Языки:** {', '.join(race_info.get('languages', ['Общий']))}\n\n"

    # Бонусы к характеристикам
    bonuses = get_race_ability_bonuses(race, None)
    if bonuses:
        text += "**Бонусы к характеристикам:**\n"
        for stat, bonus in bonuses.items():
            text += f"  • {stat}: +{bonus}\n"
        text += "\n"

    # Особенности
    text += "**Особенности:**\n"
    for trait in race_info.get('traits', []):
        text += f"  • {trait}\n"

    if subraces:
        text += f"\n**Шаг 1а/7: Выберите подрасу**"
        reply_markup = create_subrace_keyboard(race)
        new_state = CreateCharacter.subrace
    else:
        await state.update_data(subrace=None)
        text += f"\n\n**Шаг 2/7: Выберите класс**"
        reply_markup = create_class_keyboard()
        new_state = CreateCharacter.char_class

    await state.set_state(new_state)

    # Отправляем сообщение с картинкой (если есть)
    try:
        if image_exists:
            photo = FSInputFile(image_path)
            # Удаляем старое сообщение
            await call.message.delete()
            # Отправляем новое с картинкой
            await call.message.answer_photo(
                photo=photo,
                caption=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            # Если картинки нет - просто редактируем текст
            await call.message.edit_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке картинки расы: {e}")
        await call.message.edit_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    await call.answer()


@dp.callback_query(lambda c: c.data.startswith("subrace_"))
async def select_subrace(call: CallbackQuery, state: FSMContext):
    subrace = call.data.replace("subrace_", "")
    await state.update_data(subrace=subrace)
    await state.set_state(CreateCharacter.char_class)

    data = await state.get_data()
    race = data.get("race")

    race_info = get_race_info(race)
    subrace_info = race_info.get("subraces", {}).get(subrace, {})
    subrace_description = subrace_info.get("description", "")

    text = (
        f"🧝 **{race} ({subrace})**\n\n"
        f"📖 {subrace_description}\n\n"
        f"**Шаг 2/7: Выберите класс**"
    )

    await call.message.delete()
    await call.message.answer(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_class_keyboard()
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_races")
async def back_to_races(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.race)

    # Вместо edit_text используем новый ответ
    await call.message.delete()
    await call.message.answer(
        "**Шаг 1/7: Выберите расу**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_race_keyboard()
    )
    await call.answer()


# ---------------- CLASS SELECTION ----------------
@dp.callback_query(lambda c: c.data.startswith("class_"))
async def select_class(call: CallbackQuery, state: FSMContext):
    class_name = call.data.replace("class_", "")
    await state.update_data(char_class=class_name)
    await state.set_state(CreateCharacter.name)

    class_info = get_class_info(class_name)
    class_description = get_class_description(class_name)

    # Получаем путь к картинке класса
    from classes_data import get_class_image_path, get_class_image_exists
    image_path = get_class_image_path(class_name)
    image_exists = image_path and os.path.exists(image_path)

    # Формируем текст с описанием
    text = (
        f"⚔️ **{class_name}**\n\n"
        f"📖 {class_description}\n\n"
        f"❤️ **Хитовый кубик:** d{class_info.get('hit_die', 6)}\n"
        f"🎯 **Основные характеристики:** {', '.join(class_info.get('primary_stats', []))}\n"
        f"🛡️ **Спасброски:** {', '.join(class_info.get('saving_throws', []))}\n\n"
        f"**Шаг 3/7: Введите имя персонажа**\n\n"
        f"Отправьте имя вашего персонажа:"
    )

    # Отправляем сообщение с картинкой (если есть)
    try:
        await call.message.delete()

        if image_exists:
            photo = FSInputFile(image_path)
            await call.message.answer_photo(
                photo=photo,
                caption=text,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await call.message.answer(
                text,
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке картинки класса: {e}")
        await call.message.answer(
            text,
            parse_mode=ParseMode.MARKDOWN
        )

    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_class")
async def back_to_class(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.char_class)

    await call.message.delete()
    await call.message.answer(
        "**Шаг 2/7: Выберите класс**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_class_keyboard()
    )
    await call.answer()


# ---------------- NAME ----------------
@dp.message(CreateCharacter.name)
async def set_name(m: Message, state: FSMContext):
    if m.text == "❌ Отмена":
        await cancel_creation(m, state)
        return

    name = m.text.strip()
    if len(name) > 50:
        await m.answer("❌ Имя слишком длинное (максимум 50 символов). Пожалуйста, введите другое имя:")
        return

    if len(name) < 2:
        await m.answer("❌ Имя слишком короткое (минимум 2 символа). Пожалуйста, введите другое имя:")
        return

    await state.update_data(name=name)
    await state.set_state(CreateCharacter.background)

    await m.answer(
        f"✨ **Имя: {name}**\n\n"
        f"**Шаг 4/7: Выберите предысторию**\n\n"
        f"Предыстория определяет ваше прошлое и дополнительные навыки.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_background_keyboard()
    )


# ---------------- BACKGROUND ----------------
@dp.callback_query(lambda c: c.data.startswith("bg_"))
async def select_background(call: CallbackQuery, state: FSMContext):
    background = call.data.replace("bg_", "")
    await state.update_data(background=background)
    await state.set_state(CreateCharacter.equipment)

    bg_info = get_background_data(background)

    await call.message.delete()
    await call.message.answer(
        f"📜 **Предыстория: {background}**\n\n"
        f"**Шаг 5/7: Выберите снаряжение**\n\n"
        f"**Описание:** {bg_info.get('description', 'Нет описания')[:300]}...\n\n"
        f"**Черта:** {bg_info.get('trait', 'Нет')}\n"
        f"**Навыки:** {', '.join(bg_info.get('skills', []))}\n"
        f"**Инструменты:** {bg_info.get('tools', 'Нет')}\n\n"
        f"Выберите стартовое снаряжение:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_equipment_keyboard(background)
    )
    await call.answer()


@dp.callback_query(lambda c: c.data == "back_to_background")
async def back_to_background(call: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.background)

    await call.message.delete()
    await call.message.answer(
        "**Шаг 4/7: Выберите предысторию**",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_background_keyboard()
    )
    await call.answer()


# ---------------- EQUIPMENT ----------------
@dp.callback_query(lambda c: c.data.startswith("equip_"))
async def select_equipment(call: CallbackQuery, state: FSMContext):
    equipment_choice = call.data.replace("equip_", "")
    await state.update_data(equipment_choice=equipment_choice)
    await state.set_state(CreateCharacter.backstory)

    data = await state.get_data()
    background = data.get("background")
    bg_info = get_background_data(background)

    chosen_equipment = bg_info.get(f"equipment_{equipment_choice.lower()}", "Нет описания")

    await call.message.delete()
    await call.message.answer(
        f"🎒 **Выбран вариант снаряжения: {equipment_choice}**\n\n"
        f"**Снаряжение:** {chosen_equipment}\n\n"
        f"**Шаг 6/7: История персонажа**\n\n"
        f"Расскажите историю вашего персонажа:\n"
        f"- Откуда он родом?\n"
        f"- Что с ним случилось?\n"
        f"- Какие у него цели?\n\n"
        f"Отправьте текст истории (можно коротко):",
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()


# ---------------- BACKSTORY ----------------
@dp.message(CreateCharacter.backstory)
async def set_backstory(m: Message, state: FSMContext):
    if m.text == "❌ Отмена":
        await cancel_creation(m, state)
        return

    backstory = m.text.strip()
    if len(backstory) > 2000:
        await m.answer("❌ История слишком длинная (максимум 2000 символов). Пожалуйста, сократите:")
        return

    await state.update_data(backstory=backstory)
    await state.set_state(CreateCharacter.image)

    await m.answer(
        f"📖 **История сохранена!**\n\n"
        f"**Шаг 7/7: Изображение персонажа**\n\n"
        f"Загрузите картинку вашего персонажа (можно портрет или арт).\n\n"
        f"Отправьте изображение, или нажмите /skip чтобы пропустить этот шаг.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="⏩ Пропустить")]],
            resize_keyboard=True
        )
    )


@dp.message(F.text == "⏩ Пропустить")
async def skip_image(m: Message, state: FSMContext):
    await finalize_character(m, state, image_file_id=None)


@dp.message(CreateCharacter.image, F.photo)
async def set_image(m: Message, state: FSMContext):
    photo = m.photo[-1]
    file_id = photo.file_id
    await finalize_character(m, state, image_file_id=file_id)


async def finalize_character(m: Message, state: FSMContext, image_file_id: Optional[str] = None):
    """Финальное сохранение персонажа и генерация PDF"""
    temp_pdf_file = None

    try:
        await m.answer("⏳ Создаю персонажа и генерирую PDF...")

        data = await state.get_data()

        # Получаем данные
        race = data.get("race")
        subrace = data.get("subrace")
        char_class = data.get("char_class")
        name = data.get("name")
        background = data.get("background")
        backstory = data.get("backstory", "Нет истории")
        equipment_choice = data.get("equipment_choice", "A")

        # Подготовка характеристик
        stats = get_initial_stats(race, subrace)
        hp = calc_hp(char_class, stats["CON"])
        ac = calc_ac(stats["DEX"])

        # Получаем информацию о классах, расах, предысториях
        class_info = get_class_info(char_class)
        bg_info = get_background_data(background)

        # Собираем данные для сохранения
        race_traits = get_race_traits_list(race, subrace)

        # Валидация
        valid, msg = validate_character(name, char_class, race, background, stats)
        if not valid:
            await m.answer(f"❌ Ошибка валидации: {msg}")
            await state.clear()
            return

        # Формируем снаряжение из выбранного варианта
        equipment_text = bg_info.get(f"equipment_{equipment_choice.lower()}", "")
        equipment_list = [item.strip() for item in equipment_text.split(",") if item.strip()]

        # Получаем умения ТОЛЬКО для 1-го уровня
        all_features = class_info.get("features", {})
        first_level_features = all_features.get(1, [])

        # Сохраняем в БД
        char_id = save_character(
            user_id=m.from_user.id,
            name=name,
            race=race,
            class_name=char_class,
            background=background,
            backstory=backstory,
            stats=stats,
            hp=hp,
            ac=ac,
            race_traits=race_traits,
            class_features=first_level_features,
            skills=bg_info.get("skills", []),
            tools=[bg_info.get("tools", "")] if bg_info.get("tools") else [],
            equipment=equipment_list,
            spells=[],
            background_trait=bg_info.get("trait", ""),
            background_skills=bg_info.get("skills", []),
            background_tools=bg_info.get("tools", ""),
            background_equipment_choice=equipment_choice,
            image_file_id=image_file_id
        )

        # Генерация PDF
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{safe_name}.pdf")
        temp_pdf_file = tmp.name
        tmp.close()

        pdf_data = {
            "name": name,
            "class_name": char_class,
            "race": f"{race} ({subrace})" if subrace else race,
            "level": 1,
            "stats": stats,
            "hp": hp,
            "ac": ac,
            "skills": bg_info.get("skills", []),
            "equipment": equipment_list,
            "spells": [],
            "proficiency_bonus": calculate_proficiency_bonus(1),
            "background": background,
            "background_trait": bg_info.get("trait", ""),
            "background_description": bg_info.get("description", ""),
            "race_traits": race_traits,
            "class_features": first_level_features,
            "backstory": backstory
        }

        pdf_file = generate_pdf(pdf_data, temp_pdf_file)

        # Отправка результата
        caption = (
            f"✅ **Персонаж создан!**\n\n"
            f"📛 **Имя:** {name}\n"
            f"🧝 **Раса:** {race}{f' ({subrace})' if subrace else ''}\n"
            f"⚔️ **Класс:** {char_class}\n"
            f"📜 **Предыстория:** {background}\n"
            f"❤️ **HP:** {hp} | 🛡️ **AC:** {ac}\n"
            f"📊 **Уровень:** 1\n\n"
            f"🎯 **Характеристики:**\n"
            f"💪 STR: {stats['STR']} | 🤸 DEX: {stats['DEX']} | 🏋️ CON: {stats['CON']}\n"
            f"🧠 INT: {stats['INT']} | 🧙 WIS: {stats['WIS']} | ✨ CHA: {stats['CHA']}"
        )

        # Отправляем картинку если есть
        if image_file_id:
            await m.answer_photo(
                photo=image_file_id,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await m.answer(caption, parse_mode=ParseMode.MARKDOWN)

        # Отправляем PDF
        if pdf_file and os.path.exists(pdf_file):
            await m.answer_document(
                FSInputFile(pdf_file, filename=f"{safe_name}_character_sheet.pdf"),
                caption="📄 Лист персонажа в формате PDF"
            )
            await asyncio.sleep(1)
        else:
            await m.answer("⚠️ Не удалось сгенерировать PDF, но персонаж сохранён в базе данных.")

        await m.answer("🎮 Главное меню", reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при создании персонажа: {e}", exc_info=True)
        await m.answer("❌ Произошла ошибка при создании персонажа. Попробуйте позже.")
        await state.clear()

    finally:
        if temp_pdf_file and os.path.exists(temp_pdf_file):
            try:
                os.remove(temp_pdf_file)
            except:
                pass


# ---------------- VIEW CHARACTERS ----------------
@dp.message(F.text == "📋 Мои персонажи")
async def list_characters(m: Message):
    characters = get_user_characters(m.from_user.id)

    if not characters:
        await m.answer("📭 У вас пока нет созданных персонажей. Используйте кнопку '🎲 Создать персонажа'")
        return

    await m.answer(
        f"📋 **Ваши персонажи ({len(characters)}):**\n\n"
        f"Нажмите на персонажа для просмотра подробной информации.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_character_list_keyboard(m.from_user.id)
    )


@dp.callback_query(lambda c: c.data.startswith("view_"))
async def view_character(call: CallbackQuery):
    char_id = int(call.data.replace("view_", ""))
    character = get_character_by_id(char_id)

    if not character:
        await call.answer("❌ Персонаж не найден")
        return

    info = (
        f"📛 **{character['name']}**\n\n"
        f"🧝 **Раса:** {character['race']}\n"
        f"⚔️ **Класс:** {character['class_name']}\n"
        f"📜 **Предыстория:** {character.get('background', 'Нет')}\n"
        f"📊 **Уровень:** {character['level']}\n"
        f"❤️ **HP:** {character['hp']} | 🛡️ **AC:** {character['ac']}\n\n"
        f"**Характеристики:**\n"
        f"💪 STR: {character['str']} | 🤸 DEX: {character['dex']}\n"
        f"🏋️ CON: {character['con']} | 🧠 INT: {character['int']}\n"
        f"🧙 WIS: {character['wis']} | ✨ CHA: {character['cha']}\n\n"
        f"**Навыки:** {', '.join(character.get('skills', []))}\n\n"
        f"**История:** {character.get('backstory', 'Нет истории')[:200]}..."
    )

    if character.get('image_file_id'):
        await call.message.answer_photo(
            photo=character['image_file_id'],
            caption=info,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await call.message.answer(info, parse_mode=ParseMode.MARKDOWN)

    await call.answer()


# ---------------- DELETE CHARACTER ----------------
@dp.message(F.text == "🗑 Удалить персонажа")
async def delete_character_menu(m: Message):
    characters = get_user_characters(m.from_user.id)

    if not characters:
        await m.answer("📭 У вас нет персонажей для удаления.")
        return

    await m.answer(
        "🗑 **Выберите персонажа для удаления:**\n\n"
        "⚠️ Внимание! Удаление необратимо.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=create_delete_keyboard(characters)
    )


@dp.callback_query(lambda c: c.data.startswith("delete_"))
async def confirm_delete(call: CallbackQuery):
    char_id = int(call.data.replace("delete_", ""))

    character = get_character_by_id(char_id)
    if not character:
        await call.answer("❌ Персонаж не найден")
        return

    if delete_character(char_id, call.from_user.id):
        await call.message.edit_text(f"✅ Персонаж **{character['name']}** успешно удалён!",
                                     parse_mode=ParseMode.MARKDOWN)
    else:
        await call.message.edit_text("❌ Не удалось удалить персонажа. Возможно, он не принадлежит вам.")

    await call.answer()


@dp.callback_query(lambda c: c.data == "cancel_delete")
async def cancel_delete(call: CallbackQuery):
    await call.message.edit_text("❌ Удаление отменено")
    await call.answer()


@dp.callback_query(lambda c: c.data == "cancel_creation")
async def cancel_creation_callback(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Создание персонажа отменено")
    await call.answer()


# ---------------- SKIP HANDLER ----------------
@dp.message(Command("skip"))
async def skip_command(m: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == CreateCharacter.image.state:
        await finalize_character(m, state, image_file_id=None)
    else:
        await m.answer("❌ Команда /skip доступна только на шаге загрузки изображения")


# ---------------- RUN ----------------
async def main():
    """Запуск бота"""
    logger.info("=" * 50)
    logger.info("🚀 ЗАПУСК БОТА D&D CHARACTER CREATOR")
    logger.info("=" * 50)

    try:
        from db import init_database, migrate_database

        logger.info("📊 Шаг 1/5: Инициализация базы данных...")
        init_database()
        migrate_database()
        logger.info("✅ База данных готова")

        logger.info("📜 Шаг 2/5: Загрузка предысторий...")
        try:
            from backgrounds_data import reload_cache
            reload_cache()
            logger.info("✅ Предыстории загружены")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки предысторий: {e}")

        logger.info("🔌 Шаг 3/5: Проверка подключения к БД...")
        try:
            from db import get_user_characters_count
            count = get_user_characters_count(0)
            logger.info(f"✅ Подключение к БД работает (тест: {count} персонажей)")
        except Exception as e:
            logger.error(f"❌ Ошибка БД: {e}")

        logger.info("🌐 Шаг 4/5: Настройка webhook...")
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook удалён")

        logger.info("🤖 Шаг 5/5: Получение информации о боте...")
        bot_info = await bot.get_me()
        logger.info(f"✅ Бот: @{bot_info.username} (ID: {bot_info.id})")
        logger.info(f"   Ссылка: https://t.me/{bot_info.username}")

        logger.info("=" * 50)
        logger.info("🎲 БОТ ГОТОВ К РАБОТЕ!")
        logger.info("📨 Ожидание сообщений...")
        logger.info("=" * 50)

        import sys
        sys.stdout.flush()

        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
    finally:
        logger.info("🛑 Бот остановлен")


if __name__ == "__main__":
    logger.info("🔄 Запуск asyncio...")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Необработанная ошибка: {e}", exc_info=True)