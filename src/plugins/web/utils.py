from ipaddress import ip_address

import dns.resolver
from nonebot import logger

resolver = dns.resolver.Resolver()
resolver.timeout = 5  # 设置超时时间
resolver.nameservers = [
    "1.1.1.1",
    "8.8.8.8",
]


def is_valid_domain(domain: str) -> bool:
    """
    检查字符串是否为有效的域名
    :param domain: 要检查的字符串
    :return: 如果是有效的域名返回True，否则返回False
    """
    try:
        resolver.resolve(domain, "A")
        return True
    except dns.resolver.NoAnswer:
        return False
    except dns.resolver.NXDOMAIN:
        return False
    except Exception as e:
        logger.warning(f"DNS解析错误: {e!s}")
        return False


def is_domain_refer_to_private_network(domain: str) -> bool:
    """
    检查域名是否指向私有网络
    :param domain: 要检查的域名
    :return: 如果域名指向私有网络则返回True，否则返回False
    """
    records = resolve_dns_records(domain)
    if records is None:
        return False
    return any(ip_address(record).is_private for record in records if records is True)


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


def is_ip_in_private_network(address: str) -> bool:
    """
    判断IP地址是否属于私有网络
    :param ip_address: 要判断的IP地址
    :return: 如果是私有网络返回True，否则返回False
    """
    try:
        addr = ip_address(address)
        return addr.is_private
    except ValueError:
        return False


def resolve_dns_records(domain: str, v4only: bool = False) -> list[str] | None:
    """解析A/AAAA记录

    Args:
        domain (str): 域名
        v4only (bool, optional): 是否仅解析V4. Defaults to False.

    Returns:
        list[str] | None: 如果失败返回None,成功返回列表
    """

    records = []

    try:
        # 解析A记录（IPv4）
        a_answers = resolver.resolve(domain, "A")
        records.extend([answer.to_text() for answer in a_answers])

        if not v4only:
            # 解析AAAA记录（IPv6）
            aaaa_answers = resolver.resolve(domain, "AAAA")
            records.extend([answer.to_text() for answer in aaaa_answers])

        return records

    except dns.resolver.NoAnswer:
        # 没有对应记录时返回空列表
        return records or None
    except dns.resolver.NXDOMAIN:
        logger.warning(f"域名不存在: {domain}")
        return None
    except dns.resolver.Timeout:
        logger.warning("DNS查询超时")
        return None
    except Exception as e:
        logger.warning(f"DNS解析错误: {e!s}")
        return None
