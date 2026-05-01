# handlers/character_handlers.py
"""
Обработчики для создания персонажа с удалением предыдущих служебных сообщений.
Каждый шаг удаляет свой запрос, оставляя только картинки и финальный лист.
"""

import logging
import os
from typing import Optional

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, FSInputFile, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from states.character_states import CreateCharacter
from keyboards.character_keyboards import (
    create_class_keyboard,
    create_race_keyboard,
    create_background_keyboard,
    create_character_list_with_webapp_keyboard,
    create_delete_keyboard,
    create_skills_keyboard,
    cancel_kb,
    skip_kb,
    main_menu
)

from services.character_service import CharacterStatsService, CharacterFinalizationService
from services.progression_service import ProgressionService
from services.spell_service import SpellSelectionService
from repositories.character_repository import CharacterRepository
from repositories.race_repository import RaceRepository
from utils.message_utils import delete_previous, send_new, send_new_from_callback
from repositories.class_repository import ClassRepository
from repositories.background_repository import BackgroundRepository
from repositories.equipment_repository import EquipmentRepository, FightingStyleRepository
from repositories.spell_repository import SpellRepository

from engine.validators import validate_name as engine_validate_name

logger = logging.getLogger(__name__)

router = Router()

# Репозитории
_race_repo = RaceRepository()
_class_repo = ClassRepository()
_bg_repo = BackgroundRepository()
_equip_repo = EquipmentRepository()
_fighting_repo = FightingStyleRepository()
_spell_repo = SpellRepository()
_char_repo = CharacterRepository()

WEBAPP_BASE_URL = os.getenv("WEBAPP_URL", "http://localhost:8000")


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ УПРАВЛЕНИЯ СООБЩЕНИЯМИ
# =========================================================


async def send_new(state: FSMContext, message: Message, text: str, reply_markup=None):
    """Отправляет новое сообщение, удаляя предыдущее, и сохраняет его ID."""
    new_msg = await message.answer(text, reply_markup=reply_markup, parse_mode=None)
    await state.update_data(last_bot_message_id=new_msg.message_id)
    return new_msg


async def send_new_from_callback(callback: CallbackQuery, state: FSMContext, text: str, reply_markup=None):
    """Отправляет новое сообщение из callback, удаляя предыдущее."""
    new_msg = await callback.message.answer(text, reply_markup=reply_markup, parse_mode=None)
    await state.update_data(last_bot_message_id=new_msg.message_id)
    return new_msg


# =========================================================
# КОМАНДЫ
# =========================================================
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🎲 Добро пожаловать в D&D Character Creator 5.5e (2024)!\n\n"
        "Я проведу тебя через все этапы создания персонажа.\n\n"
        "🗺 Маршрут:\n"
        "1️⃣ Класс\n"
        "2️⃣ Навыки класса\n"
        "3️⃣ Снаряжение\n"
        "4️⃣ Заклинания\n"
        "5️⃣ Боевой стиль\n"
        "6️⃣ Предыстория\n"
        "7️⃣ Раса\n"
        "8️⃣ Имя и история\n"
        "9️⃣ Мировоззрение\n"
        "🔟 Готовый PDF\n\n"
        "Жми «🎲 Создать персонажа» — и погнали!",
        reply_markup=main_menu(),
        parse_mode=None
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Главное меню", reply_markup=main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 Справка по шагам создания персонажа:\n\n"
        "1. КЛАСС — боевые умения и стиль игры\n"
        "2. НАВЫКИ КЛАССА — что персонаж умеет лучше всего\n"
        "3. СНАРЯЖЕНИЕ КЛАССА — стартовый арсенал\n"
        "4. ЗАКЛИНАНИЯ (если есть) — магический арсенал\n"
        "5. БОЕВОЙ СТИЛЬ (Воину/Паладину/Следопыту) — тактика в бою\n"
        "6. ПРЕДЫСТОРИЯ — прошлое и бонусы к характеристикам\n"
        "7. РАСА — врождённые способности\n"
        "8. ИМЯ — как к тебе обращаться\n"
        "9. ИСТОРИЯ — твоя легенда\n"
        "10. МИРОВОЗЗРЕНИЕ — моральный компас\n"
        "11. ИЗОБРАЖЕНИЕ — портрет (можно пропустить)\n"
        "12. PDF — готовый лист персонажа\n\n"
        "🔹 Команды:\n"
        "/start — начать заново\n"
        "/menu — главное меню\n"
        "/help — эта справка",
        parse_mode=None
    )


