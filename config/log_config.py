import logging
import os.path
import uuid
from logging import Logger, LogRecord, getLogger
from typing import Optional
from config.app_config import settings
from logging.handlers import TimedRotatingFileHandler


class CustomContextFilter(logging.Filter):
    def __init__(self, initial_request_id: Optional[str] = None):
        super().__init__()
        self.request_id = initial_request_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = self.request_id
        return True


class RequestFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        record.request_id = getattr(record, 'request_id', '')  # Safe retrieval of request_id
        return super().format(record)


# 创建一个自定义的 ContextFilter，并设置初始的 request_id
context_filter = CustomContextFilter(None)


def set_log_id():
    # 生成一个唯一的 request_id
    request_id = str(uuid.uuid4())

    # 更新 ContextFilter 中的 request_id
    context_filter.request_id = request_id


def logger():
    # 创建一个日志记录器
    logger = logging.getLogger('fastapi_app')
    logger.setLevel(logging.INFO)

    # 添加 ContextFilter 到全局 Logger
    logger.addFilter(context_filter)

    formatter = RequestFormatter(fmt='%(asctime)s - %(request_id)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # 创建一个 handler 将日志输出到控制台
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_dir = os.path.join(settings.sys_dir, settings.log_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file_name = settings.log_file_name
    log_file_path = os.path.join(log_dir, log_file_name)
    # 创建一个文件处理器，并设置编码为 UTF-8
    # 使用 TimedRotatingFileHandler 按日期分割日志文件
    file_handler = TimedRotatingFileHandler(
        log_file_path, when='midnight', interval=1, backupCount=7, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


logger = logger()
