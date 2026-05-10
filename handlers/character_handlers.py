# handlers/character_handlers.py
"""
Обработчики для создания персонажа с удалением предыдущих служебных сообщений.
Каждый шаг удаляет свой запрос, оставляя только картинки и финальный лист.
"""

import logging
import os
from typing import Optional, List

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, FSInputFile, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from states.character_states import CreateCharacter
from keyboards.character_keyboards import (
    create_class_keyboard,
    create_race_keyboard,
    create_background_keyboard,
    create_character_list_with_webapp_keyboard,  # было create_character_list_keyboard
    create_delete_keyboard,
    create_skills_keyboard,
    cancel_kb,
    skip_kb,
    main_menu,
    create_alignment_keyboard,
    create_subrace_keyboard,
    create_fighting_style_keyboard,
    create_druid_order_keyboard,
    create_cleric_order_keyboard,
    create_warlock_pact_keyboard,
    create_rogue_expertise_keyboard,
    create_rogue_language_keyboard,
    create_background_equipment_keyboard,
    create_draconic_ancestry_keyboard,
    create_warlock_invocation_keyboard,
    create_tome_picker_keyboard,
    create_personality_intro_keyboard,
    create_favored_enemy_keyboard,
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
from db import get_connection

from engine.validators import validate_name as engine_validate_name

from services.auto_choices import (
    get_optimal_skills_for_class,
    recommend_fighting_style,
    generate_personality_traits,
)

from strings import *

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

def format_mod(mod_value: int) -> str:
    if mod_value > 0:
        return f"+{mod_value}"
    elif mod_value < 0:
        return str(mod_value)
    else:
        return "0"

# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ДОПОЛНИТЕЛЬНЫХ ШАГОВ
# =========================================================

async def proceed_to_skills(callback: CallbackQuery, state: FSMContext):
    class_name = (await state.get_data()).get("class_name")
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
    # Smart default (D&D 5.5e 2024 + популярные гайды): pre-select оптимальные
    # навыки для класса. Игрок может снять/сменить через те же кнопки toggle.
    selected_skills = get_optimal_skills_for_class(
        class_name, available_skills, skill_choices
    )
    await state.update_data(selected_class_skills=selected_skills)
    keyboard = create_skills_keyboard(available_skills, skill_choices, selected_skills)
    text_skills = SKILLS_REQUEST_TEMPLATE.format(class_name=class_name, skill_choices=skill_choices)
    if selected_skills:
        text_skills += (
            "\n\n🎯 Бот подобрал оптимальный набор: "
            + ", ".join(selected_skills)
            + ".\nМожешь принять кнопкой «Готово» или поменять выбор."
        )
    await send_new_from_callback(callback, state, text_skills, keyboard)

async def show_druid_order_selection(callback: CallbackQuery, state: FSMContext):
    text = "🌿 Выбери свой природный орден:\n\n• Ведун – +1 заговор, +1 к Интеллекту\n• Страж – владение оружием и средними доспехами"
    await send_new_from_callback(callback, state, text, reply_markup=create_druid_order_keyboard())

async def show_cleric_order_selection(callback: CallbackQuery, state: FSMContext):
    text = "⚔️ Выбери свой орден:\n\n• Защитник – владение оружием и тяжёлыми доспехами\n• Чудотворец – +1 заговор, +1 к Интеллекту"
    await send_new_from_callback(callback, state, text, reply_markup=create_cleric_order_keyboard())

async def show_warlock_pact_selection(callback: CallbackQuery, state: FSMContext):
    text = "🔮 Выбери свой договор:\n\n• Договор гримуара – книга теней\n• Договор клинка – призыв оружия\n• Договор цепи – улучшенный фамильяр\n• Доспех теней – бесплатный «Доспех мага»\n• Мистический разум – преимущество на концентрацию"
    await send_new_from_callback(callback, state, text, reply_markup=create_warlock_pact_keyboard())

async def handle_class_expertise(callback: CallbackQuery, state: FSMContext):
    """
    Шаг выбора 2 навыков для экспертности.
    D&D 5.5e (2024): Плут (Expertise на L1) и Бард (Expertise на L1) получают
    экспертизу в 2 навыках. Используем единый шаг; после выбора Плут идёт на
    шаг языка, Бард — сразу к equipment.
    """
    data = await state.get_data()
    class_name = data.get("class_name")
    # Получаем список навыков, выбранных классом (хранятся в selected_class_skills)
    class_skills = data.get("selected_class_skills", [])
    if not class_skills:
        class_info = _class_repo.get_by_name(class_name) if class_name else None
        class_skills = class_info.get('skills', []) if class_info else []
    await state.update_data(available_skills_for_expertise=class_skills, rogue_expertise_selected=[])
    await state.set_state(CreateCharacter.rogue_expertise_select)
    text = (
        "🎭 Выбери два навыка для экспертности (удвоенный бонус мастерства):"
    )
    await send_new_from_callback(callback, state, text, reply_markup=create_rogue_expertise_keyboard(class_skills, []))


# Алиас для обратной совместимости с прежним именем.
handle_rogue_extras = handle_class_expertise


async def proceed_to_favored_enemy(callback: CallbackQuery, state: FSMContext):
    """Следопыт L1 (PHB 2024): шаг выбора Избранного врага."""
    await state.set_state(CreateCharacter.ranger_favored_enemy_select)
    await send_new_from_callback(
        callback, state,
        "🎯 Следопыт L1 (2024): выбери своего Избранного врага:",
        reply_markup=create_favored_enemy_keyboard(),
    )


@router.callback_query(CreateCharacter.ranger_favored_enemy_select, lambda c: c.data and c.data.startswith("favored_enemy_"))
async def select_favored_enemy(callback: CallbackQuery, state: FSMContext):
    enemy = callback.data.replace("favored_enemy_", "")
    await state.update_data(favored_enemy=enemy)
    await callback.answer(f"✅ Избранный враг: {enemy}")
    logger.info(f"[FLOW] Следопыт Избранный враг: {enemy}")
    # Дальше — обычный путь: equipment.
    await state.set_state(CreateCharacter.class_equipment_select)
    await show_class_equipment(callback, state)

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
    temp_msg = await message.answer("⌛", reply_markup=ReplyKeyboardRemove())
    await temp_msg.delete()
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
    if img_path and os.path.exists(img_path):
        photo = FSInputFile(img_path)
        await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None)
    else:
        await callback.message.answer(text, parse_mode=None)

    if class_name == "Друид":
        await state.set_state(CreateCharacter.druid_order_select)
        await show_druid_order_selection(callback, state)
    elif class_name == "Жрец":
        await state.set_state(CreateCharacter.cleric_order_select)
        await show_cleric_order_selection(callback, state)
    elif class_name == "Колдун":
        await state.set_state(CreateCharacter.warlock_pact_select)
        await show_warlock_pact_selection(callback, state)
    else:
        await proceed_to_skills(callback, state)
    await callback.answer()

