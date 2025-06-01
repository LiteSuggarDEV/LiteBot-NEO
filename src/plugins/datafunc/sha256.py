import hashlib

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from src.plugins.menu.manager import MatcherData


@on_command(
    "sha256",
    aliases={"sha256加密", "SHA256"},
    state=MatcherData(
        rm_desc="SHA256加密", rm_name="SHA256加密", rm_usage="SHA256 <text>"
    ).model_dump(),
).handle()
async def sha256_runner(matcher: Matcher, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await matcher.finish("请输入要加密的文本")
    lib = hashlib.sha256()
    lib.update(text.encode("utf-8"))
    await matcher.finish(lib.hexdigest())
