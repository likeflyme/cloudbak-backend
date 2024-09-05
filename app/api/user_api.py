from typing import List

from fastapi import Depends, APIRouter, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_user, pwd_context
from app.models.sys import SysUser, SysSession
from app.schemas.sys_schemas import SysSessionSchemaWithId, SysSessionIn, SysSessionOut, UserCreate
from app.services.clear_session import clear_session
from app.services.sys_task_maker import TaskObj, task_execute
from config.log_config import logger
from db.sys_db import get_db

router = APIRouter(
    prefix="/user"
)


@router.get("/check-install")
def check_install(db: Session = Depends(get_db)):
    count = db.query(SysUser).count()
    return {"count": count}


@router.post("/create-user")
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user_count = db.query(SysUser).filter_by(username=user_in.username).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已使用",
        )
    email_count = db.query(SysUser).filter_by(email=user_in.email).count()
    if email_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被使用",
        )
    user = SysUser(**user_in.model_dump())
    user.password = pwd_context.hash(user_in.password)
    db.add(user)
    db.commit()


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


@router.delete("/sys-session/{sys_session_id}")
def delete_session(sys_session_id: int,
                    background_tasks: BackgroundTasks,
                   user: SysUser = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    sys_session = db.query(SysSession).filter_by(id=sys_session_id).first()
    db.delete(sys_session)
    db.commit()

    sys_user = db.query(SysUser).filter_by(id=user.id).first()
    if sys_user is not None and sys_user.current_session_id == sys_session.id:
        first_session = db.query(SysSession).first()
        if first_session is not None:
            sys_user.current_session_id = first_session.id
            db.commit()
    # 异步执行清除硬盘数据
    task_obj = TaskObj(sys_user.id, "清除session数据", clear_session, sys_session)
    background_tasks.add_task(task_execute, task_obj)

