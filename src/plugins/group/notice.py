from nonebot import get_driver, on_notice, require
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupAdminNoticeEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    MessageSegment,
)
from nonebot.matcher import Matcher
from sqlalchemy import select

require("nonebot_plugin_orm")
from nonebot_plugin_orm import get_session

from litebot_utils.event import GroupEvent
from litebot_utils.models import GroupConfig, get_or_create_group_config
from litebot_utils.utils import send_to_admin

command_start = get_driver().config.command_start

notice = on_notice(priority=11, block=False)
poke = on_notice(priority=10)


@notice.handle()
async def handle_group_notice(event: GroupEvent, bot: Bot, matcher: Matcher):
    gid, uid, self_id = event.group_id, event.user_id, event.self_id
    async with get_session() as session:
        stmt = select(GroupConfig).where(GroupConfig.group_id == gid)
        result = await session.execute(stmt)
        group_config = result.scalar_one_or_none()

        if not group_config or not group_config.switch or not group_config.welcome:
            return

        if isinstance(event, GroupDecreaseNoticeEvent):
            await handle_member_leave(bot, gid, uid, event)

        elif isinstance(event, GroupIncreaseNoticeEvent):
            await handle_member_join(bot, event, gid, uid)

        elif isinstance(event, GroupAdminNoticeEvent):
            await handle_admin_change(bot, event, gid, uid, self_id)


async def handle_member_leave(
    bot: Bot, gid: int, uid: int, event: GroupDecreaseNoticeEvent
):
    cause = event.sub_type
    if cause == "leave":
        message = (
            MessageSegment.text(str(uid))
            + MessageSegment.image(
                f"https://q.qlogo.cn/headimg_dl?dst_uin={uid}&spec=640&img_type=jpg"
            )
            + MessageSegment.text("退出了群聊")
        )
    elif event.operator_id == 0:
        message = f"{uid} 被赠送了飞机票。"
    else:
        message = f"{uid} 被 {event.operator_id} 赠送了飞机票。"
    await bot.send_group_msg(group_id=gid, message=message)


async def handle_member_join(
    bot: Bot, event: GroupIncreaseNoticeEvent, gid: int, uid: int
):
    operator_id = event.operator_id
    if uid == event.self_id:
        await send_to_admin(f"LiteBot加入了群号为{event.group_id}的聊群")
        return

    operator_info = await bot.get_group_member_info(group_id=gid, user_id=operator_id)

    operator_name = operator_info["nickname"]
    config, _ = await get_or_create_group_config(gid)
    msg = config.welcome_message
    if event.sub_type == "invite":
        message = MessageSegment.at(user_id=uid) + MessageSegment.text(
            f" 被 {operator_name}（{operator_id}） 拉进了聊群！{msg}"
        )
    else:
        message = MessageSegment.at(user_id=uid) + MessageSegment.text(msg)

    await bot.send_group_msg(group_id=gid, message=message)


async def handle_admin_change(
    bot: Bot, event: GroupAdminNoticeEvent, gid: int, uid: int, self_id: int
):
    sub_type = event.sub_type
    user_info = await bot.get_group_member_info(group_id=gid, user_id=uid)
    if self_id == uid:
        msg = (
            "LiteBot被设置为了群管理！"
            if sub_type == "set"
            else "LiteBot被取消了群管理。"
        )
        await bot.send_group_msg(group_id=gid, message=msg)
    else:
        action = "设置为了" if sub_type == "set" else "取消了"
        user_name = user_info["nickname"]

        await bot.send_group_msg(
            group_id=gid, message=f"{user_name}（{uid}） 被{action}群管理。"
        )
