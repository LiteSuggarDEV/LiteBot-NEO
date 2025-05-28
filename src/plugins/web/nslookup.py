import contextlib
from ipaddress import IPv4Address, ip_address

import dns.resolver
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from ..menu.manager import MatcherData


def nslookup_all_records(domain):
    record_types = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA", "SRV"]
    results = []

    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            results.extend([f"{record_type} 记录: {answer}" for answer in answers])
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            results.append(f"{record_type} 记录: 未找到或不存在")
        except Exception as e:
            results.append(f"{record_type} 记录: 错误 - {e!s}")

    return results


@on_command(
    "nslookup",
    aliases={"ns", "nsl"},
    state=MatcherData(
        rm_name="nslookup",
        rm_desc="域名记录查询",
        rm_usage="nslookup <域名/子域名>",
    ).model_dump(),
).handle()
async def nslookup_runner(
    event: MessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    location = args.extract_plain_text()
    if "gov.cn" in location:
        await matcher.send("你 很 刑 啊")
    if not location:
        await matcher.send("请输入地址！格式<域名/子域名>")
        return
    with contextlib.suppress(ValueError):
        ip = ip_address(location)
        return await matcher.send(
            f"这是一个IP{'v4' if isinstance(ip, IPv4Address) else 'v6'}地址"
        )
    message = MessageSegment.text(f"域名{location}的记录：\n")
    for object in nslookup_all_records(location):
        message += MessageSegment.text(f"{object}\n")
    await matcher.send(message)
