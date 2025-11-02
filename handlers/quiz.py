import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from config import config, questions, dialogs
from database import (
    check_user_passed,
    check_user_banned,
    mark_user_passed,
    PoolType,
    get_active_poll,
    remove_active_poll,
)
from utils.moderation import ban_user_after_timeout
from utils.message_utils import delete_message
from .states import UserState
from .language import get_user_language


async def group_message_handler(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
    pool: PoolType,
    **kwargs,
) -> None:
    """Обработка первого сообщения пользователя в группе."""
    if message.chat.id != config.ALLOWED_CHAT_ID or message.from_user.is_bot:
        return

    user = message.from_user
    passed = await check_user_passed(pool, user.id)
    banned = await check_user_banned(pool, user.id)
    
    # Если пользователь уже прошел квиз или забанен - пропускаем
    if passed or banned:
        return
    
    # Получаем состояние пользователя
    user_state = await state.get_state()
    
    # Если это уже не первое сообщение - удаляем
    if user_state is not None:
        await delete_message(bot, message.chat.id, message.message_id, delay=0)
        return
    
    lang = get_user_language(user)
    thread_id = message.message_thread_id
    
    await state.update_data(
        language=lang,
        thread_id=thread_id,
        group_chat_id=message.chat.id,
        first_message_id=message.message_id,
    )
    
    await state.set_state(UserState.answering_quiz)
    
    button_text = dialogs["quiz_button"][lang]
    instruction_text = dialogs["quiz_instruction"][lang]
    
    logging.info(f"First message from user {user.id} in group {message.chat.id}")

    bot_username = (await bot.get_me()).username
    user_mention = user.mention_html()
    greeting_text = f"{user_mention}, {instruction_text}"
    
    quiz_button_msg = await bot.send_message(
        chat_id=message.chat.id,
        text=greeting_text,
        parse_mode="HTML",
        reply_markup=types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text=button_text,
                        url=f"https://t.me/{bot_username}?start=quiz_{user.id}_{lang}_{message.chat.id}",
                    )
                ]
            ]
        ),
        reply_parameters=types.ReplyParameters(message_id=message.message_id),
        message_thread_id=thread_id,
    )

    await state.update_data(bot_messages=[quiz_button_msg.message_id])


async def poll_answer_handler(
    poll_answer: types.PollAnswer,
    dp: Dispatcher,
    bot: Bot,
    pool: PoolType,
) -> None:
    """Обработка ответа на опрос в ЛС."""
    poll_id = poll_answer.poll_id
    user_id = poll_answer.user.id

    poll_data = await get_active_poll(pool, poll_id)
    if not poll_data or poll_data["user_id"] != user_id:
        return

    chat_id = poll_data["chat_id"]
    message_id = poll_data["message_id"]

    state = dp.fsm.get_context(bot=bot, chat_id=chat_id, user_id=user_id)
    user_data = await state.get_data()

    if user_data.get("quiz_poll_id") != poll_id:
        return

    selected_option = poll_answer.option_ids[0]
    correct_index = user_data["correct_index"]
    lang = user_data["language"]

    await state.update_data(has_answered=True)

    if selected_option == correct_index:
        await state.set_state(UserState.completed)
        await mark_user_passed(pool, user_id)
        result_msg = await bot.send_message(
            chat_id=chat_id,
            text=f"✅ {dialogs['correct'][lang]}",
            parse_mode="HTML",
        )
        group_chat_id = user_data.get("group_chat_id")
        bot_messages = user_data.get("bot_messages", [])
        greeting_message_id = user_data.get("greeting_message_id")
        for msg_id in bot_messages:
            if group_chat_id:
                asyncio.create_task(
                    delete_message(
                        bot, group_chat_id, msg_id, config.MESSAGE_DELETE_DELAY_CORRECT
                    )
                )
        if greeting_message_id:
            asyncio.create_task(
                delete_message(
                    bot,
                    chat_id,
                    greeting_message_id,
                    config.MESSAGE_DELETE_DELAY_CORRECT,
                )
            )
        asyncio.create_task(
            delete_message(
                bot, chat_id, result_msg.message_id, config.MESSAGE_DELETE_DELAY_CORRECT
            )
        )
        logging.info(f"Пользователь {user_id} ответил правильно в ЛС")

        group_state = dp.fsm.get_context(
            bot=bot, chat_id=group_chat_id, user_id=user_id
        )
        await group_state.set_state(UserState.completed)
        logging.info(
            f"Установлено состояние completed для пользователя {user_id} в чате {group_chat_id}"
        )
    else:
        combined_message = (
            f"❌ {dialogs['incorrect'][lang].format(name=poll_answer.user.mention_html())} "
            f"{dialogs['blocked_message'][lang]}"
        )
        result_msg = await bot.send_message(
            chat_id=chat_id,
            text=combined_message,
            parse_mode="HTML",
        )
        group_chat_id = user_data.get("group_chat_id")
        first_message_id = user_data.get("first_message_id")
        bot_messages = user_data.get("bot_messages", [])
        quiz_message_id = user_data.get("quiz_message_id")
        greeting_message_id = user_data.get("greeting_message_id")

        if first_message_id and group_chat_id:
            asyncio.create_task(
                delete_message(bot, group_chat_id, first_message_id, delay=0)
            )
        for msg_id in bot_messages:
            if group_chat_id:
                asyncio.create_task(delete_message(bot, group_chat_id, msg_id, delay=0))
        if greeting_message_id:
            asyncio.create_task(
                delete_message(
                    bot,
                    chat_id,
                    greeting_message_id,
                    config.MESSAGE_DELETE_DELAY_INCORRECT,
                )
            )
        if quiz_message_id:
            asyncio.create_task(
                delete_message(
                    bot, user_id, quiz_message_id, config.MESSAGE_DELETE_DELAY_INCORRECT
                )
            )
        asyncio.create_task(
            delete_message(
                bot,
                chat_id,
                result_msg.message_id,
                config.MESSAGE_DELETE_DELAY_INCORRECT,
            )
        )

        if group_chat_id:
            await ban_user_after_timeout(bot, group_chat_id, user_id, pool)
            logging.info(f"Пользователь {user_id} забанен из-за неправильного ответа")

        group_state = dp.fsm.get_context(
            bot=bot, chat_id=group_chat_id, user_id=user_id
        )
        await group_state.clear()
        logging.info(
            f"Очищено состояние группы для пользователя {user_id} в чате {group_chat_id}"
        )
        await state.clear()

    try:
        await bot.delete_message(chat_id, message_id)
    except TelegramBadRequest:
        logging.warning(f"Не удалось удалить опрос {poll_id} в чате {chat_id}")
    await remove_active_poll(pool, poll_id)