# =========================================================
# ОБРАБОТЧИКИ ДЛЯ ДОПОЛНИТЕЛЬНЫХ ШАГОВ
# =========================================================
@router.callback_query(CreateCharacter.druid_order_select, lambda c: c.data.startswith("druid_order_"))
async def select_druid_order(callback: CallbackQuery, state: FSMContext):
    order = callback.data.replace("druid_order_", "")
    await state.update_data(druid_order=order)
    logger.info(f"[FLOW] Друид орден: {order}")
    await callback.answer(f"✅ Выбран орден: {'Ведун' if order == 'guide' else 'Страж'}")
    if order == "guide":
        await state.update_data(extra_int_bonus=1)
    elif order == "guardian":
        await state.update_data(has_weapon_proficiency=True, has_medium_armor=True)
    await proceed_to_skills(callback, state)

@router.callback_query(CreateCharacter.cleric_order_select, lambda c: c.data.startswith("cleric_order_"))
async def select_cleric_order(callback: CallbackQuery, state: FSMContext):
    order = callback.data.replace("cleric_order_", "")
    await state.update_data(cleric_order=order)
    logger.info(f"[FLOW] Жрец орден: {order}")
    await callback.answer(f"✅ Выбран орден: {'Защитник' if order == 'protector' else 'Чудотворец'}")
    if order == "miracle":
        await state.update_data(extra_int_bonus=1)
    elif order == "protector":
        await state.update_data(has_weapon_proficiency=True, has_heavy_armor=True)
    await proceed_to_skills(callback, state)

@router.callback_query(CreateCharacter.warlock_pact_select, lambda c: c.data.startswith("warlock_pact_"))
async def select_warlock_pact(callback: CallbackQuery, state: FSMContext):
    pact = callback.data.replace("warlock_pact_", "")
    await state.update_data(warlock_pact=pact)
    logger.info(f"[FLOW] Колдун договор: {pact}")
    pact_names = {"tome": "Договор гримуара", "blade": "Договор клинка", "chain": "Договор цепи", "shadow_armor": "Доспех теней", "arcane_mind": "Мистический разум"}
    await callback.answer(f"✅ Выбран договор: {pact_names.get(pact, pact)}")
    # 2024 PHB: после выбора пакта показываем шаг 1 воззвания (Eldritch Invocation)
    # на 1 уровне Колдуна. Pact-of-Tome заговоры и ритуалы — отдельный шаг,
    # будет встроен из обработчика воззвания.
    await proceed_to_warlock_invocation(callback, state)


async def proceed_to_warlock_invocation(callback: CallbackQuery, state: FSMContext):
    """
    Колдун L1 (PHB 2024): выбор 1 воззвания.
    Фильтруем воззвания по выбранному пакту: воззвания с requires_pact_boon=True
    показываются ТОЛЬКО если pact_boon_type совпадает с выбранным пактом.
    Универсальные воззвания (без требования) видны всегда.
    """
    data = await state.get_data()
    pact = (data.get("warlock_pact") or "").lower()
    # Маппинг внутреннего ключа пакта → значение pact_boon_type в БД.
    # Гомебрю-пакты (shadow_armor, arcane_mind) не дают доступа к
    # «pact-bound» воззваниям, поэтому маппим их в None.
    pact_to_db = {
        "blade": "Blade",
        "chain": "Chain",
        "tome":  "Tome",
        "shadow_armor": None,
        "arcane_mind":  None,
    }
    pact_db_value = pact_to_db.get(pact)

    all_invocations = CharacterStatsService.get_all_invocations(level=1)
    if not all_invocations:
        logger.warning("Список воззваний пуст в БД — пропускаем шаг.")
        await state.update_data(warlock_invocation=None)
        await proceed_after_warlock_invocation(callback, state)
        return

    # Фильтрация: универсальные + те, что требуют именно текущий пакт.
    invocations = [
        inv for inv in all_invocations
        if not inv.get("requires_pact_boon")
        or (pact_db_value and inv.get("pact_boon_type") == pact_db_value)
    ]
    if not invocations:
        logger.warning(f"После фильтра по пакту {pact!r} воззваний не осталось.")
        await state.update_data(warlock_invocation=None)
        await proceed_after_warlock_invocation(callback, state)
        return

    await state.set_state(CreateCharacter.warlock_invocation_select)
    text = "✨ Колдун L1 (2024): выбери одно воззвание:"
    await send_new_from_callback(
        callback, state, text,
        reply_markup=create_warlock_invocation_keyboard(invocations),
    )


@router.callback_query(CreateCharacter.warlock_invocation_select, lambda c: c.data.startswith("warlock_inv_"))
async def select_warlock_invocation(callback: CallbackQuery, state: FSMContext):
    inv_id = int(callback.data.replace("warlock_inv_", "") or 0)
    # Получаем имя воззвания по ID — простой линейный поиск по списку.
    invocations = CharacterStatsService.get_all_invocations(level=1)
    inv_name = next((i.get('name') for i in invocations if i.get('id') == inv_id), None)
    await state.update_data(warlock_invocation=inv_name)
    await callback.answer(f"✅ Воззвание: {inv_name}" if inv_name else "✅ Воззвание выбрано")
    logger.info(f"[FLOW] Колдун воззвание: {inv_name}")
    await proceed_after_warlock_invocation(callback, state)


