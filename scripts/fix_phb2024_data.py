#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/fix_phb2024_data.py

Идемпотентный скрипт исправления данных в реальной (удалённой) БД для
приведения значений к D&D 5.5e (2024) PHB. Скрипт безопасно запускать
несколько раз — он использует UPDATE ... WHERE и INSERT ... ON CONFLICT
DO NOTHING / DO UPDATE.

Использование (с любой машины, имеющей сетевой доступ к Postgres):

    python scripts/fix_phb2024_data.py

Параметры подключения берутся из .env (DB_HOST/DB_PORT/DB_NAME/DB_USER/
DB_PASSWORD), как и в остальных скриптах проекта.

Скрипт хранит список «фиксов»: каждый — функция(conn) -> int (число
изменённых строк). Главная функция выводит сводку: сколько строк было
изменено каждым фиксом и общее количество.

Этапы из мастер-списка несоответствий:
- [Этап 1] #4   Chain Mail (Кольчужный доспех) ac_base 14 -> 16
- [Этап 3] #24  Splint     (Пластинчатый доспех) ac_base 15 -> 17
- [Этап 4] #34  Breastplate alias («Нагрудник» = Кираса AC 14 Medium)
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Callable, List, Tuple

import psycopg2
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("fix_phb2024")


# =========================================================
# ПОДКЛЮЧЕНИЕ
# =========================================================

def _connect():
    """Создаёт соединение с БД по параметрам из .env."""
    load_dotenv()
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "dnd_bot"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )
    conn.autocommit = False
    return conn


# =========================================================
# ИНДИВИДУАЛЬНЫЕ ФИКСЫ
# =========================================================
# Каждый фикс — это функция, принимающая соединение и возвращающая число
# реально изменённых строк. Внутри она делает UPDATE / INSERT строго
# идемпотентно (UPDATE ... WHERE текущее_значение_неверно).

def fix_chain_mail_ac(conn) -> int:
    """
    Пункт #4: Chain Mail должен иметь AC 16 по PHB 2024 (тяжёлая броня).
    В seed_data сейчас лежит ac_base = 14 — занижает AC у Воина и Паладина
    на 2 на старте.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE armor
               SET ac_base = 16,
                   ac_modifier = 'none'
             WHERE name = 'Кольчужный доспех'
               AND (ac_base <> 16 OR ac_modifier <> 'none')
            """
        )
        return cur.rowcount


def fix_splint_ac(conn) -> int:
    """
    Пункт #24: Splint Armor (Пластинчатый доспех) — AC 17 по PHB 2024
    (тяжёлая броня). В seed_data ac_base=15 — занижает AC.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE armor
               SET ac_base = 17,
                   ac_modifier = 'none'
             WHERE name = 'Пластинчатый доспех'
               AND (ac_base <> 17 OR ac_modifier <> 'none')
            """
        )
        return cur.rowcount


def add_breastplate_alias(conn) -> int:
    """
    Пункт #34: По мастер-списку «Нагрудник и Полулаты отсутствуют».
    На самом деле в seed_data они есть под другими именами:
      Кираса   = Breastplate (AC 14, Medium)
      Полулаты = Half Plate  (AC 15, Medium)
    Добавляем явный алиас «Нагрудник» с идентичными параметрами Кирасы,
    чтобы любой пользователь / шаблон, ищущий именно это имя, нашёл строку.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO armor (name, ac_base, ac_modifier)
            VALUES ('Нагрудник', 14, 'dex_max2')
            ON CONFLICT (name) DO NOTHING
            """
        )
        return cur.rowcount


# Список фиксов в порядке применения. Каждый элемент — (имя, функция).
FIXES: List[Tuple[str, Callable]] = [
    ("#4  Chain Mail AC 14→16 (Heavy)",       fix_chain_mail_ac),
    ("#24 Splint Armor AC 15→17 (Heavy)",     fix_splint_ac),
    ("#34 Breastplate alias 'Нагрудник'",     add_breastplate_alias),
]


# =========================================================
# ВХОДНАЯ ТОЧКА
# =========================================================

def main() -> int:
    logger.info("=" * 60)
    logger.info("FIX_PHB2024_DATA — запуск")
    logger.info("=" * 60)

    try:
        conn = _connect()
    except Exception as exc:
        logger.error("Не удалось подключиться к БД: %s", exc)
        return 1

    total_changed = 0
    failed: List[str] = []

    try:
        for name, fix in FIXES:
            try:
                changed = fix(conn)
                total_changed += changed
                logger.info("  ✅ %-50s → строк изменено: %d", name, changed)
            except Exception as exc:
                conn.rollback()
                failed.append(f"{name}: {exc}")
                logger.error("  ❌ %-50s → ОШИБКА: %s", name, exc)
        conn.commit()
    finally:
        conn.close()

    logger.info("-" * 60)
    if failed:
        logger.error("Завершено с ошибками: %d", len(failed))
        for line in failed:
            logger.error("   • %s", line)
        return 2

    logger.info("✅ Готово. Всего изменено строк: %d", total_changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
