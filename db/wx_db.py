import os
from collections import defaultdict

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.dependencies.auth_dep import get_current_wx_id, get_current_sys_session
from app.helper.directory_helper import get_wx_dir
from app.models.sys import SysSession
from config import app_config
from config import data_config
from sqlalchemy.ext.declarative import declarative_base
from config.log_config import logger
from config.wx_config import settings as wx_settings

Base = declarative_base()

# 保存 session local
session_local_dict = defaultdict(lambda: None)


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


def wx_db_msg(c: int, sys_session: SysSession):
    db_path = os.path.join(get_wx_dir(sys_session), wx_settings.db_multi_msg + str(c) + '.db')
    if not os.path.exists(db_path):
        return None
    return get_session_local(db_path)


def wx_db_msg0(curren_session: SysSession = Depends(get_current_sys_session)):
    """
    获取 multi/MSG0.db 数据库 session
    :param wxid: 用户当前微信id
    :return: 数据库 session
    """
    db_path = os.path.join(get_wx_dir(curren_session), wx_settings.db_multi_msg)
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
    db_path = os.path.join(get_wx_dir(curren_session), wx_settings.db_micro_msg)
    logger.info("DB: %s", db_path)
    SessionLocal = get_session_local(db_path)
    my_db = SessionLocal()
    try:
        yield my_db
    finally:
        my_db.close()


def wx_db_hard_link_image(curren_session: SysSession = Depends(get_current_sys_session)):
    """
    获取 micro_msg.db 数据库 session
    :param wxid: 用户当前微信id
    :return: 数据库 session
    """
    db_path = os.path.join(get_wx_dir(curren_session), wx_settings.db_hard_link_image)
    logger.info("DB: %s", db_path)
    SessionLocal = get_session_local(db_path)
    my_db = SessionLocal()
    try:
        yield my_db
    finally:
        my_db.close()


