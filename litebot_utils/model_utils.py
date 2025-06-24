from typing import Any

from nonebot import logger
from pydantic import BaseModel, Field, ValidationError, create_model
from tortoise import Model, Tortoise, fields
from tqdm import tqdm


def create_model_by_tortoise_model(model: Model|type[Model]) -> type[BaseModel]:
    """使用Tortoise ORM 模型创建 Pydantic 模型

    Args:
        model (type[Model]): ORM 模型

    Returns:
        type[BaseModel]: Pydantic2 模型
    """
    fields_map = model._meta.fields_map
    pydantic_fields = {}

    for field_name, field_obj in fields_map.items():
        # 获取字段类型和默认值
        field_type = field_obj.field_type
        default_value = field_obj.default

        # 处理特殊字段类型
        if isinstance(field_obj, fields.JSONField):
            field_type = dict
        elif isinstance(field_obj, fields.TextField):
            field_type = str

        # 添加到Pydantic字段定义
        pydantic_fields[field_name] = (
            field_type,
            Field(default=default_value, description=field_obj.description),
        )

    # 创建动态Pydantic模型
    ModelSchema = create_model("ModelSchema", **pydantic_fields, __base__=BaseModel)
    return ModelSchema


def create_dynamic_model(**kwargs) -> type[BaseModel]:
    """根据传入的关键字参数动态创建 Pydantic 模型

    Returns:
        type[BaseModel]: Pydantic2 模型
    """
    # 构建字段定义字典：{字段名: (类型, 默认值)}
    fields = {}

    for key, value in kwargs.items():
        # 自动推断类型
        field_type = type(value) if value is not None else Any
        # 创建字段定义 (类型, 默认值)
        fields[key] = (field_type, Field(default=value))

    # 使用 create_model 动态创建模型类
    DynamicModel = create_model(
        "DynamicModel",
        __base__=BaseModel,
        **fields,
    )
    return DynamicModel


async def migrate_data(model:Model|type[Model]):
    # 获取所有记录
    if records := await model.all():
        validated_data = []
        fields_map = model._meta.fields_map
        GroupConfigSchema = create_model_by_tortoise_model(model)
        logger.info(f"正在校验/迁移数据库模型-{model._meta.full_name}...")
        # 遍历校验并转换数据
        with tqdm(
            total=len(validated_data), unit="个", unit_scale=True, desc="校验数据"
        ) as pbar:
            for record in records:
                try:
                    # 转换ORM对象
                    record_dict = {
                        field: getattr(record, field) for field in fields_map
                    }

                    # 校验数据
                    validated = GroupConfigSchema(**record_dict)

                    # 转换为新字典结构（可在此修改字段）
                    new_data = validated.model_dump()
                    validated_data.append(new_data)
                except ValidationError as e:
                    logger.exception(f"数据校验失败: {e}")
                    # 保留原始数据作为后备
                    record_dict = {
                        field: getattr(record, field) for field in fields_map
                    }
                    validated_data.append(record_dict)
                finally:
                    pbar.update(1)
        with tqdm(
            total=len(validated_data), unit="条", unit_scale=True, desc="更新数据库"
        ) as pbar:
            # 更新数据库
            async with Tortoise.get_connection("default")._in_transaction():
                # 清空原表
                await model.all().delete()

                # 批量插入校验后的数据
                for data in validated_data:
                    await model.create(**data)
                    pbar.update(1)
        logger.success(f"迁移完成！共处理 {len(validated_data)} 条记录")
