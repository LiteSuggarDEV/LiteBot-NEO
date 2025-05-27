from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.params import CommandArg
from ipaddress import ip_address, IPv4Address
import dns.resolver


def nslookup_all_records(domain):
    record_types = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA", "SRV"]
    results = []

    for record_type in record_types:
        try:
            answers = dns.resolver.resolve(domain, record_type)
            for answer in answers:
                results.append(f"{record_type} 记录: {answer}")
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            results.append(f"{record_type} 记录: 未找到或不存在")
        except Exception as e:
            results.append(f"{record_type} 记录: 错误 - {str(e)}")

    return results


async def nslookup_runner(event: MessageEvent, matcher: Matcher, args: Message = CommandArg()):
    location = args.extract_plain_text()
    if "gov.cn" in location:
        await matcher.send("你 很 刑 啊")
    if not location:
        await matcher.send("请输入地址！格式<域名/子域名>")
        return
    try:
        ip = ip_address(location)
        return await matcher.send(
            f"这是一个IP{'v4' if isinstance(ip, IPv4Address) else 'v6'}地址"
        )
    except ValueError:
        pass
    message = MessageSegment.text(f"域名{location}的记录：\n")
    for object in nslookup_all_records(location):
        message += MessageSegment.text(f"{object}\n")
    await matcher.send(message)
