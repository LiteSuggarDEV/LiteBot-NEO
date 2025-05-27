import time
from ipaddress import ip_address

import dns.resolver
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from ping3 import ping


def is_domain_refer_to_private_network(domain: str) -> bool:
    """
    检查域名是否指向私有网络
    :param domain: 要检查的域名
    :return: 如果域名指向私有网络则返回True，否则返回False
    """

    def resolve_dns_records(domain: str) -> list[str] | None:
        """
        解析域名的A和AAAA记录
        :param domain: 要解析的域名（如 'example.com'）
        :return: 包含所有IPv4/IPv6地址的列表，解析失败返回None
        """
        resolver = dns.resolver.Resolver()
        resolver.timeout = 10  # 设置超时时间

        records = []

        try:
            # 解析A记录（IPv4）
            a_answers = resolver.resolve(domain, "A")
            records.extend([answer.to_text() for answer in a_answers])

            # 解析AAAA记录（IPv6）
            aaaa_answers = resolver.resolve(domain, "AAAA")
            records.extend([answer.to_text() for answer in aaaa_answers])

            return records

        except dns.resolver.NoAnswer:
            # 没有对应记录时返回空列表
            return records if records else None
        except dns.resolver.NXDOMAIN:
            logger.warning(f"域名不存在: {domain}")
            return None
        except dns.resolver.Timeout:
            logger.warning("DNS查询超时")
            return None
        except Exception as e:
            logger.warning(f"DNS解析错误: {e!s}")
            return None

    records = resolve_dns_records(domain)
    if records is None:
        return False
    return any(ip_address(record).is_private for record in records if records is True)



@on_command(
    "ping",
    aliases={"PING"},
    state={
        "rm_name": "ping",
        "rm_desc": "发送Ping包",
        "rm_usage": "/ping <ip/domain> [次数（可选）]",
    },
).handle()
async def ping_runner(
    event: MessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    arg_list = args.extract_plain_text().strip().split()
    address = arg_list[0]
    if is_domain_refer_to_private_network(address):
        await matcher.send("请输入正确的地址！")
        return
    if len(arg_list) > 1:
        try:
            count = int(arg_list[1])
            if count > 5:
                raise ValueError
        except ValueError:
            await matcher.send("请输入正确的次数！")
            return
    else:
        count = 3
    try:
        _ip = ip_address(address)
        if _ip.is_private:
            await matcher.send("请输入正确的地址！")
            return
    except ValueError:
        pass
    start_time = time.time()
    result: list[float | None] = [ping(address, size=64) for _ in range(count)]
    stop_time = time.time()
    time_used = stop_time - start_time
    time_used = f"{time_used:.2f}s"
    total = len(result)
    # 统计丢包数量（None 表示超时）
    lost = result.count(None)
    # 计算丢包率百分比
    packet_loss = (lost / total) * 100  # type: float

    # 格式化输出示例（保留两位小数）
    loss_rate = f"丢包率: {packet_loss:.2f}%"
    valid_latency = [r for r in result if r is not None]  # 过滤掉丢包数据(None)
    avg_latency = (
        sum(valid_latency) / len(valid_latency) * 1000 if valid_latency else 0
    )  # 转换为毫秒
    latency_info = f"有效平均延迟: {avg_latency:.2f}ms"
    result_msg = f"""已PING  {address} ({total}个具有64bytes大小发包):{"".join(f"\n第{i}/{len(result)}次 来自 {address} 的响应：{f'{v:2f}ms' if v is not None else '丢包！'}" for i, v in enumerate(result))}
---统计数据---
共发{total}个包 其中{len([i for i in result if i is None])}个丢包 平均丢包率：{loss_rate} 共用时{time_used} {latency_info}"""
    await matcher.send(result_msg)
