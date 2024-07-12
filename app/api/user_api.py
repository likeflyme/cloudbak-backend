from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_user
from app.models.sys import SysUser, SysSession
from app.schemas.sys_schemas import SysSessionSchemaWithId, SysSessionIn, SysSessionOut
from config.log_config import logger
from db.sys_db import get_db

router = APIRouter(
    prefix="/user"
)


@router.put("/set-current-session-id", response_model=SysSessionSchemaWithId)
def update_current_session(sys_session_id: int, user: SysUser = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    db_user = db.query(SysUser).filter_by(id=user.id).first()
    db_user.current_session_id = sys_session_id
    db.commit()
    # 缓存中的数据
    user.current_session_id = sys_session_id
    return db.query(SysSession).filter_by(id=sys_session_id).first()


@router.get("/sys-sessions", response_model=List[SysSessionOut])
def session_list(user: SysUser = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    return db.query(SysSession).filter_by(owner_id=user.id).all()


@router.post("/sys-session", response_model=SysSessionSchemaWithId)
def create_session(
        sys_session_in: SysSessionIn,
        user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)):
    logger.info("sys_session创建")
    logger.info(sys_session_in)

    sys_session = SysSession(**sys_session_in.__dict__)
    sys_session.owner = user
    db.add(sys_session)
    db.commit()
    db.refresh(sys_session)
    # 没有设置用户 session，则设置新添加的 session 为用户当前 session
    db_user = db.query(SysUser).filter_by(id=user.id).first()
    if not db_user.current_session_id:
        db_user.current_session_id = sys_session.id
        user.current_session_id = sys_session.id
        db.commit()
    return sys_session