async def proceed_after_warlock_invocation(callback: CallbackQuery, state: FSMContext):
    """После воззвания: для пакта Гримуара — заговоры и ритуалы; иначе → к навыкам."""
    data = await state.get_data()
    pact = data.get("warlock_pact")
    if pact == "tome":
        await proceed_to_tome_cantrips(callback, state)
        return
    await proceed_to_skills(callback, state)


# ─── Гримуар: 3 заговора + 2 ритуала (D&D 5.5e 2024) ─────────────────

async def proceed_to_tome_cantrips(callback: CallbackQuery, state: FSMContext):
    """Pact of the Tome: выбор 3 заговоров ИЗ ЛЮБОГО списка классов (PHB 2024).
    Раньше тут был `get_cantrips_for_class("Колдун")` — что давало только
    Warlock-заговоры. Правильно — `get_all(is_cantrip=True)`: вся БД заговоров.
    """
    cantrips = _spell_repo.get_all(is_cantrip=True) or []
    if not cantrips:
        logger.warning("Список заговоров пуст — пропускаем шаг tome cantrips.")
        await state.update_data(pact_tome_cantrips=[])
        await proceed_to_tome_rituals(callback, state)
        return
    await state.update_data(pact_tome_cantrips_selected=[])
    await state.set_state(CreateCharacter.warlock_tome_cantrips_select)
    await send_new_from_callback(
        callback, state,
        "📖 Книга теней: выбери 3 заговора:",
        reply_markup=create_tome_picker_keyboard(
            items=cantrips, selected=[],
            callback_prefix="tome_cantrip_",
            ready_callback="tome_cantrip_ready",
            limit=3,
        ),
    )


@router.callback_query(CreateCharacter.warlock_tome_cantrips_select, lambda c: c.data and (c.data.startswith("tome_cantrip_") or c.data == "tome_pick_info"))
async def select_tome_cantrip(callback: CallbackQuery, state: FSMContext):
    if callback.data == "tome_pick_info":
        await callback.answer()
        return
    if callback.data == "tome_cantrip_ready":
        data = await state.get_data()
        selected = data.get("pact_tome_cantrips_selected", [])
        if len(selected) != 3:
            await callback.answer(f"❌ Нужно выбрать ровно 3 заговора (выбрано {len(selected)})", show_alert=True)
            return
        await state.update_data(pact_tome_cantrips=selected)
        await callback.answer("✅ Заговоры Книги теней выбраны")
        await proceed_to_tome_rituals(callback, state)
        return
    # callback_data теперь содержит spell_id (а не имя — длинные русские
    # названия превышали 64-байтный лимит Telegram). Резолвим ID → имя.
    try:
        sp_id = int(callback.data.replace("tome_cantrip_", ""))
    except ValueError:
        await callback.answer("❌ Некорректный ID заговора", show_alert=True)
        return
    sp_data = _spell_repo.get_by_id(sp_id)
    if not sp_data:
        await callback.answer("❌ Заговор не найден", show_alert=True)
        return
    name = sp_data.get("name")
    data = await state.get_data()
    selected = list(data.get("pact_tome_cantrips_selected", []))
    if name in selected:
        selected.remove(name)
    elif len(selected) >= 3:
        await callback.answer("❌ Уже выбрано 3 заговора", show_alert=True)
        return
    else:
        selected.append(name)
    await state.update_data(pact_tome_cantrips_selected=selected)
    # Перерисовка клавиатуры — items должны быть тем же списком,
    # что и в proceed_to_tome_cantrips (все cantrips, не только Колдун).
    cantrips = _spell_repo.get_all(is_cantrip=True) or []
    try:
        await callback.message.edit_reply_markup(
            reply_markup=create_tome_picker_keyboard(
                items=cantrips, selected=selected,
                callback_prefix="tome_cantrip_",
                ready_callback="tome_cantrip_ready",
                limit=3,
            ),
        )
    except Exception as e:
        logger.warning(f"Не удалось обновить клавиатуру tome cantrips: {e}")
    await callback.answer()


async def proceed_to_tome_rituals(callback: CallbackQuery, state: FSMContext):
    """Pact of the Tome: 2 ритуала 1 уровня из любого списка."""
    # Берём заклинания 1 уровня с флагом is_ritual для Колдуна.
    # Если spell_repo не имеет такого метода — fallback на пустой список.
    rituals = []
    try:
        all_lvl1 = _spell_repo.get_level1_spells_for_class("Колдун") or []
        rituals = [s for s in all_lvl1 if s.get("is_ritual")]
    except Exception as e:
        logger.warning(f"Не удалось получить ритуалы из БД: {e}")
    if not rituals:
        logger.info("Ритуалов 1 уровня нет — пропускаем шаг.")
        await state.update_data(pact_tome_rituals=[])
        await proceed_to_skills(callback, state)
        return
    await state.update_data(pact_tome_rituals_selected=[])
    await state.set_state(CreateCharacter.warlock_tome_rituals_select)
    await send_new_from_callback(
        callback, state,
        "📜 Книга теней: выбери 2 ритуала 1 уровня:",
        reply_markup=create_tome_picker_keyboard(
            items=rituals, selected=[],
            callback_prefix="tome_ritual_",
            ready_callback="tome_ritual_ready",
            limit=2,
        ),
    )


