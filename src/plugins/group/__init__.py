import random

from nonebot import get_driver, on_fullmatch, on_message, on_notice
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupAdminNoticeEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
    GroupMessageEvent,
    MessageSegment,
    PokeNotifyEvent,
)
from nonebot.matcher import Matcher
from nonebot.plugin import PluginMetadata

from litebot_utils.models import GroupConfig
from litebot_utils.utils import send_to_admin

from .utils import get_disk_usage_percentage

__plugin_meta__ = PluginMetadata(
    name="群组插件",
    description="群组插件",
    usage="群组插件",
    type="application",
)


switch = on_fullmatch("switch")
recall = on_message()
welcome_switch = on_fullmatch("welcome")


@switch.handle()
async def _(event: GroupMessageEvent, matcher: Matcher):
    """开关"""
    # 获取当前群组的开关状态
    gid = event.group_id
    group_config, _ = await GroupConfig.get_or_create(group_id=gid)
    # 切换开关状态
    group_config.switch = not group_config.switch
    await group_config.save()

    await matcher.send(
        f"该群LiteBot已经 {'开启' if group_config.switch else '关闭'} ！"
    )


SUPERUSER_list = list(get_driver().config.superusers)


@recall.handle()
async def _(event: GroupMessageEvent, bot: Bot, matcher: Matcher):
    gid = event.group_id
    uid = event.user_id
    if "recall" not in event.raw_message:
        return
    user_info = await bot.get_group_member_info(group_id=gid, user_id=uid)
    if user_info["role"] == "member" and str(uid) not in SUPERUSER_list:
        await matcher.finish("你还没有权限执行")

    if not event.reply:
        await matcher.finish("请回复消息选择撤回")

    await bot.delete_msg(message_id=event.reply.message_id)
    await matcher.finish("消息已成功撤回！")


@welcome_switch.handle()
async def _(event: GroupMessageEvent, matcher: Matcher):
    """开关"""
    # 获取当前群组的开关状态
    gid = event.group_id
    group_config, _ = await GroupConfig.get_or_create(group_id=gid)
    # 切换开关状态
    group_config.switch = not group_config.welcome_message
    await group_config.save()

    await matcher.send(f"成员变动提醒已 {'开启' if group_config.switch else '关闭'} ！")


notice = on_notice()


@notice.handle()
async def handle_group_notice(event: GroupMessageEvent, bot: Bot, matcher: Matcher):
    if isinstance(event, PokeNotifyEvent) and int(event.target_id) == int(
        event.self_id
    ):
        await matcher.finish(random.choice(generate_fun_response()))
        return

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
        "机箱受到打击",
        "是铁御，我们有救啦！",
        "服务器被你踢炸了",
        "嘟嘟哒嘟嘟哒",
        "?",
        (
            f"LiteBot V1.12.1 FullVersion\n"
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
        message = f"{uid}[CQ:image,file=http://q.qlogo.cn/headimg_dl?dst_uin={uid}&spec=640&img_type=jpg] 离开了群聊。"
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