# =========================================================
# КНОПКИ ГЛАВНОГО МЕНЮ
# =========================================================
@router.message(F.text == "🎲 Создать персонажа")
async def create_character_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CreateCharacter.class_select)
    # Отправляем первое сообщение с клавиатурой выбора класса
    msg = await message.answer(
        "🏰 Твой класс\n\nКласс = стиль игры, умения и стартовое снаряжение.\n\nВыбери класс:",
        reply_markup=create_class_keyboard()
    )
    await state.update_data(last_bot_message_id=msg.message_id)


@router.message(F.text == "📋 Мои персонажи")
async def list_characters(message: Message):
    characters = _char_repo.get_by_user_id(message.from_user.id)
    if not characters:
        await message.answer("📭 У тебя пока нет ни одного персонажа.\n\nНажми «🎲 Создать персонажа», чтобы исправить это.")
        return
    await message.answer("📋 Твои персонажи:", reply_markup=create_character_list_with_webapp_keyboard(message.from_user.id, WEBAPP_BASE_URL))


@router.message(F.text == "🗑 Удалить персонажа")
async def delete_character_menu(message: Message):
    characters = _char_repo.get_by_user_id(message.from_user.id)
    if not characters:
        await message.answer("📭 Некого удалять — список пуст.")
        return
    await message.answer(
        "🗑 Выбери, кого отправить в легенды…\n\n⚠️ Это навсегда. Восстановить будет нельзя.",
        reply_markup=create_delete_keyboard(characters)
    )


@router.message(F.text == "ℹ️ О боте")
async def info_button(message: Message):
    await message.answer(
        "🧙‍♂️ D&D Character Creator 5.5e (2024)\n\n"
        "Что внутри:\n"
        "• 16 рас (с подрасами)\n"
        "• 13 классов\n"
        "• 16 предысторий\n"
        "• 50+ заклинаний\n"
        "• 30+ видов оружия\n"
        "• Авторасчёт характеристик\n"
        "• Генерация PDF\n\n"
        "⚙️ Фишки:\n"
        "• Умные бонусы от предыстории\n"
        "• Заклинания по категориям\n"
        "• Оружейные приёмы (Weapon Mastery)\n"
        "• Боевые стили\n\n"
        "🐉 Создай героя — и в бой!",
        parse_mode=None
    )


@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    await cmd_help(message)


@router.message(F.text == "❌ Отмена")
async def cancel_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Создание прервано.\n\nХочешь попробовать снова? Жми «🎲 Создать персонажа».",
        reply_markup=main_menu()
    )


# =========================================================
# ШАГ 1: ВЫБОР КЛАССА
# =========================================================
@router.callback_query(CreateCharacter.class_select, lambda c: c.data.startswith("class_"))
async def select_class(callback: CallbackQuery, state: FSMContext):
    class_name = callback.data.replace("class_", "")
    await state.update_data(class_name=class_name)
    logger.info(f"[FLOW] Выбран класс: {class_name}")

    class_desc = CharacterStatsService.get_class_description(class_name)
    class_info = CharacterStatsService.get_class_info(class_name)

    text = (f"🎭 {class_name}\n\n"
            f"{class_desc}\n\n"
            f"📊 Данные класса:\n"
            f"• Кость хитов: d{class_info.get('hit_die', 6)}\n"
            f"• Основные характеристики: {', '.join(class_info.get('primary_stats', []))}\n"
            f"• Спасброски: {', '.join(class_info.get('saving_throws', []))}\n"
            f"• Заклинания: {'Да' if class_info.get('spellcasting', False) else 'Нет'}\n")

    img_path = CharacterStatsService.get_class_image_path(class_name)

    # Отправляем картинку отдельно (не удаляется)
    if img_path and os.path.exists(img_path):
        photo = FSInputFile(img_path)
        await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None)
    else:
        await callback.message.answer(text, parse_mode=None)

    # Получаем данные для навыков
    class_data = _class_repo.get_by_name(class_name)
    available_skills = class_data.get('skills', []) if class_data else []
    skill_choices = class_data.get('skill_choices', 2) if class_data else 2
    if not available_skills:
        available_skills = [
            "Акробатика", "Атлетика", "Восприятие", "Выживание", "Выступление",
            "Запугивание", "История", "Ловкость рук", "Медицина", "Обман",
            "Обращение с животными", "Природа", "Проницательность", "Расследование",
            "Религия", "Скрытность", "Тайная магия", "Убеждение"
        ]

    await state.set_state(CreateCharacter.skills_select)
    selected_skills = []
    await state.update_data(selected_class_skills=selected_skills)

    keyboard = create_skills_keyboard(available_skills, skill_choices, selected_skills)
    text_skills = (f"📚 Навыки класса {class_name}\n\n"
                   f"Ты можешь выбрать {skill_choices} навыка(ов). Отмеченные ✅ войдут в лист.\n\n"
                   f"Когда наберёшь нужное количество, жми «✅ Готово».")

    await send_new_from_callback(callback, state, text_skills, keyboard)
    await callback.answer()


