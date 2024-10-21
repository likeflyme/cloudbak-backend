from datetime import timedelta

from fastapi import Depends, HTTPException, APIRouter, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import create_access_token, get_current_user, verify_password, get_current_sys_session
from app.models.sys import SysUser, SysSession, SysConfig
from app.schemas.sys_conf_schemas import SysConfigOut
from app.schemas.sys_schemas import Token, User
from config.auth_config import settings
from db.sys_db import get_db

router = APIRouter(
    prefix="/auth"
)


@router.post("/token")
def create_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_db)) -> Token:
    user = session.query(SysUser).filter(
        or_(SysUser.username == form_data.username, SysUser.email == form_data.username)
    ).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="错误的用户名或密码",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=User)
def read_curren_user(db: Session = Depends(get_db),
                     user: User = Depends(get_current_user),
                     session: SysSession = Depends(get_current_sys_session)):
    # 加载用户配置
    session_confs = db.query(SysConfig).filter_by(conf_key='session_conf', user_id=user.id).all()
    user_conf = db.query(SysConfig).filter_by(conf_key='user_conf', user_id=user.id).first()
    sys_conf = None
    if user.id == 1:
        sys_conf = db.query(SysConfig).filter_by(conf_key='sys_conf').first()
    if user_conf:
        session_confs.append(user_conf)
    if sys_conf:
        session_confs.append(sys_conf)
    configs = []
    for conf in session_confs:
        configs.append(SysConfigOut(**conf.__dict__))
    return {
        "id": user.id,
        "username": user.username,
        "current_session_id": user.current_session_id,
        "current_session": session,
        "configs": configs
    }
