import os
import zipfile

from app.models.sys import SysSession
from app.schemas.sys_schemas import User
from app.services.decode_wx_db import decode_one
from config.app_config import settings as app_settings
from config.data_config import settings as data_settings
from config.log_config import logger
from db.sys_db import SessionLocal
from .decode_wx_pictures import decrypt_files_in_directory

SQLITE_FILE_HEADER = bytes('SQLite format 3', encoding='ASCII') + bytes(1)
IV_SIZE = 16
HMAC_SHA1_SIZE = 20
KEY_SIZE = 32
DEFAULT_PAGESIZE = 4096
DEFAULT_ITER = 64000


def analyze(zip_path: str, user: User, sys_session_id: int):
    """
    用户上传的zip文件分析处理
    :param zip_path: zip 文件路径
    :param user: 用户
    :param sys_session_id: 用户建立的 session_id
    :return:
    """
    logger.info("执行 analyze 任务")
    db = SessionLocal()
    try:
        # 1. 解包
        sys_session = db.query(SysSession).filter_by(id=sys_session_id).first()
        logger.info('解压 zip 文件: %s', zip_path)
        session_dir = os.path.join(app_settings.sys_dir, data_settings.home, sys_session.name)
        os.makedirs(session_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(str(session_dir))
        logger.info("解压完成")
        # 解压后的微信文件目录
        wx_dir = os.path.join(str(session_dir), sys_session.wx_id)
        # 2. 数据库解密
        logger.info("数据库解密")
        # 生成password
        password = bytes.fromhex(sys_session.wx_key.replace(' ', ''))
        # Msg 路径
        msg_dir = os.path.join(str(wx_dir), data_settings.msg_path)
        # 遍历
        for dirpath, dirnames, filenames in os.walk(msg_dir):
            for filename in filenames:
                if filename.endswith('.db'):
                    db_file = os.path.join(dirpath, filename)
                    # 解密，解密的文件为原文件名加 decoded_ 前缀
                    decode_one(db_file, password)
        logger.info("数据库解密完成")
        # 3. 头像提取
        # 4. 图片解码
        # 图片路径
        logger.info("图片解码")
        msg_attach_dir = os.path.join(str(wx_dir), data_settings.file_storage_path, data_settings.msg_attach_path)
        logger.info('图片文件根路径: %s', msg_attach_dir)
        decrypt_files_in_directory(msg_attach_dir)
        logger.info("图片解码完成")
        # 5. 语音文件解码
    finally:
        db.close()

