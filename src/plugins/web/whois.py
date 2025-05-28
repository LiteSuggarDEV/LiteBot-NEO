from aiohttp import ClientSession
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from ..menu.manager import MatcherData


@on_command(
    "whois",
    aliases={"WHOIS"},
    state=MatcherData(
        **{
            "rm_name": "whois",
            "rm_desc": "域名WHOIS查询",
            "rm_usage": "whois <top_domain>",
        }
    ).model_dump(),
).handle()
async def whois_runner(
    event: MessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5"
    }

    if location := args.extract_plain_text():
        async with ClientSession() as session:
            async with session.get(
                f"https://v2.xxapi.cn/api/whois?domain={location}", headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    code = data.get("code")
                    msg = data.get("msg")
                    if data.get("code") == 200:
                        if data.get("DNS Serve") is not None:
                            dns_servers = data.get("DNS Serve")
                            await matcher.send(
                                f"域名：{data.get('Domain')}\n"
                                f"注册人：{data.get('Registrant') if data.get('Registrant') else '未知'}\n"
                                f"注册时间：{data.get('Registration Time')}\n"
                                f"注册商URL：{data.get('Registrar URL')}"
                                f"到期时间：{data.get('Expiration Time')}\n"
                                f"DNS服务器：{''.join(server for server in dns_servers)}\n"
                            )
                        else:
                            await matcher.send("该域名不存在或并非顶级域名。")
                    elif code == -2:
                        await matcher.finish(msg)
                else:
                    logger.error(f"Whois查询失败，状态码：{response.status}")
    else:
        await matcher.finish("请输入要查询的域名")
