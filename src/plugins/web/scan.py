import asyncio
from concurrent.futures import ThreadPoolExecutor

import nmap
import nonebot
import ping3
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.params import CommandArg

from litebot_utils.utils import send_to_admin
from plugins.menu.manager import MatcherData

from .utils import (
    is_domain_refer_to_private_network,
    is_ip_address,
    is_ip_in_private_network,
    is_valid_domain,
    resolve_dns_records,
)

task_queue = asyncio.Queue(maxsize=15)
executor = ThreadPoolExecutor(max_workers=10)
user_tasks = {}
map_scan = on_command(
    "nmap",
    state=MatcherData(
        rm_name="NMAP端口扫描", rm_desc="扫描端口", rm_usage="nmap <host>"
    ).model_dump(),
)


def scan_ports_sync(host,arg1:None|str=None):
    nm = nmap.PortScanner()
    if arg1 is None:
        arg1 = "1-1023"
    if not is_ip_address(host):
        try:
            ips = resolve_dns_records(host)
            if not ips:
                raise
        except:  # noqa: E722
            return [
                {
                    "port": -1,
                    "state": "Error",
                    "name": "Resolve failed",
                    "product": "N/A",
                    "version": "N/A",
                }
            ]
    if ping3.ping(host, timeout=2) is None:
        return [
            {
                "port": -1,
                "state": "Error",
                "name": "Connect failed",
                "product": "N/A",
                "version": "N/A",
            }
        ]
    nm.scan(host, arguments=f"-p {arg1} -sS -Pn")
    port_info_list = []

    for protocol in nm[host].all_protocols():
        ports = nm[host][protocol].keys()
        for port in ports:
            port_info = {
                "port": port,
                "state": nm[host][protocol][port]["state"],
                "name": nm[host][protocol][port].get("name", "N/A"),
                "product": nm[host][protocol][port].get("product", "N/A"),
                "version": nm[host][protocol][port].get("version", "N/A"),
            }
            logger.debug(port_info)
            port_info_list.append(port_info)
    return port_info_list


async def scan_ports(host, user_id, event,arg1 :None|str=None):
    try:
        # 在任务队列中等待获取任务
        await task_queue.put(user_id)

        # 此处确保 scan_ports_sync 返回一个可迭代对象
        info_list = await asyncio.get_event_loop().run_in_executor(
            executor, scan_ports_sync, (host,arg1)
        )

        # 确保 port_info_list 是一个可迭代列表
        if not isinstance(info_list, list):
            raise TypeError("scan_ports_sync 需要返回一个可迭代对象")

        message = MessageSegment.text(f"主机：{host}\n端口：\n")
        for one_port in info_list:
            message += MessageSegment.text(
                f"  {one_port['port']} {one_port['state']} {one_port['name']} {one_port['product']} {one_port['version']}\n"
            )
        message += MessageSegment.text("==========")

        # 发送消息
        await nonebot.get_bot().send(event, message)
    finally:
        # 从任务队列中移除该用户
        if not task_queue.empty():
            task_queue.get_nowait()
        user_tasks.pop(user_id, None)


async def start_background_task(host, user_id, event,arg1):
    if user_id not in user_tasks:  # 防止同一用户同时运行多个任务
        await scan_ports(host, user_id, event,arg1)
    else:
        logger.info(f"用户 {user_id} 的任务正在运行中。")


@map_scan.handle()
async def _(event: MessageEvent, args: Message = CommandArg()):
    location = args.extract_plain_text()
    if not location:
        await map_scan.send("请输入地址！格式<host>")
        return

    cmd = location.split(maxsplit=1)
    if not len(cmd) > 1:
        cmd = []
        cmd.append(location)
        cmd.append("1-1023")
    if "gov.cn" in cmd[0] or "gov.hk" in cmd[0]:
        await send_to_admin (f"{event.user_id} 尝试扫描gov网站！")
        return
    if not 65535 > int(cmd[1]) > 0:
        await map_scan.send("不合法端口范围！")
        return
    if (not is_valid_domain(cmd[0]) and not is_ip_address(cmd[0])) or (
        is_domain_refer_to_private_network(cmd[0]) or is_ip_in_private_network(cmd[0])
    ):
        await map_scan.send("请输入正确地址！")
        return
    try:
        if not is_ip_address(cmd[0]):
            answers = resolve_dns_records(cmd[0])
            if  not answers:
                await map_scan.send("请输入正确的地址！")
                return
            for answer in answers:
                if is_ip_in_private_network(str(answer)):
                    await map_scan.send("不允许查询此地址！")
                    return
    except Exception:
        await map_scan.send("无法查询该地址。")
        return

    if task_queue.full():
        await map_scan.send("队列已经满！请稍后再尝试。")
        return

    await map_scan.send("少女祈祷中（notice:此结果稍后会发送。）")

    arg1 = cmd[1] if len(cmd) > 1 else None
    # 将任务放入队列，开始执行
    await start_background_task(cmd[0], event.user_id, event,arg1)
