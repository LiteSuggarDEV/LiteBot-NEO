from nonebot import CommandGroup
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent
from nonebot.params import CommandArg

from litebot_utils.blacklist.black import bl_manager
from src.plugins.menu.manager import MatcherData

from .rule import is_admin

ban = CommandGroup("ban", priority=1, rule=is_admin)

ban_group = ban.command(
    "-group",
    state=MatcherData(
        rm_name="封禁群", rm_usage="ban-group <group-id>", rm_desc="封禁聊群"
    ).model_dump(),
)
ban_user = ban.command(
    "-user",
    state=MatcherData(
        rm_name="封禁用户", rm_desc="用于封禁用户", rm_usage="ban-user <user-id>"
    ).model_dump(),
)


@ban_group.handle()
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    arg_list = args.extract_plain_text().strip().split(maxsplit=1)
    if await bl_manager.is_group_black(arg_list[0]):
        await ban_group.finish("该群已被封禁！")
    else:
        await bl_manager.group_append(arg_list[0], arg_list[1]) if len(
            arg_list
        ) > 1 else await bl_manager.group_append(arg_list[0])
        await ban_group.finish(f"封禁群{arg_list[0]}成功！")


@ban_user.handle()
async def ban_user_handle(args: Message = CommandArg()):
    arg_list = args.extract_plain_text().strip().split(maxsplit=1)
    if await bl_manager.is_private_black(arg_list[0]):
        await ban_user.finish("该用户已被封禁！")
    else:
        await bl_manager.private_append(arg_list[0], arg_list[1]) if len(
            arg_list
        ) > 1 else await bl_manager.private_append(arg_list[0])
        await ban_user.finish(f"封禁用户{arg_list[0]}成功！")
