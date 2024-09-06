import os

from app.helper.directory_helper import get_wx_dir, get_head_session_dir
from app.models.micro_msg import ContactHeadImgUrl
from app.models.misc import ContactHeadImg
from app.models.sys import SysSession
from config.app_config import settings as app_settings
from config.log_config import logger
from db.sys_db import SessionLocal
from db.wx_db import get_session_local
from config.app_config import settings as app_settings
from config.wx_config import settings as wx_settings
from sqlalchemy import text

# 头像固定为 jpg 格式
suffix = '.jpg'


def analyze_head_images(sys_session_id: int):
    logger.info("执行 analyze 任务")
    db = SessionLocal()
    sys_session = db.query(SysSession).filter_by(id=sys_session_id).one()
    try:
        save_header_images(sys_session)
    finally:
        db.close()


def save_header_images(sys_session: SysSession):
    try:
        db_file_path = os.path.join(get_wx_dir(sys_session), wx_settings.db_misc)
        db_session = get_session_local(db_file_path)
        db = db_session()

        db_micro_file_path = os.path.join(get_wx_dir(sys_session), wx_settings.db_micro_msg)
        db_micro_session = get_session_local(db_micro_file_path)
        db_micro_db = db_micro_session()
        try:
            head_path = get_head_session_dir(sys_session)
            if not os.path.exists(head_path):
                os.makedirs(head_path)
            images = db.query(ContactHeadImg).all()
            img_urls_to_insert = []  # 用于批量插入的列表
            for img in images:

                try:
                    img_url = db_micro_db.query(ContactHeadImgUrl).filter_by(usrName=img.usrName).first()
                    if img_url is None:
                        img_url = ContactHeadImgUrl(usrName=img.usrName)
                        # 写入头像到 head/session_id 目录
                        if not os.path.exists(head_path):
                            logger.info(f"写入头像：{head_path}")
                            save_image(str(head_path), img)
                        # 保存头像信息到 ContactHeadImgUrl 表
                        # 访问路径
                        access_path = os.path.join(app_settings.head_mapping, str(sys_session.id), f'{img.usrName}{suffix}')
                        img_url.smallHeadImgUrl = str(access_path)
                        db_micro_db.add(img_url)  # 添加新记录
                    # 每500条插入一次
                    if len(img_urls_to_insert) >= 500:
                        db_micro_db.bulk_save_objects(img_urls_to_insert)
                        db_micro_db.commit()  # 批量提交
                        img_urls_to_insert.clear()  # 清空列表
                except Exception as e:
                    logger.error("写入头像异常")
                    logger.error(e)
            # 处理剩余未满500条的数据
            if img_urls_to_insert:
                db_micro_db.bulk_save_objects(img_urls_to_insert)
                db_micro_db.commit()
        finally:
            db.close()
            db_micro_db.close()
    except Exception as e:
        logger.error("save_header_images error", e)


def save_image(head_path: str, img: ContactHeadImg):
    try:
        img_file_path = os.path.join(head_path, f'{img.usrName}{suffix}')
        logger.info(img_file_path)
        with open(img_file_path, 'wb') as f:
            f.write(img.smallHeadBuf)
    except Exception as e:
        logger.error('保存头像错误', e)
