# handlers/character_handlers.py
"""
Обработчики для создания персонажа
Используют сервисы для бизнес-логики
"""

import logging
import os
import re
import tempfile
from typing import Optional

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, FSInputFile, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from states.character_states import CreateCharacter
from keyboards.character_keyboards import (
    create_class_keyboard,
    create_class_equipment_keyboard,
    create_subclass_keyboard,
    create_race_keyboard,
    create_subrace_keyboard,
    create_background_keyboard,
    create_background_equipment_keyboard,
    create_fighting_style_keyboard,
    create_invocations_keyboard,
    create_character_list_keyboard,
    create_delete_keyboard,
    create_skills_keyboard,   # ✅ добавлен импорт
    cancel_kb,
    skip_kb,
    continue_kb_for_spells,
    main_menu
)

from services.character_service import CharacterStatsService, CharacterFinalizationService
from services.progression_service import ProgressionService
from services.spell_service import SpellSelectionService
from repositories.character_repository import CharacterRepository
from repositories.race_repository import RaceRepository
from repositories.class_repository import ClassRepository
from repositories.background_repository import BackgroundRepository
from repositories.equipment_repository import EquipmentRepository, FightingStyleRepository, InvocationRepository
from repositories.spell_repository import SpellRepository

from pdf_generator import generate_pdf
from engine.validators import validate_name as engine_validate_name

logger = logging.getLogger(__name__)

router = Router()

# Репозитории
_race_repo = RaceRepository()
_class_repo = ClassRepository()
_bg_repo = BackgroundRepository()
_equip_repo = EquipmentRepository()
_fighting_repo = FightingStyleRepository()
_inv_repo = InvocationRepository()
_spell_repo = SpellRepository()
_char_repo = CharacterRepository()


# =========================================================
# КОМАНДЫ
# =========================================================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🎮 Добро пожаловать в D&D Character Creator 5.5e (2024)!\n\n"
        "Я помогу тебе создать персонажа для Dungeons & Dragons 5-й редакции.\n\n"
        "📋 **Порядок создания:**\n"
        "1️⃣ Выбор класса\n"
        "2️⃣ Выбор навыков класса\n"
        "3️⃣ Выбор снаряжения\n"
        "4️⃣ Выбор заклинаний\n"
        "5️⃣ Выбор боевого стиля\n"
        "6️⃣ Выбор предыстории\n"
        "7️⃣ Выбор расы\n"
        "8️⃣ Ввод имени и истории\n"
        "9️⃣ Генерация PDF\n\n"
        "Нажми кнопку «🎲 Создать персонажа» и следуй инструкциям!",
        reply_markup=main_menu(),
        parse_mode=None
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🎮 Главное меню", reply_markup=main_menu())


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "❓ **Помощь по использованию бота**\n\n"
        "**Порядок создания персонажа:**\n"
        "1️⃣ Выберите КЛАСС\n"
        "2️⃣ Выберите НАВЫКИ КЛАССА\n"
        "3️⃣ Выберите СНАРЯЖЕНИЕ КЛАССА\n"
        "4️⃣ Выберите ЗАКЛИНАНИЯ (если есть)\n"
        "5️⃣ Выберите БОЕВОЙ СТИЛЬ (для Воина, Паладина, Следопыта)\n"
        "6️⃣ Выберите ПРЕДЫСТОРИЮ\n"
        "7️⃣ Выберите РАСУ\n"
        "8️⃣ Введите ИМЯ\n"
        "9️⃣ Введите ИСТОРИЮ\n"
        "🔟 Загрузите ИЗОБРАЖЕНИЕ\n"
        "1️⃣1️⃣ Получите PDF лист персонажа\n\n"
        "**Команды:**\n"
        "/start - начать работу\n"
        "/menu - главное меню\n"
        "/help - эта справка",
        parse_mode=None
    )


# =========================================================
# КНОПКИ ГЛАВНОГО МЕНЮ
# =========================================================

