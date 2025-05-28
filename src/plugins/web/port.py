import sys

import dns.resolver as resolver
import nmap
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from litebot_utils.web_utils import (
    is_domain_refer_to_private_network,
    is_ip_address,
    is_ip_in_private_network,
)

from ..menu.manager import MatcherData

nm = nmap.PortScanner()


async def nmap_port(address, port):
    nm.scan(address, arguments=f"-p {port} -Pn")

    # 准备一个列表用于存储结果

    # 遍历扫描结果
    print()
    for protocol in nm[address].all_protocols():
        ports = nm[address][protocol].keys()
        for port in ports:
            port_info = {
                "port": port,
                "state": nm[address][protocol][port]["state"],
                "name": nm[address][protocol][port].get("name", "N/A"),
                "product": nm[address][protocol][port].get("product", "N/A"),
                "version": nm[address][protocol][port].get("version", "N/A"),
            }

    return port_info


@on_command(
    "port",
    state=MatcherData(
        rm_name="端口扫描",
        rm_desc="扫描指定主机的端口",
        rm_usage="port [ip:port]",
    ).model_dump(),
).handle()
async def _(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    if location := args.extract_plain_text():
        url = []
        url = location.split(":", maxsplit=1)
        logger.debug(url[0])
        logger.debug(url[1])

        if len(url) <= 1:
            await matcher.send("请输入端口！")
            return
        if is_ip_address(url[0]):
            if not is_ip_in_private_network(url[0]):
                await matcher.send("请输入正确的地址！")
                return
        elif is_domain_refer_to_private_network(url[0]):
            await matcher.send("请输入正确的地址！")
            return
        try:
            if not is_ip_address(url[0]):
                answers = resolver.resolve(url[0], "A")
                answers = (
                    [rdata.to_text() for rdata in answers]
                    if answers
                    else [
                        rdata.to_text()
                        for rdata in resolver.resolve(url[0], "AAAA")
                    ]
                )

            else:
                answers = [url[0]]
            maps = await nmap_port(answers[0], url[1])
            message = f"""结果：
端口：{maps["port"]}
状态：{maps["state"]}
服务：{maps["name"]}
product:{maps["product"]}
版本：{maps["version"]}"""

        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            await matcher.send(
                f"过程发生了错误：{exc_type.__name__ if exc_type is not None else 'nil'}\n{exc_value!s}"
            )
            logger.error(
                f"Exception type: {exc_type.__name__ if exc_type is not None else 'nil'}"
            )
            logger.error(f"Exception message: {exc_value!s}")
            import traceback

            logger.error(
                f"Detailed exception info:\n{''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}"
            )
            return
        await matcher.send(message)
    else:
        await matcher.send("请输入地址！格式<host>:<port>")
