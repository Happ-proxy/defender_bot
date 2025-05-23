import logging

from aiogram import types, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext

from config import config
from database import check_user_passed
from utils.message_utils import get_docs_argument, get_docs_arguments
from .states import UserState
from .language import language_selection_handler


async def docs_handler(message: types.Message, command: CommandObject, bot: Bot):
    args = command.args

    if args is None:
        arguments = get_docs_arguments()
        text = "\n".join(arguments)
        await message.answer(text)
        return
    args = args.split()
    if len(args) == 0 or len(args) > 2:
        return
    langs = ["ru", "en"]
    lang = "ru"
    docs_command = args[0]
    if len(args) == 2:
        lang = args[1]
        if lang not in langs:
            return

    answer = get_docs_argument(docs_command, lang)
    if answer is None:
        return
    message_to_reply = None
    if message.reply_to_message is not None:
        message_to_reply = message.reply_to_message.message_id
    await bot.send_message(
        text=answer,
        chat_id=message.chat.id,
        reply_to_message_id=message_to_reply)


async def message_handler(
        message: types.Message, state: FSMContext, bot: Bot, pool
) -> None:
    """Обработка сообщений пользователя."""
    if message.from_user.is_bot or message.chat.id != config.ALLOWED_CHAT_ID:
        return

    current_state = await state.get_state()

    # Сохраняем ID первого сообщения пользователя
    user_data = await state.get_data()
    if not user_data.get("first_message_id"):
        await state.update_data(first_message_id=message.message_id)

    if current_state == UserState.waiting_for_language:
        try:
            await bot.delete_message(message.chat.id, message.message_id)
            logging.info(
                f"Удалено сообщение {message.message_id} во время выбора языка"
            )
        except TelegramBadRequest:
            logging.warning(f"Не удалось удалить сообщение {message.message_id}")
        return

    # Удаляем сообщения во время квиза
    elif current_state == UserState.answering_quiz:
        try:
            await bot.delete_message(message.chat.id, message.message_id)
            logging.info(f"Удалено сообщение {message.message_id} во время квиза")
        except TelegramBadRequest:
            logging.warning(f"Не удалось удалить сообщение {message.message_id}")
        return

    if current_state in [UserState.waiting_for_language, UserState.answering_quiz]:
        return

    await language_selection_handler(message, state, bot, pool)
