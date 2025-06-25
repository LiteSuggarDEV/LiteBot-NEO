import base64
import io

import qrcode
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from src.plugins.menu.models import MatcherData


@on_command(
    "qr",
    aliases={"QR", "make_qr", "二维码"},
    state=MatcherData(
        rm_name="qr", rm_usage="qr <text>", rm_desc="文本->二维码"
    ).model_dump(),
).handle()
async def qr_runner(matcher: Matcher, args: Message = CommandArg()):
    if location := args.extract_plain_text().strip():
        try:
            img = qrcode.make(location)
            bytesio = io.BytesIO()
            img.save(bytesio, "PNG")
            qrbytes = bytesio.getvalue()
            base64_str = base64.b64encode(qrbytes).decode()
            message = MessageSegment.image(
                f"base64://{base64_str}", cache=False, proxy=False
            )
            logger.debug(message)
            await matcher.send(message)
        except Exception as e:
            logger.exception(e)
            await matcher.finish("生成二维码失败，详情请查看日志")
    else:
        await matcher.finish("请输入要生成的内容")
