from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_user, get_current_sys_session
from app.models.sys import SysUser, SysConfig, SysSession
from app.schemas.sys_conf_schemas import SysConfigOut, SysConfigUpdate
from app.sheduler import reload_all_jobs
from db.sys_db import get_db
from sqlalchemy import select
from config.log_config import logger

router = APIRouter(
    prefix="/conf"
)


@router.post("/update-conf")
def update_conf(conf: SysConfigUpdate,
                sys_user: SysUser = Depends(get_current_user),
                sys_session: SysSession = Depends(get_current_sys_session),
                db: Session = Depends(get_db)):
    """
    修改配置
    配置分三个级别：sys_conf 系统级别配置，user_conf 用户级别配置，session_conf 会话级别配置
    用户为配置则设置默认配置
    :param conf:
    :param sys_user:
    :param sys_session:
    :param db:
    :return:
    """
    stmt = select(SysConfig).where(SysConfig.conf_key == conf.conf_key)
    if conf.conf_key == 'user_conf':
        stmt = stmt.where(SysConfig.user_id == sys_user.id)
    elif conf.conf_key == 'session_conf':
        stmt = stmt.where(SysConfig.session_id == sys_session.id).where(SysConfig.user_id == sys_user.id)
    result = db.execute(stmt).first()
    if result and len(result) == 1:
        conf_instance = result[0]  # or use result.SysConfig if using ORM
        conf_instance.conf_value = conf.conf_value  # Assuming conf_value is what you want to update
        db.commit()
    else:
        logger.info("初始化配置")
        conf = SysConfig(**conf.__dict__)
        if conf.conf_key == 'user_conf':
            conf.user_id = sys_user.id
        elif conf.conf_key == 'session_conf':
            conf.user_id = sys_user.id
            conf.session_id = sys_session.id
        db.add(conf)
        db.commit()

    if conf.conf_key == 'session_conf':
        reload_all_jobs()