async def poll_handler(
    poll: types.Poll,
    dp: Dispatcher,
    bot: Bot,
    pool: PoolType,
) -> None:
    """Обработка закрытия опроса (таймаут) в ЛС как запасной вариант."""
    if not poll.is_closed:
        return

    poll_data = await get_active_poll(pool, poll.id)
    if not poll_data:
        return

    user_id = poll_data["user_id"]
    chat_id = poll_data["chat_id"]
    message_id = poll_data["message_id"]

    state = dp.fsm.get_context(bot=bot, chat_id=chat_id, user_id=user_id)
    user_data = await state.get_data()

    if not user_data.get("has_answered", False):
        lang = user_data.get("language", "en")
        user_link = f'<a href="tg://user?id={user_id}">{user_id}</a>'
        combined_message = (
            f"⏰ {dialogs['timeout'][lang].format(name=user_link)} "
            f"{dialogs['blocked_message'][lang]}"
        )
        first_message_id = user_data.get("first_message_id")
        timeout_msg = await bot.send_message(
            chat_id,
            combined_message,
            parse_mode="HTML",
            reply_parameters=types.ReplyParameters(message_id=first_message_id) if first_message_id else None,
        )
        group_chat_id = user_data.get("group_chat_id")
        first_message_id = user_data.get("first_message_id")
        bot_messages = user_data.get("bot_messages", [])
        quiz_message_id = user_data.get("quiz_message_id")
        greeting_message_id = user_data.get("greeting_message_id")

        if first_message_id and group_chat_id:
            asyncio.create_task(
                delete_message(bot, group_chat_id, first_message_id, delay=0)
            )
        for msg_id in bot_messages:
            if group_chat_id:
                asyncio.create_task(delete_message(bot, group_chat_id, msg_id, delay=0))
        if greeting_message_id:
            asyncio.create_task(
                delete_message(
                    bot,
                    chat_id,
                    greeting_message_id,
                    config.MESSAGE_DELETE_DELAY_TIMEOUT,
                )
            )
        if quiz_message_id:
            asyncio.create_task(
                delete_message(
                    bot, user_id, quiz_message_id, config.MESSAGE_DELETE_DELAY_TIMEOUT
                )
            )
        asyncio.create_task(
            delete_message(
                bot,
                chat_id,
                timeout_msg.message_id,
                config.MESSAGE_DELETE_DELAY_TIMEOUT,
            )
        )

        if group_chat_id:
            await ban_user_after_timeout(bot, group_chat_id, user_id, pool)
            logging.info(
                f"Пользователь {user_id} забанен из-за таймаута опроса (запасной обработчик)"
            )

        group_state = dp.fsm.get_context(
            bot=bot, chat_id=group_chat_id, user_id=user_id
        )
        await group_state.clear()
        logging.info(
            f"Очищено состояние группы для пользователя {user_id} в чате {group_chat_id}"
        )
        await state.clear()

    try:
        await bot.delete_message(chat_id, message_id)
    except TelegramBadRequest:
        logging.warning(f"Не удалось удалить опрос {poll.id} в чате {chat_id}")
    await remove_active_poll(pool, poll.id)
