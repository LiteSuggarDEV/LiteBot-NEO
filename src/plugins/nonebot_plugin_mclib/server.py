import re

import dns.resolver
from mcstatus import BedrockServer, JavaServer
from mcstatus.status_response import BedrockStatusResponse, JavaStatusResponse
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg

from src.plugins.menu.manager import MatcherData

java_status = on_command(
    "mc_java",
    aliases={"mcjava", "mc_java_status", "java服务器"},
    state=MatcherData(
        rm_name="我的世界java服务器查询",
        rm_desc="获取一个Java版服务器状态",
        rm_usage="mc_java <server_address>",
    ).model_dump(),
)
be_status = on_command(
    "mc_be",
    aliases={"mcbedrock", "mc_bedrock_status", "bedrock服务器"},
    state=MatcherData(
        rm_name="我的世界基岩版服务器查询",
        rm_desc="获取一个基岩版服务器状态",
        rm_usage="mc_be <server_address>",
    ).model_dump(),
)


async def resolve_srv_record(host: str):
    try:
        query = f"_minecraft._tcp.{host}"
        srv_ans = dns.resolver.resolve(query, "SRV")
        return [
            {

                "priority": r.priority,
                "weight": r.weight,
                "port": r.port,
                "target": r.target.to_text(),
            }
            for r in srv_ans.response.answer[0].items
        ]
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN) as e:
        logger.warning(f"SRV lookup failed: {e!s}")
        return None


def parse_host_port(location: str) -> tuple[str, int]:
    host_port_args = location.split(":", maxsplit=1)
    host = host_port_args[0]
    port = int(host_port_args[1]) if len(host_port_args) > 1 else 25565
    return host, port



async def get_server_status(address: str) -> JavaStatusResponse:
    server = await JavaServer.async_lookup(address)
    return await server.async_status()


async def get_ip(address: str) -> str:
    """获取服务器IP地址"""
    host, port = parse_host_port(address)
    try:
        a_record = dns.resolver.resolve(host, "A")[0]
        logger.info(f"A record for {host}: {a_record}")
        return str(a_record)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        srv_records = await resolve_srv_record(host)
        logger.info(f"SRV records for {host}: {srv_records}")
        if srv_records:
            srv_host = srv_records[0]["target"]
            try:
                a_record = dns.resolver.resolve(srv_host, "A")[0]
                return str(a_record)
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                return srv_host
        return host


def format_be_status_message(
    address: str, status_response: BedrockStatusResponse
) -> str:
    # 正则过滤motd的颜色字符和多余的空格
    motd = re.sub(
        r"\n\s*",
        "\n",
        re.sub(
            r"§[0-9a-fk-or]",
            "",
            status_response.motd.to_minecraft(),
            flags=re.IGNORECASE,
        ),
    )
    return (
        "成功获取到服务器信息！\n"
        + f"服务器地址：{address}\n"
        + f"服务器版本/信息：{status_response.version}\n"
        + f"延迟：{int(status_response.latency)}ms\n"
        + f"地图名称：{status_response.map_name}\n"
        + f"游戏模式：{status_response.gamemode}\n"
        + f"玩家数{status_response.players.online}/{status_response.players.max}\n"
        + f"玩家数：{status_response.players.online}/{status_response.players.max}\n"
        + f"MOTD: {motd}\n"

    )


def format_status_message(

    address: str, ip: str, status_response: JavaStatusResponse
) -> str:
    # 正则过滤motd的颜色字符和多余的空格
    motd = re.sub(
        r"\n\s*",
        "\n",
        re.sub(
            r"§[0-9a-fk-or]",
            "",
            status_response.motd.to_minecraft(),
            flags=re.IGNORECASE,
        ),
    )
    return (
        "成功获取到服务器信息！\n"
        + f"服务器地址：{address}\n"
        + f"服务器IP：{ip}\n"
        + f"服务器延迟：{status_response.latency}ms\n"
        + f"服务器协议版本：{status_response.version.protocol}\n"
        + f"服务端版本/信息：{status_response.version.name}\n"
        + f"玩家数：{status_response.players.online}/{status_response.players.max}\n"
        + f"MOTD: {motd}"
    )


@java_status.handle()
async def _(args: Message = CommandArg()):
    if not (location := args.extract_plain_text()):
        await java_status.send("请输入地址！")
        return

    try:
        status_response = await get_server_status(location)
        ip = await get_ip(location)
    except Exception:
        logger.exception("获取Java服务器状态失败")
        await java_status.finish(
            "获取失败（服务器不在线吗？）\n请检查地址格式是否正确。"
        )
    else:
        await java_status.finish(format_status_message(location, ip, status_response))


@be_status.handle()
async def _(args: Message = CommandArg()):
    if not (location := args.extract_plain_text()):
        await be_status.finish("请输入地址！")
    try:
        server = BedrockServer.lookup(location)
        status = await server.async_status()
        await be_status.send(format_be_status_message(location, status))
    except Exception:
        await be_status.send("获取失败（服务器不在线吗？）")
