import os

from app.helper.directory_helper import get_wx_dir, get_head_session_dir
from app.models.micro_msg import ContactHeadImgUrl
from app.models.misc import ContactHeadImg
from app.models.sys import SysSession
from config.app_config import settings as app_settings
from config.log_config import get_context_logger
from db.sys_db import SessionLocal
from db.wx_db import get_session_local
from config.app_config import settings as app_settings
from config.wx_config import settings as wx_settings
from sqlalchemy import text

# 头像固定为 jpg 格式
suffix = '.jpg'


def analyze_head_images(sys_session_id: int):
    db = SessionLocal()
    sys_session = db.query(SysSession).filter_by(id=sys_session_id).one()
    try:
        save_header_images(sys_session)
    finally:
        db.close()


def save_header_images(sys_session: SysSession):
    logger = get_context_logger()
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
        for img in images:
            img_url = db_micro_db.query(ContactHeadImgUrl).filter_by(usrName=img.usrName).first()
            if img_url is None:
                logger.info(f"插入 ContactHeadImgUrl: {img.usrName}")
                img_url = ContactHeadImgUrl(usrName=img.usrName)
                db_micro_db.add(img_url)
            if img_url.smallHeadImgUrl is None or len(img_url.smallHeadImgUrl) == 0:
                # 写入头像到 head/session_id 目录
                if os.path.exists(head_path):
                    save_image(str(head_path), img)

                # 保存头像信息到 ContactHeadImgUrl 表
                # 访问路径
                access_path = os.path.join(app_settings.head_mapping, str(sys_session.id), f'{img.usrName}{suffix}')
                logger.info(f"设置头像地址: {access_path}")
                img_url.smallHeadImgUrl = str(access_path)
                db_micro_db.commit()
    finally:
        db.close()
        db_micro_db.close()


def save_image(head_path: str, img: ContactHeadImg):
    logger = get_context_logger()
    try:
        img_file_path = os.path.join(head_path, f'{img.usrName}{suffix}')
        logger.info(f"写入头像 {img_file_path}")
        with open(img_file_path, 'wb') as f:
            f.write(img.smallHeadBuf)
    except Exception as e:
        logger.error('保存头像错误', e)