@router.callback_query(CreateCharacter.warlock_tome_rituals_select, lambda c: c.data and (c.data.startswith("tome_ritual_") or c.data == "tome_pick_info"))
async def select_tome_ritual(callback: CallbackQuery, state: FSMContext):
    if callback.data == "tome_pick_info":
        await callback.answer()
        return
    if callback.data == "tome_ritual_ready":
        data = await state.get_data()
        selected = data.get("pact_tome_rituals_selected", [])
        if len(selected) != 2:
            await callback.answer(f"❌ Нужно выбрать ровно 2 ритуала (выбрано {len(selected)})", show_alert=True)
            return
        await state.update_data(pact_tome_rituals=selected)
        await callback.answer("✅ Ритуалы Книги теней выбраны")
        await proceed_to_skills(callback, state)
        return
    # callback_data — spell_id (избегаем 64-байтного лимита Telegram).
    try:
        sp_id = int(callback.data.replace("tome_ritual_", ""))
    except ValueError:
        await callback.answer("❌ Некорректный ID ритуала", show_alert=True)
        return
    sp_data = _spell_repo.get_by_id(sp_id)
    if not sp_data:
        await callback.answer("❌ Ритуал не найден", show_alert=True)
        return
    name = sp_data.get("name")
    data = await state.get_data()
    selected = list(data.get("pact_tome_rituals_selected", []))
    if name in selected:
        selected.remove(name)
    elif len(selected) >= 2:
        await callback.answer("❌ Уже выбрано 2 ритуала", show_alert=True)
        return
    else:
        selected.append(name)
    await state.update_data(pact_tome_rituals_selected=selected)
    rituals = []
    try:
        all_lvl1 = _spell_repo.get_level1_spells_for_class("Колдун") or []
        rituals = [s for s in all_lvl1 if s.get("is_ritual")]
    except Exception:
        rituals = []
    try:
        await callback.message.edit_reply_markup(
            reply_markup=create_tome_picker_keyboard(
                items=rituals, selected=selected,
                callback_prefix="tome_ritual_",
                ready_callback="tome_ritual_ready",
                limit=2,
            ),
        )
    except Exception as e:
        logger.warning(f"Не удалось обновить клавиатуру tome rituals: {e}")
    await callback.answer()

# =========================================================
# ШАГ 2: ВЫБОР НАВЫКОВ КЛАССА
# =========================================================
@router.callback_query(CreateCharacter.skills_select, lambda c: c.data.startswith("class_skill_toggle_") or c.data == "class_skills_ready" or c.data == "class_skills_info")
async def handle_skills_selection(callback: CallbackQuery, state: FSMContext):
    logger.info(f"handle_skills_selection: data={callback.data}, state={await state.get_state()}")
    user_data = await state.get_data()
    class_name = user_data.get("class_name")
    class_info = _class_repo.get_by_name(class_name)
    skill_choices = class_info.get('skill_choices', 2) if class_info else 2
    selected_skills = user_data.get("selected_class_skills", [])
    logger.info(f"selected_skills={selected_skills}, skill_choices={skill_choices}")
    data = callback.data
    user_data = await state.get_data()
    class_name = user_data.get("class_name")
    class_info = _class_repo.get_by_name(class_name)
    if not class_info:
        await callback.answer(SKILLS_ERROR_CLASS_NOT_FOUND)
        return
    available_skills = class_info.get('skills', [])
    if not available_skills:
        available_skills = ["Акробатика", "Атлетика", "Восприятие", "Выживание", "Выступление", "Запугивание", "История", "Ловкость рук", "Медицина", "Обман", "Обращение с животными", "Природа", "Проницательность", "Расследование", "Религия", "Скрытность", "Тайная магия", "Убеждение"]
    skill_choices = class_info.get('skill_choices', 2)
    selected_skills = user_data.get("selected_class_skills", [])



    if data == "class_skills_ready":
        if len(selected_skills) == skill_choices:
            await state.update_data(selected_class_skills=selected_skills)
            # 2024 PHB: Плут и Бард на 1 уровне получают экспертизу в 2 навыках.
            if class_name in ("Плут", "Бард"):
                await handle_class_expertise(callback, state)
            elif class_name == "Следопыт":
                # 2024 PHB: Ranger L1 — Favored Enemy. Игрок выбирает тип
                # существ. После выбора — переход к equipment.
                await proceed_to_favored_enemy(callback, state)
            else:
                await state.set_state(CreateCharacter.class_equipment_select)
                await show_class_equipment(callback, state)
            await callback.answer(SKILLS_SUCCESS)
        else:
            await callback.answer(SKILLS_ERROR_WRONG_COUNT.format(skill_choices=skill_choices, selected=len(selected_skills)), show_alert=True)
        return
    if data == "class_skills_info":
        await callback.answer(SKILLS_INFO_SELECTED.format(selected=len(selected_skills), max=skill_choices), show_alert=False)
        return
    if data.startswith("class_skill_toggle_"):
        skill_name = data.replace("class_skill_toggle_", "")
        if skill_name in selected_skills:
            selected_skills.remove(skill_name)
        else:
            if len(selected_skills) >= skill_choices:
                await callback.answer(SKILLS_ERROR_TOO_MANY.format(skill_choices=skill_choices), show_alert=True)
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
# ОБРАБОТЧИКИ ДЛЯ ПЛУТА (ЭКСПЕРТИЗА И ЯЗЫК)
# =========================================================
@router.callback_query(CreateCharacter.rogue_expertise_select, lambda c: c.data.startswith("rogue_expertise_"))
async def select_rogue_expertise(callback: CallbackQuery, state: FSMContext):
    skill = callback.data.replace("rogue_expertise_", "")
    data = await state.get_data()
    selected = data.get("rogue_expertise_selected", [])
    if skill in selected:
        selected.remove(skill)
        await callback.answer(f"❌ {skill} убран из экспертности")
    else:
        if len(selected) >= 2:
            await callback.answer("❌ Нельзя выбрать больше двух навыков", show_alert=True)
            return
        selected.append(skill)
        await callback.answer(f"✅ {skill} добавлен в экспертность")
    await state.update_data(rogue_expertise_selected=selected)
    available = data.get("available_skills_for_expertise", [])
    keyboard = create_rogue_expertise_keyboard(available, selected)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    if len(selected) == 2:
        # Сохраняем выбранные навыки в state.
        # Имя поля — `rogue_expertise` сохранено для совместимости с БД и
        # другими хендлерами; на самом деле это «class_expertise» — фича Плута
        # и Барда (2024 PHB).
        await state.update_data(rogue_expertise=selected)
        data = await state.get_data()
        class_name = data.get("class_name")
        # Бард не получает доп. язык от класса — сразу к выбору снаряжения.
        if class_name != "Плут":
            await state.set_state(CreateCharacter.class_equipment_select)
            await show_class_equipment(callback, state)
            await callback.answer()
            return
        # Плут — выбор воровского доп. языка.
        await state.set_state(CreateCharacter.rogue_language_select)
        # Получаем список языков из БД
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM languages ORDER BY name")
                languages = [row[0] for row in cur.fetchall()]
        text = "🗣️ Выбери дополнительный язык (кроме Воровского жаргона):"
        await send_new_from_callback(callback, state, text, reply_markup=create_rogue_language_keyboard(languages))
    await callback.answer()

