from functools import partial

from aiogram import Dispatcher, types
from aiogram.filters import Command, ChatMemberUpdatedFilter, JOIN_TRANSITION, Filter

from filters.user_passed import UserPassedFilter

from .language import language_selection_handler, language_callback_handler
from .quiz import group_message_handler, poll_answer_handler, poll_handler
from .start import start_handler
from .message import message_handler
from .custom_commands import add_command_handler, add_text_handler, delete_command_handler, list_commands_handler, \
    execute_custom_command, pass_command_handler


# Пользовательский фильтр для проверки, что отправитель не бот
class IsNotBot(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return not message.from_user.is_bot


# Пользовательский фильтр для проверки типа чата (группа или супергруппа)
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
    # Команда /start
    dp.message.register(
        partial(start_handler, bot=bot, pool=pool, dp=dp),
        Command(commands=["start"]),
    )

    # Присоединение участника к чату
    dp.chat_member.register(
        partial(group_message_handler, bot=bot, pool=pool),
        ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION),
    )

    # Callback-запросы для выбора языка
    dp.callback_query.register(
        partial(language_callback_handler, pool=pool),
        lambda c: c.data.startswith("lang_"),
    )

    # Сообщения в группах и супергруппах (не от ботов)
    dp.message.register(
        partial(message_handler, bot=bot, pool=pool),
        ChatTypeGroup(),
        IsNotBot(),
        UserPassedFilter(pool=pool)
    )

    # Ответы на опросы
    dp.poll_answer.register(partial(poll_answer_handler, dp=dp, bot=bot, pool=pool))

    # События опросов
    dp.poll.register(partial(poll_handler, dp=dp, bot=bot, pool=pool))

    # Команды для управления пользовательскими командами
    dp.message.register(
        partial(add_command_handler, pool=pool),
        Command(commands=["addcommand"]),
    )
    dp.message.register(
        partial(add_text_handler, pool=pool),
        Command(commands=["addtext"]),
    )
    dp.message.register(
        partial(delete_command_handler, pool=pool),
        Command(commands=["del"]),
    )
    dp.message.register(
        partial(list_commands_handler, pool=pool),
        Command(commands=["list"]),
    )

    dp.message.register(
        partial(pass_command_handler, pool=pool),
        Command(commands=["pass"]),
    )

    # Обработка пользовательских команд
    dp.message.register(
        partial(execute_custom_command, pool=pool),
        lambda message: message.text and message.text.startswith("/"),
    )
