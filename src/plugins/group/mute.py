from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from litebot_utils.rule import is_group_admin, is_self_admin
from src.plugins.menu.models import MatcherData


@on_command(
    "unmute-all",
    aliases={"全体解禁"},
    state=MatcherData(
        rm_name="全体解禁",
        rm_desc="解除全员禁言",
        rm_usage="unmute-all",
    ).model_dump(),
).handle()
async def unmute_all(bot: Bot, event: GroupMessageEvent, matcher: Matcher) -> None:
    if not await is_group_admin(event, bot):
        return
    await bot.set_group_whole_ban(group_id=event.group_id, enable=False)


@on_command(
    "mute-all",
    aliases={"全体禁言"},
    state=MatcherData(
        rm_name="全体禁言",
        rm_desc="设置全员禁言",
        rm_usage="mute-all",
    ).model_dump(),
).handle()
async def cmd(bot: Bot, event: GroupMessageEvent) -> None:
    if not await is_group_admin(event, bot):
        return
    await bot.set_group_whole_ban(group_id=event.group_id, enable=True)
@on_command(
    "解禁",
    aliases={"unmute"},
    state=MatcherData(
        rm_name="解禁",
        rm_desc="解除指定群员的禁言",
        rm_usage="unmute @user",
    ).model_dump(),
).handle()
async def _(
    bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    if not await is_group_admin(event, bot):
        return
    if not await is_self_admin(event, bot):
        return
    for segment in args:
        if segment.type == "at":
            uid = segment.data["qq"]
            await bot.set_group_ban(
                group_id=event.group_id, user_id=int(uid), duration=0
            )
            break
    else:
        return await matcher.finish("请指定要解禁的人")


@on_command(
    "禁言",
    aliases={"mute"},
    state=MatcherData(
        rm_name="禁言群员",
        rm_desc="禁言指定群员（分钟）",
        rm_usage="mute @user 10(正整数)",
    ).model_dump(),
).handle()
async def _(
    bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    if not await is_group_admin(event, bot):
        return
    if not await is_self_admin(event, bot):
        return
    for segment in args:
        if segment.type == "at":
            uid = segment.data["qq"]
            break
    else:
        return await matcher.finish("请指定要禁言的人")
    arg_text = args.extract_plain_text().strip()
    try:
        if not int(arg_text) > 0:
            raise ValueError
    except ValueError:
        return await matcher.finish("请输入合法的正整数(分钟)")
    await bot.set_group_ban(
        group_id=event.group_id, user_id=int(uid), duration=int(arg_text) * 60
    )
