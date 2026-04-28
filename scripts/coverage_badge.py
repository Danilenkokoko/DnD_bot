#!/usr/bin/env python3
# scripts/coverage_badge.py
"""
Генератор бейджа покрытия кода для README.md
"""

import json
import os
import sys
from typing import Optional


def get_coverage_from_json(filepath: str = "reports/coverage_full.json") -> Optional[float]:
    """
    Извлекает процент покрытия из JSON отчёта

    Args:
        filepath: путь к JSON файлу

    Returns:
        Optional[float]: процент покрытия или None при ошибке
    """
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('totals', {}).get('percent_covered_display', 0)
    except (json.JSONDecodeError, KeyError):
        return None


def get_coverage_color(percentage: float) -> str:
    """
    Возвращает цвет для бейджа в зависимости от процента покрытия

    Args:
        percentage: процент покрытия

    Returns:
        str: цвет в формате hex
    """
    if percentage >= 90:
        return "#4c1"  # зелёный
    elif percentage >= 80:
        return "#97ca00"  # жёлто-зелёный
    elif percentage >= 70:
        return "#dfb317"  # жёлтый
    elif percentage >= 60:
        return "#fe7a37"  # оранжевый
    else:
        return "#e05d44"  # красный


def generate_badge(percentage: float) -> str:
    """
    Генерирует HTML код для бейджа

    Args:
        percentage: процент покрытия

    Returns:
        str: HTML код бейджа
    """
    color = get_coverage_color(percentage)
    return f'<img src="https://img.shields.io/badge/coverage-{percentage:.1f}%25-{color}" alt="Coverage">'


def main():
    """Основная функция"""
    coverage = get_coverage_from_json()

    if coverage is None:
        print("❌ Не удалось получить данные о покрытии", file=sys.stderr)
        sys.exit(1)

    badge = generate_badge(coverage)
    print(f"✅ Coverage: {coverage:.1f}%")
    print(f"\nБейдж для README.md:\n{badge}")


if __name__ == "__main__":
    main()