import os

from app.helper.directory_helper import get_wx_dir, get_head_session_dir
from app.models.misc import ContactHeadImg
from app.models.sys import SysSession
from config.app_config import settings as app_settings
from config.log_config import logger
from db.wx_db import get_session_local
from config.app_config import settings as app_settings
from config.wx_config import settings as wx_settings

# 头像固定为 jpg 格式
suffix = '.jpg'


def save_header_images(sys_session: SysSession):
    try:
        db_file_path = os.path.join(get_wx_dir(sys_session), wx_settings.db_misc)
        db_session = get_session_local(db_file_path)
        db = db_session()
        try:
            head_path = get_head_session_dir(sys_session)
            if not os.path.exists(head_path):
                os.makedirs(head_path)
            images = db.query(ContactHeadImg).all()
            for img in images:
                save_image(str(head_path), img)
        finally:
            db.close()
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
