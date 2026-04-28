# repositories/base_repository.py
"""
Базовый репозиторий для работы с базой данных
Предоставляет общие методы для всех репозиториев
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

from db import get_connection

logger = logging.getLogger(__name__)


class BaseRepository:
    """Базовый класс для всех репозиториев"""

    def __init__(self):
        self._table_name = None  # Должен быть переопределён в наследниках

    @contextmanager
    def _get_cursor(self):
        """Контекстный менеджер для получения курсора БД"""
        with get_connection() as conn:
            with conn.cursor() as cur:
                yield cur

    def _execute_query(self, query: str, params: tuple = ()) -> None:
        """Выполняет запрос без возврата результата"""
        with self._get_cursor() as cur:
            cur.execute(query, params)

    def _fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Выполняет запрос и возвращает одну строку в виде словаря"""
        from psycopg2.extras import RealDictCursor

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchone()

    def _fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Выполняет запрос и возвращает все строки в виде списка словарей"""
        from psycopg2.extras import RealDictCursor

        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return cur.fetchall()

    def _fetch_value(self, query: str, params: tuple = ()) -> Optional[Any]:
        """Выполняет запрос и возвращает значение первой колонки первой строки"""
        with self._get_cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return row[0] if row else None

    def exists(self, **conditions) -> bool:
        """Проверяет существование записи по условиям"""
        if not self._table_name:
            raise NotImplementedError("Table name not set")

        where_clause = " AND ".join([f"{k} = %s" for k in conditions.keys()])
        query = f"SELECT 1 FROM {self._table_name} WHERE {where_clause} LIMIT 1"
        result = self._fetch_value(query, tuple(conditions.values()))
        return result is not None

    def count(self, **conditions) -> int:
        """Возвращает количество записей, удовлетворяющих условиям"""
        if not self._table_name:
            raise NotImplementedError("Table name not set")

        if conditions:
            where_clause = " AND ".join([f"{k} = %s" for k in conditions.keys()])
            query = f"SELECT COUNT(*) FROM {self._table_name} WHERE {where_clause}"
            params = tuple(conditions.values())
        else:
            query = f"SELECT COUNT(*) FROM {self._table_name}"
            params = ()

        return self._fetch_value(query, params) or 0