from nonebot import CommandGroup
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent
from nonebot.params import CommandArg
from nonebot.rule import to_me

from litebot_utils.black import bl_manager

from .rule import is_admin

ban = CommandGroup("ban", priority=10, rule=to_me() & is_admin)

ban_group = ban.command("-group")
ban_user = ban.command("-user")


@ban_group.handle()
async def _(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    arg_list = args.extract_plain_text().strip().split(maxsplit=1)
    if bl_manager.is_group_black(arg_list[0]):
        await ban_group.finish("该群已被封禁！")
    else:
        bl_manager.group_append(arg_list[0], arg_list[1]) if len(
            arg_list
        ) > 1 else bl_manager.group_append(arg_list[0])
        await ban_group.finish(f"封禁群{arg_list[0]}成功！")

@ban_user.handle()
async def ban_user_handle(args: Message = CommandArg()):
    arg_list =  args.extract_plain_text().strip().split(maxsplit=1)
    if bl_manager.is_private_black(arg_list[0]):
        await ban_user.finish("该用户已被封禁！")
    else:
        bl_manager.private_append(arg_list[0], arg_list[1]) if len(
            arg_list
        ) > 1 else bl_manager.private_append(arg_list[0])
        await ban_user.finish(f"封禁用户{arg_list[0]}成功！")
