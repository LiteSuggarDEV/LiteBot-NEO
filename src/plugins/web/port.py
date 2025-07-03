import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import dns.resolver as resolver
import nmap
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from src.plugins.menu.models import MatcherData

from .utils import (
    is_domain_refer_to_private_network,
    is_ip_address,
    is_ip_in_private_network,
)

nm = nmap.PortScanner()
executor = ThreadPoolExecutor(max_workers=10)


def scan_ports(address, port) -> dict[str, Any]:
    nm.scan(address, arguments=f"-p {port} -Pn")

    # 准备一个列表用于存储结果

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


async def send_nmap_port(matcher: Matcher, data: asyncio.Future[dict[Any, Any]]):
    try:
        port_info = data.result()
        message = f"""结果：
端口：{port_info["port"]}
状态：{port_info["state"]}
服务：{port_info["name"]}
product:{port_info["product"]}
版本：{port_info["version"]}"""
        await matcher.send(message)
    except Exception:
        await matcher.send("发生错误！请查看日志！")
        logger.opt()


@on_command(
    "port",
    state=MatcherData(
        rm_name="端口扫描",
        rm_desc="扫描指定主机的端口",
        rm_usage="port [ip:port]",
    ).model_dump(),
).handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    if location := args.extract_plain_text():
        url = []
        url = location.split(":", maxsplit=1)
        logger.debug(f"Host: {url[0]}, Port: {url[1]}")

        if len(url) <= 1:
            await matcher.finish("请输入端口")
        if is_ip_address(url[0]):
            if not is_ip_in_private_network(url[0]):
                await matcher.finish("请输入正确的地址")
        elif is_domain_refer_to_private_network(url[0]):
            await matcher.finish("请输入正确的地址")
        try:
            if not is_ip_address(url[0]):
                answers = resolver.resolve(url[0], "A")
                answers = (
                    [rdata.to_text() for rdata in answers]
                    if answers
                    else [rdata.to_text() for rdata in resolver.resolve(url[0], "AAAA")]
                )

            else:
                answers = [url[0]]

                asyncio.get_running_loop().run_in_executor(
                    executor, lambda: scan_ports(answers[0], url[1])
                ).add_done_callback(
                    lambda future: asyncio.create_task(send_nmap_port(matcher, future))
                )

        except Exception:
            await matcher.finish("过程发生了错误，请检查日志以获取详细信息。")
    else:
        await matcher.send("请输入地址！格式<host>:<port>")
