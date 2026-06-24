"""
路径工具函数。
根目录：backend/
"""
import os
from pathlib import Path


def get_root_dir() -> str:
    """获取项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_abs_path(rel_path: str) -> str:
    """获取绝对路径"""
    return os.path.join(get_root_dir(), rel_path)
