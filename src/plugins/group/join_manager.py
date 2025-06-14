import random

from nonebot import on_command, on_message, on_notice
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupIncreaseNoticeEvent,
    GroupMessageEvent,
    Message,
    MessageSegment,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from litebot_utils.captcha_manager import captcha_manager
from litebot_utils.models import GroupConfig
from litebot_utils.rule import is_group_admin
from src.plugins.menu.manager import MatcherData


@on_command(
    "入群验证",
    aliases={"robot_fight", "anti_robot"},
    rule=is_group_admin,
    state=MatcherData(
        rm_name="入群验证",
        rm_desc="入群验证",
        rm_usage="入群验证 [开启|关闭]",
    ).model_dump(),
).handle()
async def cmd(
    bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()
) -> None:
    config, _ = await GroupConfig.get_or_create(group_id=event.group_id)
    if arg := args.extract_plain_text().strip().lower():
        if arg in ("启用", "on", "enable", "开启", "yes", "y", "true"):
            config.auto_manage_join = True
            await config.save()
        elif arg in ("关闭", "off", "disable", "关闭", "no", "n", "false"):
            config.auto_manage_join = False
            await config.save()
        else:
            await matcher.finish("请输入 on/off 来开启或关闭！")

    await matcher.send(
        f"群组进群验证码已 {'开启' if config.auto_manage_join else '关闭'} ！"
    )


@on_message(priority=5, block=False).handle()
async def checker(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    config, _ = await GroupConfig.get_or_create(group_id=event.group_id)
    if not config.auto_manage_join:
        return
    if (captcha := captcha_manager.query(event.group_id, event.user_id)) is not None:
        message: str = event.message.extract_plain_text().strip()
        group_name: str = (await bot.get_group_info(group_id=event.group_id))[
            "group_name"
        ]
        if str(captcha) == message:
            await matcher.send(
                MessageSegment.at(event.user_id)
                + MessageSegment.text(f"验证成功！欢迎加入{group_name}！"),
            )
            captcha_manager.remove(event.group_id, event.user_id)
            matcher.stop_propagation()
        elif any(
            (
                msg.get("type") == "json"
                or msg.get("type") == "xml"
                or msg.get("type") == "share"
            )
            for msg in event.message
        ):
            await bot.delete_msg(message_id=event.message_id)


@on_notice(priority=9, block=False).handle()
async def handle_join(bot: Bot, event: GroupIncreaseNoticeEvent, matcher: Matcher):
    config, _ = await GroupConfig.get_or_create(group_id=event.group_id)
    if not config.auto_manage_join:
        return
    self_role = (
        await bot.get_group_member_info(
            group_id=event.group_id, user_id=int(bot.self_id)
        )
    )["role"]
    if self_role == "member":
        return
    captcha = random.randint(10000, 99999)
    captcha_manager.add(event.group_id, event.user_id, captcha)
    captcha_manager.pending(event.group_id, event.user_id, bot)
    await matcher.send(
        MessageSegment.at(event.user_id)
        + MessageSegment.text(
            f"请完成以下操作，验证您是真人。\n请在5分钟内输入验证码 {captcha} ，否则您将被移出聊群\n继续之前，该群需要先检查您的账号安全性。"
        ),
    )
    matcher.stop_propagation()
