import hashlib

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.rule import to_me

from src.plugins.menu.manager import MatcherData


@on_command(
    "sha1",
    aliases={"sha1加密", "sha1"},
    state=MatcherData(
        rm_desc="sha1加密", rm_name="sha1加密", rm_usage="sha1 <text>"
    ).model_dump(),
    rule=to_me(),
).handle()
async def sha1_runner(matcher: Matcher, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await matcher.finish("请输入要加密的文本")
    lib = hashlib.sha1()
    lib.update(text.encode("utf-8"))
    await matcher.finish(lib.hexdigest())
