from nonebot import require
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from sqlalchemy import select

require("nonebot_plugin_orm")
from nonebot_plugin_orm import get_session

from litebot_utils.config import ConfigManager
from litebot_utils.event import GroupEvent, UserIDEvent
from litebot_utils.models import GroupConfig


async def rule_switch(event: Event):
    """开关"""
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
        async with get_session() as session:
            stmt = select(GroupConfig).where(GroupConfig.group_id == group_id)
            result = await session.execute(stmt)
            group_config = result.scalar_one_or_none()
            return group_config.switch if group_config else True


async def is_admin(event: UserIDEvent) -> bool:
    return event.user_id in ConfigManager.instance().config.admins


async def is_group_admin(event: GroupEvent, bot: Bot) -> bool:
    return (
        await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
    )["role"] != "member" or await is_admin(event)


async def is_self_admin(event: GroupEvent, bot: Bot) -> bool:
    return (
        await bot.get_group_member_info(
            group_id=event.group_id, user_id=int(bot.self_id)
        )
    )["role"] != "member"
