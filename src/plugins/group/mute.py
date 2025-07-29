import re

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from litebot_utils.rule import is_bot_group_admin, is_event_group_admin
from src.plugins.menu.models import MatcherData


def parse_duration(duration_str: str) -> int:
    """
    解析时间字符串为分钟数

    支持的格式:
    - 纯数字: 10 (表示10分钟)
    - 简写格式: 1h, 1d, 1m (分别表示1小时、1天、1分钟)
    - 组合格式: 1h10m, 1d1h1m (自动转换为分钟)

    Args:
        duration_str: 时间字符串

    Returns:
        int: 总分钟数

    Raises:
        ValueError: 当输入格式不合法时
    """
    duration_str = duration_str.strip().lower()
    if duration_str.isdigit():
        minutes = int(duration_str)
        if minutes <= 0:
            raise ValueError("时间必须为正整数")
        return minutes
    pattern = r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?"
    match = re.fullmatch(pattern, duration_str)

    if not match:
        raise ValueError("时间格式不正确")

    days = int(match.group(1)) if match.group(1) else 0
    hours = int(match.group(2)) if match.group(2) else 0
    minutes = int(match.group(3)) if match.group(3) else 0
    if days == 0 and hours == 0 and minutes == 0:
        raise ValueError("时间不能为空")

    total_minutes = days * 24 * 60 + hours * 60 + minutes

    if total_minutes <= 0:
        raise ValueError("时间必须为正整数")

    return total_minutes


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
    if not await is_event_group_admin(event, bot):
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
    if not await is_event_group_admin(event, bot):
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
    if not await is_event_group_admin(event, bot):
        return
    if not await is_bot_group_admin(event, bot):
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
        rm_desc="禁言指定群员（时间）",
        rm_usage="mute @user 10(或1h 1d 1h1m,不填则默认10分钟）)",
    ).model_dump(),
).handle()
async def _(
    bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    if not await is_event_group_admin(event, bot):
        return
    if not await is_bot_group_admin(event, bot):
        return
    for segment in args:
        if segment.type == "at":
            uid = segment.data["qq"]
            break
    else:
        return await matcher.finish("请指定要禁言的人")
    arg_text = (
        args.extract_plain_text().strip() if args.extract_plain_text().strip() else "10"
    )

    try:
        duration_minutes = parse_duration(arg_text)
    except ValueError as e:
        return await matcher.finish(
            f"请输入合法的时间格式: {e!s}\n支持格式: 纯数字(分钟), 1h, 1d, 1m, 1h10m, 1d1h1m"
        )
    await bot.set_group_ban(
        group_id=event.group_id, user_id=int(uid), duration=duration_minutes * 60
    )
