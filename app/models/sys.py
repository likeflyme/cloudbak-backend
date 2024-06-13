from sqlalchemy import Column, Integer, String

from db.sys_db import Base


class SysUser(Base):
    __tablename__ = "sys_user"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True)
    password = Column(String)
    nickname = Column(String)
    current_wx_id = Column(String)
    state = Column(Integer)
    create_time = Column(Integer)
    update_time = Column(Integer)
