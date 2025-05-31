from nonebot.adapters.onebot.v11 import MessageEvent

from src.plugins.config.config import config_manager


async def is_admin(event: MessageEvent) -> bool:
    if event.user_id in config_manager.config.admins:
        return True
    return False
