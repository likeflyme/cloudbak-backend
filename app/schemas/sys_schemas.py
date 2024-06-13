from typing import Union

from pydantic import BaseModel


class TokenData(BaseModel):
    username: Union[str, None] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    id: int
    username: str
    nickname: Union[str, None] = None
    current_wx_id: Union[str, None] = None
    state: int
    create_time: int
    update_time: int


class UserInDB(User):
    hashed_password: str
