import hashlib

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from src.plugins.menu.manager import MatcherData


@on_command(
    "md5",
    aliases={"md5加密", "md5"},
    state=MatcherData(
        rm_desc="md5加密", rm_name="md5加密", rm_usage="md5 <text>"
    ).model_dump(),
).handle()
async def md5_runner(matcher: Matcher, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await matcher.finish("请输入要加密的文本")
    lib = hashlib.md5()
    lib.update(text.encode("utf-8"))
    await matcher.finish(lib.hexdigest())
