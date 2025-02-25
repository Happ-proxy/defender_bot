from functools import partial

from aiogram import Dispatcher
from aiogram.filters import Command, ChatMemberUpdatedFilter, JOIN_TRANSITION

from .language import language_selection_handler, language_callback_handler
from .quiz import group_message_handler, quiz_callback_handler
from .start import start_handler


def setup_handlers(dp: Dispatcher, bot, pool) -> None:
    """Регистрация всех хэндлеров для бота с передачей bot и pool."""
    dp.message.register(start_handler, Command(commands=["start"]))
    dp.chat_member.register(
        partial(group_message_handler, bot=bot, pool=pool),
        ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION),
    )
    dp.message.register(
        partial(language_selection_handler, bot=bot, pool=pool),
        lambda m: m.chat.type in ["group", "supergroup"],
    )
    dp.callback_query.register(
        partial(language_callback_handler, pool=pool),
        lambda c: c.data.startswith("lang_"),
    )
    dp.callback_query.register(
        partial(quiz_callback_handler, pool=pool),
        lambda c: c.data.startswith("quiz_"),
    )