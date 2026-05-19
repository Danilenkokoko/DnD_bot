# services/progression_service.py
"""
Сервис управления порядком шагов создания персонажа
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message
    from aiogram.fsm.context import FSMContext

from repositories.class_repository import ClassRepository

logger = logging.getLogger(__name__)

_class_repo = ClassRepository()


class ProgressionService:
    """Определяет следующий шаг в создании персонажа"""

    @staticmethod
    def is_spellcaster(class_name: str) -> bool:
        """Проверяет, является ли класс заклинателем на 1 уровне"""
        return _class_repo.is_spellcaster(class_name)

    @staticmethod
    def should_select_fighting_style(class_name: str) -> bool:
        """
        Проверяет, нужно ли выбирать боевой стиль на 1-м уровне.

        Этап 3.6 (PHB 2024): по правилам 2024 года Fighting Style на
        1 уровне выбирает ТОЛЬКО Воин. Паладин и Следопыт получают
        Fighting Style через черту класса на 2-м/3-м уровне — это
        перенесено на левелап.
        """
        return class_name == "Воин"

    @staticmethod
    async def go_to_spells(message: "Message", state: "FSMContext") -> None:
        """Переход к выбору заклинаний"""
        from services.spell_service import SpellSelectionService
        await SpellSelectionService.start_cantrips_selection(message, state)

    @staticmethod
    async def go_to_fighting_style(message: "Message", state: "FSMContext") -> None:
        """Переход к выбору боевого стиля (заглушка)"""
        from services.character_service import CharacterStatsService
        data = await state.get_data()
        class_name = data.get("class_name")
        if ProgressionService.should_select_fighting_style(class_name):
            styles = CharacterStatsService.get_fighting_styles_for_class(class_name)
            if not styles:
                await message.answer(f"⚠️ Для класса {class_name} нет доступных боевых стилей.\n\nПереходим к следующему шагу...")
                await ProgressionService.go_to_background(message, state)
                return
            # Здесь должен быть вызов создания клавиатуры и установки состояния
            await message.answer(f"⚔️ Выберите боевой стиль для {class_name}")
        else:
            await ProgressionService.go_to_background(message, state)

    @staticmethod
    async def go_to_background(message: "Message", state: "FSMContext") -> None:
        """Переход к выбору предыстории"""
        from handlers.character_handlers import go_to_background as _go_to_background
        await _go_to_background(message, state)

# =============================================================================
# ЭТАП 4: WizardStep + state-machine (PHB 2024)
# =============================================================================
#
# Цель — единый источник правды о порядке шагов создания персонажа.
# Framework-first: само пользовательское поведение сейчас НЕ меняется,
# существующие direct-вызовы (`go_to_spells`, `go_to_fighting_style`,
# `go_to_name`, `proceed_to_skills`, etc.) продолжают работать.
#
# План — в Этапе 4b/4c постепенно перевести все эти переходы через
# `ProgressionService.next_step(...)`. Для пользователя при этом ничего
# не меняется. После полного перевода физический порядок шагов можно
# будет переставить, отредактировав одну функцию `next_step()`.

from enum import Enum


class WizardStep(str, Enum):
    """Каноническое имя каждого шага создания персонажа (PHB 2024)."""

    # Стартовое состояние
    IDLE = "idle"

    # Шаг 1 — класс и его подвыборы
    CLASS = "class"
    DRUID_ORDER = "druid_order"
    CLERIC_ORDER = "cleric_order"
    WARLOCK_PACT = "warlock_pact"
    SORCERER_ORIGIN = "sorcerer_origin"

    # Шаг 2 — навыки и оружие
    SKILLS = "skills"

    # Шаг 3 — заклинания (для кастеров)
    SPELLS = "spells"
    INVOCATIONS = "invocations"

    # Шаг 4 — боевой стиль (только Воин на 1-м уровне, PHB 2024)
    FIGHTING_STYLE = "fighting_style"

    # Шаг 5 — снаряжение от класса (+ опция «50 GP», Этап 3.4)
    CLASS_EQUIPMENT = "class_equipment"

    # Шаг 6 — предыстория и её части
    BACKGROUND = "background"
    ORIGIN_FEAT = "origin_feat"          # Этап 3.3
    BACKGROUND_EQUIPMENT = "background_equipment"

    # Шаг 7 — назначение характеристик (стандартный массив, Этап 2)
    ABILITIES = "abilities"

    # Шаг 8 — раса/подраса/драконье наследие
    RACE = "race"
    SUBRACE = "subrace"
    DRACONIC_ANCESTRY = "draconic_ancestry"

    # Шаг 9 — общий выбор языков (Этап 3.1)
    LANGUAGES = "languages"

    # Шаг 10 — нарративные шаги
    NAME = "name"
    BACKSTORY = "backstory"
    ALIGNMENT = "alignment"
    TRINKET = "trinket"                  # Этап 3.2
    IMAGE = "image"

    # Финал
    DONE = "done"


# Видимая нумерация для UX-индикатора «Шаг X из N».
# Сгруппирована до 10 крупных шагов — то, что видит пользователь.
# Подвыборы внутри одного шага (например, druid_order внутри class) делят
# номер с родительским шагом.
_STEP_NUMBER: dict = {
    WizardStep.CLASS:                1,
    WizardStep.DRUID_ORDER:          1,
    WizardStep.CLERIC_ORDER:         1,
    WizardStep.WARLOCK_PACT:         1,
    WizardStep.SORCERER_ORIGIN:      1,
    WizardStep.SKILLS:               2,
    WizardStep.SPELLS:               3,
    WizardStep.INVOCATIONS:          3,
    WizardStep.FIGHTING_STYLE:       4,
    WizardStep.CLASS_EQUIPMENT:      5,
    WizardStep.BACKGROUND:           6,
    WizardStep.ORIGIN_FEAT:          6,
    WizardStep.BACKGROUND_EQUIPMENT: 6,
    WizardStep.ABILITIES:            7,
    WizardStep.RACE:                 8,
    WizardStep.SUBRACE:              8,
    WizardStep.DRACONIC_ANCESTRY:    8,
    WizardStep.LANGUAGES:            9,
    WizardStep.NAME:                 10,
    WizardStep.BACKSTORY:            10,
    WizardStep.ALIGNMENT:            10,
    WizardStep.TRINKET:              10,
    WizardStep.IMAGE:                10,
}

TOTAL_VISIBLE_STEPS = 10


def step_number(step: WizardStep) -> int:
    """Возвращает номер шага (1..10) для UX-индикатора."""
    return _STEP_NUMBER.get(step, 0)


def format_step_indicator(step: WizardStep, total: int = TOTAL_VISIBLE_STEPS) -> str:
    """Строка «Шаг 3 из 10» — для добавления в заголовки экранов."""
    num = step_number(step)
    if not num:
        return ""
    return f"Шаг {num} из {total}"


# ── State-machine ───────────────────────────────────────────────────────────


def _is_caster(class_name: str) -> bool:
    """Проверка кастера через ClassRepository (без импортов handlers)."""
    try:
        return _class_repo.is_spellcaster(class_name)
    except Exception:
        return False


def next_step(state_data: dict, current: WizardStep) -> WizardStep:
    """
    Pure-функция: по текущему шагу и накопленному state'у возвращает
    следующий канонический шаг создания персонажа.

    Используется как источник правды о порядке шагов. Реально
    переключение state'а и рендер экрана — на стороне handlers
    (см. ProgressionService.advance()).

    На момент Этапа 4 эту функцию НЕ зовут из боевого кода — она
    нужна как контракт. Существующие direct-переходы работают.
    """
    class_name = state_data.get("class_name") or ""
    race = state_data.get("race") or ""

    if current == WizardStep.IDLE:
        return WizardStep.CLASS

    if current == WizardStep.CLASS:
        if class_name == "Друид":
            return WizardStep.DRUID_ORDER
        if class_name == "Жрец":
            return WizardStep.CLERIC_ORDER
        if class_name == "Колдун":
            return WizardStep.WARLOCK_PACT
        if class_name == "Чародей":
            return WizardStep.SORCERER_ORIGIN
        return WizardStep.SKILLS

    if current in (WizardStep.DRUID_ORDER, WizardStep.CLERIC_ORDER,
                   WizardStep.WARLOCK_PACT, WizardStep.SORCERER_ORIGIN):
        return WizardStep.SKILLS

    if current == WizardStep.SKILLS:
        if _is_caster(class_name):
            return WizardStep.SPELLS
        if ProgressionService.should_select_fighting_style(class_name):
            return WizardStep.FIGHTING_STYLE
        return WizardStep.CLASS_EQUIPMENT

    if current == WizardStep.SPELLS:
        if class_name == "Колдун":
            return WizardStep.INVOCATIONS
        if ProgressionService.should_select_fighting_style(class_name):
            return WizardStep.FIGHTING_STYLE
        return WizardStep.CLASS_EQUIPMENT

    if current == WizardStep.INVOCATIONS:
        if ProgressionService.should_select_fighting_style(class_name):
            return WizardStep.FIGHTING_STYLE
        return WizardStep.CLASS_EQUIPMENT

    if current == WizardStep.FIGHTING_STYLE:
        return WizardStep.CLASS_EQUIPMENT

    if current == WizardStep.CLASS_EQUIPMENT:
        return WizardStep.BACKGROUND

    if current == WizardStep.BACKGROUND:
        # Этап 3.3: если есть origin_feat — отдельный экран показа.
        if state_data.get("background_origin_feat"):
            return WizardStep.ORIGIN_FEAT
        return WizardStep.BACKGROUND_EQUIPMENT

    if current == WizardStep.ORIGIN_FEAT:
        return WizardStep.BACKGROUND_EQUIPMENT

    if current == WizardStep.BACKGROUND_EQUIPMENT:
        return WizardStep.ABILITIES

    if current == WizardStep.ABILITIES:
        return WizardStep.RACE

    if current == WizardStep.RACE:
        # Подраса — если есть. Драконорождённый → ancestry.
        try:
            race_data = _class_repo  # placeholder для подсказки IDE
        except Exception:
            pass
        from repositories.race_repository import RaceRepository
        _rr = RaceRepository()
        if _rr.has_subraces(race):
            return WizardStep.SUBRACE
        if race == "Драконорожденный":
            return WizardStep.DRACONIC_ANCESTRY
        return WizardStep.LANGUAGES

    if current == WizardStep.SUBRACE:
        if race == "Драконорожденный":
            return WizardStep.DRACONIC_ANCESTRY
        return WizardStep.LANGUAGES

    if current == WizardStep.DRACONIC_ANCESTRY:
        return WizardStep.LANGUAGES

    if current == WizardStep.LANGUAGES:
        return WizardStep.NAME

    if current == WizardStep.NAME:
        return WizardStep.BACKSTORY

    if current == WizardStep.BACKSTORY:
        return WizardStep.ALIGNMENT

    if current == WizardStep.ALIGNMENT:
        return WizardStep.TRINKET

    if current == WizardStep.TRINKET:
        return WizardStep.IMAGE

    if current == WizardStep.IMAGE:
        return WizardStep.DONE

    return WizardStep.DONE

