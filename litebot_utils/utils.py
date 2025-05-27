from ipaddress import ip_address

import dns.resolver
import nonebot
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot


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


async def send_to_admin(message):
    """
    发送消息到管理员。

    参数:
    message (str): 要发送的消息内容。
    """
    bot = nonebot.get_bot()
    if isinstance(bot, Bot):
        await bot.send_group_msg(group_id=966016220, message=message)
    print(f"Sending to admin: {message}")
