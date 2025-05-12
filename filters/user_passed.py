from aiogram.enums.poll_type import PollType
from aiogram.filters import BaseFilter
from aiogram.types import Message

from config import config
from database import check_user_passed

class UserPassedFilter(BaseFilter):
    def __init__(self, pool: PollType):
        self.pool = pool

    async def __call__(self, message: Message) -> bool:
        return not (
            message.chat.id != config.ALLOWED_CHAT_ID
            or await check_user_passed(self.pool, message.from_user.id)
            or message.from_user.is_bot
        )
