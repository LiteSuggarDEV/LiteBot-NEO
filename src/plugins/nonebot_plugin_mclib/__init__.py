from nonebot.plugin import PluginMetadata

from . import player, server

__all__ = ["player", "server"]


__plugin_meta__ = PluginMetadata(
    name="MC服务器/玩家查询",
    description="我的世界服务器状态查询或正版玩家信息查询",
    homepage="https://github.com/LiteSuggarDEV/nonebot_plugin_mclib/",
    usage="https://github.com/LiteSuggarDEV/nonebot_plugin_mclib/",
    type="application",
    supported_adapters={"~onebot.v11"},
)
