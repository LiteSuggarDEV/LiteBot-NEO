import base64
import hashlib
from datetime import datetime
from pathlib import Path

from nonebot_plugin_htmlrender import md_to_pic
from nonebot_plugin_localstore import get_config_dir

from .models import PluginData

dir_path = Path(__file__).parent
PAGE_DIR = get_config_dir("LiteBot") / "pages"
PAGE_DIR.mkdir(parents=True, exist_ok=True)
_md_cache: dict[str, str] = {}

def get_css_path() -> str:
    if datetime.now().hour < 7 or datetime.now().hour > 20:
        return str(dir_path / "dark.css")
    else:
        return str(dir_path / "light.css")

def _hash_md(md: str) -> str:
    return hashlib.sha256(md.encode("utf-8")).hexdigest()


async def cached_md_to_pic(md: str, css_path: str) -> str:
    key = _hash_md(md)
    if key in _md_cache:
        return _md_cache[key]

    # 渲染图片，得到 base64
    base64_img = f"base64://{base64.b64encode(await md_to_pic(md=md, css_path=css_path)).decode()}"

    _md_cache[key] = base64_img
    return base64_img





def generate_markdown_menus(plugins: list[PluginData]) -> list[str]:
    """生成 Markdown 菜单列表"""
    head = (
        "# LiteBot 菜单\n\n"
        + "> 这是 LiteBot 的菜单列表，包含所有可用的功能和用法。\n\n"
    )
    head += "## 模块列表\n\n"
    for plugin in plugins:
        if not plugin.metadata or not plugin.matcher_grouping:
            continue
        plugin_name = plugin.metadata.name
        plugin_desc = plugin.metadata.description or "无描述"
        head += f"\n\n- **{plugin_name}**: {plugin_desc}"

    markdown_menus: list[str] = [head.strip()]
    for plugin in plugins:
        if not plugin.matcher_grouping or not plugin.metadata:
            continue

        plugin_title = f"## {plugin.metadata.name}\n"
        plugin_description = (
            f"> {plugin.metadata.description}\n\n"
            if plugin.metadata.description
            else ""
        )
        plugin_markdown = plugin_title + plugin_description
        for matchers in plugin.matcher_grouping.values():
            for matcher_data in matchers:
                plugin_markdown += (
                    f"- **{matcher_data.rm_name}**: {matcher_data.rm_desc}"
                )
                if matcher_data.rm_usage:
                    plugin_markdown += f"\n    - 用法: `{matcher_data.rm_usage}`"
                plugin_markdown += "\n\n"
        markdown_menus.append(plugin_markdown.strip())

    return markdown_menus




