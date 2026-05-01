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
from repositories.class_repository import ClassRepository
from repositories.background_repository import BackgroundRepository
from repositories.equipment_repository import EquipmentRepository, FightingStyleRepository
from repositories.spell_repository import SpellRepository

from engine.validators import validate_name as engine_validate_name

# Импорт строковых констант
from strings import *

def format_mod(mod_value: int) -> str:
    if mod_value > 0:
        return f"+{mod_value}"
    elif mod_value < 0:
        return str(mod_value)
    else:
        return "0"

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
    data = await state.get_data()
    prev_msg_id = data.get("last_bot_message_id")
    if prev_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=prev_msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {prev_msg_id}: {e}")
    new_msg = await message.answer(text, reply_markup=reply_markup, parse_mode=None)
    await state.update_data(last_bot_message_id=new_msg.message_id)
    return new_msg

async def send_new_from_callback(callback: CallbackQuery, state: FSMContext, text: str, reply_markup=None):
    """Отправляет новое сообщение из callback, удаляя предыдущее."""
    data = await state.get_data()
    prev_msg_id = data.get("last_bot_message_id")
    if prev_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=prev_msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {prev_msg_id}: {e}")
    new_msg = await callback.message.answer(text, reply_markup=reply_markup, parse_mode=None)
    await state.update_data(last_bot_message_id=new_msg.message_id)
    return new_msg


# =========================================================
# КОМАНДЫ
# =========================================================
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(GREETING, reply_markup=main_menu(), parse_mode=None)


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(MENU_TITLE, reply_markup=main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(HELP_TEXT, parse_mode=None)


# =========================================================
# КНОПКИ ГЛАВНОГО МЕНЮ
# =========================================================
@router.message(F.text == BTN_CREATE_CHAR)
async def create_character_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CreateCharacter.class_select)
    # Отправляем временное сообщение с ReplyKeyboardRemove (непустой текст)
    temp_msg = await message.answer("⌛", reply_markup=ReplyKeyboardRemove())
    # Сразу удаляем его, чтобы не мешал
    await temp_msg.delete()
    # Отправляем основное сообщение с inline-клавиатурой
    msg = await message.answer(CLASS_SELECT_TITLE, reply_markup=create_class_keyboard())
    await state.update_data(last_bot_message_id=msg.message_id)


@router.message(F.text == BTN_MY_CHARS)
async def list_characters(message: Message):
    characters = _char_repo.get_by_user_id(message.from_user.id)
    if not characters:
        await message.answer(NO_CHARACTERS)
        return
    await message.answer(YOUR_CHARACTERS, reply_markup=create_character_list_with_webapp_keyboard(message.from_user.id, WEBAPP_BASE_URL))


@router.message(F.text == BTN_DELETE_CHAR)
async def delete_character_menu(message: Message):
    characters = _char_repo.get_by_user_id(message.from_user.id)
    if not characters:
        await message.answer(NOTHING_TO_DELETE)
        return
    await message.answer(DELETE_PROMPT, reply_markup=create_delete_keyboard(characters))


@router.message(F.text == BTN_ABOUT)
async def info_button(message: Message):
    await message.answer(ABOUT_TEXT, parse_mode=None)


@router.message(F.text == BTN_HELP)
async def help_button(message: Message):
    await cmd_help(message)


