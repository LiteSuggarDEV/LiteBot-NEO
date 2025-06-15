from nonebot import CommandGroup
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg

from litebot_utils.blacklist.black import bl_manager
from litebot_utils.rule import is_admin
from src.plugins.menu.manager import MatcherData

pardon = CommandGroup("pardon", permission=is_admin)

pardon_group = pardon.command(
    "group",
    state=MatcherData(
        rm_name="解封群组", rm_desc="用于解封群", rm_usage="pardon-group <group-id>"
    ).model_dump(),
)
pardon_user = pardon.command(
    "user",
    state=MatcherData(
        rm_name="解封用户", rm_desc="用于解封用户", rm_usage="pardon-user <user-id>"
    ).model_dump(),
)


@pardon_group.handle()
async def _(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    if not arg:
        await pardon_group.finish("请提供要解封的群ID！")
    if not await bl_manager.is_group_black(arg):
        await pardon_group.finish("该群未被封禁！")
    else:
        await bl_manager.group_remove(arg)
        await pardon_group.finish(f"解封禁群{arg}成功！")


@pardon_user.handle()
async def pardon_user_handle(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    if not arg:
        await pardon_group.finish("请提供要解封的用户ID！")
    if not await bl_manager.is_private_black(arg):
        await pardon_user.finish("该用户没有被封禁！")
    else:
        await bl_manager.private_remove(arg)
        await pardon_user.finish(f"解封禁用户{arg}成功！")
