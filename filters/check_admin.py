from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from config import config


class IsAdmin(BaseFilter):

    def __init__(self):
        self.admin_ids = config.BOT_ADMINS

    async def __call__(self, obj: TelegramObject) -> bool:
        return obj.from_user.id in self.admin_ids
