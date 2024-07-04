from collections import defaultdict

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.dependencies.auth_dep import get_current_wx_id, get_current_sys_session
from app.models.sys import SysSession
from config import app_config
from config import data_config
from sqlalchemy.ext.declarative import declarative_base
from config.log_config import logger

Base = declarative_base()

# 保存 session local
session_local_dict = defaultdict(lambda: None)

multi_msg0_db = data_config.settings.msg_path + data_config.settings.multi_msg_db
micro_msg_db = data_config.settings.msg_path + data_config.settings.micro_msg_db


def get_session_local(db_path):
    """
    获取对应数据库文件的 session local
    :param db_path: 数据库路径
    :return: SessionLocal
    """
    if session_local_dict[db_path] is None:
        engine = create_engine(
            f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
        )
        session_local_dict[db_path] = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_local_dict[db_path]


def wx_db_msg0(curren_session: SysSession = Depends(get_current_sys_session)):
    """
    获取 multi/MSG0.db 数据库 session
    :param wxid: 用户当前微信id
    :return: 数据库 session
    """
    db_path = f"{app_config.settings.sys_dir}{data_config.settings.home}{curren_session.name}/{curren_session.wx_id}/{multi_msg0_db}"
    SessionLocal = get_session_local(db_path)
    my_db = SessionLocal()
    try:
        yield my_db
    finally:
        my_db.close()


def wx_db_micro_msg(curren_session: SysSession = Depends(get_current_sys_session)):
    """
    获取 micro_msg.db 数据库 session
    :param wxid: 用户当前微信id
    :return: 数据库 session
    """
    db_path = f"{app_config.settings.sys_dir}{data_config.settings.home}{curren_session.name}/{curren_session.wx_id}/{micro_msg_db}"
    logger.info("DB: %s", db_path)
    SessionLocal = get_session_local(db_path)
    my_db = SessionLocal()
    try:
        yield my_db
    finally:
        my_db.close()


