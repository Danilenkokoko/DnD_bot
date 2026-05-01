# utils/message_utils.py
import logging
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)

async def delete_previous(state: FSMContext, bot, chat_id: int):
    """Удаляет предыдущее служебное сообщение, если оно сохранено."""
    data = await state.get_data()
    prev_msg_id = data.get("last_bot_message_id")
    if prev_msg_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=prev_msg_id)
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение {prev_msg_id}: {e}")

async def send_new(state: FSMContext, message: Message, text: str, reply_markup=None):
    """Отправляет новое сообщение, удаляя предыдущее, и сохраняет его ID."""
    await delete_previous(state, message.bot, message.chat.id)
    new_msg = await message.answer(text, reply_markup=reply_markup, parse_mode=None)
    await state.update_data(last_bot_message_id=new_msg.message_id)
    return new_msg

async def send_new_from_callback(callback: CallbackQuery, state: FSMContext, text: str, reply_markup=None):
    """Отправляет новое сообщение из callback, удаляя предыдущее."""
    await delete_previous(state, callback.bot, callback.message.chat.id)
    new_msg = await callback.message.answer(text, reply_markup=reply_markup, parse_mode=None)
    await state.update_data(last_bot_message_id=new_msg.message_id)
    return new_msg