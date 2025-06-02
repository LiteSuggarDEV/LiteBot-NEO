from nonebot import logger
from nonebot.adapters.onebot.v11 import MessageEvent

from litebot_utils.config import ConfigManager


async def is_admin(event: MessageEvent) -> bool:
