import shutil


def get_disk_usage_percentage(directory):
    """
    获取指定目录所在磁盘的存储使用百分比。

    参数:
    directory (str): 要检查的目录路径。

    返回:
    float: 磁盘存储使用百分比。
    """
    # 获取目录所在磁盘使用情况
    disk_usage = shutil.disk_usage(directory)

    return (disk_usage.used / disk_usage.total) * 100
