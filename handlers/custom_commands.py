import html
import logging
from contextlib import suppress

from aiogram import types, Dispatcher, Bot

from database import PoolType, add_custom_command, update_command_text, delete_custom_command, get_all_custom_commands, \
    delete_active_pool_by_user_id, delete_user_from_passed, mark_user_passed


async def add_command_handler(message: types.Message, pool: PoolType) -> None:
    """Обработка команды /addcommand для создания новой команды."""
    args = message.text.split(maxsplit=2)
    if len(args) != 3:
        await message.reply("Использование: /addcommand /команда аргумент")
        return

    command_name = args[1].strip()
    argument = args[2].strip()

    if not command_name.startswith("/"):
        await message.reply("Команда должна начинаться с '/'")
        return

    success = await add_custom_command(pool, command_name, argument)
    if success:
        await message.reply(f"Команда {command_name} с аргументом {argument} успешно добавлена.")
    else:
        await message.reply(f"Команда {command_name} с аргументом {argument} уже существует.")

async def add_text_handler(message: types.Message, pool: PoolType) -> None:
    """Обработка команды /addtext для добавления текста к команде."""
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.reply("Использование: /addtext /команда аргумент текст")
        return

    command_name = args[1].strip()
    argument = args[2].strip()
    response_text = args[3].strip()

    success = await update_command_text(pool, command_name, argument, response_text)
    if success:
        await message.reply(f"Текст для команды {command_name} с аргументом {argument} успешно добавлен.")
    else:
        await message.reply(f"Команда {command_name} с аргументом {argument} не найдена.")


async def delete_command_handler(message: types.Message, pool: PoolType) -> None:
    """Обработка команды /del для удаления команды."""
    args = message.text.split(maxsplit=2)
    if len(args) != 3:
        await message.reply("Использование: /del /команда аргумент")
        return

    command_name = args[1].strip()
    argument = args[2].strip()

    success = await delete_custom_command(pool, command_name, argument)
    if success:
        await message.reply(f"Команда {command_name} с аргументом {argument} успешно удалена.")
    else:
        await message.reply(f"Команда {command_name} с аргументом {argument} не найдена.")


async def list_commands_handler(message: types.Message, pool: PoolType) -> None:
    """Обработка команды /list для отображения всех команд и их аргументов."""
    commands = await get_all_custom_commands(pool)
    if not commands:
        await message.reply("Нет доступных команд.")
        return

    response = "Список команд:\n"
    for cmd in commands:
        response += f"{cmd['command_name']} {cmd['argument']}\n"
    await message.reply(response)


async def execute_custom_command(message: types.Message, pool: PoolType) -> None:
    """Обработка пользовательских команд."""
    if not message.text:
        return

    args = message.text.split(maxsplit=2)
    command_name = args[0].strip()
    argument = args[1].strip() if len(args) > 1 else ""

    logging.info(f"Проверка команды: {command_name} с аргументом: {argument}")

    commands = await get_all_custom_commands(pool)
    for cmd in commands:
        if cmd["command_name"] == command_name and cmd["argument"] == argument and cmd["response_text"]:
            # Проверяем, есть ли процитированное сообщение
            if message.reply_to_message and message.reply_to_message.from_user:
                target_user_id = message.reply_to_message.from_user.id
                target_chat_id = message.chat.id  # Отправляем в тот же чат
                try:
                    # Пробуем отправить с reply_to_message_id
                    await message.bot.send_message(
                        chat_id=target_chat_id,
                        text=cmd["response_text"],
                        reply_to_message_id=message.reply_to_message.message_id
                    )
                    logging.info(f"Ответ отправлен процитированному пользователю {target_user_id} в чате {target_chat_id} для команды {command_name} с аргументом {argument}")
                except Exception as e:
                    if "message to be replied not found" in str(e):
                        # Если сообщение не найдено, отправляем без reply_to_message_id
                        try:
                            await message.bot.send_message(
                                chat_id=target_chat_id,
                                text=cmd["response_text"]
                            )
                            logging.info(f"Ответ отправлен без привязки к сообщению пользователю {target_user_id} в чате {target_chat_id}")
                        except Exception as e2:
                            logging.error(f"Не удалось отправить сообщение пользователю {target_user_id} без привязки: {e2}")
                            await message.reply("Не удалось отправить ответ процитированному пользователю.")
                    else:
                        logging.error(f"Не удалось отправить сообщение пользователю {target_user_id}: {e}")
                        await message.reply("Не удалось отправить ответ процитированному пользователю.")
            else:
                await message.reply(cmd["response_text"])
                logging.info(f"Команда {command_name} с аргументом {argument} выполнена для текущего пользователя")
            return
    logging.info(f"Команда {command_name} с аргументом {argument} не найдена")


async def pass_command_handler(message: types.Message, pool: PoolType,
                               dp: Dispatcher, bot: Bot
                               ) -> None:
    if not message.reply_to_message:
        await message.answer("Используйте команду реплеем на сообщение")
        return

    user_id = message.reply_to_message.from_user.id
    user_state = dp.fsm.get_context(
        bot=bot, chat_id=message.chat.id, user_id=user_id
    )
    data = await user_state.get_data()
    if data.get("bot_messages"):
        for message_id in data["bot_messages"]:
            with suppress(Exception):
                await bot.delete_message(message.chat.id, message_id)
    await user_state.clear()
    await delete_active_pool_by_user_id(pool, message.chat.id, user_id)
    await mark_user_passed(pool, user_id)
    await message.answer(f"Пользователь {html.escape(message.from_user.first_name)} пропущен без квиза")


async def quiz_again_command_handler(message: types.Message, pool: PoolType) -> None:
    if not message.reply_to_message:
        await message.answer("Используйте команду реплеем на сообщение")
        return

    user_id = message.reply_to_message.from_user.id
    await delete_user_from_passed(pool, user_id)
    await message.answer(f"Пользователь {html.escape(message.from_user.first_name)} забыт")

