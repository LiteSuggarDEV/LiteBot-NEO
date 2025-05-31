import json
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Optional

from nonebot import logger, require
from nonebot_plugin_localstore import get_config_dir
from pydantic import BaseModel
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

require("nonebot_plugin_localstore")

config_dir = get_config_dir("LiteBot")


class Config(BaseModel):
    """插件配置"""

    rate_limit: int = 3  # 请求节流时间（秒）
    admins: list[str] = ["3196373166"]


class _ConfigFileChangeHandler(FileSystemEventHandler):
    """配置文件变更监听器"""

    def __init__(self, manager: "ConfigManager"):
        self.manager = manager

    def on_modified(self, event):
        if event.src_path == str(self.manager.config_path):
            logger.info("检测到配置文件变更，正在自动重载...")
            self.manager.reload_config()


@dataclass
class ConfigManager:
    config_path: Path = config_dir / "config.json"
    _config: Config = field(default_factory=Config)
    _lock: Lock = field(default_factory=Lock, init=False)

    _instance: Optional["ConfigManager"] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self.load_config()
        self._start_watchdog()

    def load_config(self) -> None:
        """加载配置文件"""
        with self._lock:
            if not self.config_path.exists():
                self.save_config()
            else:
                with self.config_path.open("r", encoding="utf-8") as f:
                    self._config = Config.model_validate(json.load(f))

    def reload_config(self) -> Config:
        """重载配置文件"""
        self.load_config()
        return self._config

    def save_config(self) -> None:
        """保存配置文件"""
        with self._lock:
            with self.config_path.open("w", encoding="utf-8") as f:
                json.dump(self._config.model_dump(), f, ensure_ascii=False, indent=4)

    def override_config(self, config: Config) -> None:
        """覆写配置文件"""
        safe_old = self._safe_dump(self._config)
        safe_new = self._safe_dump(config)

        logger.warning(
            "正在覆写配置文件!\n原始值:\n%s\n修改后:\n%s", safe_old, safe_new
        )

        with self._lock:
            self._config = Config.model_validate(config)
            self.save_config()

    def get_config(self) -> Config:
        """获取配置对象"""
        return self._config

    @property
    def config(self) -> Config:
        """只读配置属性"""
        return self._config

    def _start_watchdog(self):
        """启动配置文件监听器（自动热重载）"""
        event_handler = _ConfigFileChangeHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.config_path.parent), recursive=False)
        observer.daemon = True
        observer.start()

    @staticmethod
    def _safe_dump(config: Config) -> str:
        """脱敏配置（隐藏敏感字段）"""
        config_dict = config.model_dump()
        if "admins" in config_dict:
            config_dict["admins"] = ["***"]
        return json.dumps(config_dict, ensure_ascii=False, indent=2)

    @classmethod
    def instance(cls) -> "ConfigManager":
        """获取单例实例"""
        if not hasattr(cls, "_singleton_instance") or cls._singleton_instance is None:
            cls._singleton_instance = cls()
        return cls._singleton_instance
