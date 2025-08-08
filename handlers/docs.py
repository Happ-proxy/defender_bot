# handlers/docs.py
from aiogram import types
from config import config, docs   # docs мы только что экспортировали
import logging
logger = logging.getLogger(__name__)

async def docs_handler(message: types.Message) -> None:
    # Игнорируем лишние чаты и ботов
    if (message.chat.id != config.ALLOWED_CHAT_ID) or message.from_user.is_bot:
        return

    # Формат: /docs <lang>; если аргумент не указан – берём ru
    parts = message.text.split(maxsplit=1)
    lang  = parts[1].lower() if len(parts) > 1 else "ru"

    reply_text = docs.get(lang) or docs.get("en") \
                 or "Docs template is not configured."

    await message.reply(reply_text, disable_web_page_preview=True)
