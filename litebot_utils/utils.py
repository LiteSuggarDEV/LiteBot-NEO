
import nonebot
from nonebot.adapters.onebot.v11 import Bot


async def send_to_admin(message):
    """
    发送消息到管理员。

    参数:
    message (str): 要发送的消息内容。
    """
    bot = nonebot.get_bot()
    if isinstance(bot, Bot):
        await bot.send_group_msg(group_id=966016220, message=message)
    print(f"Sending to admin: {message}")
