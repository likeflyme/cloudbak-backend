import time
from typing import Union

from pydantic import BaseModel


class TokenData(BaseModel):
    username: Union[str, None] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class UserSession(BaseModel):
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
    current_session_id: Union[str, None] = None
    state: Union[int, None] = None
    create_time: Union[int, None] = None
    update_time: Union[int, None] = None
    current_session: Union[UserSession, None] = None


class UserInDB(User):
    hashed_password: str
    

class SysSessionSchema(BaseModel):
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

    class Config:
        from_attributes = True


class SysSessionSchemaWithId(SysSessionSchema):
    id: int


