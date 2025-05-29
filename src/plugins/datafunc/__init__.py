from nonebot.plugin import PluginMetadata

from . import base64, md5, qr, sha1, sha256

__plugin_meta__ = PluginMetadata(
    name="数据插件",
    description="数据处理功能插件",
    usage="数据处理功能插件",
    type="application",
)

__all__ = ["base64", "md5", "qr", "sha1", "sha256"]
