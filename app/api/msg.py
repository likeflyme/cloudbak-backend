from typing import List

from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.models import micro_msg
from app.models.multi import msg
from app.schemas import schemas
from db.wx_db import wx_db_micro_msg, wx_db_msg0

router = APIRouter(
    prefix="/msg"
)


@router.get("/sessions", response_model=List[schemas.SessionBaseOut])
def red_sessions(db: Session = Depends(wx_db_micro_msg)):
    """
    查询会话分页列表
    :param db:
    :return:
    """
    return db.query(micro_msg.Session).order_by(micro_msg.Session.nOrder.desc()).all()


@router.get("/msgs", response_model=Page[schemas.MsgBase])
def red_msgs(strUsrName: str,
             page: int = 1,
             size: int = 20,
             db: Session = Depends(wx_db_msg0)):
    """
    分页查询用户分页消息
    :param strUsrName: 微信号
    :param page: 页码
    :param size: 分页大小
    :param db: 数据库
    :return: 分页数据
    """
    # 先根据 strUsrName 在 Name2ID 表中查询 id
    names = db.query(msg.Name2ID).all()
    talker_id = 1
    for name in names:
        if name.UsrName == strUsrName:
            break
        talker_id = talker_id + 1
    # 再根据id查询消息列表
    return paginate(db.query(msg.Msg).filter_by(TalkerId=talker_id).order_by(msg.Msg.localId.desc()).offset(
        (page - 1) * size).limit(size))
