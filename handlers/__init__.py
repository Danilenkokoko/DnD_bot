# handlers/__init__.py
"""
Обработчики Telegram бота
"""

from handlers.character_handlers import router as character_router

__all__ = ['character_router']