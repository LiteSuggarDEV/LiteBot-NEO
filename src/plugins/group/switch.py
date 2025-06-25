
from nonebot import get_driver, on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from litebot_utils.models import GroupConfig
from litebot_utils.rule import is_group_admin
from src.plugins.menu.models import MatcherData

command_start = get_driver().config.command_start
switch = on_command(
    "switch",
    state=MatcherData(
        rm_name="切换LiteBot启用状态",
        rm_desc="切换LiteBot启用状态",
        rm_usage="switch on/off",
    ).model_dump(),
)

@switch.handle()
async def _(
    event: GroupMessageEvent, matcher: Matcher, bot: Bot, arg: Message = CommandArg()
):
    if not await is_group_admin(event, bot):
        await switch.finish("你没有权限使用此命令！")
    """开关"""
    # 获取当前群组的开关状态
    group_id = event.group_id
    str_arg = arg.extract_plain_text().strip()
    group_config, _ = await GroupConfig.get_or_create(group_id=group_id)
    if not str_arg:
        await matcher.send(
            f"该群LiteBot已经 {'开启' if group_config.switch else '关闭'} ！"
        )
    elif str_arg in ("on", "enable", "开启"):
        group_config.switch = True
        await group_config.save()
        await matcher.finish("已开启本群LiteBot！")
    elif str_arg in ("off", "disable", "关闭"):
        group_config.switch = False
        await group_config.save()
        await matcher.finish("已关闭本群LiteBot！")
    else:
        await matcher.finish("请输入正确参数！")
