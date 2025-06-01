from aiohttp import ClientSession
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from src.plugins.menu.manager import MatcherData


@on_command(
    "whois",
    aliases={"WHOIS"},
    state=MatcherData(
        rm_name="whois",
        rm_desc="域名WHOIS查询",
        rm_usage="whois <top_domain>",
    ).model_dump(),
).handle()
async def whois_runner(
    event: MessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    if location := args.extract_plain_text():
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5"
        }

        try:
            async with ClientSession() as session:
                async with session.get(
                    f"https://v2.xxapi.cn/api/whois?domain={location}",
                    headers=headers,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        code = data.get("code")
                        msg = data.get("msg")
                        if code == 200:
                            dns_servers = (
                                data.get("DNS Serve")
                                or data.get("DNS Server")
                                or data.get("DNS Servers")
                            )
                            if dns_servers:
                                await matcher.send(
                                    f"域名：{data.get('Domain')}\n注册人：{data.get('Registrant') or '未知'}\n注册时间：{data.get('Registration Time')}\n注册商URL：{data.get('Registrar URL')}到期时间：{data.get('Expiration Time')}\nDNS服务器：{''.join(dns_servers)}\n"
                                )
                            else:
                                await matcher.send("该域名不存在或并非顶级域名。")
                        elif code == -2:
                            await matcher.finish(msg)
                        else:
                            await matcher.finish(msg or "查询失败")
                    else:
                        logger.error(f"Whois查询失败，状态码：{response.status}")
                        await matcher.finish("查询失败")
        except Exception as e:
            logger.error(f"Whois查询异常: {e!s}")
            await matcher.finish("查询失败，请稍后再试")
    else:
        await matcher.finish("请输入要查询的域名")
