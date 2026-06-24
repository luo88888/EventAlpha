"""日志基础设施：统一配置 root logger，同时输出到文件和控制台。

文件输出使用 RotatingFileHandler（按大小自动轮转），控制台输出使用 StreamHandler。
使用方式：各模块通过 logging.getLogger(__name__) 获取 logger，自动继承此配置。
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

from utils.config_handler import load_logging_config


def setup_logging() -> None:
    """配置全局日志系统。

    应在应用启动时调用一次（main.py 模块加载阶段即可）。
    - 控制台输出：StreamHandler -> sys.stdout
    - 文件输出：RotatingFileHandler（按大小自动切分）
    """
    config = load_logging_config()

    # 确保日志目录存在
    log_path = Path(config.file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 获取 root logger 并设置级别
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper(), logging.INFO))

    # 清除已有 handler（避免 uvicorn reload 时重复添加）
    root_logger.handlers.clear()

    # 日志格式化器
    formatter = logging.Formatter(config.format, datefmt=config.datefmt)

    # 控制台 handler
    if config.console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # 文件 handler（按大小轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_path),
        maxBytes=config.file_max_bytes,
        backupCount=config.file_backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 确保 uvicorn 等第三方 logger 传播到 root（否则它们的日志只走自己的 handler）
    for _name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        _logger = logging.getLogger(_name)
        _logger.handlers.clear()
        _logger.propagate = True