@router.message(F.text == BTN_CANCEL)
async def cancel_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(CANCEL_CREATION, reply_markup=main_menu())


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

    spellcasting_text = "Да" if class_info.get('spellcasting', False) else "Нет"
    text = CLASS_INFO_TEMPLATE.format(
        class_name=class_name,
        class_desc=class_desc,
        hit_die=class_info.get('hit_die', 6),
        primary_stats=", ".join(class_info.get('primary_stats', [])),
        saving_throws=", ".join(class_info.get('saving_throws', [])),
        spellcasting=spellcasting_text
    )

    img_path = CharacterStatsService.get_class_image_path(class_name)

    # Отправляем картинку отдельно (не удаляется)
    if img_path and os.path.exists(img_path):
        photo = FSInputFile(img_path)
        await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None)
    else:
        await callback.message.answer(text, parse_mode=None)

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
    text_skills = SKILLS_REQUEST_TEMPLATE.format(class_name=class_name, skill_choices=skill_choices)

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
        await callback.answer(SKILLS_ERROR_CLASS_NOT_FOUND)
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
            await show_class_equipment(callback, state)
            await callback.answer(SKILLS_SUCCESS)
        else:
            msg = SKILLS_ERROR_WRONG_COUNT.format(skill_choices=skill_choices, selected=len(selected_skills))
            await callback.answer(msg, show_alert=True)
        return

    if data == "class_skills_info":
        info = SKILLS_INFO_SELECTED.format(selected=len(selected_skills), max=skill_choices)
        await callback.answer(info, show_alert=False)
        return

    if data.startswith("class_skill_toggle_"):
        skill_name = data.replace("class_skill_toggle_", "")
        if skill_name in selected_skills:
            selected_skills.remove(skill_name)
        else:
            if len(selected_skills) >= skill_choices:
                msg = SKILLS_ERROR_TOO_MANY.format(skill_choices=skill_choices)
                await callback.answer(msg, show_alert=True)
                return
            selected_skills.append(skill_name)
        await state.update_data(selected_class_skills=selected_skills)
        keyboard = create_skills_keyboard(available_skills, skill_choices, selected_skills)
        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Ошибка обновления клавиатуры: {e}")
            await callback.answer(SKILLS_ERROR_GENERIC, show_alert=True)
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
        msg = EQUIPMENT_NOT_FOUND.format(class_name=class_name)
        await send_new_from_callback(callback, state, msg)
        await go_to_spells(callback, state)
        return

    has_equipment_choice = len(equipment) > 1
    if has_equipment_choice:
        text = EQUIPMENT_TITLE_TEMPLATE.format(class_name=class_name)
        for eq in equipment:
            choice = eq.get('choice', 'A')
            weapon = eq.get('weapon', 'нет оружия')
            armor = eq.get('armor', 'нет брони')
            text += EQUIPMENT_OPTION_TEMPLATE.format(choice=choice, weapon=weapon, armor=armor)
        text += EQUIPMENT_CHOICE_PROMPT

        buttons = []
        for eq in equipment:
            choice = eq.get('choice', 'A')
            btn_text = BTN_EQUIP_OPTION.format(choice=choice, weapon="", armor="")  # упростим, можно без оружия/брони для краткости
            # лучше оставить как было, но для чистоты используем константу с параметрами
            buttons.append([InlineKeyboardButton(text=f"📦 Вариант {choice}", callback_data=f"equip_{choice}")])
        buttons.append([InlineKeyboardButton(text=BACK_TO_CLASSES, callback_data="back_to_classes")])
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

    msg = EQUIPMENT_SELECTED.format(choice=choice)
    await send_new_from_callback(callback, state, msg)
    await go_to_spells(callback, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_classes")
async def back_to_classes(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.class_select)
    await send_new_from_callback(callback, state, BACK_TO_CLASSES, reply_markup=create_class_keyboard())
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
            msg = FIGHTING_STYLE_NO_STYLES.format(class_name=class_name)
            await send_new_from_callback(callback, state, msg)
            await go_to_background(callback, state)
            return

        styles_list = "\n".join([f"• {s['name']} – {s['description']}" for s in styles])
        text = FIGHTING_STYLE_TITLE_TEMPLATE.format(class_name=class_name, styles_list=styles_list)

        buttons = []
        for s in styles:
            buttons.append([InlineKeyboardButton(text=f"⚔️ {s['name']}", callback_data=f"style_{s['id']}")])
        buttons.append([InlineKeyboardButton(text=FIGHTING_STYLE_BACK, callback_data="back_to_spells")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

        await state.set_state(CreateCharacter.fighting_style_select)
        await send_new_from_callback(callback, state, text, keyboard)
    else:
        await go_to_background(callback, state)


async def go_to_background(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.background_select)
    await send_new_from_callback(callback, state, BACKGROUND_SELECT_TITLE, reply_markup=create_background_keyboard())


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
        msg = FIGHTING_STYLE_SELECTED.format(style_name=style_name)
        await callback.answer(msg)
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
        msg = BACKGROUND_ERROR.format(background=background)
        await send_new_from_callback(callback, state, msg)
        await state.clear()
        return

    await state.update_data(
        selected_skills_bg=bg_info.get('skills', []),
        background_trait=bg_info.get('trait', 'Нет'),
        background_origin_feat=bg_info.get('origin_feat', '')
    )

    trait = bg_info.get('trait', 'Нет')
    skills = ", ".join(bg_info.get('skills', []))
    tools = bg_info.get('tools', 'Нет')
    description = bg_info.get('description', 'Нет описания')[:300]
    text = BACKGROUND_INFO_TEMPLATE.format(
        background=background,
        description=description,
        trait=trait,
        skills=skills,
        tools=tools
    )
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

    text = STATS_RESULT_TEMPLATE.format(
        class_name=class_name,
        background=background,
        STR=stats['STR'], mod_str=format_mod(mod(stats['STR'])),
        DEX=stats['DEX'], mod_dex=format_mod(mod(stats['DEX'])),
        CON=stats['CON'], mod_con=format_mod(mod(stats['CON'])),
        INT=stats['INT'], mod_int=format_mod(mod(stats['INT'])),
        WIS=stats['WIS'], mod_wis=format_mod(mod(stats['WIS'])),
        CHA=stats['CHA'], mod_cha=format_mod(mod(stats['CHA'])),
        hp=stats_result['hp'],
        ac=stats_result['ac']
    )

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

    text = RACE_INFO_TEMPLATE.format(race=race, desc=race_desc, speed=race_speed, size=race_size)
    img_path = CharacterStatsService.get_race_image_path(race)

    if img_path and os.path.exists(img_path):
        photo = FSInputFile(img_path)
        await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None)
    else:
        await callback.message.answer(text, parse_mode=None)

    if has_sub and subraces_list:
        from keyboards.character_keyboards import create_subrace_keyboard
        await send_new_from_callback(callback, state, RACE_SUBRACE_PROMPT, reply_markup=create_subrace_keyboard(race))
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
    msg = SUBRACE_SELECTED.format(subrace=subrace)
    await callback.answer(msg)
    await go_to_name(callback, state)


@router.callback_query(lambda c: c.data == "back_to_races")
async def back_to_races(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.race_select)
    await send_new_from_callback(callback, state, BACK_TO_RACES, reply_markup=create_race_keyboard())
    await callback.answer()


# =========================================================
# ИМЯ И ИСТОРИЯ
# =========================================================
async def go_to_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.name_input)
    await send_new_from_callback(callback, state, NAME_REQUEST, reply_markup=cancel_kb())


async def go_to_backstory_step(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.backstory_input)
    await send_new_from_callback(callback, state, BACKSTORY_REQUEST, reply_markup=cancel_kb())


@router.message(CreateCharacter.name_input)
async def set_name(message: Message, state: FSMContext):
    if message.text == BTN_CANCEL:
        await cancel_creation(message, state)
        return
    valid, msg = engine_validate_name(message.text)
    if not valid:
        await message.answer(NAME_INVALID, reply_markup=cancel_kb())
        return
    await state.update_data(name=message.text.strip())
    await message.delete()
    confirm = NAME_CONFIRM.format(name=message.text.strip())
    await send_new(state, message, confirm)
    await state.set_state(CreateCharacter.backstory_input)
    await send_new(state, message, BACKSTORY_REQUEST, reply_markup=cancel_kb())


@router.message(CreateCharacter.backstory_input)
async def set_backstory(message: Message, state: FSMContext):
    if message.text == BTN_CANCEL:
        await cancel_creation(message, state)
        return
    backstory = message.text.strip()
    if len(backstory) > 2000:
        await message.answer(BACKSTORY_TOO_LONG, reply_markup=cancel_kb())
        return
    await state.update_data(backstory=backstory)
    await message.delete()
    await state.set_state(CreateCharacter.alignment_select)
    from keyboards.character_keyboards import create_alignment_keyboard
    await send_new(state, message, ALIGNMENT_REQUEST, reply_markup=create_alignment_keyboard())


# =========================================================
# МИРОВОЗЗРЕНИЕ
# =========================================================
@router.callback_query(CreateCharacter.alignment_select, lambda c: c.data.startswith("alignment_"))
async def select_alignment(callback: CallbackQuery, state: FSMContext):
    alignment_value = callback.data.replace("alignment_", "")
    alignment_name = BTN_ALIGNMENT_NAMES.get(alignment_value, "Нейтральный")
    await state.update_data(alignment=alignment_name)
    logger.info(f"[FLOW] Выбрано мировоззрение: {alignment_name}")
    msg = ALIGNMENT_SELECTED.format(alignment=alignment_name)
    await callback.answer(msg)

    await state.set_state(CreateCharacter.image_input)
    await send_new_from_callback(callback, state, IMAGE_REQUEST, reply_markup=skip_kb())


# =========================================================
# ИЗОБРАЖЕНИЕ И ФИНАЛИЗАЦИЯ
# =========================================================
@router.message(F.text == BTN_SKIP)
async def skip_image(message: Message, state: FSMContext):
    await finalize_character(message, state, image_file_id=None)


@router.message(CreateCharacter.image_input, F.photo)
async def set_image(message: Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    await finalize_character(message, state, image_file_id=file_id)


async def finalize_character(message: Message, state: FSMContext, image_file_id: Optional[str] = None):
    try:
        await message.answer(SAVING_START, reply_markup=ReplyKeyboardRemove())

        data = await state.get_data()
        char_data = CharacterFinalizationService.prepare_character_data(data, message.from_user.id)
        char_data['image_file_id'] = image_file_id
        char_data['origin_feat'] = data.get("background_origin_feat", "")
        char_data['alignment'] = data.get("alignment", "Нейтральный")

        name = char_data['name']
        if not name:
            await message.answer(SAVING_ERROR_NAME_MISSING, reply_markup=main_menu())
            await state.clear()
            return

        class_skills = data.get("selected_class_skills", [])
        bg_skills = data.get("selected_skills_bg", [])
        all_skills = list(set(class_skills + bg_skills))
        char_data['selected_skills'] = all_skills

        char_id = CharacterFinalizationService.save_character(char_data)
        if not char_id:
            await message.answer(SAVING_ERROR_GENERIC, reply_markup=main_menu())
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
            spells_preview = ", ".join(char_data['selected_spells'][:5])
        caption = FINAL_CAPTION_TEMPLATE.format(
            name=name,
            race=char_data['race'],
            class_name=char_data['class_name'],
            hp=char_data['hp'],
            ac=char_data['ac'],
            STR=stats['STR'], mod_str=format_mod(mod(stats['STR'])),
            DEX=stats['DEX'], mod_dex=format_mod(mod(stats['DEX'])),
            CON=stats['CON'], mod_con=format_mod(mod(stats['CON'])),
            INT=stats['INT'], mod_int=format_mod(mod(stats['INT'])),
            WIS=stats['WIS'], mod_wis=format_mod(mod(stats['WIS'])),
            CHA=stats['CHA'], mod_cha=format_mod(mod(stats['CHA'])),
            spells_preview=spells_preview,
            alignment=char_data['alignment'],
            origin_feat=char_data['origin_feat'] if char_data['origin_feat'] else 'Нет'
        )

        await message.answer(caption, reply_markup=keyboard)

        if image_file_id:
            await message.answer_photo(photo=image_file_id, caption="🏴‍☠️ Портрет персонажа", parse_mode=None)

        await message.answer(MENU_TITLE, reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при создании персонажа: {name} {e}", exc_info=True)
        await message.answer(f"❌ Произошла ошибка: {str(e)[:200]}", reply_markup=main_menu())
        await state.clear()


# =========================================================
# ПРОСМОТР И УДАЛЕНИЕ ПЕРСОНАЖЕЙ
# =========================================================
@router.callback_query(lambda c: c.data.startswith("view_"))
async def view_character(callback: CallbackQuery):
    char_id = int(callback.data.replace("view_", ""))
    character = _char_repo.get_by_id(char_id, callback.from_user.id)
    if not character:
        await callback.answer("❌ Персонаж не найден")
        return
    text = VIEW_CHARACTER_TEMPLATE.format(
        name=character['name'],
        race=character.get('race_name', 'Неизвестно'),
        class_name=character.get('class_name', 'Неизвестно'),
        background=character.get('background_name', 'Нет'),
        alignment=character.get('alignment', 'Нейтральный'),
        level=character['level'],
        hp=character['hp'],
        ac=character['ac'],
        str=character['str'],
        dex=character['dex'],
        con=character['con'],
        int=character['int'],
        wis=character['wis'],
        cha=character['cha']
    )
    if character.get('image_file_id'):
        await callback.message.answer_photo(photo=character['image_file_id'], caption=text, parse_mode=None)
    else:
        await callback.message.answer(text, parse_mode=None)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("delete_"))
async def confirm_delete(callback: CallbackQuery):
    char_id = int(callback.data.replace("delete_", ""))
    character = _char_repo.get_by_id(char_id, callback.from_user.id)
    if not character:
        await callback.answer("❌ Персонаж не найден")
        return
    if _char_repo.delete(char_id, callback.from_user.id):
        msg = DELETE_SUCCESS.format(name=character['name'])
        await callback.message.edit_text(msg, parse_mode=None)
    else:
        await callback.message.edit_text(DELETE_FAIL, parse_mode=None)
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.edit_text(DELETE_CANCEL, parse_mode=None)
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_creation")
async def cancel_creation_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(CANCEL_CREATION_CALLBACK, reply_markup=main_menu())
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
        await message.answer(UNKNOWN_IN_PROGRESS, reply_markup=cancel_kb())
    else:
        await message.answer(UNKNOWN_IDLE, reply_markup=main_menu())