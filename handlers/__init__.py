from functools import partial

from aiogram import Dispatcher, types
from aiogram.filters import Command, Filter

from filters.check_admin import IsAdmin
from filters.user_passed import UserPassedFilter

from .quiz import group_message_handler, poll_answer_handler, poll_handler
from .start import start_handler
from .message import message_handler, admin_handler_messages
from .custom_commands import (
    add_command_handler,
    add_text_handler,
    delete_command_handler,
    list_commands_handler,
    execute_custom_command,
    pass_command_handler,
    quiz_again_command_handler,
)


class IsNotBot(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return not message.from_user.is_bot


class ChatTypeGroup(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in ["group", "supergroup"]


def setup_handlers(dp: Dispatcher, bot, pool) -> None:
    """Регистрация хэндлеров для бота с использованием aiogram 3.

    Args:
        dp (Dispatcher): Объект диспетчера для маршрутизации событий.
        bot: Объект бота для взаимодействия с Telegram API.
        pool: Пул подключений к базе данных.
    """
    dp.message.register(
        partial(start_handler, bot=bot, pool=pool, dp=dp),
        Command(commands=["start"]),
    )

    dp.message.register(
        partial(group_message_handler, bot=bot, pool=pool),
        ChatTypeGroup(),
        IsNotBot(),
    )

    dp.message.register(
        partial(message_handler, bot=bot, pool=pool),
        ChatTypeGroup(),
        IsNotBot(),
        UserPassedFilter(pool=pool)
    )
    dp.message.register(
        partial(admin_handler_messages),
        ChatTypeGroup(),
        IsAdmin(),
    )

    dp.poll_answer.register(partial(poll_answer_handler, dp=dp, bot=bot, pool=pool))

    dp.poll.register(partial(poll_handler, dp=dp, bot=bot, pool=pool))

    dp.message.register(
        partial(add_command_handler, pool=pool),
        Command(commands=["addcommand"]),
        IsAdmin()
    )
    dp.message.register(
        partial(add_text_handler, pool=pool),
        Command(commands=["addtext"]),
        IsAdmin()
    )
    dp.message.register(
        partial(delete_command_handler, pool=pool),
        Command(commands=["del"]),
        IsAdmin()
    )
    dp.message.register(
        partial(list_commands_handler, pool=pool),
        Command(commands=["list"]),
    )

    dp.message.register(
        partial(pass_command_handler, pool=pool, dp=dp),
        Command(commands=["pass"]),
        IsAdmin(),
    )
    dp.message.register(
        partial(quiz_again_command_handler, pool=pool),
        Command(commands=["quiz-again"]),
        IsAdmin(),
    )

    dp.message.register(
        partial(execute_custom_command, pool=pool),
        lambda message: message.text and message.text.startswith("/"),
    )
