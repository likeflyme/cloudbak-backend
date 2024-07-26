import os
import zipfile

from app.models.sys import SysSession
from app.services.decode_wx_db import decode_msg
from config.log_config import logger
from db.sys_db import SessionLocal
from .decode_wx_pictures import decrypt_images
from .save_head_images import save_header_images
from ..helper.directory_helper import get_session_dir, get_wx_dir


def unzip(zip_path: str, extract_path: str):
    logger.info('解压 zip 文件: %s', zip_path)
    os.makedirs(extract_path, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(str(extract_path))
    logger.info("解压完成")


def analyze(sys_session_id: int):
    """
    用户上传的zip文件分析处理
    :param sys_session_id: 用户建立的 session_id
    :return:
    """
    logger.info("执行 analyze 任务")
    db = SessionLocal()
    try:
        sys_session = db.query(SysSession).filter_by(id=sys_session_id).first()
    finally:
        db.close()
    # 1. decode 数据库
    logger.info("数据库文件解密")
    decode_msg(sys_session)
    logger.info("数据库解密完成")

    # 2. 头像提取
    logger.info("头像提取")
    save_header_images(sys_session)
    logger.info("头像提取完成")

    # 3. 图片解码
    # 图片路径
    logger.info("图片解码")
    decrypt_images(sys_session)
    logger.info("图片解码完成")

    # 4. 语音文件解码


