from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from litebot_utils.rule import is_group_admin, is_self_admin
from src.plugins.menu.manager import MatcherData


@on_command(
    "kick",
    aliases={"踢出"},
    state=MatcherData(
        rm_name="踢出群员",
        rm_desc="踢出群内的指定成员",
        rm_usage="/kick @user",
    ).model_dump(),
).handle()
async def kick(
    bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    if not await is_group_admin(event, bot):
        return
    if not await is_self_admin(event, bot):
        return
    for segment in args:
        if segment.type == "at":
            uid = segment.data["qq"]
            await bot.set_group_kick(group_id=event.group_id, user_id=int(uid))
            await matcher.finish(f"已踢出{uid}")
