import base64
import binascii

from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.rule import to_me

from src.plugins.menu.manager import MatcherData


@on_command(
    "base64",
    aliases={"b64", "BASE64"},
    state=MatcherData(
        rm_name="base64",
        rm_usage="base64 encode/decode [content]",
        rm_desc="Base64编码解码功能",
    ).model_dump(),
    rule=to_me(),
).handle()
async def base64_runner(matcher: Matcher, args: Message = CommandArg()):
    if location := args.extract_plain_text():
        location = location.strip().split(maxsplit=1)
        logger.debug(location)
        if location[0].lower() not in ["decode", "encode"]:
            await matcher.send("请输入正确选项！可用的：decode encode")
            return
        if len(location) > 1:
            if location[0].lower() == "decode":
                try:
                    finish = base64.b64decode(location[1].encode("utf-8"))
                    message = None
                    message = str(finish.decode("utf-8"))
                    await matcher.finish(message)
                except binascii.Error:
                    await matcher.finish("不合法的Base64格式！")
                except ValueError:
                    await matcher.finish("不合法的Base64格式（非4倍数位）！")
            elif location[0].lower() == "encode":
                finish = base64.b64encode(location[1].encode("utf-8"))
                message = str(finish.decode("utf-8"))
                await matcher.finish(message)
            else:
                await matcher.finish("输入正确选项！可用的：decode encode")
        else:
            await matcher.send("请输入文本！")
    else:
        await matcher.send("请输入选项！可用的：decode encode")
