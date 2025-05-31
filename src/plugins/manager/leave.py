from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.rule import to_me

from litebot_utils.utils import send_to_admin

from .rule import is_admin


@on_command("set_leave", rule=to_me() & is_admin).handle()
async def leave(
    bot: Bot, matcher: Matcher, event: MessageEvent, arg: Message = CommandArg()
):
    str_id = arg.extract_plain_text().strip()
    if isinstance(event, GroupMessageEvent):
        if not str_id:
            await matcher.finish("请输入--this来离开这个群！或者指定群号！")
        if str_id == "--this":
            await send_to_admin(f"尝试离开群：{event.group_id}")
            await matcher.send("正在尝试退出本群")
            await bot.set_group_leave(group_id=event.group_id)

    try:
        int(str_id)
    except:  # noqa: E722
        await matcher.finish("请输入一个数字")
    else:
        await matcher.send(f"尝试离开{str_id}")
        await bot.set_group_leave(group_id=int(str_id))
