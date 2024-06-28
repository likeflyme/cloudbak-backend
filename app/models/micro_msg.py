from sqlalchemy import Column, Integer, String, LargeBinary

from db.wx_db import Base


class Session(Base):
    __tablename__ = "Session"
    __table_args__ = {'extend_existing': True}

    strUsrName = Column(String, primary_key=True)
    nOrder = Column(Integer)
    nUnReadCount = Column(Integer)
    parentRef = Column(String)
    Reserved0 = Column(Integer)
    Reserved1 = Column(String)
    strNickName = Column(String)
    nStatus = Column(Integer)
    nIsSend = Column(Integer)
    strContent = Column(String)
    nMsgType = Column(Integer)
    nMsgLocalID = Column(Integer)
    nMsgStatus = Column(Integer)
    nTime = Column(Integer)
    editContent = Column(String)
    othersAtMe = Column(Integer)
    Reserved2 = Column(Integer)
    Reserved3 = Column(String)
    Reserved4 = Column(Integer)
    Reserved5 = Column(String)
    bytesXml = Column(LargeBinary)


