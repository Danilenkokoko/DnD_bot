#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Проверка доступных заклинаний для каждого класса D&D 5.5e.
Выводит заговоры (cantrips) и заклинания 1 уровня, доступные для выбора.
"""

import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from repositories.class_repository import ClassRepository
from repositories.spell_repository import SpellRepository


def main():
    class_repo = ClassRepository()
    spell_repo = SpellRepository()

    classes = class_repo.get_all_names()
    print("=" * 80)
    print("ПРОВЕРКА ДОСТУПНЫХ ЗАКЛИНАНИЙ ДЛЯ КЛАССОВ")
    print("=" * 80)

    for class_name in classes:
        class_data = class_repo.get_by_name(class_name)
        cantrips_required = class_data.get('cantrips_count', 0) if class_data else 0
        level1_required = class_data.get('spells_count_level1', 0) if class_data else 0

        print(f"\n📚 КЛАСС: {class_name}")
        print(f"   Должен выбрать заговоров: {cantrips_required}")
        print(f"   Должен выбрать заклинаний 1 уровня: {level1_required}")

        # Заговоры
        cantrips = spell_repo.get_cantrips_for_class(class_name)
        print(f"\n   📖 ЗАГОВОРЫ (доступно: {len(cantrips)}):")
        if cantrips:
            by_cat = defaultdict(list)
            for s in cantrips:
                cat = s.get('category', 'Прочее')
                by_cat[cat].append(s['name'])
            for cat, names in sorted(by_cat.items()):
                print(f"      [{cat}] ({len(names)}): {', '.join(names)}")
        else:
            print("      (нет)")

        # Заклинания 1 уровня
        level1_spells = spell_repo.get_level1_spells_for_class(class_name)
        print(f"\n   🔮 ЗАКЛИНАНИЯ 1 УРОВНЯ (доступно: {len(level1_spells)}):")
        if level1_spells:
            by_cat = defaultdict(list)
            for s in level1_spells:
                cat = s.get('category', 'Прочее')
                by_cat[cat].append(s['name'])
            for cat, names in sorted(by_cat.items()):
                print(f"      [{cat}] ({len(names)}): {', '.join(names)}")
        else:
            print("      (нет)")

        # Предупреждения о нехватке
        if cantrips_required > len(cantrips):
            print(f"   ⚠️ ВНИМАНИЕ: требуется {cantrips_required} заговоров, доступно только {len(cantrips)}")
        if level1_required > len(level1_spells):
            print(f"   ⚠️ ВНИМАНИЕ: требуется {level1_required} заклинаний 1 уровня, доступно только {len(level1_spells)}")

    print("\n" + "=" * 80)
    print("ПРОВЕРКА ЗАВЕРШЕНА")


if __name__ == "__main__":
    main()