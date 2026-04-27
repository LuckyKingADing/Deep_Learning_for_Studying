import os

def get_parent_directory(path):
    """
    获取给定路径的父目录
    :param path: 输入路径
    :return: 父目录路径
    """
    # 第一次分割：获取文件所在目录（即路径部分）
    path_str = os.path.dirname(path)
    
    # 第二次分割：提取父目录
    parent_dir = os.path.dirname(path_str)
    
    return parent_dir
