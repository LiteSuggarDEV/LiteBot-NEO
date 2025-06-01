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
