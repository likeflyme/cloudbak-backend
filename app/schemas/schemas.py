from typing import Optional

from pydantic import BaseModel


class MsgBase(BaseModel):
    localId: int
    TalkerId: int
    Type: int
    SubType: int
    IsSender: int
    CreateTime: int
    Sequence: int
    StatusEx: int
    Status: int
    MsgServerSeq: Optional[int] = None
    MsgSequence: Optional[int] = None
    StrTalker: Optional[str] = None
    StrContent: Optional[str] = None
    DisplayContent: Optional[str] = None


class Msg(MsgBase):

    class Config:
        from_attributes = True


class Session(BaseModel):
    strUsrName: str
    nOrder: Optional[int] = None
    nUnReadCount: Optional[int] = None
    parentRef: Optional[str] = None
    Reserved0: Optional[int] = None
    Reserved1: Optional[str] = None
    strNickName: Optional[str] = None
    nStatus: Optional[int] = None
    nIsSend: Optional[int] = None
    strContent: Optional[str] = None
    nMsgType: Optional[int] = None
    nMsgLocalID: Optional[int] = None
    nMsgStatus: Optional[int] = None
    nTime: Optional[int] = None
    editContent: Optional[str] = None
    othersAtMe: Optional[int] = None
    Reserved2: Optional[int] = None
    Reserved3: Optional[str] = None
    Reserved4: Optional[int] = None
    Reserved5: Optional[str] = None


class MsgDetail(MsgBase):
    Reserved0: Optional[int] = None
    Reserved1: Optional[int] = None
    Reserved2: Optional[int] = None
    Reserved3: Optional[int] = None
    Reserved4: Optional[int] = None
    Reserved5: Optional[int] = None
    Reserved6: Optional[int] = None
    CompressContent: Optional[str] = None
    BytesExtra: Optional[str] = None
    BytesTrans: Optional[str] = None
