# handlers/__init__.py
"""
Обработчики Telegram бота
"""

from handlers.character_handlers import router as character_router

# Если в будущем появится роутер для заклинаний, можно добавить:
# from handlers.spell_handlers import router as spell_router

__all__ = ['character_router']