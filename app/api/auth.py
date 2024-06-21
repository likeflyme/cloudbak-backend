from datetime import timedelta

from fastapi import Depends, HTTPException, APIRouter, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import create_access_token, get_current_user, verify_password
from app.models.sys import SysUser
from app.schemas.sys_schemas import Token, User
from config.auth_config import settings
from db.sys_db import get_db

router = APIRouter(
    prefix="/auth"
)


@router.post("/token")
def create_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_db)) -> Token:
    user = session.query(SysUser).filter_by(username=form_data.username).first()
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


@router.get("/users/me/", response_model=User)
def read_curren_user(user: User = Depends(get_current_user)):
    return user
