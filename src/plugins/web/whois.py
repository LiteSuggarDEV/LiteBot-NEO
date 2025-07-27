from aiohttp import ClientSession
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.exception import NoneBotException
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from src.plugins.menu.models import MatcherData


@on_command(
    "whois",
    aliases={"WHOIS"},
    state=MatcherData(
        rm_name="whois",
        rm_desc="域名WHOIS查询",
        rm_usage="whois <top_domain>",
    ).model_dump(),
).handle()
async def whois_runner(matcher: Matcher, args: Message = CommandArg()):
    location = args.extract_plain_text()
    if not location:
        await matcher.finish("请输入要查询的域名")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5"
    }

    try:
        async with ClientSession() as session:
            async with session.get(
                f"https://v2.xxapi.cn/api/whois?domain={location}",
                headers=headers,
            ) as response:
                if response.status != 200:
                    logger.error(f"Whois查询失败，状态码：{response.status}")
                    await matcher.finish("查询失败")

                data: dict = await response.json()
                code = data.get("code")
                msg = data.get("msg")

                if code == 200:
                    dns_data: dict = data.get("data", {})
                    if dns_servers := dns_data.get("DNS Serve", []):
                        await matcher.send(
                            f"域名：{dns_data.get('Domain Name')}\n"
                            f"注册人：{dns_data.get('Registrant') or '未知'}\n"
                            f"注册人邮箱：{dns_data.get('Registrant Contact Email') or '未知'}\n"
                            f"注册时间：{dns_data.get('Registration Time')}\n"
                            f"注册商URL：{dns_data.get('Registrar URL') or '未知'}\n"
                            f"到期时间：{dns_data.get('Expiration Time')}\n"
                            f"DNS服务器：{', '.join(dns_servers)}\n"
                            f"注册商：{dns_data.get('Sponsoring Registrar') or '未知'}\n"
                            f"域名状态：{dns_data.get('domain_status') or '未知'}"
                        )
                    else:
                        await matcher.send("该域名不存在或并非顶级域名。")
                elif code == -2:
                    await matcher.finish(msg)
                else:
                    await matcher.finish(msg or "查询失败")
    except NoneBotException:
        raise
    except Exception as e:
        logger.error(f"Whois查询异常: {e!s}")
        await matcher.finish("查询失败，请稍后再试")
