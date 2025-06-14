from nonebot_plugin_tortoise_orm import add_model
from tortoise import Model, fields

add_model(__name__)


class GroupConfig(Model):
    """群配置"""

    group_id = fields.BigIntField(pk=True, index=True)
    switch = fields.BooleanField(default=True)
    welcome = fields.BooleanField(default=False)
    judge = fields.BooleanField(default=False)
    anti_recall = fields.BooleanField(default=False)
    welcome_message = fields.TextField(default="欢迎加入群组！")
    nailong = fields.BooleanField(default=False)
    anti_spam = fields.JSONField(
        default={"limit": 5, "interval": 5, "ban_time": 5, "enable": False}
    )
    anti_link = fields.BooleanField(default=False)
    auto_manage_join = fields.BooleanField(default=False)

    class Meta:
        table = "group_config"