@router.message(F.text == "🎲 Создать персонажа")
async def create_character_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CreateCharacter.class_select)
    await message.answer(
        "🏰 **СОЗДАНИЕ ПЕРСОНАЖА**\n\nШаг 1/12: Выберите КЛАСС\n\n"
        "Каждый класс даёт уникальные способности, стиль игры и снаряжение.",
        parse_mode=None,
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("Выберите класс:", reply_markup=create_class_keyboard())


@router.message(F.text == "📋 Мои персонажи")
async def list_characters(message: Message):
    characters = _char_repo.get_by_user_id(message.from_user.id)
    if not characters:
        await message.answer("📭 У вас пока нет персонажей.")
        return
    await message.answer("📋 Ваши персонажи:", reply_markup=create_character_list_keyboard(message.from_user.id))


@router.message(F.text == "🗑 Удалить персонажа")
async def delete_character_menu(message: Message):
    characters = _char_repo.get_by_user_id(message.from_user.id)
    if not characters:
        await message.answer("📭 У вас нет персонажей для удаления.")
        return
    await message.answer(
        "🗑 Выберите персонажа для удаления:\n\n⚠️ Удаление необратимо.",
        reply_markup=create_delete_keyboard(characters)
    )


@router.message(F.text == "ℹ️ О боте")
async def info_button(message: Message):
    await message.answer(
        "ℹ️ **D&D Character Creator 5.5e (2024)**\n\n"
        "📊 **Данные:**\n"
        "• 16 рас с подрасами\n"
        "• 13 классов\n"
        "• 16 предысторий\n"
        "• 50+ заклинаний\n"
        "• 30+ видов оружия\n"
        "• Автоматическое распределение характеристик\n"
        "• Генерация PDF листа персонажа\n\n"
        "🎲 **Особенности:**\n"
        "• Умное распределение бонусов предыстории\n"
        "• Группировка заклинаний по категориям\n"
        "• Оружейные приёмы (Weapon Mastery)\n"
        "• Боевые стили и возвания\n\n"
        "🐉 **Приятной игры!**",
        parse_mode=None
    )


@router.message(F.text == "❓ Помощь")
async def help_button(message: Message):
    await cmd_help(message)


@router.message(F.text == "❌ Отмена")
async def cancel_creation(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Создание персонажа отменено.\n\nЧтобы начать заново, нажмите «🎲 Создать персонажа»",
        reply_markup=main_menu()
    )


# =========================================================
# ШАГ 1: ВЫБОР КЛАССА
# =========================================================

@router.callback_query(lambda c: c.data.startswith("class_") and not c.data.startswith("class_skill"))
async def select_class(callback: CallbackQuery, state: FSMContext):
    class_name = callback.data.replace("class_", "")
    class_name = callback.data.replace("class_", "")
    await state.update_data(class_name=class_name)
    logger.info(f"[FLOW] Выбран класс: {class_name}")

    class_desc = CharacterStatsService.get_class_description(class_name)
    class_info = CharacterStatsService.get_class_info(class_name)
    subclasses = _class_repo.get_subclasses(class_name, level=1)

    text = (f"⚔️ **{class_name}**\n\n📖 {class_desc}\n\n"
            f"📊 **Характеристики класса:**\n"
            f"• ❤️ Хитовый кубик: d{class_info.get('hit_die', 6)}\n"
            f"• 🎯 Основные характеристики: {', '.join(class_info.get('primary_stats', []))}\n"
            f"• 🛡️ Спасброски: {', '.join(class_info.get('saving_throws', []))}\n"
            f"• 🔮 Заклинания: {'Да' if class_info.get('spellcasting', False) else 'Нет'}\n")

    if subclasses and class_name in ["Жрец", "Друид", "Колдун"]:
        text += f"\n📖 **На 1 уровне вы можете выбрать подкласс:**\n"
        for sub in subclasses:
            text += f"   • {sub['name']} — {sub['description'][:60]}...\n"
        reply_markup = create_subclass_keyboard(class_name)
        await state.set_state(CreateCharacter.subclass_select)
        img_path = CharacterStatsService.get_class_image_path(class_name)
        try:
            await callback.message.delete()
            if img_path and os.path.exists(img_path):
                photo = FSInputFile(img_path)
                await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None, reply_markup=reply_markup)
            else:
                await callback.message.answer(text, parse_mode=None, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            await callback.message.answer(text, parse_mode=None, reply_markup=reply_markup)
        await callback.answer()
        return

    # НЕТ ПОДКЛАССА НА 1 УРОВНЕ — ПЕРЕХОДИМ К ВЫБОРУ НАВЫКОВ
    await state.update_data(class_name=class_name)

    class_data = _class_repo.get_by_name(class_name)
    available_skills = class_data.get('skills', []) if class_data else []
    if not available_skills:
    available_skills = [
        "Акробатика", "Атлетика", "Восприятие", "Выживание", "Выступление",
        "Запугивание", "История", "Ловкость рук", "Медицина", "Обман",
        "Обращение с животными", "Природа", "Проницательность", "Расследование",
        "Религия", "Скрытность", "Тайная магия", "Убеждение"
    ]
    skill_choices = class_data.get('skill_choices', 2) if class_data else 2

    await state.set_state(CreateCharacter.skills_select)
    selected_skills = []
    await state.update_data(selected_class_skills=selected_skills)
    keyboard = create_skills_keyboard(available_skills, skill_choices, selected_skills)
    text_skills = (f"📚 **Шаг 2/12: Выбор НАВЫКОВ класса {class_name}**\n\n"
                   f"Выберите {skill_choices} навык(а) из списка ниже. "
                   f"Навыки, отмеченные ✅, будут добавлены к вашему персонажу.\n\n"
                   f"После выбора нажмите «✅ Готово».")
    img_path = CharacterStatsService.get_class_image_path(class_name)
    try:
        await callback.message.delete()
        if img_path and os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await callback.message.answer_photo(photo=photo, caption=text_skills, parse_mode=None, reply_markup=keyboard)
        else:
            await callback.message.answer(text_skills, parse_mode=None, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.message.answer(text_skills, parse_mode=None, reply_markup=keyboard)
    await callback.answer()


# =========================================================
# НОВЫЙ ШАГ: ВЫБОР НАВЫКОВ КЛАССА
# =========================================================

@router.callback_query(lambda c: c.data.startswith("class_skills_") or c.data.startswith("class_skill_toggle_"))
async def handle_skills_selection(callback: CallbackQuery, state: FSMContext):
    """Обработчик callback-запросов для выбора навыков класса"""
    logger.info(f"🟢 Обработчик навыков вызван, data={callback.data}")
    data = callback.data
    user_data = await state.get_data()
    class_name = user_data.get("class_name")
    
    class_info = _class_repo.get_by_name(class_name)
    if not class_info:
        await callback.answer("❌ Ошибка: класс не найден")
        return
    
    available_skills = class_info.get('skills', [])
    skill_choices = class_info.get('skill_choices', 2)
    selected_skills = user_data.get("selected_class_skills", [])
    
    if data == "class_skills_ready":
        if len(selected_skills) == skill_choices:
            await state.update_data(selected_class_skills=selected_skills)
            await state.set_state(CreateCharacter.class_equipment_select)
            await callback.message.delete()
            await show_class_equipment(callback.message, state, class_name)
            await callback.answer("✅ Навыки класса выбраны!")
        else:
            await callback.answer(f"❌ Нужно выбрать ровно {skill_choices} навыков. Выбрано: {len(selected_skills)}", show_alert=True)
        return
    
    if data == "class_skills_ready_disabled":
        await callback.answer(f"❌ Сначала выберите {skill_choices} навыков. Выбрано: {len(selected_skills)}", show_alert=True)
        return
    
    if data == "class_skills_info":
        await callback.answer(f"Выбрано {len(selected_skills)} из {skill_choices} навыков", show_alert=False)
        return
    
    if data.startswith("class_skill_toggle_"):
        skill_name = data.replace("class_skill_toggle_", "")
        if skill_name in selected_skills:
            selected_skills.remove(skill_name)
        else:
            if len(selected_skills) >= skill_choices:
                await callback.answer(f"❌ Нельзя выбрать больше {skill_choices} навыков", show_alert=True)
                return
            selected_skills.append(skill_name)
        await state.update_data(selected_class_skills=selected_skills)
        # Обновляем клавиатуру
        keyboard = create_skills_keyboard(available_skills, skill_choices, selected_skills)
        try:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Ошибка обновления клавиатуры: {e}")
        await callback.answer()
        return


async def show_class_equipment(message: Message, state: FSMContext, class_name: str):
    """Показывает выбор снаряжения класса"""
    equipment = CharacterStatsService.get_class_equipment(class_name)
    has_equipment_choice = len(equipment) > 1
    if has_equipment_choice:
        reply_markup = create_class_equipment_keyboard(class_name)
        text = f"⚔️ **Шаг 3/12: СНАРЯЖЕНИЕ класса {class_name}**\n\nВыберите один из вариантов снаряжения:"
        await message.answer(text, parse_mode=None, reply_markup=reply_markup)
    else:
        if equipment:
            eq = equipment[0]
            await state.update_data(
                selected_armor=eq.get('armor'),
                selected_weapon=eq.get('weapon'),
                selected_secondary_weapon=eq.get('secondary_weapon'),
                selected_other_items=eq.get('other_items'),
                selected_coins=eq.get('coins', 0)
            )
        await go_to_spells(message, state)


# =========================================================
# ШАГ 3: ВЫБОР СНАРЯЖЕНИЯ КЛАССА
# =========================================================

@router.callback_query(lambda c: c.data.startswith("equip_"))
async def select_class_equipment(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("equip_", "")
    data = await state.get_data()
    class_name = data.get("class_name")
    logger.info(f"[FLOW] Выбор снаряжения: class_name='{class_name}', choice='{choice}'")

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

    await callback.message.delete()
    await callback.message.answer(f"✅ Снаряжение выбрано (вариант {choice})")
    await go_to_spells(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_classes")
async def back_to_classes(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.class_select)
    await callback.message.delete()
    await callback.message.answer("Шаг 1/12: Выберите КЛАСС", parse_mode=None, reply_markup=create_class_keyboard())
    await callback.answer()


# =========================================================
# ПЕРЕХОДЫ МЕЖДУ ШАГАМИ
# =========================================================

async def go_to_spells(message: Message, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    is_spellcaster = ProgressionService.is_spellcaster(class_name)
    logger.info(f"[FLOW] go_to_spells: class={class_name}, is_spellcaster={is_spellcaster}")
    if is_spellcaster:
        await SpellSelectionService.start_cantrips_selection(message, state)
    else:
        await go_to_fighting_style(message, state)


async def go_to_fighting_style(message: Message, state: FSMContext):
    logger.info("=" * 50)
    logger.info("🔧 go_to_fighting_style ВЫЗВАНА!")
    logger.info("=" * 50)
    data = await state.get_data()
    class_name = data.get("class_name")
    logger.info(f"   class_name = {class_name}")
    if ProgressionService.should_select_fighting_style(class_name):
        styles = CharacterStatsService.get_fighting_styles_for_class(class_name)
        logger.info(f"   Найдено стилей: {len(styles) if styles else 0}")
        if not styles:
            logger.warning(f"⚠️ Нет боевых стилей для класса {class_name}")
            await message.answer(f"⚠️ Для класса {class_name} нет доступных боевых стилей.\n\nПереходим к следующему шагу...")
            await go_to_invocations(message, state)
            return
        await state.set_state(CreateCharacter.fighting_style_select)
        await message.answer(
            f"⚔️ **Шаг 5/12: Выбор БОЕВОГО СТИЛЯ**\n\n"
            f"Класс **{class_name}** может выбрать один боевой стиль.\n\n"
            f"Боевой стиль даёт постоянный бонус в бою.\n\n"
            f"Доступные стили ({len(styles)}):",
            parse_mode=None,
            reply_markup=create_fighting_style_keyboard(class_name)
        )
    else:
        logger.info(f"   Класс {class_name} не в списке, идём к invocations")
        await go_to_invocations(message, state)


async def go_to_invocations(message: Message, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    logger.info(f"🔧 go_to_invocations вызвана для класса: {class_name}")
    if ProgressionService.should_select_invocations(class_name):
        await state.set_state(CreateCharacter.invocations_select)
        invocations = CharacterStatsService.get_all_invocations(level=1)
        if invocations:
            selected_count = len(data.get("selected_invocations", []))
            await message.answer(
                f"🔮 **Шаг 6/12: Выбор ТАИНСТВЕННЫХ ВОЗВАНИЙ**\n\n"
                f"Колдун может выбрать таинственные возвания.\n"
                f"Вы можете выбрать до 2 возваний на 1 уровне.",
                parse_mode=None,
                reply_markup=create_invocations_keyboard(level=1, selected_count=selected_count)
            )
        else:
            await message.answer("📖 Нет доступных возваний для вашего уровня.")
            await go_to_background(message, state)
    else:
        logger.info(f"   Переход к выбору предыстории для {class_name}")
        await go_to_background(message, state)


async def go_to_background(message: Message, state: FSMContext):
    logger.info("🔧 go_to_background вызвана")
    await state.set_state(CreateCharacter.background_select)
    await message.answer(
        f"📜 **Шаг 7/12: Выбор ПРЕДЫСТОРИИ**\n\n"
        f"Предыстория определяет ваше прошлое и даёт бонусы к характеристикам.\n\n"
        f"Выберите предысторию:",
        parse_mode=None,
        reply_markup=create_background_keyboard()
    )


# =========================================================
# БОЕВОЙ СТИЛЬ И ВОЗВАНИЯ
# =========================================================

@router.callback_query(lambda c: c.data.startswith("style_") and c.data != "style_skip")
async def select_fighting_style(callback: CallbackQuery, state: FSMContext):
    style_id = int(callback.data.replace("style_", ""))
    style = _fighting_repo.get_by_id(style_id)
    style_name = style.get('name') if style else None
    if style_name:
        await state.update_data(selected_fighting_style=style_name)
        await callback.answer(f"✅ Выбран стиль: {style_name}")
        logger.info(f"[FLOW] Выбран боевой стиль: {style_name}")
    await go_to_invocations(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "style_skip")
async def skip_fighting_style(callback: CallbackQuery, state: FSMContext):
    await callback.answer("⏩ Боевой стиль пропущен")
    await go_to_invocations(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("inv_") and c.data not in ("inv_skip", "inv_continue"))
async def select_invocation(callback: CallbackQuery, state: FSMContext):
    inv_id = int(callback.data.replace("inv_", ""))
    invocation = _inv_repo.get_by_id(inv_id)
    inv_name = invocation.get('name') if invocation else None
    if not inv_name:
        await callback.answer("❌ Возвание не найдено")
        return
    data = await state.get_data()
    selected = data.get("selected_invocations", [])
    old_count = len(selected)
    if inv_name in selected:
        selected.remove(inv_name)
        await callback.answer(f"❌ Возвание '{inv_name}' удалено")
    else:
        if len(selected) >= 2:
            await callback.answer("⚠️ Можно выбрать не более 2 возваний!", show_alert=True)
            return
        selected.append(inv_name)
        await callback.answer(f"✅ Возвание '{inv_name}' добавлено")
    await state.update_data(selected_invocations=selected)
    new_count = len(selected)
    if (old_count == 0 and new_count > 0) or (old_count > 0 and new_count == 0):
        await callback.message.edit_reply_markup(reply_markup=create_invocations_keyboard(level=1, selected_count=new_count))


@router.callback_query(lambda c: c.data == "inv_skip")
async def skip_invocations(callback: CallbackQuery, state: FSMContext):
    await go_to_background(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "inv_continue")
async def continue_invocations(callback: CallbackQuery, state: FSMContext):
    await go_to_background(callback.message, state)
    await callback.answer()


# =========================================================
# ПРЕДЫСТОРИЯ
# =========================================================

@router.callback_query(lambda c: c.data.startswith("bg_") and not c.data.startswith("bg_equip_"))
async def select_background(callback: CallbackQuery, state: FSMContext):
    background = callback.data.replace("bg_", "")
    await state.update_data(background=background)
    logger.info(f"[FLOW] Выбрана предыстория: {background}")

    bg_info = _bg_repo.get_by_name(background)
    if not bg_info:
        await callback.message.answer(f"❌ Ошибка: предыстория '{background}' не найдена.", reply_markup=main_menu())
        await state.clear()
        return

    await state.update_data(
        selected_skills_bg=bg_info.get('skills', []),
        background_trait=bg_info.get('trait', 'Нет'),
        background_origin_feat=bg_info.get('origin_feat', '')
    )
    await state.set_state(CreateCharacter.background_equipment_select)

    equip_a = bg_info.get('equipment_a', 'Нет описания')[:120]
    equip_b = bg_info.get('equipment_b', 'Нет описания')[:120]
    origin_feat = bg_info.get('origin_feat', '')
    origin_feat_text = f"✨ **Черта происхождения:** {origin_feat}\n\n" if origin_feat else ""

    await callback.message.delete()
    await callback.message.answer(
        f"📜 **Предыстория: {background}**\n\n"
        f"📖 {bg_info.get('description', 'Нет описания')[:300]}...\n\n"
        f"{origin_feat_text}"
        f"✨ **Бонусы к характеристикам:**\n   • +2 к {bg_info['characteristics'][0]}\n   • +1 к {bg_info['characteristics'][1]}\n\n"
        f"🔧 **Черта:** {bg_info.get('trait', 'Нет')}\n"
        f"📚 **Навыки:** {', '.join(bg_info.get('skills', []))}\n"
        f"🛠️ **Инструменты:** {bg_info.get('tools', 'Нет')}\n\n"
        f"**Шаг 8/12: Выберите СНАРЯЖЕНИЕ от предыстории**\n\n"
        f"📦 Вариант А: {equip_a}...\n🎒 Вариант Б: {equip_b}...",
        parse_mode=None,
        reply_markup=create_background_equipment_keyboard(background)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("bg_equip_"))
async def select_background_equipment(callback: CallbackQuery, state: FSMContext):
    equipment_choice = callback.data.replace("bg_equip_", "")
    data = await state.get_data()
    background = data.get("background")
    if not background or background in ["equip_A", "equip_B", "equip_", "A", "B", None]:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: background = '{background}'")
        await callback.message.answer(
            "❌ Ошибка: данные о предыстории потеряны.\nПожалуйста, начните создание заново: /start",
            reply_markup=main_menu())
        await state.clear()
        return
    await state.update_data(background_equipment_choice=equipment_choice)
    await calculate_and_show_stats(callback.message, state)
    await callback.message.delete()
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_background")
async def back_to_background_list(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.background_select)
    await callback.message.delete()
    await callback.message.answer("Шаг 7/12: Выберите ПРЕДЫСТОРИЮ", parse_mode=None,
                                  reply_markup=create_background_keyboard())
    await callback.answer()


# =========================================================
# РАСЧЁТ ХАРАКТЕРИСТИК
# =========================================================

async def calculate_and_show_stats(message: Message, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    background = data.get("background")
    equipment_choice = data.get("equipment_choice", "A")
    selected_armor = data.get("selected_armor")

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

    await message.answer(
        f"📊 **Шаг 9/12: ХАРАКТЕРИСТИКИ РАССЧИТАНЫ!**\n\n"
        f"⚔️ **Класс:** {class_name}\n"
        f"📜 **Предыстория:** {background}\n\n"
        f"✨ **Бонусы предыстории:** +2 к {stats_result['bg_chars'][0]}, +1 к {stats_result['bg_chars'][1]}\n\n"
        f"📊 **Итоговые характеристики:**\n"
        f"{stats_result['stats_text']}\n\n"
        f"❤️ **Хиты (HP):** {stats_result['hp']}\n"
        f"🛡️ **Класс брони (AC):** {stats_result['ac']}\n\n"
        f"Теперь выберите РАСУ:",
        parse_mode=None,
        reply_markup=create_race_keyboard()
    )
    await state.set_state(CreateCharacter.race_select)


# =========================================================
# РАСА
# =========================================================

@router.callback_query(lambda c: c.data.startswith("race_"))
async def select_race(callback: CallbackQuery, state: FSMContext):
    race = callback.data.replace("race_", "")
    await state.update_data(race=race)
    logger.info(f"[FLOW] Выбрана раса: {race}")

    race_desc = CharacterStatsService.get_race_description(race)
    race_speed = CharacterStatsService.get_race_speed(race)
    race_size = CharacterStatsService.get_race_size(race)
    has_sub = CharacterStatsService.has_subraces(race)
    subraces_list = CharacterStatsService.get_subraces(race) if has_sub else []

    text = f"🧝 **Раса: {race}**\n\n📖 {race_desc}\n\n🏃 **Скорость:** {race_speed} футов\n📏 **Размер:** {race_size}\n"

    if has_sub and subraces_list:
        text += f"\n🌟 **Доступные подрасы:**\n"
        for sub in subraces_list:
            sub_trait = CharacterStatsService.get_subrace_trait(race, sub)
            text += f"   • **{sub}** — {sub_trait[:50] + '...' if len(sub_trait) > 50 else sub_trait}\n"
        text += f"\n**Шаг 10/12: Выберите ПОДРАСУ**"
        reply_markup = create_subrace_keyboard(race)
        await state.set_state(CreateCharacter.subrace_select)
    else:
        await go_to_name(callback.message, state)
        await callback.answer()
        return

    img_path = CharacterStatsService.get_race_image_path(race)
    try:
        await callback.message.delete()
        if img_path and os.path.exists(img_path):
            photo = FSInputFile(img_path)
            await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None, reply_markup=reply_markup)
        else:
            await callback.message.answer(text, parse_mode=None, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await callback.message.answer(text, parse_mode=None, reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("subrace_") and c.data != "subrace_skip")
async def select_subrace(callback: CallbackQuery, state: FSMContext):
    subrace = callback.data.replace("subrace_", "")
    await state.update_data(subrace=subrace)
    data = await state.get_data()
    race = data.get("race")
    sub_desc = CharacterStatsService.get_subrace_description(race, subrace)
    sub_trait = CharacterStatsService.get_subrace_trait(race, subrace)
    text = f"🧝 **{race} — {subrace}**\n\n📖 {sub_desc}\n\n✨ **Особенность:** {sub_trait}\n\nПереходим к вводу имени..."
    await callback.message.delete()
    await callback.message.answer(text, parse_mode=None)
    await go_to_name(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "subrace_skip")
async def skip_subrace(callback: CallbackQuery, state: FSMContext):
    await state.update_data(subrace=None)
    await callback.message.delete()
    await go_to_name(callback.message, state)
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_races")
async def back_to_races(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.race_select)
    await callback.message.delete()
    await callback.message.answer("Шаг 9/12: Выберите РАСУ", parse_mode=None, reply_markup=create_race_keyboard())
    await callback.answer()


# =========================================================
# ИМЯ И ИСТОРИЯ
# =========================================================

async def go_to_name(message: Message, state: FSMContext):
    logger.info("🔧 go_to_name вызвана")
    await state.set_state(CreateCharacter.name_input)
    await message.answer(
        "📛 **Шаг 11/12: Введите ИМЯ персонажа**\n\n"
        "Имя может быть любым (от 2 до 50 символов).\n\n"
        "Введите имя:",
        parse_mode=None,
        reply_markup=cancel_kb()
    )


async def go_to_backstory(message: Message, state: FSMContext):
    logger.info("🔧 go_to_backstory вызвана")
    await state.set_state(CreateCharacter.backstory_input)
    await message.answer(
        "📖 **Шаг 12/12: История персонажа**\n\n"
        "Расскажите историю вашего персонажа:\n"
        "- Откуда он родом?\n"
        "- Что привело его к приключениям?\n"
        "- Какие у него цели?\n\n"
        "Введите историю (максимум 2000 символов):",
        parse_mode=None,
        reply_markup=cancel_kb()
    )


@router.message(CreateCharacter.name_input)
async def set_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_creation(message, state)
        return
    valid, msg = engine_validate_name(message.text)
    if not valid:
        await message.answer(f"{msg}\nПожалуйста, введите другое имя:", reply_markup=cancel_kb())
        return
    await state.update_data(name=message.text.strip())
    logger.info(f"✅ Имя сохранено: {message.text.strip()}")
    await message.answer(f"✅ Имя: {message.text.strip()}", reply_markup=ReplyKeyboardRemove())
    await go_to_backstory(message, state)


@router.message(CreateCharacter.backstory_input)
async def set_backstory(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await cancel_creation(message, state)
        return
    backstory = message.text.strip()
    if len(backstory) > 2000:
        await message.answer("❌ История слишком длинная (максимум 2000 символов).", reply_markup=cancel_kb())
        return
    await state.update_data(backstory=backstory)
    await state.set_state(CreateCharacter.image_input)
    await message.answer(
        f"📖 История сохранена!\n\n🖼️ **Финальный шаг: Изображение персонажа**\n\n"
        f"Загрузите картинку или нажмите «⏩ Пропустить».",
        parse_mode=None,
        reply_markup=skip_kb()
    )


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
    temp_pdf_file = None
    try:
        await message.answer("⏳ Создаю персонажа и генерирую PDF...", reply_markup=ReplyKeyboardRemove())

        data = await state.get_data()
        char_data = CharacterFinalizationService.prepare_character_data(data, message.from_user.id)
        char_data['image_file_id'] = image_file_id

        name = char_data['name']
        if not name:
            await message.answer("❌ Ошибка: имя не сохранено.", reply_markup=main_menu())
            await state.clear()
            return

        # Объединяем навыки класса и предыстории, убирая дубликаты
        class_skills = data.get("selected_class_skills", [])
        bg_skills = data.get("selected_skills_bg", [])
        all_skills = list(set(class_skills + bg_skills))
        char_data['selected_skills'] = all_skills

        # Добавляем черту происхождения
        char_data['origin_feat'] = data.get("background_origin_feat", "")

        # Сохраняем персонажа
        char_id = CharacterFinalizationService.save_character(char_data)

        bg_info = _bg_repo.get_by_name(char_data['background']) if char_data['background'] else None
        pdf_data = {
            "name": name,
            "class_name": char_data['class_name'],
            "race": f"{char_data['race']} ({char_data['subrace']})" if char_data['subrace'] else char_data['race'],
            "level": 1,
            "stats": char_data['stats'],
            "hp": char_data['hp'],
            "ac": char_data['ac'],
            "speed": 30,
            "skills": all_skills,
            "equipment": [item for item in [char_data['selected_weapon'], char_data['selected_armor']] if item],
            "spells": char_data['selected_spells'],
            "proficiency_bonus": CharacterStatsService.calculate_proficiency_bonus(1),
            "background": char_data['background'],
            "background_trait": bg_info.get('trait', '') if bg_info else '',
            "background_description": bg_info.get('description', '') if bg_info else '',
            "origin_feat": char_data.get('origin_feat', ''),
            "race_traits": [],
            "class_features": [],
            "backstory": char_data['backstory'],
            "alignment": "Нейтральное",
            "player_name": message.from_user.full_name,
            "experience": 0,
            "saving_throws": [],
            "notes": "",
            "coins": data.get("selected_coins", 0)
        }

        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{safe_name}.pdf")
        temp_pdf_file = tmp.name
        tmp.close()

        pdf_file = generate_pdf(pdf_data, temp_pdf_file)

        caption = (f"✅ **Персонаж создан!**\n\n📛 **{name}**\n⚔️ **Класс:** {char_data['class_name']}\n"
                   f"📜 **Предыстория:** {char_data['background']}\n"
                   f"🧝 **Раса:** {char_data['race']}{f' ({char_data['subrace']})' if char_data['subrace'] else ''}\n"
                   f"❤️ **HP:** {char_data['hp']} | 🛡️ **AC:** {char_data['ac']}\n\n"
                   f"🎯 **Характеристики:**\n{CharacterStatsService.format_stats_display(char_data['stats'])}")

        if image_file_id:
            await message.answer_photo(photo=image_file_id, caption=caption, parse_mode=None)
        else:
            await message.answer(caption, parse_mode=None)

        if pdf_file and os.path.exists(pdf_file):
            await message.answer_document(
                FSInputFile(pdf_file, filename=f"{safe_name}_character_sheet.pdf"),
                caption="📄 Лист персонажа в формате PDF"
            )
        else:
            logger.error(f"PDF не создан: {pdf_file}")
            await message.answer("⚠️ Не удалось создать PDF файл, но персонаж сохранён!")

        await message.answer("🎮 Главное меню", reply_markup=main_menu())
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка при создании персонажа: {e}", exc_info=True)
        await message.answer(f"❌ Произошла ошибка: {str(e)[:200]}\n\nПерсонаж может быть сохранён, но PDF не создан.",
                             reply_markup=main_menu())
        await state.clear()
    finally:
        if temp_pdf_file and os.path.exists(temp_pdf_file):
            try:
                os.remove(temp_pdf_file)
            except:
                pass


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
    info = (f"📛 **{character['name']}**\n\n🧝 **Раса:** {character.get('race_name', 'Неизвестно')}\n"
            f"⚔️ **Класс:** {character.get('class_name', 'Неизвестно')}\n"
            f"📜 **Предыстория:** {character.get('background_name', 'Нет')}\n"
            f"📊 **Уровень:** {character['level']}\n"
            f"❤️ **HP:** {character['hp']} | 🛡️ **AC:** {character['ac']}\n\n"
            f"**Характеристики:\n"
            f"STR {character['str']} | DEX {character['dex']} | CON {character['con']} | "
            f"INT {character['int']} | WIS {character['wis']} | CHA {character['cha']}")
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
        await callback.message.edit_text(f"✅ Персонаж {character['name']} удалён!", parse_mode=None)
    else:
        await callback.message.edit_text("❌ Не удалось удалить персонажа.")
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.edit_text("❌ Удаление отменено")
    await callback.answer()


@router.callback_query(lambda c: c.data == "cancel_creation")
async def cancel_creation_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Создание персонажа отменено")
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
            "⏳ Вы в процессе создания персонажа.\n\nСледуйте инструкциям или нажмите «❌ Отмена».",
            reply_markup=cancel_kb()
        )
    else:
        await message.answer(
            "❓ Я не понимаю эту команду.\n\nИспользуйте кнопки меню или /help.",
            reply_markup=main_menu()
        )
