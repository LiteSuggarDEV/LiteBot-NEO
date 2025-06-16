import shutil

import nonebot
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot
from nonebot.adapters.onebot.v11.event import GroupMessageEvent, MessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment

from litebot_utils.config import ConfigManager


async def send_to_admin(message):
    """
    发送消息到管理员。

    参数:
    message (str): 要发送的消息内容。
    """
    bot = nonebot.get_bot()
    if isinstance(bot, Bot):
        for group_id in ConfigManager.instance().config.notify_group:
            await bot.send_group_msg(group_id=group_id, message=message)
    logger.info(f"Sending to admin: {message}")


def get_disk_usage_percentage(directory):
    """
    获取指定目录所在磁盘的存储使用百分比。

    参数:
    directory (str): 要检查的目录路径。

    返回:
    float: 磁盘存储使用百分比。
    """
    # 获取目录所在磁盘使用情况
    disk_usage = shutil.disk_usage(directory)

    return (disk_usage.used / disk_usage.total) * 100


def generate_info():
    # 动态导入
    import os
    import platform
    import sys

    import psutil

    system_name = platform.system()
    system_version = platform.version()
    python_version = sys.version
    memory = psutil.virtual_memory()
    cpu_usage = psutil.cpu_percent(interval=1)
    logical_cores = psutil.cpu_count(logical=True)
    physical_cores = psutil.cpu_count(logical=False)
    current_dir = os.getcwd()
    disk_usage = get_disk_usage_percentage(current_dir)

    return (
        f"# LiteBot NEO\n\n"
        "---\n\n"
        f"* 系统类型: `{system_name}`\n\n"
        f"* 系统版本: `{system_version}`\n\n"
        "---\n\n"
        f"* CPU 物理核心数：`{physical_cores}`\n\n"
        f"* CPU 总核心: `{logical_cores}`\n\n"
        f"* CPU 已使用: `{cpu_usage}%`\n\n"
        "---\n\n"
        f"* 已用内存: `{memory.percent}%`\n\n"
        f"* 总共内存: `{memory.total / (1024**3):.2f} GB`\n\n"
        f"* 可用内存: `{memory.available / (1024**3):.2f} GB`\n\n"
        "---\n\n"
        f"* 磁盘存储占用：`{disk_usage:.2f}%`\n\n"
        f"* Python 版本: `{python_version}`\n\n"
        "> Bot of NoneBot2💪"
    )


async def send_forward_msg(
    bot: Bot,
    event: MessageEvent,
    name: str,
    uin: str,
    msgs: list[MessageSegment],
) -> dict:
    """
    发送转发消息的异步函数。

    参数:
        bot (Bot): 机器人实例
        event (MessageEvent): 消息事件
        name (str): 转发消息的名称
        uin (str): 转发消息的 UIN
        msgs (list[Message]): 转发的消息列表

    返回:
        dict: API 调用结果
    """

    def to_json(msg: MessageSegment) -> dict:
        return {"type": "node", "data": {"name": name, "uin": uin, "content": msg}}

    messages = [to_json(msg) for msg in msgs]
    if isinstance(event, GroupMessageEvent):
        return await bot.send_group_forward_msg(
            group_id=event.group_id, messages=messages
        )
    return await bot.send_private_forward_msg(user_id=event.user_id, messages=messages)
