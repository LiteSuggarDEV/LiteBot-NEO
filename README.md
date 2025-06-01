# LiteBot-NEO

![lt](https://github.com/user-attachments/assets/cea6ea42-6c01-4e8f-8960-0cfffd301280)

## LiteBot完全重构版

## 如何开始？

1. 克隆仓库 `git clone https://github.com/LiteSuggarDEV/LiteBot-NEO.git`
2. 打开文件夹 `cd LiteBot-NEO`
3. 使用 `uv venv` 创建虚拟环境
    > 如果没有uv，请使用这个命令安装UV `pip install uv`
4. 使用 `uv sync` 安装所有依赖
    > 以上步骤可以使用我们提供的init脚本实现
5. 运行Bot `uv run ./bot.py`
    > 我们在bot.py里做了特殊处理，不建议使用**nb-cli**来运行
