from ipaddress import ip_address

import dns.resolver
from nonebot import logger


def is_ip_address(address: str) -> bool:
    """
    判断字符串是否为有效的IP地址
    :param address: 要判断的字符串
    :return: 如果是IP地址返回True，否则返回False
    """
    try:
        ip_address(address)
        return True
    except ValueError:
        return False

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
