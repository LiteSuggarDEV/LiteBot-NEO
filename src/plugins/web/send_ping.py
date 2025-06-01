import contextlib
import time
from ipaddress import ip_address

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from ping3 import ping

from src.plugins.menu.manager import MatcherData

from .utils import is_domain_refer_to_private_network

MAX_PING_COUNT = 5

# 确保不抛异常，便于统一处理


@on_command(
    "ping",
    aliases={"PING"},
    state=MatcherData(
        rm_name="ping",
        rm_desc="发送Ping包",
        rm_usage="ping <ip/domain> [次数（可选，最大5次）]",
    ).model_dump(),
).handle()
async def ping_runner(
    event: MessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    arg_list = args.extract_plain_text().strip().split()

    if not arg_list:
        await matcher.send("请提供 IP 或域名地址。")
        return

    address = arg_list[0]

    if is_domain_refer_to_private_network(address):
        await matcher.send("请输入正确的地址（不能为私有网络地址）！")
        return

    count = 3
    if len(arg_list) > 1:
        try:
            count = int(arg_list[1])
            if count < 1 or count > MAX_PING_COUNT:
                raise ValueError
        except ValueError:
            await matcher.send(f"请输入1~{MAX_PING_COUNT}之间的有效次数！")
            return

    # 检查 IP 是否为私网
    with contextlib.suppress(ValueError):
        if ip_address(address).is_private:
            await matcher.send("请输入正确的地址（不能为私有IP）！")
            return

    await matcher.send(f"正在 ping {address} {count} 次，请稍候...")

    result: list[float | None] = []
    start_time = time.time()
    for _ in range(count):
        try:
            res = ping(address, size=64, timeout=2)
            if not res or res <= 0.0:  # ping3 返回 None 或小于等于0的值表示请求失败
                res = None
        except Exception:
            res = None
        result.append(res)
    stop_time = time.time()

    total = len(result)
    lost = result.count(None)
    packet_loss = (lost / total) * 100
    valid_latency = [r for r in result if r is not None]
    avg_latency = sum(valid_latency) / len(valid_latency) * 1000 if valid_latency else 0
    time_used = stop_time - start_time

    if lost == total:
        await matcher.send(
            f"无法连接 {address}，全部请求丢失。请检查目标地址是否可达。"
        )
        return

    response_lines = [f"已PING {address} ({total}次, 每次64bytes):"]
    for i, rtt in enumerate(result):
        response = f"{rtt * 1000:.2f}ms" if rtt is not None else "丢包！"
        response_lines.append(f"第{i + 1}次：{response}")

    response_lines.extend(
        [
            "\n---统计数据---",
            f"共发送：{total} 包，丢失：{lost} 包",
            f"丢包率：{packet_loss:.2f}%",
            f"平均延迟：{avg_latency:.2f}ms",
            f"总耗时：{time_used:.2f}s",
        ]
    )

    await matcher.send("\n".join(response_lines))
