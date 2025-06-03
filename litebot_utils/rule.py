from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, MessageEvent

from litebot_utils.config import ConfigManager
from litebot_utils.models import GroupConfig


async def rule_switch(event: Event):
    """开关"""
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
        group_config = await GroupConfig.get_or_none(group_id=group_id)
        return group_config.switch if group_config else True


async def is_admin(event: MessageEvent) -> bool:
    return event.user_id in ConfigManager.instance().config.admins

async def is_group_admin(event: GroupMessageEvent, bot: Bot) -> bool:
    return (
        await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
    )["role"] != "member" or await is_admin(event)
