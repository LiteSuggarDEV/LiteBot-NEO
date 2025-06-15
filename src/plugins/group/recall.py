from nonebot import on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
)
from nonebot.matcher import Matcher

from litebot_utils.rule import is_group_admin
from src.plugins.menu.manager import MatcherData

recall = on_message(
    state=MatcherData(
        rm_name="撤回消息",
        rm_desc="用机器人撤回一条消息",
        rm_usage="<REPLY> /recall",
    ).model_dump(),
)

@recall.handle()
async def _(event: GroupMessageEvent, bot: Bot, matcher: Matcher):
    if "/recall" not in event.raw_message:
        return
    if not event.reply:
        await matcher.finish("请回复消息选择撤回")
    if not await is_group_admin(event, bot):
        return
    await bot.delete_msg(message_id=event.reply.message_id)
    await matcher.finish("已尝试撤回消息！")
