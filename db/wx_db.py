from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import app_config
from config import data_config
from collections import defaultdict
from app.models.multi import msg
from app.dependencies import dependencies


# 保存 session local
session_local_dict = defaultdict(lambda: None)

multi_msg0_db = data_config.settings.msg_path + data_config.settings.multi_msg_db
micro_msg_db = data_config.settings.msg_path + data_config.settings.micro_msg_db


def get_session_local(db_path):
    """Retrieve or create a SessionLocal for the given db_path."""
    if session_local_dict[db_path] is None:
        engine = create_engine(
            f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
        )
        session_local_dict[db_path] = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return session_local_dict[db_path]


def get_default_db():
    return "D:\wxdec\wx\wxid_b125nd5rc59r12\Msg\Multi\decoded_MSG0.db"


def get_db(db_path: str = Depends(get_default_db)):
    """Generate a new database session for the given db_path."""
    SessionLocal = get_session_local(db_path)
    my_db = SessionLocal()
    try:
        yield my_db
    finally:
        my_db.close()


def wx_db_msg0(wxid: str = Depends(dependencies.get_wx_id)):
    db_path = "%s%s%s/%s" % (app_config.settings.sys_dir, data_config.settings.home, wxid, multi_msg0_db)
    SessionLocal = get_session_local(db_path)
    my_db = SessionLocal()
    try:
        yield my_db
    finally:
        my_db.close()


def wx_db_micro_msg(wxid: str = Depends(dependencies.get_wx_id)):
    db_path = "%s%s%s/%s" % (app_config.settings.sys_dir, data_config.settings.home, wxid, micro_msg_db)
    print(db_path)
    SessionLocal = get_session_local(db_path)
    my_db = SessionLocal()
    try:
        yield my_db
    finally:
        my_db.close()