# =========================================================
# ШАГ 2: ВЫБОР НАВЫКОВ КЛАССА
# =========================================================
@router.callback_query(CreateCharacter.skills_select, lambda c: c.data.startswith("class_skill_toggle_") or c.data == "class_skills_ready" or c.data == "class_skills_info")
async def handle_skills_selection(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Обработчик навыков, data={callback.data}")
    data = callback.data
    user_data = await state.get_data()
    class_name = user_data.get("class_name")

    class_info = _class_repo.get_by_name(class_name)
    if not class_info:
        await callback.answer("❌ Ошибка: класс не найден")
        return

    available_skills = class_info.get('skills', [])
    if not available_skills:
        available_skills = [
            "Акробатика", "Атлетика", "Восприятие", "Выживание", "Выступление",
            "Запугивание", "История", "Ловкость рук", "Медицина", "Обман",
            "Обращение с животными", "Природа", "Проницательность", "Расследование",
            "Религия", "Скрытность", "Тайная магия", "Убеждение"
        ]
    skill_choices = class_info.get('skill_choices', 2)
    selected_skills = user_data.get("selected_class_skills", [])

    if data == "class_skills_ready":
        if len(selected_skills) == skill_choices:
            await state.update_data(selected_class_skills=selected_skills)
            await state.set_state(CreateCharacter.class_equipment_select)
            # Переходим к снаряжению класса
            await show_class_equipment(callback, state)
            await callback.answer("✅ Навыки класса выбраны!")
        else:
            await callback.answer(f"❌ Нужно выбрать ровно {skill_choices} навыка(ов). Сейчас выбрано: {len(selected_skills)}",
                                  show_alert=True)
        return

    if data == "class_skills_info":
        await callback.answer(f"Выбрано {len(selected_skills)} из {skill_choices}", show_alert=False)
        return

    if data.startswith("class_skill_toggle_"):
        skill_name = data.replace("class_skill_toggle_", "")
        if skill_name in selected_skills:
            selected_skills.remove(skill_name)
        else:
            if len(selected_skills) >= skill_choices:
                await callback.answer(f"❌ Нельзя взять больше {skill_choices} навыков.", show_alert=True)
                return
            selected_skills.append(skill_name)
        await state.update_data(selected_class_skills=selected_skills)
        keyboard = create_skills_keyboard(available_skills, skill_choices, selected_skills)
        try:
            # Редактируем текущее сообщение (только клавиатуру) – это допустимо
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Ошибка обновления клавиатуры: {e}")
            await callback.answer("⚠️ Что-то пошло не так. Попробуй ещё раз.", show_alert=True)
        await callback.answer()
        return


# =========================================================
# ШАГ 3: ВЫБОР СНАРЯЖЕНИЯ КЛАССА
# =========================================================
async def show_class_equipment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    if not class_name:
        logger.error("class_name не найден в state")
        await callback.answer("❌ Ошибка: класс не определён")
        return

    equipment = CharacterStatsService.get_class_equipment(class_name)
    if not equipment:
        logger.error(f"Нет снаряжения для {class_name}")
        await send_new_from_callback(callback, state, f"⚠️ Для класса {class_name} нет готового набора снаряжения. Переходим к следующему шагу.")
        await go_to_spells(callback, state)
        return

    has_equipment_choice = len(equipment) > 1
    if has_equipment_choice:
        text = f"⚔️ Снаряжение для {class_name}\n\nВыбери один стартовый набор:\n"
        for eq in equipment:
            choice = eq.get('choice', 'A')
            weapon = eq.get('weapon', 'нет оружия')
            armor = eq.get('armor', 'нет брони')
            secondary = eq.get('secondary_weapon', '')
            other = eq.get('other_items', '')
            coins = eq.get('coins', 0)
            text += f"\n📦 Вариант {choice}: {weapon}, {armor}"
            if secondary:
                text += f", {secondary}"
            if other:
                text += f", {other}"
            if coins:
                text += f", {coins} зм"
        text += "\n\nНажми на кнопку с подходящим вариантом."

        buttons = []
        for eq in equipment:
            choice = eq.get('choice', 'A')
            buttons.append([InlineKeyboardButton(text=f"📦 Вариант {choice}", callback_data=f"equip_{choice}")])
        buttons.append([InlineKeyboardButton(text="⬅️ Назад к классам", callback_data="back_to_classes")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await send_new_from_callback(callback, state, text, keyboard)
    else:
        eq = equipment[0]
        await state.update_data(
            selected_armor=eq.get('armor'),
            selected_weapon=eq.get('weapon'),
            selected_secondary_weapon=eq.get('secondary_weapon'),
            selected_other_items=eq.get('other_items'),
            selected_coins=eq.get('coins', 0)
        )
        weapon_name = eq.get('weapon')
        if weapon_name:
            masteries = CharacterStatsService.auto_assign_masteries(weapon_name, class_name)
            await state.update_data(selected_masteries=masteries)
        await go_to_spells(callback, state)


@router.callback_query(CreateCharacter.class_equipment_select, lambda c: c.data.startswith("equip_"))
async def select_class_equipment(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("equip_", "")
    data = await state.get_data()
    class_name = data.get("class_name")
    await state.update_data(equipment_choice=choice)

    equipment = CharacterStatsService.get_class_equipment(class_name, choice)
    if equipment:
        eq = equipment[0]
        await state.update_data(
            selected_armor=eq.get('armor'),
            selected_weapon=eq.get('weapon'),
            selected_secondary_weapon=eq.get('secondary_weapon'),
            selected_other_items=eq.get('other_items'),
            selected_coins=eq.get('coins', 0)
        )
        weapon_name = eq.get('weapon')
        if weapon_name:
            masteries = CharacterStatsService.auto_assign_masteries(weapon_name, class_name)
            await state.update_data(selected_masteries=masteries)

    await send_new_from_callback(callback, state, f"✅ Взят вариант {choice}")
    await go_to_spells(callback, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_classes")
async def back_to_classes(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.class_select)
    await send_new_from_callback(callback, state, "Выбери класс заново:", reply_markup=create_class_keyboard())
    await callback.answer()


# =========================================================
# ПЕРЕХОДЫ МЕЖДУ ШАГАМИ
# =========================================================
async def go_to_spells(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    is_spellcaster = ProgressionService.is_spellcaster(class_name)
    if is_spellcaster:
        await SpellSelectionService.start_cantrips_selection(callback, state)
    else:
        await go_to_fighting_style(callback, state)


async def go_to_fighting_style(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")

    if ProgressionService.should_select_fighting_style(class_name):
        styles = CharacterStatsService.get_fighting_styles_for_class(class_name)
        if not styles:
            await send_new_from_callback(callback, state, f"⚠️ У класса {class_name} нет боевых стилей. Переходим к предыстории.")
            await go_to_background(callback, state)
            return

        text = f"⚔️ Боевой стиль\n\nКласс {class_name} позволяет взять один стиль.\n\nДоступно:\n"
        for s in styles:
            text += f"• {s['name']} – {s['description']}\n"
        text += "\nНажми на название, чтобы выбрать."

        buttons = []
        for s in styles:
            buttons.append([InlineKeyboardButton(text=f"⚔️ {s['name']}", callback_data=f"style_{s['id']}")])
        buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_spells")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await state.set_state(CreateCharacter.fighting_style_select)
        await send_new_from_callback(callback, state, text, keyboard)
    else:
        await go_to_background(callback, state)


async def go_to_background(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.background_select)
    await send_new_from_callback(callback, state,
                            "📜 Твоё прошлое (предыстория)\n\n"
                            "Предыстория даёт бонусы к характеристикам, черту происхождения, навыки и инструменты.\n\n"
                            "Выбери одну:",
                            reply_markup=create_background_keyboard())


# =========================================================
# БОЕВОЙ СТИЛЬ
# =========================================================
@router.callback_query(CreateCharacter.fighting_style_select, lambda c: c.data.startswith("style_"))
async def select_fighting_style(callback: CallbackQuery, state: FSMContext):
    style_id = int(callback.data.replace("style_", ""))
    style = _fighting_repo.get_by_id(style_id)
    style_name = style.get('name') if style else None
    if style_name:
        await state.update_data(selected_fighting_style=style_name)
        logger.info(f"[FLOW] Выбран боевой стиль: {style_name}")
        await callback.answer(f"✅ Выбран стиль: {style_name}")
    await go_to_background(callback, state)


@router.callback_query(lambda c: c.data == "back_to_spells")
async def back_to_spells(callback: CallbackQuery, state: FSMContext):
    await go_to_spells(callback, state)


# =========================================================
# ПРЕДЫСТОРИЯ
# =========================================================
@router.callback_query(CreateCharacter.background_select, lambda c: c.data.startswith("bg_"))
async def select_background(callback: CallbackQuery, state: FSMContext):
    background = callback.data.replace("bg_", "")
    await state.update_data(background=background)
    logger.info(f"[FLOW] Выбрана предыстория: {background}")

    bg_info = _bg_repo.get_by_name(background)
    if not bg_info:
        await send_new_from_callback(callback, state, f"❌ Ошибка: предыстория '{background}' не найдена.")
        await state.clear()
        return

    await state.update_data(
        selected_skills_bg=bg_info.get('skills', []),
        background_trait=bg_info.get('trait', 'Нет'),
        background_origin_feat=bg_info.get('origin_feat', '')
    )

    origin_feat = bg_info.get('origin_feat', '')
    origin_feat_text = f"✨ Черта происхождения: {origin_feat}\n\n" if origin_feat else ""

    text = (f"📜 {background}\n\n"
            f"📖 {bg_info.get('description', 'Нет описания')[:300]}...\n\n"
            f"{origin_feat_text}"
            f"✨ Бонусы характеристик: +2 {bg_info['characteristics'][0]}, +1 {bg_info['characteristics'][1]}\n\n"
            f"🔧 Черта: {bg_info.get('trait', 'Нет')}\n"
            f"📚 Навыки: {', '.join(bg_info.get('skills', []))}\n"
            f"🛠️ Инструменты: {bg_info.get('tools', 'Нет')}\n\n"
            f"Теперь перейдём к расчёту характеристик и выбору расы.")
    await send_new_from_callback(callback, state, text)
    await calculate_and_show_stats(callback, state)
    await callback.answer()


# =========================================================
# РАСЧЁТ ХАРАКТЕРИСТИК
# =========================================================
async def calculate_and_show_stats(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    background = data.get("background")
    equipment_choice = data.get("equipment_choice", "A")

    stats_result = CharacterStatsService.calculate_and_format_stats(
        class_name=class_name,
        background=background,
        base_stats_dict=None,
        equipment_choice=equipment_choice
    )

    await state.update_data(
        final_stats=stats_result['stats'],
        stats=stats_result['stats'],
        hp=stats_result['hp'],
        ac=stats_result['ac']
    )

    stats = stats_result['stats']
    def mod(s): return (s-10)//2

    text = (f"📊 Твои характеристики\n\n"
            f"Класс: {class_name}\n"
            f"Предыстория: {background}\n\n"
            f"✨ Бонусы предыстории: +2 к {stats_result['bg_chars'][0]}, +1 к {stats_result['bg_chars'][1]}\n\n"
            f"📈 Итоговые значения (модификатор):\n"
            f"💪 Сила (STR): {stats['STR']} ({mod(stats['STR']):+d})\n"
            f"🤸 Ловкость (DEX): {stats['DEX']} ({mod(stats['DEX']):+d})\n"
            f"🏋️ Телосложение (CON): {stats['CON']} ({mod(stats['CON']):+d})\n"
            f"🧠 Интеллект (INT): {stats['INT']} ({mod(stats['INT']):+d})\n"
            f"🧙 Мудрость (WIS): {stats['WIS']} ({mod(stats['WIS']):+d})\n"
            f"✨ Харизма (CHA): {stats['CHA']} ({mod(stats['CHA']):+d})\n\n"
            f"❤️ Хиты (HP): {stats_result['hp']}\n"
            f"🛡️ Класс брони (AC): {stats_result['ac']}\n\n"
            f"А теперь выбери расу:")

    await send_new_from_callback(callback, state, text, reply_markup=create_race_keyboard())
    await state.set_state(CreateCharacter.race_select)


# =========================================================
# РАСА
# =========================================================
@router.callback_query(CreateCharacter.race_select, lambda c: c.data.startswith("race_"))
async def select_race(callback: CallbackQuery, state: FSMContext):
    race = callback.data.replace("race_", "")
    await state.update_data(race=race)
    logger.info(f"[FLOW] Выбрана раса: {race}")

    race_desc = CharacterStatsService.get_race_description(race)
    race_speed = CharacterStatsService.get_race_speed(race)
    race_size = CharacterStatsService.get_race_size(race)
    has_sub = CharacterStatsService.has_subraces(race)
    subraces_list = CharacterStatsService.get_subraces(race) if has_sub else []

    text = f"🧝 Раса: {race}\n\n📖 {race_desc}\n\n🏃 Скорость: {race_speed} футов\n📏 Размер: {race_size}\n"
    img_path = CharacterStatsService.get_race_image_path(race)

    # Отправляем картинку расы отдельным сообщением (не удаляется)
    if img_path and os.path.exists(img_path):
        photo = FSInputFile(img_path)
        await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None)
    else:
        await callback.message.answer(text, parse_mode=None)

    if has_sub and subraces_list:
        from keyboards.character_keyboards import create_subrace_keyboard
        sub_text = "🌟 Выбери подрасу:"
        await send_new_from_callback(callback, state, sub_text, reply_markup=create_subrace_keyboard(race))
        await state.set_state(CreateCharacter.subrace_select)
    else:
        await go_to_name(callback, state)
    await callback.answer()


@router.callback_query(CreateCharacter.subrace_select, lambda c: c.data.startswith("subrace_"))
async def select_subrace(callback: CallbackQuery, state: FSMContext):
    subrace = callback.data.replace("subrace_", "")
    await state.update_data(subrace=subrace)
    data = await state.get_data()
    race = data.get("race")
    sub_desc = CharacterStatsService.get_subrace_description(race, subrace)
    sub_trait = CharacterStatsService.get_subrace_trait(race, subrace)
    # Короткое уведомление, затем переход
    await callback.answer(f"✅ Выбрана подраса: {subrace}")
    await go_to_name(callback, state)


@router.callback_query(lambda c: c.data == "back_to_races")
async def back_to_races(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.race_select)
    await send_new_from_callback(callback, state, "Выбери расу заново:", reply_markup=create_race_keyboard())
    await callback.answer()


# =========================================================
# ИМЯ И ИСТОРИЯ
# =========================================================
async def go_to_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.name_input)
    text = "📛 Как зовут твоего героя?\n\nИмя: от 2 до 50 символов. Любое на твой вкус.\n\nВведи имя:"
    await send_new_from_callback(callback, state, text, reply_markup=cancel_kb())


async def go_to_backstory_step(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.backstory_input)
    text = "📖 История персонажа\n\nКоротко расскажи:\n• Откуда он родом?\n• Что привело его к приключениям?\n• Какая цель движет им?\n\nВведи текст (до 2000 символов):"
    await send_new_from_callback(callback, state, text, reply_markup=cancel_kb())


@router.message(CreateCharacter.name_input)
async def set_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_creation(message, state)
        return
    valid, msg = engine_validate_name(message.text)
    if not valid:
        await message.answer(f"{msg}\nПопробуй другое имя:", reply_markup=cancel_kb())
        return
    await state.update_data(name=message.text.strip())
    # Удаляем сообщение пользователя (можно, но необязательно)
    await message.delete()
    # Отправляем новое служебное сообщение с подтверждением и переходом
    await send_new(state, message, f"✅ Имя: {message.text.strip()}\n\nТеперь введи историю:")
    # Устанавливаем состояние и отправляем запрос истории
    await state.set_state(CreateCharacter.backstory_input)
    text_history = "📖 История персонажа\n\nКоротко расскажи:\n• Откуда он родом?\n• Что привело его к приключениям?\n• Какая цель движет им?\n\nВведи текст (до 2000 символов):"
    await send_new(state, message, text_history, reply_markup=cancel_kb())


@router.message(CreateCharacter.backstory_input)
async def set_backstory(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_creation(message, state)
        return
    backstory = message.text.strip()
    if len(backstory) > 2000:
        await message.answer("❌ История не помещается — максимум 2000 символов. Сократи немного.", reply_markup=cancel_kb())
        return
    await state.update_data(backstory=backstory)
    await message.delete()
    await state.set_state(CreateCharacter.alignment_select)
    from keyboards.character_keyboards import create_alignment_keyboard
    text = "⚖️ Выбери мировоззрение своего персонажа:"
    await send_new(state, message, text, reply_markup=create_alignment_keyboard())


# =========================================================
# МИРОВОЗЗРЕНИЕ
# =========================================================
@router.callback_query(CreateCharacter.alignment_select, lambda c: c.data.startswith("alignment_"))
async def select_alignment(callback: CallbackQuery, state: FSMContext):
    alignment_value = callback.data.replace("alignment_", "")
    alignment_map = {
        "lawful_good": "Законно-добрый",
        "neutral_good": "Нейтрально-добрый",
        "chaotic_good": "Хаотично-добрый",
        "lawful_neutral": "Законно-нейтральный",
        "neutral": "Нейтральный",
        "chaotic_neutral": "Хаотично-нейтральный",
        "lawful_evil": "Законно-злой",
        "neutral_evil": "Нейтрально-злой",
        "chaotic_evil": "Хаотично-злой"
    }
    alignment_name = alignment_map.get(alignment_value, "Нейтральный")
    await state.update_data(alignment=alignment_name)
    logger.info(f"[FLOW] Выбрано мировоззрение: {alignment_name}")
    await callback.answer(f"✅ Мировоззрение: {alignment_name}")

    await state.set_state(CreateCharacter.image_input)
    text = f"⚖️ Мировоззрение: {alignment_name}\n\n🖼️ Теперь портрет\n\nЗагрузи изображение (можно пропустить кнопкой)."
    await send_new_from_callback(callback, state, text, reply_markup=skip_kb())


# =========================================================
# ИЗОБРАЖЕНИЕ И ФИНАЛИЗАЦИЯ
# =========================================================
@router.message(F.text == "⏩ Пропустить")
async def skip_image(message: Message, state: FSMContext):
    await finalize_character(message, state, image_file_id=None)


@router.message(CreateCharacter.image_input, F.photo)
async def set_image(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    await finalize_character(message, state, image_file_id=file_id)


async def finalize_character(message: Message, state: FSMContext, image_file_id: Optional[str] = None):
    try:
        await message.answer("⏳ Сохраняю персонажа...", reply_markup=ReplyKeyboardRemove())

        data = await state.get_data()
        char_data = CharacterFinalizationService.prepare_character_data(data, message.from_user.id)
        char_data['image_file_id'] = image_file_id
        char_data['origin_feat'] = data.get("background_origin_feat", "")
        char_data['alignment'] = data.get("alignment", "Нейтральный")

        name = char_data['name']
        if not name:
            await message.answer("❌ Ошибка: имя не сохранено.", reply_markup=main_menu())
            await state.clear()
            return

        class_skills = data.get("selected_class_skills", [])
        bg_skills = data.get("selected_skills_bg", [])
        all_skills = list(set(class_skills + bg_skills))
        char_data['selected_skills'] = all_skills

        char_id = CharacterFinalizationService.save_character(char_data)
        if not char_id:
            await message.answer("❌ Не удалось сохранить персонажа.", reply_markup=main_menu())
            await state.clear()
            return

        web_app_url = f"{WEBAPP_BASE_URL}/character/{char_id}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📄 Открыть лист персонажа", web_app=WebAppInfo(url=web_app_url))]
        ])

        stats = char_data['stats']
        def mod(s): return (s - 10) // 2
        spells_preview = ""
        if char_data.get('selected_spells'):
            spells_preview = f"\n🔮 Заклинания: {', '.join(char_data['selected_spells'][:5])}"
        caption = (f"✅ Персонаж {name} ({char_data['class_name']}, {char_data['race']}) создан!\n"
                   f"❤️ HP: {char_data['hp']} | 🛡️ AC: {char_data['ac']}\n"
                   f"📊 Характеристики: STR {stats['STR']} ({mod(stats['STR']):+d}), DEX {stats['DEX']} ({mod(stats['DEX']):+d}), "
                   f"CON {stats['CON']} ({mod(stats['CON']):+d}), INT {stats['INT']} ({mod(stats['INT']):+d}), "
                   f"WIS {stats['WIS']} ({mod(stats['WIS']):+d}), CHA {stats['CHA']} ({mod(stats['CHA']):+d}){spells_preview}\n\n"
                   f"⚖️ Мировоззрение: {char_data['alignment']}\n"
                   f"✨ Черта происхождения: {char_data['origin_feat'] if char_data['origin_feat'] else 'Нет'}\n\n"
                   f"Нажмите на кнопку, чтобы открыть полный лист.")

        # Финальное сообщение – не удаляем, оно нужно пользователю
        await message.answer(caption, reply_markup=keyboard)

        # Отправляем фото, если есть
        if image_file_id:
            await message.answer_photo(photo=image_file_id, caption="🏴‍☠️ Портрет персонажа", parse_mode=None)

        await message.answer("🏠 Главное меню", reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при создании персонажа: {e}", exc_info=True)
        await message.answer(f"❌ Произошла ошибка: {str(e)[:200]}", reply_markup=main_menu())
        await state.clear()


# =========================================================
# ПРОСМОТР И УДАЛЕНИЕ ПЕРСОНАЖЕЙ (без изменений)
# =========================================================
@router.callback_query(lambda c: c.data.startswith("view_"))
async def view_character(callback: CallbackQuery):
    char_id = int(callback.data.replace("view_", ""))
    character = _char_repo.get_by_id(char_id, callback.from_user.id)
    if not character:
        await callback.answer("❌ Персонаж не найден")
        return
    info = (f"📛 {character['name']}\n\n"
            f"🧝 Раса: {character.get('race_name', 'Неизвестно')}\n"
            f"⚔️ Класс: {character.get('class_name', 'Неизвестно')}\n"
            f"📜 Предыстория: {character.get('background_name', 'Нет')}\n"
            f"⚖️ Мировоззрение: {character.get('alignment', 'Нейтральный')}\n"
            f"📊 Уровень: {character['level']}\n"
            f"❤️ HP: {character['hp']} | 🛡️ AC: {character['ac']}\n\n"
            f"Характеристики:\n"
            f"Сила {character['str']} | Ловкость {character['dex']} | Телосложение {character['con']} | "
            f"Интеллект {character['int']} | Мудрость {character['wis']} | Харизма {character['cha']}")
    if character.get('image_file_id'):
        await callback.message.answer_photo(photo=character['image_file_id'], caption=info, parse_mode=None)
    else:
        await callback.message.answer(info, parse_mode=None)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("delete_"))
async def confirm_delete(callback: CallbackQuery):
    char_id = int(callback.data.replace("delete_", ""))
    character = _char_repo.get_by_id(char_id, callback.from_user.id)
    if not character:
        await callback.answer("❌ Персонаж не найден")
        return
    if _char_repo.delete(char_id, callback.from_user.id):
        await callback.message.edit_text(f"✅ {character['name']} навсегда ушёл в прошлое.", parse_mode=None)
    else:
        await callback.message.edit_text("❌ Не получилось удалить. Попробуй позже.")
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.edit_text("❌ Удаление отменено")
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_creation")
async def cancel_creation_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "❌ Создание отменено.\n\nНачать заново? Кнопка «🎲 Создать персонажа».",
        reply_markup=main_menu()
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "progress_info")
async def progress_info(callback: CallbackQuery):
    await callback.answer("Это информационное сообщение", show_alert=False)


# =========================================================
# НЕИЗВЕСТНЫЕ КОМАНДЫ
# =========================================================
@router.message()
async def unknown_command(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await message.answer(
            "⏳ Ты сейчас создаёшь персонажа. Продолжай по шагам или нажми «❌ Отмена».",
            reply_markup=cancel_kb()
        )
    else:
        await message.answer(
            "❓ Не знаю такой команды.\n\nПопробуй кнопки меню или /help.",
            reply_markup=main_menu()
        )