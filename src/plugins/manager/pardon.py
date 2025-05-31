from nonebot import CommandGroup
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent
from nonebot.params import CommandArg
from nonebot.rule import to_me

from litebot_utils.black import bl_manager

from .rule import is_admin

pardon = CommandGroup("pardon", priority=10, rule=to_me() & is_admin)

pardon_group = pardon.command("-group")
pardon_user = pardon.command("-user")


@pardon_group.handle()
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    if not bl_manager.is_group_black(arg):
        await pardon_group.finish("该群未被封禁！")
    else:
        bl_manager.group_remove(arg)
        await pardon_group.finish(f"解封禁群{arg}成功！")


@pardon_user.handle()
async def pardon_user_handle(args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()
    if bl_manager.is_private_black(arg):
        await pardon_user.finish("该用户没有被封禁！")
    else:
        bl_manager.private_remove(arg)
        await pardon_user.finish(f"解封禁用户{arg}成功！")
