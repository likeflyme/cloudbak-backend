import os

from app.models.misc import ContactHeadImg
from config.app_config import settings as app_settings
from config.data_config import settings as data_settings
from config.log_config import logger
from db.wx_db import get_session_local

# 头像固定为 jpg 格式
suffix = '.jpg'


def save_header_images(wx_dir: str, sys_session_id, wx_id):
    try:
        db_file_path = os.path.join(wx_dir, data_settings.msg_path, data_settings.misc_db)
        db_session = get_session_local(db_file_path)
        db = db_session()
        try:
            head_path = os.path.join(app_settings.head_dir, sys_session_id, wx_id)
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
