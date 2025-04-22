from nonebot.adapters import Event
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from litebot.models import GroupConfig


async def rule_switch(event: Event):
    """开关"""
    if isinstance(event, GroupMessageEvent):
        group_id = event.group_id
        group_config = await GroupConfig.get_or_none(group_id=group_id)
        return group_config.switch if group_config else True
