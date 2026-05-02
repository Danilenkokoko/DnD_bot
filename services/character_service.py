# services/character_service.py
"""
Сервис для работы с характеристиками персонажа
Использует engine и репозитории для доступа к данным
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

# Engine (чистая логика)
from engine.stats import AbilityScores, BackgroundBonusDistributor
from engine.hp import calculate_hp_at_level, HpCalculationMethod, calculate_modifier as hp_calculate_modifier
from engine.ac import calculate_ac_with_armor, calculate_base_ac, calculate_unarmored_ac
from engine.proficiency import calculate_proficiency_bonus
from engine.validators import validate_all_ability_scores, validate_ability_score, validate_level

# Репозитории
from repositories.class_repository import ClassRepository
from repositories.background_repository import BackgroundRepository
from repositories.race_repository import RaceRepository
from repositories.equipment_repository import EquipmentRepository, FightingStyleRepository, InvocationRepository
from repositories.spell_repository import SpellRepository
from repositories.character_repository import CharacterRepository

# Для обратной совместимости (временные импорты)
from dnd_logic import get_class_starting_stats

logger = logging.getLogger(__name__)

# Инициализация репозиториев (синглтоны)
_class_repo = ClassRepository()
_background_repo = BackgroundRepository()
_race_repo = RaceRepository()
_equipment_repo = EquipmentRepository()
_fighting_style_repo = FightingStyleRepository()
_invocation_repo = InvocationRepository()
_spell_repo = SpellRepository()
_character_repo = CharacterRepository()


class CharacterStatsService:
    """Сервис расчёта характеристик персонажа"""

    # =========================================================
    # ДОСТУП К ДАННЫМ ЧЕРЕЗ РЕПОЗИТОРИИ
    # =========================================================

    @staticmethod
    def get_class_primary_stats(class_name: str) -> List[str]:
        return _class_repo.get_primary_stats(class_name)

    @staticmethod
    def get_class_hit_die(class_name: str) -> int:
        return _class_repo.get_hit_die(class_name)

    @staticmethod
    def get_class_info(class_name: str) -> Dict[str, Any]:
        class_data = _class_repo.get_by_name(class_name)
        if not class_data:
            return {}
        return {
            'hit_die': class_data.get('hit_die', 8),
            'primary_stats': class_data.get('primary_stats', []),
            'saving_throws': class_data.get('saving_throws', []),
            'skill_choices': class_data.get('skill_choices', 2),
            'description': class_data.get('description', ''),
            'spellcasting': class_data.get('is_spellcaster', False),
            'spellcasting_ability': class_data.get('spellcasting_ability')
        }

    @staticmethod
    def get_class_description(class_name: str) -> str:
        class_data = _class_repo.get_by_name(class_name)
        return class_data.get('description', '') if class_data else ''

    @staticmethod
    def get_class_image_path(class_name: str) -> Optional[str]:
        class_data = _class_repo.get_by_name(class_name)
        return class_data.get('image_path') if class_data else None

    @staticmethod
    def get_class_spell_counts(class_name: str) -> Dict[str, int]:
        return _class_repo.get_spell_counts(class_name)

    @staticmethod
    def get_background_characteristics(background_name: str) -> List[str]:
        return _background_repo.get_characteristics(background_name)

    @staticmethod
    def get_background_data(background_name: str) -> Dict[str, Any]:
        return _background_repo.get_by_name(background_name) or {}

    @staticmethod
    def get_race_list() -> List[str]:
        return _race_repo.get_all_names()

    @staticmethod
    def get_race_description(race_name: str) -> str:
        race = _race_repo.get_by_name(race_name)
        return race.get('description', '') if race else ''

    @staticmethod
    def get_race_speed(race_name: str) -> int:
        race = _race_repo.get_by_name(race_name)
        return race.get('speed', 30) if race else 30

    @staticmethod
    def get_race_size(race_name: str) -> str:
        race = _race_repo.get_by_name(race_name)
        return race.get('size', 'Средний') if race else 'Средний'

    @staticmethod
    def get_race_image_path(race_name: str) -> Optional[str]:
        race = _race_repo.get_by_name(race_name)
        return race.get('image_path') if race else None

    @staticmethod
    def has_subraces(race_name: str) -> bool:
        return _race_repo.has_subraces(race_name)

    @staticmethod
    def get_subraces(race_name: str) -> List[str]:
        return _race_repo.get_subrace_names(race_name)

    @staticmethod
    def get_subrace_description(race_name: str, subrace_name: str) -> str:
        subrace = _race_repo.get_subrace_by_name(race_name, subrace_name)
        return subrace.get('description', '') if subrace else ''

    @staticmethod
    def get_subrace_trait(race_name: str, subrace_name: str) -> str:
        subrace = _race_repo.get_subrace_by_name(race_name, subrace_name)
        return subrace.get('trait', '') if subrace else ''

    @staticmethod
    def get_class_equipment(class_name: str, choice: Optional[str] = None) -> List[Dict[str, Any]]:
        return _equipment_repo.get_class_equipment(class_name, choice)

    @staticmethod
    def get_fighting_styles_for_class(class_name: str) -> List[Dict[str, Any]]:
        return _fighting_style_repo.get_for_class(class_name)

    @staticmethod
    def get_all_invocations(level: int = 1) -> List[Dict[str, Any]]:
        return _invocation_repo.get_all(level)

    @staticmethod
    def auto_assign_masteries(weapon_name: str, class_name: str) -> List[str]:
        return _equipment_repo.auto_assign_masteries(weapon_name, class_name)

    @staticmethod
    def get_spells_grouped_by_category(class_name: str, is_cantrip: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        return _spell_repo.get_categories_for_class(class_name, is_cantrip)

    @staticmethod
    def get_spell_by_id(spell_id: int) -> Optional[Dict[str, Any]]:
        return _spell_repo.get_by_id(spell_id)

    # =========================================================
    # РАСЧЁТ ХАРАКТЕРИСТИК (ENGINE) - без расовых бонусов
    # =========================================================

    @staticmethod
    def calculate_stats(
        class_name: str,
        background_name: str,
        base_stats_dict: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        class_primary = _class_repo.get_primary_stats(class_name)
        background_stats = _background_repo.get_characteristics(background_name)

        if base_stats_dict:
            try:
                base_stats = AbilityScores.from_dict(base_stats_dict)
            except ValueError as e:
                logger.warning(f"Ошибка создания AbilityScores: {e}, используем стандартные")
                base_stats = AbilityScores.create_default()
        else:
            base_stats = AbilityScores.create_default()

        distributor = BackgroundBonusDistributor()
        bonuses = distributor.distribute(
            primary_stats=class_primary,
            background_stats=background_stats
        )
        final_stats = bonuses.apply_to(base_stats)
        return {
            'stats': final_stats.to_str_dict(),
            'bonuses': bonuses.to_str_dict(),
            'class_primary': class_primary,
            'background_stats': background_stats
        }

    @staticmethod
    def calculate_hp(
        class_name: str,
        constitution: int,
        level: int = 1,
        use_average: bool = True
    ) -> int:
        hit_die = _class_repo.get_hit_die(class_name)
        valid, msg = validate_level(level)
        if not valid:
            logger.warning(f"Невалидный уровень {level}: {msg}, используем уровень 1")
            level = 1
        valid, msg = validate_ability_score(constitution, "CON")
        if not valid:
            logger.warning(f"Невалидное значение CON {constitution}: {msg}, используем 10")
            constitution = 10
        method = HpCalculationMethod.AVERAGE if use_average else HpCalculationMethod.MAX
        hp = calculate_hp_at_level(hit_die, constitution, level, method)
        return max(1, hp)

    @staticmethod
    def calculate_ac(
        dexterity: int,
        armor_name: Optional[str] = None,
        has_shield: bool = False,
        class_name: Optional[str] = None,
        second_stat: Optional[int] = None
    ) -> int:
        valid, msg = validate_ability_score(dexterity, "DEX")
        if not valid:
            logger.warning(f"Невалидное значение DEX {dexterity}: {msg}, используем 10")
            dexterity = 10
        if not armor_name and class_name in ["Варвар", "Монах"] and second_stat is not None:
            valid_second, _ = validate_ability_score(second_stat, "CON" if class_name == "Варвар" else "WIS")
            if not valid_second:
                logger.warning(f"Невалидное значение second_stat {second_stat} для {class_name}, используем 10")
                second_stat = 10
            ac = calculate_unarmored_ac(class_name, dexterity, second_stat)
            if has_shield:
                ac += 2
            return ac
        if armor_name:
            ac = calculate_ac_with_armor(dexterity, armor_name, has_shield)
        else:
            ac = calculate_base_ac(dexterity)
            if has_shield:
                ac += 2
        return ac

    @staticmethod
    def calculate_proficiency_bonus(level: int) -> int:
        return calculate_proficiency_bonus(level)

    @staticmethod
    def format_stats_display(stats: Dict[str, int]) -> str:
        def modifier(stat_value: int) -> int:
            return hp_calculate_modifier(stat_value)
        return (f"💪 STR: {stats['STR']} ({modifier(stats['STR']):+d})\n"
                f"🤸 DEX: {stats['DEX']} ({modifier(stats['DEX']):+d})\n"
                f"🏋️ CON: {stats['CON']} ({modifier(stats['CON']):+d})\n"
                f"🧠 INT: {stats['INT']} ({modifier(stats['INT']):+d})\n"
                f"🧙 WIS: {stats['WIS']} ({modifier(stats['WIS']):+d})\n"
                f"✨ CHA: {stats['CHA']} ({modifier(stats['CHA']):+d})")

    @staticmethod
    def validate_character_stats(stats: Dict[str, int]) -> Tuple[bool, List[str]]:
        valid, msg = validate_all_ability_scores(stats)
        if not valid:
            return False, [msg]
        errors = []
        for stat, value in stats.items():
            valid, msg = validate_ability_score(value, stat)
            if not valid:
                errors.append(msg)
        return len(errors) == 0, errors

    @staticmethod
    def calculate_and_format_stats(
        class_name: str,
        background: str,
        base_stats_dict: Optional[Dict[str, int]] = None,
        equipment_choice: str = "A"
    ) -> Dict[str, Any]:
        if base_stats_dict is None:
            base_stats_dict = get_class_starting_stats(class_name, equipment_choice)
        stats_result = CharacterStatsService.calculate_stats(
            class_name=class_name,
            background_name=background,
            base_stats_dict=base_stats_dict
        )
        final_stats = stats_result['stats']
        constitution = final_stats.get('CON', 10)
        dexterity = final_stats.get('DEX', 10)
        hp = CharacterStatsService.calculate_hp(class_name, constitution, level=1)
        ac = CharacterStatsService.calculate_ac(dexterity, armor_name=None, class_name=class_name,
                                                 second_stat=constitution if class_name == "Варвар" else final_stats.get('WIS', 10))
        proficiency_bonus = CharacterStatsService.calculate_proficiency_bonus(1)
        stats_text = CharacterStatsService.format_stats_display(final_stats)
        bg_chars = stats_result['background_stats']
        return {
            'stats': final_stats,
            'stats_text': stats_text,
            'hp': hp,
            'ac': ac,
            'bg_chars': bg_chars,
            'proficiency_bonus': proficiency_bonus,
            'bonuses': stats_result['bonuses']
        }


class CharacterFinalizationService:
    """Сервис для подготовки и сохранения персонажа"""

    @staticmethod
    def prepare_character_data(
        state_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Подготавливает данные персонажа для сохранения.
        Получает ID сущностей через репозитории.
        """
        class_name = state_data.get('class_name')
        background = state_data.get('background')
        race = state_data.get('race')
        subrace = state_data.get('subrace')
        name = state_data.get('name')
        backstory = state_data.get('backstory', 'Нет истории')
        stats = state_data.get('final_stats', {})
        if not stats:
            stats = state_data.get('stats', {})

        # Получаем ID сущностей через репозитории
        class_data = _class_repo.get_by_name(class_name) if class_name else None
        class_id = class_data['id'] if class_data else None

        background_data = _background_repo.get_by_name(background) if background else None
        background_id = background_data['id'] if background_data else None

        race_data = _race_repo.get_by_name(race) if race else None
        race_id = race_data['id'] if race_data else None

        subrace_id = None
        if subrace and race_id:
            subrace_info = _race_repo.get_subrace_by_name(race, subrace)
            if subrace_info:
                subrace_id = subrace_info['id']

        # Заклинания
        selected_spells = []
        selector_data = state_data.get('spell_selector')
        if selector_data and isinstance(selector_data, dict) and 'class_name' in selector_data:
            try:
                from spell_selector import SpellSelector
                selector = SpellSelector.from_dict(selector_data)
                selected_spells = selector.get_all_selected_spells()
            except Exception as e:
                logger.warning(f"Ошибка восстановления селектора заклинаний: {e}")

        selected_masteries = state_data.get('selected_masteries', [])
        selected_fighting_style = state_data.get('selected_fighting_style')
        selected_invocations = state_data.get('selected_invocations', [])
        selected_weapon = state_data.get('selected_weapon')
        selected_armor = state_data.get('selected_armor')

        # Пересчёт HP и AC
        dexterity = stats.get('DEX', 10)
        constitution = stats.get('CON', 10)
        wisdom = stats.get('WIS', 10)
        hp = CharacterStatsService.calculate_hp(class_name, constitution, level=1)
        ac = CharacterStatsService.calculate_ac(dexterity, selected_armor, False, class_name,
                                                 constitution if class_name == "Варвар" else wisdom)

        # Навыки от предыстории
        bg_skills = background_data.get('skills', []) if background_data else []

        # Origin feat и alignment (уже есть)
        origin_feat = state_data.get('background_origin_feat', '')
        alignment = state_data.get('alignment', 'Нейтральный')

        # НОВЫЕ ПОЛЯ
        druid_order = state_data.get('druid_order')
        cleric_order = state_data.get('cleric_order')
        warlock_pact = state_data.get('warlock_pact')
        rogue_expertise = state_data.get('rogue_expertise', [])
        rogue_extra_language = state_data.get('rogue_extra_language')
        auto_spells = state_data.get('auto_spells', [])
        pact_tome_cantrips = state_data.get('pact_tome_cantrips', [])
        pact_tome_rituals = state_data.get('pact_tome_rituals', [])
        pact_blade_weapon = state_data.get('pact_blade_weapon')

        return {
            'user_id': user_id,
            'name': name,
            'class_id': class_id,
            'class_name': class_name,
            'background_id': background_id,
            'background': background,
            'race_id': race_id,
            'race': race,
            'subrace_id': subrace_id,
            'subrace': subrace,
            'stats': stats,
            'hp': hp,
            'ac': ac,
            'backstory': backstory,
            'selected_spells': selected_spells,
            'selected_masteries': selected_masteries,
            'selected_fighting_style': selected_fighting_style,
            'selected_invocations': selected_invocations,
            'selected_weapon': selected_weapon,
            'selected_armor': selected_armor,
            'selected_skills_bg': bg_skills,
            'origin_feat': origin_feat,
            'alignment': alignment,
            # Новые поля
            'druid_order': druid_order,
            'cleric_order': cleric_order,
            'warlock_pact': warlock_pact,
            'rogue_expertise': rogue_expertise,
            'rogue_extra_language': rogue_extra_language,
            'auto_spells': auto_spells,
            'pact_tome_cantrips': pact_tome_cantrips,
            'pact_tome_rituals': pact_tome_rituals,
            'pact_blade_weapon': pact_blade_weapon,
        }

    @staticmethod
    def save_character(character_data: Dict[str, Any]) -> int:
        """Сохраняет персонажа через репозиторий"""
        repo_data = {
            'user_id': character_data['user_id'],
            'name': character_data['name'],
            'race_id': character_data.get('race_id'),
            'subrace_id': character_data.get('subrace_id'),
            'class_id': character_data.get('class_id'),
            'background_id': character_data.get('background_id'),
            'level': 1,
            'experience': 0,
            'stats': character_data['stats'],
            'hp': character_data['hp'],
            'ac': character_data['ac'],
            'speed': 30,
            'selected_skills': character_data.get('selected_skills', []),
            'selected_masteries': character_data.get('selected_masteries', []),
            'selected_fighting_style': character_data.get('selected_fighting_style'),
            'selected_invocations': character_data.get('selected_invocations', []),
            'selected_spells': character_data.get('selected_spells', []),
            'selected_weapon': character_data.get('selected_weapon'),
            'selected_armor': character_data.get('selected_armor'),
            'backstory': character_data['backstory'],
            'image_file_id': character_data.get('image_file_id'),
            'origin_feat': character_data.get('origin_feat', ''),
            'alignment': character_data.get('alignment', 'Нейтральный'),
            # Новые поля
            'druid_order': character_data.get('druid_order'),
            'cleric_order': character_data.get('cleric_order'),
            'warlock_pact': character_data.get('warlock_pact'),
            'rogue_expertise': character_data.get('rogue_expertise', []),
            'rogue_extra_language': character_data.get('rogue_extra_language'),
            'auto_spells': character_data.get('auto_spells', []),
            'pact_tome_cantrips': character_data.get('pact_tome_cantrips', []),
            'pact_tome_rituals': character_data.get('pact_tome_rituals', []),
            'pact_blade_weapon': character_data.get('pact_blade_weapon'),
        }
        return _character_repo.create(repo_data)