@router.callback_query(CreateCharacter.rogue_language_select, lambda c: c.data.startswith("rogue_lang_"))
async def select_rogue_language(callback: CallbackQuery, state: FSMContext):
    language = callback.data.replace("rogue_lang_", "")
    await state.update_data(rogue_extra_language=language)
    await callback.answer(f"✅ Выбран язык: {language}")
    await state.set_state(CreateCharacter.class_equipment_select)
    await show_class_equipment(callback, state)

# =========================================================
# ШАГ 3: ВЫБОР СНАРЯЖЕНИЯ КЛАССА
# =========================================================
async def show_class_equipment(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    class_name = data.get("class_name")
    if not class_name:
        logger.error("class_name не найден")
        await callback.answer("❌ Ошибка: класс не определён")
        return
    equipment = CharacterStatsService.get_class_equipment(class_name)
    if not equipment:
        logger.error(f"Нет снаряжения для {class_name}")
        await send_new_from_callback(callback, state, EQUIPMENT_NOT_FOUND.format(class_name=class_name))
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
            buttons.append([InlineKeyboardButton(text=f"📦 Вариант {choice}", callback_data=f"equip_{choice}")])
        buttons.append([InlineKeyboardButton(text=BACK_TO_CLASSES, callback_data="back_to_classes")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await send_new_from_callback(callback, state, text, keyboard)
    else:
        eq = equipment[0]
        await state.update_data(selected_armor=eq.get('armor'), selected_weapon=eq.get('weapon'), selected_secondary_weapon=eq.get('secondary_weapon'), selected_other_items=eq.get('other_items'), selected_coins=eq.get('coins', 0))
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
        await state.update_data(selected_armor=eq.get('armor'), selected_weapon=eq.get('weapon'), selected_secondary_weapon=eq.get('secondary_weapon'), selected_other_items=eq.get('other_items'), selected_coins=eq.get('coins', 0))
        weapon_name = eq.get('weapon')
        if weapon_name:
            masteries = CharacterStatsService.auto_assign_masteries(weapon_name, class_name)
            await state.update_data(selected_masteries=masteries)
    await send_new_from_callback(callback, state, EQUIPMENT_SELECTED.format(choice=choice))
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
            await send_new_from_callback(callback, state, FIGHTING_STYLE_NO_STYLES.format(class_name=class_name))
            await go_to_background(callback, state)
            return
        # Рекомендуем стиль по выбранному оружию (D&D 5.5e 2024 + гайды).
        recommended_style_name = recommend_fighting_style(data.get("selected_weapon"))
        # Сортируем так, чтобы рекомендуемый шёл первым (если он вообще доступен).
        styles_sorted = sorted(
            styles,
            key=lambda s: 0 if s.get('name') == recommended_style_name else 1,
        )
        styles_list = "\n".join([
            f"• {'⭐ ' if s['name'] == recommended_style_name else ''}{s['name']} – {s['description']}"
            for s in styles_sorted
        ])
        text = FIGHTING_STYLE_TITLE_TEMPLATE.format(class_name=class_name, styles_list=styles_list)
        if any(s.get('name') == recommended_style_name for s in styles_sorted):
            text += f"\n\n🎯 Рекомендация бота: {recommended_style_name} (выделен ⭐)."
        buttons = []
        for s in styles_sorted:
            label_prefix = "⭐ " if s['name'] == recommended_style_name else "⚔️ "
            buttons.append([InlineKeyboardButton(text=f"{label_prefix}{s['name']}", callback_data=f"style_{s['id']}")])
        buttons.append([InlineKeyboardButton(text=FIGHTING_STYLE_BACK, callback_data="back_to_spells")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await state.set_state(CreateCharacter.fighting_style_select)
        await send_new_from_callback(callback, state, text, keyboard)
    else:
        await go_to_background(callback, state)

async def go_to_background(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.background_select)
    await send_new_from_callback(callback, state, BACKGROUND_SELECT_TITLE, reply_markup=create_background_keyboard())


# ─── Message-варианты переходов (для случаев, когда хендлер триггерит Message,
# а не CallbackQuery — например, кнопка «Продолжить» в spell_handlers).
# Без них callback.message.answer() ломается, т.к. Message не имеет .message ─

async def go_to_fighting_style_from_message(message: Message, state: FSMContext):
    """Аналог go_to_fighting_style, но для контекста Message."""
    data = await state.get_data()
    class_name = data.get("class_name")
    if ProgressionService.should_select_fighting_style(class_name):
        styles = CharacterStatsService.get_fighting_styles_for_class(class_name)
        if not styles:
            await send_new(state, message, FIGHTING_STYLE_NO_STYLES.format(class_name=class_name))
            await go_to_background_from_message(message, state)
            return
        recommended_style_name = recommend_fighting_style(data.get("selected_weapon"))
        styles_sorted = sorted(
            styles,
            key=lambda s: 0 if s.get('name') == recommended_style_name else 1,
        )
        styles_list = "\n".join([
            f"• {'⭐ ' if s['name'] == recommended_style_name else ''}{s['name']} – {s['description']}"
            for s in styles_sorted
        ])
        text = FIGHTING_STYLE_TITLE_TEMPLATE.format(class_name=class_name, styles_list=styles_list)
        if any(s.get('name') == recommended_style_name for s in styles_sorted):
            text += f"\n\n🎯 Рекомендация бота: {recommended_style_name} (выделен ⭐)."
        buttons = []
        for s in styles_sorted:
            label_prefix = "⭐ " if s['name'] == recommended_style_name else "⚔️ "
            buttons.append([InlineKeyboardButton(text=f"{label_prefix}{s['name']}", callback_data=f"style_{s['id']}")])
        buttons.append([InlineKeyboardButton(text=FIGHTING_STYLE_BACK, callback_data="back_to_spells")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await state.set_state(CreateCharacter.fighting_style_select)
        await send_new(state, message, text, keyboard)
    else:
        await go_to_background_from_message(message, state)


async def go_to_background_from_message(message: Message, state: FSMContext):
    """Аналог go_to_background, но для контекста Message."""
    await state.set_state(CreateCharacter.background_select)
    await send_new(state, message, BACKGROUND_SELECT_TITLE, reply_markup=create_background_keyboard())

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
        await callback.answer(FIGHTING_STYLE_SELECTED.format(style_name=style_name))
    await go_to_background(callback, state)

@router.callback_query(lambda c: c.data == "back_to_spells")
async def back_to_spells(callback: CallbackQuery, state: FSMContext):
    await go_to_spells(callback, state)

# =========================================================
# ПРЕДЫСТОРИЯ
# =========================================================
@router.callback_query(CreateCharacter.background_equipment_select, lambda c: c.data.startswith("bg_equip_"))
async def select_background_equipment(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("bg_equip_", "")
    await state.update_data(background_equipment_choice=choice)
    await callback.answer(f"✅ Выбран вариант {choice}")
    await calculate_and_show_stats(callback, state)

@router.callback_query(CreateCharacter.background_equipment_select, lambda c: c.data == "back_to_background")
async def back_to_background_from_equipment(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.background_select)
    await send_new_from_callback(callback, state, "Выбери предысторию заново:",
                                 reply_markup=create_background_keyboard())
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
    await state.update_data(final_stats=stats_result['stats'], stats=stats_result['stats'], hp=stats_result['hp'], ac=stats_result['ac'])
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
    # 2024 PHB: на этом шаге AC показан без снаряжения. Финальное значение
    # пересчитывается на этапе сохранения с учётом брони и щита.
    text += "\n\n💡 AC показан без брони и щита; финальный AC учитывает снаряжение."
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
    # PHB 2024: у Драконорожденного НЕТ подрас — есть только Draconic Ancestry,
    # который запрашивается отдельным шагом в `proceed_after_race`. Если в БД
    # ошибочно остались записи в `subraces` (наследие старого seed_data.py),
    # принудительно пропускаем шаг подрасы, чтобы не спрашивать игрока цвет
    # дракона дважды.
    if race == "Драконорожденный":
        has_sub = False
        subraces_list = []
    text = RACE_INFO_TEMPLATE.format(race=race, desc=race_desc, speed=race_speed, size=race_size)
    img_path = CharacterStatsService.get_race_image_path(race)
    if img_path and os.path.exists(img_path):
        photo = FSInputFile(img_path)
        await callback.message.answer_photo(photo=photo, caption=text, parse_mode=None)
    else:
        await callback.message.answer(text, parse_mode=None)
    if has_sub and subraces_list:
        await send_new_from_callback(callback, state, RACE_SUBRACE_PROMPT, reply_markup=create_subrace_keyboard(race))
        await state.set_state(CreateCharacter.subrace_select)
    else:
        await proceed_after_race(callback, state)
    await callback.answer()

@router.callback_query(CreateCharacter.subrace_select, lambda c: c.data.startswith("subrace_"))
async def select_subrace(callback: CallbackQuery, state: FSMContext):
    subrace = callback.data.replace("subrace_", "")
    await state.update_data(subrace=subrace)
    await callback.answer(SUBRACE_SELECTED.format(subrace=subrace))
    await proceed_after_race(callback, state)


async def proceed_after_race(callback: CallbackQuery, state: FSMContext):
    """
    Хук после выбора расы/подрасы. По правилам D&D 5.5e (2024) у некоторых
    рас есть дополнительный обязательный выбор:
    — Драконорождённый: тип дракона (10 опций), определяет урон Оружия Дыхания
      и сопротивление.
    """
    data = await state.get_data()
    race = data.get("race")
    if race == "Драконорожденный":
        await state.set_state(CreateCharacter.draconic_ancestry_select)
        await send_new_from_callback(
            callback,
            state,
            "🐉 Выбери тип дракона своего предка (он определит вид урона и сопротивление):",
            reply_markup=create_draconic_ancestry_keyboard(),
        )
        return
    await go_to_name(callback, state)


@router.callback_query(CreateCharacter.draconic_ancestry_select, lambda c: c.data.startswith("draconic_"))
async def select_draconic_ancestry(callback: CallbackQuery, state: FSMContext):
    ancestry = callback.data.replace("draconic_", "")
    # Канонические русские имена для хранения в БД (короткие, чтобы влезло в VARCHAR(30))
    ancestry_labels = {
        "black": "Чёрный", "blue": "Синий", "brass": "Латунный",
        "bronze": "Бронзовый", "copper": "Медный", "gold": "Золотой",
        "green": "Зелёный", "red": "Красный", "silver": "Серебряный",
        "white": "Белый",
    }
    label = ancestry_labels.get(ancestry, ancestry)
    await state.update_data(draconic_ancestry=label)
    await callback.answer(f"✅ Тип дракона: {label}")
    logger.info(f"[FLOW] Драконорождённый: {label}")
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
    # 2024 PHB: backstory — необязательное нарративное поле, даём кнопку «Пропустить».
    await send_new(state, message, BACKSTORY_REQUEST, reply_markup=skip_kb())

@router.message(CreateCharacter.backstory_input)
async def set_backstory(message: Message, state: FSMContext):
    if message.text == BTN_CANCEL:
        await cancel_creation(message, state)
        return
    # Игрок может нажать «⏩ Пропустить» — пишем дефолтную историю и идём дальше.
    if message.text == BTN_SKIP:
        await state.update_data(backstory="Нет истории")
        try:
            await message.delete()
        except Exception:
            pass
        await state.set_state(CreateCharacter.alignment_select)
        await send_new(state, message, ALIGNMENT_REQUEST, reply_markup=create_alignment_keyboard())
        return
    backstory = message.text.strip()
    if len(backstory) > 2000:
        await message.answer(BACKSTORY_TOO_LONG, reply_markup=skip_kb())
        return
    await state.update_data(backstory=backstory)
    await message.delete()
    await state.set_state(CreateCharacter.alignment_select)
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
    await callback.answer(ALIGNMENT_SELECTED.format(alignment=alignment_name))
    # 2024 PHB: после мировоззрения — шаг 4 черт личности (Trait/Ideal/Bond/Flaw),
    # затем картинка.
    await proceed_to_personality_intro(callback, state)


# =========================================================
# 4 ЧЕРТЫ ЛИЧНОСТИ (D&D 5.5e 2024) — пункт #30
# =========================================================

async def proceed_to_personality_intro(callback: CallbackQuery, state: FSMContext):
    """Экран выбора режима: 🎲 авто / ✍️ ручной ввод / ⏩ пропустить."""
    text = (
        "🎭 Черты личности (D&D 5.5e 2024)\n\n"
        "Выбери, как сформировать 4 нарративных поля:\n"
        "• Черта личности\n• Идеал\n• Привязанность\n• Недостаток"
    )
    await state.set_state(CreateCharacter.personality_intro)
    await send_new_from_callback(
        callback, state, text,
        reply_markup=create_personality_intro_keyboard(),
    )


@router.callback_query(CreateCharacter.personality_intro, lambda c: c.data == "pers_auto")
async def personality_auto(callback: CallbackQuery, state: FSMContext):
    auto = generate_personality_traits()
    await state.update_data(
        personality_trait=auto["personality_trait"],
        ideal=auto["ideal"],
        bond=auto["bond"],
        flaw=auto["flaw"],
    )
    await callback.answer("✅ Черты сгенерированы")
    await _go_to_image_step(callback, state)


@router.callback_query(CreateCharacter.personality_intro, lambda c: c.data == "pers_skip")
async def personality_skip(callback: CallbackQuery, state: FSMContext):
    # Оставляем поля пустыми; auto-дефолты подставятся в save_character.
    await callback.answer("⏩ Шаг пропущен")
    await _go_to_image_step(callback, state)


@router.callback_query(CreateCharacter.personality_intro, lambda c: c.data == "pers_manual")
async def personality_manual(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateCharacter.personality_trait_input)
    await send_new_from_callback(
        callback, state,
        "✍️ Введи свою Черту личности (одной фразой). До 500 символов.",
        reply_markup=skip_kb(),
    )
    await callback.answer()


def _validate_personality_text(text: str, max_len: int = 500) -> Optional[str]:
    """Валидирует текстовый ввод. Возвращает обрезанную строку или None если пусто."""
    if not text:
        return None
    text = text.strip()
    if not text:
        return None
    return text[:max_len]


@router.message(CreateCharacter.personality_trait_input)
async def input_personality_trait(message: Message, state: FSMContext):
    if message.text == BTN_CANCEL:
        await cancel_creation(message, state)
        return
    if message.text == BTN_SKIP:
        # Заполним пустую черту через auto и пропустим к идеалу.
        auto = generate_personality_traits()
        await state.update_data(personality_trait=auto["personality_trait"])
    else:
        val = _validate_personality_text(message.text)
        if not val:
            await message.answer("❌ Пустой ввод. Введи текст или нажми «⏩ Пропустить».", reply_markup=skip_kb())
            return
        await state.update_data(personality_trait=val)
        try:
            await message.delete()
        except Exception:
            pass
    await state.set_state(CreateCharacter.personality_ideal_input)
    await send_new(state, message, "✍️ Введи свой Идеал. Можно с указанием мировоззрения в скобках.", reply_markup=skip_kb())


@router.message(CreateCharacter.personality_ideal_input)
async def input_personality_ideal(message: Message, state: FSMContext):
    if message.text == BTN_CANCEL:
        await cancel_creation(message, state)
        return
    if message.text == BTN_SKIP:
        auto = generate_personality_traits()
        await state.update_data(ideal=auto["ideal"])
    else:
        val = _validate_personality_text(message.text)
        if not val:
            await message.answer("❌ Пустой ввод. Введи текст или нажми «⏩ Пропустить».", reply_markup=skip_kb())
            return
        await state.update_data(ideal=val)
        try:
            await message.delete()
        except Exception:
            pass
    await state.set_state(CreateCharacter.personality_bond_input)
    await send_new(state, message, "✍️ Введи свою Привязанность (что или кто важно для персонажа).", reply_markup=skip_kb())


@router.message(CreateCharacter.personality_bond_input)
async def input_personality_bond(message: Message, state: FSMContext):
    if message.text == BTN_CANCEL:
        await cancel_creation(message, state)
        return
    if message.text == BTN_SKIP:
        auto = generate_personality_traits()
        await state.update_data(bond=auto["bond"])
    else:
        val = _validate_personality_text(message.text)
        if not val:
            await message.answer("❌ Пустой ввод. Введи текст или нажми «⏩ Пропустить».", reply_markup=skip_kb())
            return
        await state.update_data(bond=val)
        try:
            await message.delete()
        except Exception:
            pass
    await state.set_state(CreateCharacter.personality_flaw_input)
    await send_new(state, message, "✍️ Введи Недостаток своего персонажа.", reply_markup=skip_kb())


@router.message(CreateCharacter.personality_flaw_input)
async def input_personality_flaw(message: Message, state: FSMContext):
    if message.text == BTN_CANCEL:
        await cancel_creation(message, state)
        return
    if message.text == BTN_SKIP:
        auto = generate_personality_traits()
        await state.update_data(flaw=auto["flaw"])
    else:
        val = _validate_personality_text(message.text)
        if not val:
            await message.answer("❌ Пустой ввод. Введи текст или нажми «⏩ Пропустить».", reply_markup=skip_kb())
            return
        await state.update_data(flaw=val)
        try:
            await message.delete()
        except Exception:
            pass
    await _go_to_image_step_from_message(message, state)


async def _go_to_image_step(callback: CallbackQuery, state: FSMContext):
    """Переход на шаг загрузки картинки персонажа."""
    await state.set_state(CreateCharacter.image_input)
    await send_new_from_callback(callback, state, IMAGE_REQUEST, reply_markup=skip_kb())


async def _go_to_image_step_from_message(message: Message, state: FSMContext):
    """Тот же переход, но из контекста message-хендлера."""
    await state.set_state(CreateCharacter.image_input)
    await send_new(state, message, IMAGE_REQUEST, reply_markup=skip_kb())

# =========================================================
# ИЗОБРАЖЕНИЕ И ФИНАЛИЗАЦИЯ
# =========================================================
@router.message(CreateCharacter.image_input, F.text == BTN_SKIP)
async def skip_image(message: Message, state: FSMContext):
    # Срабатывает только в состоянии загрузки картинки. На других шагах
    # «Пропустить» обрабатывается локальными хендлерами (например, backstory).
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
        char_data['druid_order'] = data.get("druid_order")
        char_data['cleric_order'] = data.get("cleric_order")
        char_data['warlock_pact'] = data.get("warlock_pact")
        char_data['rogue_expertise'] = data.get("rogue_expertise", [])
        char_data['rogue_extra_language'] = data.get("rogue_extra_language")
        char_data['auto_spells'] = data.get("auto_spells", [])
        char_data['pact_tome_cantrips'] = data.get("pact_tome_cantrips", [])
        char_data['pact_tome_rituals'] = data.get("pact_tome_rituals", [])
        char_data['pact_blade_weapon'] = data.get("pact_blade_weapon")
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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📄 Открыть лист персонажа", web_app=WebAppInfo(url=web_app_url))]])
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
        if image_file_id:
            await message.answer_photo(photo=image_file_id, caption=caption, reply_markup=keyboard, parse_mode=None)
        else:
            await message.answer(caption, reply_markup=keyboard, parse_mode=None)
        await message.answer(MENU_TITLE, reply_markup=main_menu())
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка при создании персонажа: {e}", exc_info=True)
        await message.answer(f"❌ Произошла ошибка: {str(e)[:200]}", reply_markup=main_menu())
        await state.clear()

@router.callback_query(CreateCharacter.background_select, lambda c: c.data.startswith("bg_"))
async def select_background(callback: CallbackQuery, state: FSMContext):
    background = callback.data.replace("bg_", "")
    await state.update_data(background=background)
    logger.info(f"[FLOW] Выбрана предыстория: {background}")

    bg_info = _bg_repo.get_by_name(background)
    if not bg_info:
        await send_new_from_callback(callback, state, BACKGROUND_ERROR.format(background=background))
        await state.clear()
        return

    await state.update_data(
        selected_skills_bg=bg_info.get('skills', []),
        background_trait=bg_info.get('trait', 'Нет'),
        background_origin_feat=bg_info.get('origin_feat', '')
    )

    trait = bg_info.get('trait', 'Нет')
    skills = ", ".join(bg_info.get("skills", []))
    tools = bg_info.get('tools', 'Нет')
    description = bg_info.get('description', 'Нет описания')[:300]
    origin_feat = bg_info.get('origin_feat', '')
    origin_feat_text = f"✨ Черта происхождения: {origin_feat}\n\n" if origin_feat else ""

    user_data = await state.get_data()
    class_name = user_data.get("class_name")
    bonus_text = ""
    try:
        from engine.stats import BackgroundBonusDistributor
        primary = CharacterStatsService.get_class_primary_stats(class_name) if class_name else []
        bg_chars = bg_info.get('characteristics', []) or []
        if primary and bg_chars:
            distributor = BackgroundBonusDistributor()
            bonuses = distributor.distribute(primary_stats=primary, background_stats=bg_chars)
            parts = [f"+{v} {k}" for k, v in bonuses.to_str_dict().items() if v > 0]
            bonus_text = f"✨ Бонусы характеристик: {', '.join(parts)}\n\n"
    except Exception as e:
        logger.warning(f"Не удалось рассчитать распределение бонусов предыстории: {e}")
        chars = bg_info.get('characteristics', [])
        if len(chars) >= 2:
            bonus_text = f"✨ Бонусы характеристик: +2 {chars[0]}, +1 {chars[1]}\n\n"

    text = (f"📜 {background}\n\n"
            f"📖 {description}...\n\n"
            f"{origin_feat_text}"
            f"{bonus_text}"
            f"🔧 Черта: {trait}\n"
            f"📚 Навыки: {skills}\n"
            f"🛠️ Инструменты: {tools}\n\n"
            f"Теперь выбери снаряжение от предыстории:")

    await send_new_from_callback(callback, state, text)
    await state.set_state(CreateCharacter.background_equipment_select)
    await send_new_from_callback(callback, state, "Выбери один из стартовых наборов:",
                                 reply_markup=create_background_equipment_keyboard(background))
    await callback.answer()

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
        await callback.message.edit_text(DELETE_SUCCESS.format(name=character['name']), parse_mode=None)
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
