import random

from nonebot import get_driver, on_notice
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupAdminNoticeEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    MessageSegment,
    PokeNotifyEvent,
)
from nonebot.matcher import Matcher

from litebot_utils.event import GroupEvent
from litebot_utils.models import GroupConfig
from litebot_utils.utils import send_to_admin

from .utils import get_disk_usage_percentage

command_start = get_driver().config.command_start

notice = on_notice(priority=11, block=False)
poke = on_notice(priority=10)


@poke.handle()
async def handle_poke(event: PokeNotifyEvent, bot: Bot, matcher: Matcher):
    if not event.group_id:
        return
    if event.target_id != bot.self_id:
        return
    await matcher.finish(random.choice(generate_fun_response()))


@notice.handle()
async def handle_group_notice(event: GroupEvent, bot: Bot, matcher: Matcher):
    gid, uid, self_id = event.group_id, event.user_id, event.self_id
    group_config = await GroupConfig.get_or_none(group_id=gid)
    if not group_config or not group_config.switch or not group_config.welcome:
        return

    if isinstance(event, GroupDecreaseNoticeEvent):
        await handle_member_leave(bot, gid, uid, event)

    elif isinstance(event, GroupIncreaseNoticeEvent):
        await handle_member_join(bot, event, gid, uid)

    elif isinstance(event, GroupAdminNoticeEvent):
        await handle_admin_change(bot, event, gid, uid, self_id)


def generate_fun_response():
    # 动态导入
    import os
    import platform
    import sys

    import psutil

    system_name = platform.system()
    system_version = platform.version()
    cpu_name = platform.processor()
    python_version = sys.version
    memory = psutil.virtual_memory()
    cpu_usage = psutil.cpu_percent(interval=1)
    logical_cores = psutil.cpu_count(logical=True)
    physical_cores = psutil.cpu_count(logical=False)
    current_dir = os.getcwd()
    disk_usage = get_disk_usage_percentage(current_dir)

    return [
        "检测到机箱疑似遭受到黑👇暗👆森～～林～～打击",
        "机箱发生弹性形变！",
        "未知物体敲击",
        "检测到未知电平变化",
        '机箱被敲口,口口口！\nNonePointerException:Because "status" is None!',
        "戳瘪了",
        "机箱被压扁了",
        "电阻戳掉了",
        "机箱炸了",
        "再戳就让你飞起来！",
        "机箱受到打击",
        "服务器被你踢炸了",
        "嘟嘟哒嘟嘟哒",
        "?",
        (
            f"LiteBot NEO\n"
            f"系统类型: {system_name}\n"
            f"系统版本: {system_version}\n"
            f"Python 版本: {python_version}\n"
            f"磁盘存储占用：{disk_usage:.2f}%\n"
            f"CPU架构：{cpu_name}\n"
            f"CPU 已使用: {cpu_usage}%\n"
            f"CPU 物理核心：{physical_cores}\n"
            f"CPU 总核心: {logical_cores}\n"
            f"已用内存: {memory.percent}%\n"
            f"总共内存: {memory.total / (1024**3):.2f} GB\n"
            f"可用内存: {memory.available / (1024**3):.2f} GB"
        ),
    ]


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
    else:
        if event.operator_id == 0:
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

    if event.sub_type == "invite":
        message = MessageSegment.at(user_id=uid) + MessageSegment.text(
            f" 被 {operator_name}（{operator_id}） 拉进了聊群！欢迎！"
        )
    else:
        message = MessageSegment.at(user_id=uid) + MessageSegment.text(" 欢迎加入 ！")

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
