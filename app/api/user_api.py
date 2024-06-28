from typing import List

from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_user
from app.models.sys import SysUser, SysSession
from app.schemas.sys_schemas import SysSessionSchema, SysSessionSchemaWithId
from config.log_config import logger
from db.sys_db import get_db

router = APIRouter(
    prefix="/user"
)


@router.put("set-current-session-id")
def update_current_session(sys_session_id: int, user: SysUser = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    user.current_session_id = sys_session_id
    db.commit()


@router.get("/sessions", response_model=List[SysSessionSchema])
def session_list(user: SysUser = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    return db.query(SysSession).filter_by(owner_id=user.id).all()


@router.post("/session", response_model=SysSessionSchemaWithId)
def create_session(
        sys_session_schema: SysSessionSchema,
        user: SysUser = Depends(get_current_user),
        db: Session = Depends(get_db)):
    logger.info("sys_session创建")
    logger.info(sys_session_schema)
    sys_session = SysSession(**sys_session_schema.__dict__)
    sys_session.owner = user
    db.add(sys_session)
    db.commit()
    db.refresh(sys_session)
    return sys_session

