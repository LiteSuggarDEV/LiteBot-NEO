import time

from aiohttp import ClientSession, ClientTimeout
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from src.plugins.menu.models import MatcherData

from .utils import is_ip_address, resolve_dns_records


@on_command(
    "httping",
    aliases={"wget", "curl", "wping"},
    state=MatcherData(
        rm_name="httping",
        rm_usage="httping <uri>",
        rm_desc="Get一个网站",
    ).model_dump(),
).handle()
async def httping(matcher: Matcher, args: Message = CommandArg()):
    if arg := args.extract_plain_text().strip():
        if not is_ip_address(arg) and resolve_dns_records(arg) is None:
            await matcher.finish("请输入正确的地址！")
        url = (
            arg
            if (arg.startswith("http") or arg.startswith("https"))
            else f"http://{arg}"
        )
        try:
            start_time = time.time()
            async with ClientSession(timeout=ClientTimeout(5, 1.5, 2)) as session:
                async with session.get(url) as response:
                    end_time = time.time()
                    latency = end_time - start_time
                    await matcher.send(
                        f"{url}\nHttp版本{response.version}\n响应状态码：{response.status}\n延迟{latency:.2f}ms"
                    )
        except TimeoutError:
            await matcher.finish("请求超时！")
        except Exception as e:
            await matcher.finish(f"请求失败！错误信息：{e}")
    else:
        await matcher.finish("请输入地址！格式<http/https://example.com>")
