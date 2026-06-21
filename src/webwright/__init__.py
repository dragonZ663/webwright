from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol

# 如果未安装dotenv，用一个 _DotvimShim 桩类替代，其 load_dotenv 什么也不做直接返回 False。、
# 这样程序在不安装 python-dotenv 的情况下也能导入
try:
    import dotenv
except ModuleNotFoundError:
    class _DotenvShim:
        @staticmethod
        def load_dotenv(*args, **kwargs):
            return False
    dotenv = _DotenvShim()

# 如果未安装platformdirs，用一个简单的 user_config_dir 函数替代，直接返回 ~/.config/<appname>。
try:
    from platformdirs import user_config_dir
except ModuleNotFoundError:
    def user_config_dir(appname: str) -> str:
        return str(Path.home() / ".config" / appname)

__version__ = "0.1.0"

package_dir = Path(__file__).resolve().parent
# 通过环境变量 MSWEBA_GLOBAL_CONFIG_DIR 或 系统约定配置目录（跨平台，如 Linux 的 ~/.config/webwright）确定全局配置目录。
global_config_dir = Path(
    os.getenv("MSWEBA_GLOBAL_CONFIG_DIR") or user_config_dir("webwright")
)
global_config_dir.mkdir(parents=True, exist_ok=True)
global_config_file = global_config_dir / ".env"
# 从该目录下的 .env 文件加载环境变量。这意味着用户可以在 ~/.config/webwright/.env 中放置配置，程序启动时自动读取。
dotenv.load_dotenv(dotenv_path=global_config_file)


class Model(Protocol):
    config: Any

    def __call__(self, messages: list[dict[str, Any]], **kwargs) -> str: ...

    def query(self, messages: list[dict[str, Any]], **kwargs) -> dict[str, Any]: ...

    def format_message(self, **kwargs) -> dict[str, Any]: ...

    def format_observation_messages(
        self,
        message: dict[str, Any],
        outputs: list[dict[str, Any]],
        template_vars: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...

    def get_template_vars(self, **kwargs) -> dict[str, Any]: ...

    def serialize(self) -> dict[str, Any]: ...


class Environment(Protocol):
    config: Any

    def prepare(self, **kwargs) -> None: ...

    def execute(self, action: dict[str, Any], cwd: str = "") -> dict[str, Any]: ...

    def get_template_vars(self, **kwargs) -> dict[str, Any]: ...

    def serialize(self) -> dict[str, Any]: ...

    def close(self) -> None: ...


class Agent(Protocol):
    config: Any

    def run(self, task: str, **kwargs) -> dict[str, Any]: ...

    def save(self, path: Path | None, *extra_dicts) -> dict[str, Any]: ...


#  导出控制，限制 from webwright import * 时只导出这四个名称。
__all__ = [
    "Agent",
    "Environment",
    "Model",
    "__version__",
    "global_config_dir",
    "global_config_file",
    "package_dir",
]
