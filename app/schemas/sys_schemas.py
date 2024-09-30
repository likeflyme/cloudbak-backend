import time
from typing import Union

from pydantic import BaseModel


class TokenData(BaseModel):
    username: Union[str, None] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class UserSession(BaseModel):
    id: int
    name: str | None = None
    desc: str | None = None
    wx_id: str | None = None
    wx_name: str | None = None
    wx_acct_name: str | None = None
    wx_key: str | None = None
    wx_mobile: str | None = None
    wx_email: str | None = None
    create_time: int = time.time()
    update_time: int = time.time()
    owner_id: int


class User(BaseModel):
    id: int
    username: str
    nickname: Union[str, None] = None
    current_session_id: Union[int, None] = None
    state: Union[int, None] = None
    create_time: Union[int, None] = None
    update_time: Union[int, None] = None
    current_session: Union[UserSession, None] = None


class UserInDB(User):
    hashed_password: str


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class SysSessionIn(BaseModel):
    name: str | None = None
    desc: str | None = None
    wx_id: str | None = None
    wx_name: str | None = None
    wx_acct_name: str | None = None
    wx_key: str | None = None
    wx_mobile: str | None = None
    wx_dir: str | None = None

    class Config:
        from_attributes = True


class SysSessionUpdate(BaseModel):
    name: str
    desc: str | None = None
    wx_key: str
    wx_id: str
    wx_name: str
    wx_acct_name: str
    wx_key: str
    wx_mobile: str | None = None
    update_time: int

    class Config:
        from_attributes = True


class SysSessionSchema(BaseModel):
    id: int
    name: str | None = None
    desc: str | None = None
    wx_id: str | None = None
    wx_name: str | None = None
    wx_acct_name: str | None = None
    wx_mobile: str | None = None
    wx_email: str | None = None
    wx_dir: str | None = None
    create_time: int | None = None
    update_time: int | None = None
    owner_id: int

    class Config:
        from_attributes = True


class SysSessionOut(BaseModel):
    id: int
    name: str | None = None
    desc: str | None = None
    wx_id: str | None = None
    wx_name: str | None = None
    wx_acct_name: str | None = None
    wx_mobile: str | None = None
    wx_email: str | None = None
    wx_dir: str | None = None
    owner_id: int
    analyze_state: int
    create_time: int
    update_time: int

    class Config:
        from_attributes = True


class SysSessionSchemaWithId(SysSessionSchema):
    id: int


class SysSessionSchemaWithHeadImg(SysSessionSchema):
    id: int
    smallHeadImgUrl: str | None = None
    bigHeadImgUrl: str | None = None
    wx_key: str | None = None
    data_path: str | None = None


class CreateSysSessionSchema(BaseModel):
    name: str
    wx_key: str
    wx_id: str
    wx_name: str
    wx_acct_name: str
    wx_mobile: str | None = None


class SysTaskOut(BaseModel):
    id: int
    name: str
    state: int
    detail: str | None = None
    create_time: float
    update_time: float
    owner_id: int



