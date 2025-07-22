"""
权限和规则管理模块

提供用户权限检查、群组权限验证、开关状态检查等功能
包含全局管理员、群管理员、协管权限的统一管理
"""

from nonebot import require
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from sqlalchemy import select

require("nonebot_plugin_orm")
from nonebot_plugin_orm import get_session

from litebot_utils.config import ConfigManager
from litebot_utils.event import GroupEvent, UserIDEvent
from litebot_utils.models import GroupConfig, SubAdmin


async def rule_switch(event: Event) -> bool:
    """
    检查群组功能开关状态

    Args:
        event: 事件对象

    Returns:
        群组开关状态，True表示开启，False表示关闭
        如果不是群组消息或未找到配置则默认返回True
    """
    if not isinstance(event, GroupMessageEvent):
        return True

    group_id = event.group_id
    async with get_session() as session:
        stmt = select(GroupConfig).where(GroupConfig.group_id == group_id)
        result = await session.execute(stmt)
        group_config = result.scalar_one_or_none()
        return group_config.switch if group_config else True


async def check_global_admin(user_id: int) -> bool:
    """
    检查用户是否为全局管理员

    Args:
        user_id: 用户ID

    Returns:
        是否为全局管理员
    """
    return user_id in ConfigManager.instance().config.admins


async def is_global_admin(event: UserIDEvent) -> bool:
    """
    检查事件发送者是否为全局管理员

    Args:
        event: 包含用户ID的事件对象

    Returns:
        是否为全局管理员
    """
    return await check_global_admin(event.user_id)


async def is_sub_admin(group_id: int, user_id: int) -> bool:
    """
    检查用户是否为指定群组的协管

    Args:
        group_id: 群组ID
        user_id: 用户ID

    Returns:
        是否为该群协管
    """
    return await SubAdmin.exists(group_id, user_id)


async def check_group_admin(group_id: int, user_id: int, bot: Bot) -> bool:
    """
    检查用户是否在指定群组中拥有管理权限

    管理权限包括：群主、群管理员、全局管理员、群协管

    Args:
        group_id: 群组ID
        user_id: 用户ID
        bot: Bot实例

    Returns:
        是否拥有管理权限
    """
    try:
        member_info = await bot.get_group_member_info(
            group_id=group_id, user_id=user_id
        )
        role = member_info.get("role", "member")

        if role in ["owner", "admin"]:
            return True

        if await check_global_admin(user_id):
            return True

        return await is_sub_admin(group_id, user_id)

    except Exception:
        return await check_global_admin(user_id) or await is_sub_admin(
            group_id, user_id
        )


async def is_event_group_admin(event: GroupEvent, bot: Bot) -> bool:
    """
    检查事件发送者是否在事件群组中拥有管理权限

    Args:
        event: 群组事件对象
        bot: Bot实例

    Returns:
        是否拥有管理权限
    """
    return await check_group_admin(event.group_id, event.user_id, bot)


async def is_bot_group_admin(event: GroupEvent, bot: Bot) -> bool:
    """
    检查机器人是否在指定群组中拥有管理权限

    Args:
        event: 群组事件对象
        bot: Bot实例

    Returns:
        机器人是否为群管理员或群主
    """
    try:
        bot_info = await bot.get_group_member_info(
            group_id=event.group_id, user_id=int(bot.self_id)
        )
        return bot_info.get("role", "member") != "member"
    except Exception:
        return False
