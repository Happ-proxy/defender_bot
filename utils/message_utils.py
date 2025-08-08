import asyncio
import json
from functools import lru_cache

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
import logging
import pathlib

from utils.ttl import admin_replies


@lru_cache()
def read_file_args_docs():
    path = pathlib.Path(__file__).parent.parent / "args_docs.json"
    with open(path, 'r', encoding='utf-8') as file:
        return json.load(file)


async def delete_message(bot: Bot, chat_id: int, message_id: int, delay: int) -> None:
    """Удаление сообщения с задержкой."""
    logging.info(message_id)
    logging.info(admin_replies)
    if message_id in admin_replies.keys():
        return
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id, message_id)
        logging.info(f"Удалено сообщение {message_id} в чате {chat_id}")
    except TelegramBadRequest:
        logging.warning(f"Не удалось удалить сообщение {message_id} в чате {chat_id}")


def get_docs_argument(arg: str, lang: str = "ru") -> str:
    args_docs = read_file_args_docs()
    args_docs = args_docs.get("args")
    answer = args_docs.get(arg)
    if answer is None:
        return None
    return answer.get(lang)


def get_docs_arguments() -> list:
    args_docs = read_file_args_docs()
    args_docs = args_docs.get("args")
    return [args for args in args_docs.keys()]
