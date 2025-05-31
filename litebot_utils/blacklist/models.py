from nonebot_plugin_tortoise_orm import add_model
from tortoise import fields
from tortoise.models import Model

add_model(__name__)


class GroupBlacklist(Model):
    group_id = fields.CharField(max_length=50, pk=True)
    reason = fields.TextField()

    class Meta:
        table = "group_blacklist"


class PrivateBlacklist(Model):
    user_id = fields.CharField(max_length=50, pk=True)
    reason = fields.TextField()

    class Meta:
        table = "private_blacklist"
