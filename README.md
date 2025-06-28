# LiteBot-NEO

![lt](https://github.com/user-attachments/assets/cea6ea42-6c01-4e8f-8960-0cfffd301280)

## LiteBot完全重构版

### 如何开始？

1. 克隆仓库 `git clone https://github.com/LiteSuggarDEV/LiteBot-NEO.git`
2. 打开文件夹 `cd LiteBot-NEO`
3. 使用 `uv sync` 安装所有依赖
4. 运行Bot `uv run bot.py`

### 配置

### 配置文件

我们有两个配置文件，一个是dotenv文件，一个是yaml文件。

**1.dotenv文件**

参考.env.example（bot启动时会自动创建基于.env.example的.env，请不要修改.env.example，这可能会为后期更新带来麻烦）

```dotenv
DRIVER=~fastapi
HOST=0.0.0.0
PORT=14321
LOCALSTORE_CONFIG_DIR=./config
LOCALSTORE_USE_CWD=true
COMMAND_SEP=[".", " ",""]
SQLALCHEMY_DATABASE_URL=sqlite+aiosqlite:///data.db
```

说明：

1. `DRIVER`: 运行时使用的Nonebot驱动器，LiteBot仅支持fastapi
2. `HOST`: 运行时监听的地址
3. `PORT`: 运行时监听的端口（反向WebSocket）
4. `LOCALSTORE_CONFIG_DIR`: 配置文件存储目录
5. `LOCALSTORE_USE_CWD`: 是否使用当前目录作为配置文件存储目录
6. `COMMAND_SEP`: 命令分隔符
7. `SQLALCHEMY_DATABASE_URL`: 数据库连接字符串

**2.yaml**

```yaml
admins:
- 3196373166
notify_group: []
rate_limit: 3

```

说明：

1. `admins`: 管理员QQ（给出了一个示例）
2. `notify_group`: 日志推送群
3. `rate_limit`: 命令频率限制(秒)W

#### 数据库

- 1. 全新配置

  数据库会自动创建，但是您仍需要注意数据库创建的位置（参考.env.example）。

  e.g.

  ```dotenv
  SQLALCHEMY_DATABASE_URL=sqlite+aiosqlite:///data.db
  ```

- 2. 旧数据库迁移

  **常规迁移更新：**

  开启时ORM插件会询问是否更新数据库，勾选Y继续。或者使用nb-cli

  ```shell
  nb orm upgrade
  ```

  **从TortiseORM迁移（LiteBot旧版本）：**

  由于使用TortoiseORM不会为数据库写入版本，那么您需要手动初始化数据库版本：

  ```shell
  nb orm stamp head
  ```
