from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from config import config


class IsAdmin(BaseFilter):

    def __init__(self):
        self.admin_ids = config.BOT_ADMINS

    async def __call__(self, obj: TelegramObject) -> bool:
        check_obj = obj.from_user
        if obj.sender_chat is not None:
            check_obj = obj.sender_chat

        return check_obj.id in self.admin_ids
