from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_user, get_current_sys_session
from app.models.sys import SysUser, SysConfig, SysSession
from app.schemas.sys_conf_schemas import SysConfigOut
from db.sys_db import get_db
from sqlalchemy import select

router = APIRouter(
    prefix="/conf"
)


@router.post("/update-conf")
def update_conf(conf_key, conf_value,
                sys_user: SysUser = Depends(get_current_user),
                sys_session: SysSession = Depends(get_current_sys_session),
                db: Session = Depends(get_db)):
    """
    修改配置
    配置分三个级别：sys_conf 系统级别配置，user_conf 用户级别配置，session_conf 会话级别配置
    用户为配置则设置默认配置
    :param conf_key:
    :param conf_value:
    :param sys_user:
    :param sys_session:
    :param db:
    :return:
    """
    stmt = select(SysConfig).where(SysConfig.conf_key == conf_key)
    if conf_key == 'user_conf':
        stmt = stmt.where(SysConfig.user_id == sys_user.id)
    elif conf_key == 'session_conf':
        stmt = stmt.where(SysConfig.session_id == sys_session.id).where(SysConfig.user_id == sys_user.id)
    conf = db.execute(stmt).first()
    if conf:
        conf.conf_value = conf_value
        conf.commit()



