import os
import shutil

from config.log_config import logger
from app.models.sys import SysSession
from db.wx_db import clear_session_db_cache
from ..helper.directory_helper import get_session_dir


def clear_session(sys_session: SysSession):
    logger.info(f"清除session数据，session id： {sys_session.id}")
    session_dir = get_session_dir(sys_session.id)
    clear_session_db_cache(session_dir)
    logger.info(f"session_dir: {session_dir}")
    if os.path.exists(session_dir):
        logger.info(f"folder exists, execute delete")
        try:
            shutil.rmtree(session_dir)
            logger.info("session directory deleted successfully")
        except PermissionError as e:
            logger.error(f"PermissionError: {e}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
