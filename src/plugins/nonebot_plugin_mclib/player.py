import base64
import json
import sys

from aiohttp import ClientSession, ClientTimeout
from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.params import CommandArg

from src.plugins.menu.manager import MatcherData

mc_body = on_command(
    "mc_body",
    aliases={"MC_BODY"},
    priority=10,
    block=True,
    state=MatcherData(
        rm_name="mc皮肤渲染图",
        rm_desc="获取一个正版玩家的皮肤渲染图",
        rm_usage="mc_body <player_name>",
    ).model_dump(),
)
mc_uuid = on_command(
    "mc_uuid",
    aliases={"MC_UUID", "mc_UUID", "MC_uuid"},
    priority=10,
    block=True,
    state=MatcherData(
        rm_name="mc-uuid获取",
        rm_desc="获取一个正版玩家的uuid",
        rm_usage="mc_uuid <player_name>",
    ).model_dump(),
)
mc_avatar = on_command(
    "mc_avatar",
    priority=10,
    block=True,
    state=MatcherData(
        rm_name="mc皮肤头像渲染图",
        rm_desc="获取一个正版玩家的皮肤头像渲染图",
        rm_usage="mc_avatar <player_name>",
    ).model_dump(),
)
mc_skin = on_command(
    "mc_skin",
    priority=10,
    block=True,
    state=MatcherData(
        rm_name="mc皮肤",
        rm_desc="获取一个正版玩家的皮肤",
        rm_usage="mc_skin <player_name>",
    ).model_dump(),
)


async def get_uuid(player: str) -> str | None:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5"
    }
    async with ClientSession(headers=headers) as session:
        dicts: dict = await (
            await session.get(
                f"https://api.mojang.com/users/profiles/minecraft/{player}",
            )
        ).json()
    return dicts.get("id")


@mc_avatar.handle()
async def _(event: MessageEvent, bot: Bot, args: Message = CommandArg()):
    if location := args.extract_plain_text():
        async with ClientSession(
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5"
            }
        ) as session:
            UUID = await get_uuid(player=location)
            message = MessageSegment.image(
                await (
                    await session.get(
                        f"https://crafatar.com/avatars/{UUID}?size=512&overlay",
                        timeout=ClientTimeout(total=5),
                    )
                ).read()
            )
            await mc_avatar.send(message)


@mc_uuid.handle()
async def _(event: MessageEvent, bot: Bot, args: Message = CommandArg()):
    if location := args.extract_plain_text():
        UUID = await get_uuid(player=location)
        if UUID is None:
            await mc_uuid.send("没有这个玩家！")
            return
        await mc_uuid.send(f"{location}的UUID是{UUID}")


@mc_skin.handle()
async def _(event: MessageEvent, bot: Bot, args: Message = CommandArg()):
    if location := args.extract_plain_text():
        async with ClientSession() as session:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5"
            }
            UUID = await get_uuid(player=location)
            if UUID is None:
                await mc_skin.send("没有这个玩家！")
                return
            try:
                SKIN_dict = await (
                    await session.get(
                        f"https://sessionserver.mojang.com/session/minecraft/profile/{UUID}",
                        headers=headers,
                    )
                ).json()
            except Exception:
                await mc_skin.send("查询失败！")
                return
            unbase = base64.b64decode(SKIN_dict["properties"][0]["value"])
            SKIN_LAST = json.loads(unbase)
            message = MessageSegment.image(
                await (await session.get(SKIN_LAST["textures"]["SKIN"]["url"])).read()
            )
            await mc_skin.send(message)

    else:
        await mc_skin.send("请输入玩家ID！")


@mc_body.handle()
async def _(event: MessageEvent, bot: Bot, args: Message = CommandArg()):
    if arg := args.extract_plain_text():
        async with ClientSession(
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5"
            }
        ) as session:
            try:
                UUID = await get_uuid(player=arg)
                if UUID is None:
                    await mc_body.send("没有这个玩家！")
                    return
                image = await (
                    await session.get(
                        f"https://crafatar.com/renders/body/{UUID}?overlay",
                        timeout=ClientTimeout(total=5),
                    )
                ).read()
                await mc_body.send(MessageSegment.image(image))
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                await mc_body.send(f"过程发生了错误：{exc_value!s}")

                return
    else:
        await mc_body.send("请输入玩家名！")
