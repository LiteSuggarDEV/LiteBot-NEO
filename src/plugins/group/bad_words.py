from base64 import b64decode, b64encode
from json import load
from pathlib import Path

from nonebot import on_command, on_message, require
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

require("src.plugins.menu")
require("nonebot_plugin_orm")
import logging

import jieba
from async_lru import alru_cache
from nonebot_plugin_orm import get_session

from litebot_utils.models import get_or_create_group_config
from litebot_utils.rule import is_bot_group_admin, is_event_group_admin
from src.plugins.menu.models import MatcherData

jieba.initialize()


def load_bad_words() -> list[str]:
    with open(Path(__file__).parent / "badwords.json", encoding="utf-8") as f:
        b64_words: list[str] = load(f)
    data = []
    for word in b64_words:
        try:
            decoded = b64decode(word.encode("utf-8")).decode("utf-8")
            data.append(decoded)
        except Exception as e:
            logging.warning(f"Invalid base64 entry in badwords.json: {word} ({e})")
    data.sort()
    return data


BAD_WORDS = tuple(load_bad_words())

print(f"加载了{len(BAD_WORDS)} 个内置敏感词")


def check_bad_words(text: str) -> bool:
    return len(set(jieba.cut(text)) & set(BAD_WORDS)) != 0


@alru_cache(1024)
async def is_check_enabled(group_id: int) -> bool:
    async with get_session() as session:
        config, _ = await get_or_create_group_config(group_id)
        session.add(config)
        return config.badwords_check is True


@on_message(priority=1, block=False).handle()
async def _(event: GroupMessageEvent, bot: Bot, matcher: Matcher):
    group_id = event.group_id
    if event.sender.role != "member":
        return
    if check_bad_words(event.message.extract_plain_text()):
        if not await is_check_enabled():
            return
        self_role = (
            await bot.get_group_member_info(group_id=group_id, user_id=event.self_id)
        )["role"]
        if self_role == "member":
            return
        await bot.delete_msg(message_id=event.message_id)
        matcher.stop_propagation()


@on_command(
    "bw_list",
    aliases={"违禁词列表"},
    priority=10,
    block=True,
    state=MatcherData(
        rm_name="违禁词列表", rm_usage="/bw_list", rm_desc="查看违禁词列表"
    ).model_dump(),
).handle()
async def _(event: GroupMessageEvent, matcher: Matcher, bot: Bot):
    if not await is_event_group_admin(event, bot):
        return
    if not await is_bot_group_admin(event, bot):
        return
    async with get_session() as session:
        config, _ = await get_or_create_group_config(event.group_id)
        session.add(config)
        match config.badwords_check_mode:
            case "builtin":
                await matcher.finish("❌内置违禁词模式")
            case "custom" | "mixed":
                await matcher.finish(
                    "自定义/混合违禁词模式:"
                    + "\n".join(
                        [
                            b64encode(word.encode("utf-8")).decode("utf-8")
                            for word in config.custom_badwords
                        ]
                        if config.custom_badwords
                        else ["无"]
                    )
                )


@on_command(
    "bw_mode",
    aliases={"违禁词模式"},
    priority=10,
    block=True,
    state=MatcherData(
        rm_name="违禁词模式",
        rm_usage="/bw_mode [builtin|custom|mixed]",
        rm_desc="设置违禁词模式",
    ).model_dump(),
).handle()
async def _(
    event: GroupMessageEvent, matcher: Matcher, bot: Bot, args: Message = CommandArg()
):
    if not await is_event_group_admin(event, bot):
        return
    if not await is_bot_group_admin(event, bot):
        return
    self_role = (
        await bot.get_group_member_info(
            group_id=event.group_id, user_id=event.self_id, no_cache=True
        )
    )["role"]
    group_id = event.group_id
    arg = args.extract_plain_text().strip().split()
    if len(arg) != 1:
        await matcher.finish("参数错误")
    async with get_session() as session:
        config, _ = await get_or_create_group_config(group_id)
        session.add(config)
        if self_role == "member":
            config.badwords_check = False
            await session.commit()
            await matcher.finish("❌Bot为普通群员")
        match arg[0]:
            case "builtin":
                config.badwords_check_mode = "builtin"
            case "custom":
                config.badwords_check_mode = "custom"
            case "mixed":
                config.badwords_check_mode = "mixed"
            case _:
                await matcher.finish("参数错误,可用：builtin|custom|mixed")
        await session.commit()
        await matcher.finish("✔已完成操作")


@on_command(
    "设置违禁词",
    aliases={"bw_set"},
    priority=10,
    block=True,
    state=MatcherData(
        rm_desc="设置自定义违禁词",
        rm_name="设置自定义词",
        rm_usage="/bw_set [add|del] <词>",
    ).model_dump(),
).handle()
async def _(
    event: GroupMessageEvent, matcher: Matcher, bot: Bot, args: Message = CommandArg()
):
    if not await is_event_group_admin(event, bot):
        return
    if not await is_bot_group_admin(event, bot):
        return
    self_role = (
        await bot.get_group_member_info(
            group_id=event.group_id, user_id=event.self_id, no_cache=True
        )
    )["role"]
    group_id = event.group_id
    arg = args.extract_plain_text().strip().split()
    if len(arg) != 2:
        await matcher.finish("参数错误")
    async with get_session() as session:
        config, _ = await get_or_create_group_config(group_id)
        session.add(config)
        if self_role == "member":
            config.badwords_check = False
            await session.commit()
            await matcher.finish("❌Bot为普通群员")
        if config.custom_badwords is None:
            config.custom_badwords = []
        bw_list = config.custom_badwords
        match arg[0]:
            case "add":
                if arg[1] not in bw_list:
                    bw_list.append(arg[1])
            case "del":
                if arg[1] in bw_list:
                    bw_list.remove(arg[1])
            case _:
                await matcher.finish("❌未知操作")
        await session.commit()
        await matcher.finish("✔已完成操作")


@on_command(
    "违禁词检测",
    aliases={"bw_ck"},
    priority=10,
    block=True,
    state=MatcherData(
        rm_name="违禁词检测",
        rm_usage="/bw_ck [开启|关闭]",
        rm_desc="是否开启违禁词检查功能",
    ).model_dump(),
).handle()
async def _(event: GroupMessageEvent, matcher: Matcher, bot: Bot):
    if not await is_event_group_admin(event, bot):
        return
    if not await is_bot_group_admin(event, bot):
        return
    self_role = (
        await bot.get_group_member_info(
            group_id=event.group_id, user_id=event.self_id, no_cache=True
        )
    )["role"]
    group_id = event.group_id
    async with get_session() as session:
        config, _ = await get_or_create_group_config(group_id)
        session.add(config)
        if self_role == "member":
            config.badwords_check = False
            await session.commit()
            await matcher.finish("❌Bot为普通群员")
        if arg := event.message.extract_plain_text().strip():
            match arg:
                case "enable" | "on" | "1" | "yes" | "true" | "启用" | "开启":
                    config.badwords_check = True
                case "disable" | "off" | "0" | "no" | "false" | "禁用" | "关闭":
                    config.badwords_check = False
                case _:
                    await matcher.finish("❌ 请输入on/off")
            is_check_enabled.cache_clear()
            await session.commit()
            await matcher.finish("✔ 已完成操作")
        else:
            await matcher.finish("❌ 请输入on/off")
