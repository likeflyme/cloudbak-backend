import os
import zipfile

from app.models.sys import SysSession
from app.services.decode_wx_db import decode_msg
from config.log_config import logger
from db.sys_db import SessionLocal
from db.wx_db import clear_wx_db_cache
from .db_order import clear_session_msg_sort, get_sorted_db
from .decode_wx_pictures import decrypt_images
from .save_head_images import save_header_images, analyze_head_images
from ..helper.directory_helper import get_session_dir, get_wx_dir
from app.models.sys import session_analyze_running, session_analyze_end


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
    sys_session = db.query(SysSession).filter_by(id=sys_session_id).first()
    try:
        sys_session.analyze_state = session_analyze_running
        db.commit()

        # 清除微信数据库链接缓存
        logger.info("清除缓存数据库连接")
        clear_wx_db_cache()
        logger.info("清除session消息库排序缓存")
        clear_session_msg_sort(sys_session_id)

        # 1. decode 数据库
        logger.info("数据库文件解密")
        decode_msg(sys_session)
        logger.info("数据库解密完成")

        try:
            logger.info("开始数据库排序")
            get_sorted_db(sys_session)
            logger.info("数据库排序完成")
        except Exception as e:
            logger.error("数据库排序异常")
            logger.error(e)

        # 头像提取
        logger.info("头像提取")
        try:
            analyze_head_images(sys_session_id)
            logger.info("头像提取完成")
        except Exception as e:
            logger.error("头像提取异常")
            logger.error(e)

        # 修改状态为解析完成
        sys_session.analyze_state = session_analyze_end
        db.commit()
    except Exception as e:
        logger.error(e)
    finally:
        db.close()
