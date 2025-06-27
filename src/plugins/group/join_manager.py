import contextlib
import random

from nonebot import get_driver, on_command, on_message, on_notice
from nonebot.adapters.onebot.v11 import (
    ActionFailed,
    Bot,
    GroupIncreaseNoticeEvent,
    GroupMessageEvent,
    Message,
    MessageSegment,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from litebot_utils.captcha_manager import captcha_manager
from litebot_utils.event import GroupEvent
from litebot_utils.models import get_or_create_group_config
from litebot_utils.rule import is_group_admin, is_self_admin
from src.plugins.menu.models import MatcherData

pending_cancelable_msg: dict[str, dict[str, str]] = {}


async def captacha(
    bot: Bot, matcher: Matcher, event: GroupEvent, uid: int | None = None
):
    captcha = random.randint(10000, 99999)
    user_id = event.user_id if uid is None else uid
    await captcha_manager.add(event.group_id, user_id, captcha)
    sent_msg_id: int = (
        await matcher.send(
            MessageSegment.at(user_id)
            + MessageSegment.text(
                f"请完成以下操作，验证您是真人。\n请在5分钟内输入验证码 {captcha} ，否则您将被移出聊群\n继续之前，该群需要先检查您的账号安全性。"
            ),
        )
    )["message_id"]
    await captcha_manager.pending(event.group_id, user_id, bot)

    pending_cancelable_msg[str(sent_msg_id)] = {
        "group_id": str(event.group_id),
        "user_id": str(user_id),
    }
    matcher.stop_propagation()


@on_command(
    "captcha",
    aliases={"验证"},
    state=MatcherData(
        rm_name="验证特定人",
        rm_desc="验证群内特定成员是否为机器人",
        rm_usage="captcha [@user|<user_id>]",
    ).model_dump(),
).handle()
async def _(
    matcher: Matcher, event: GroupMessageEvent, bot: Bot, args: Message = CommandArg()
):
    if not await is_group_admin(event, bot):
        return
    config, _ = await get_or_create_group_config(group_id=event.group_id)

    if not await is_self_admin(event, bot):
        config.auto_manage_join = False
        await matcher.send("LiteBot为普通群成员！")
        # 在 SQLAlchemy 中需要通过 session 来保存
        from nonebot_plugin_orm import get_session

        async with get_session() as session:
            session.add(config)
            await session.commit()
        return
    for segment in args:
        if segment.type == "at":
            uid = segment.data["qq"]
            await captacha(bot, matcher, event, int(uid))
            break
    else:
        await matcher.finish("请at需要验证的人。")


@on_command(
    "入群验证",
    aliases={"robot_fight", "anti_robot"},
    state=MatcherData(
        rm_name="入群验证",
        rm_desc="入群验证",
        rm_usage="入群验证 [开启|关闭]",
    ).model_dump(),
).handle()
async def cmd(
    bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()
) -> None:
    if not await is_group_admin(event, bot):
        return
    config, _ = await get_or_create_group_config(group_id=event.group_id)
    if arg := args.extract_plain_text().strip().lower():
        from nonebot_plugin_orm import get_session

        async with get_session() as session:
            session.add(config)
            if arg in ("启用", "on", "enable", "开启", "yes", "y", "true"):
                if not await is_self_admin(event, bot):
                    config.auto_manage_join = False
                    await matcher.send("LiteBot为普通群成员，无法开启！")
                    await session.commit()
                    return
                config.auto_manage_join = True
                await session.commit()
            elif arg in ("关闭", "off", "disable", "关闭", "no", "n", "false"):
                config.auto_manage_join = False
                await session.commit()
            else:
                await matcher.finish("请输入 on/off 来开启或关闭！")

    await matcher.send(
        f"群组进群验证码已 {'开启' if config.auto_manage_join else '关闭'} ！"
    )


@on_message(priority=5, block=False).handle()
async def checker(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    config, _ = await get_or_create_group_config(group_id=event.group_id)
    if not config.auto_manage_join:
        return
    if (
        captcha := await captcha_manager.query(event.group_id, event.user_id)
    ) is not None:
        message: str = event.message.extract_plain_text().strip()
        group_name: str = (await bot.get_group_info(group_id=event.group_id))[
            "group_name"
        ]
        if str(captcha) == message:
            await matcher.send(
                MessageSegment.at(event.user_id)
                + MessageSegment.text(f"验证成功！欢迎加入{group_name}！"),
            )
            await captcha_manager.remove(event.group_id, event.user_id)
            for k in list(pending_cancelable_msg):
                v = pending_cancelable_msg[k]
                if v.get("user_id") == str(event.user_id) and v.get("group_id") == str(
                    event.group_id
                ):
                    del pending_cancelable_msg[k]
                    break
            matcher.stop_propagation()
        elif any(
            isinstance(msg, dict) and msg.get("type") in ["json", "xml", "share"]
            for msg in event.message
        ):
            await bot.delete_msg(message_id=event.message_id)


@on_message(
    priority=10,
    block=False,
    state=MatcherData(
        rm_name="取消验证",
        rm_desc="引用机器人发送的验证消息取消单次验证",
        rm_usage="<REPLY> /skip",
    ).model_dump(),
).handle()
async def handle_cancel(bot: Bot, event: GroupMessageEvent, matcher: Matcher):
    if not event.reply:
        return
    if str(event.reply.message_id) not in pending_cancelable_msg:
        return
    if event.message.extract_plain_text().strip() not in (
        f"{prefix}skip" for prefix in get_driver().config.command_start
    ):
        return
    if not await is_group_admin(event, bot):
        return
    if (
        await bot.get_group_member_info(
            user_id=event.self_id, group_id=event.group_id
        )
    )["role"] == "member":
        return
    with contextlib.suppress(ActionFailed):
        await bot.delete_msg(message_id=event.reply.message_id)
    await captcha_manager.remove(
        event.group_id,
        int(pending_cancelable_msg[str(event.reply.message_id)]["user_id"]),
    )
    del pending_cancelable_msg[str(event.reply.message_id)]

    await matcher.send("已取消该验证！")
    matcher.stop_propagation()


@on_notice(priority=9, block=False).handle()
async def handle_join(bot: Bot, event: GroupIncreaseNoticeEvent, matcher: Matcher):
    if event.user_id == event.self_id:
        return
    config, _ = await get_or_create_group_config(group_id=event.group_id)
    if not config.auto_manage_join:
        return
    if not await is_self_admin(event, bot):
        return
    await captacha(bot, matcher, event)
