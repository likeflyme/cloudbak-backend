from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models import micro_msg, msg_pb2
from app.models.multi import msg
from app.schemas import schemas
from db.wx_db import wx_db_micro_msg, wx_db_msg0
from config.log_config import logger

router = APIRouter(
    prefix="/msg"
)


@router.get("/session", response_model=schemas.SessionBaseOut)
def red_session(strUsrName: str, db: Session = Depends(wx_db_micro_msg)):
    return db.query(micro_msg.Session).filter_by(strUsrName=strUsrName).first()


@router.get("/sessions", response_model=List[schemas.SessionBaseOut])
def red_sessions(db: Session = Depends(wx_db_micro_msg)):
    """
    查询会话分页列表
    :param db:
    :return:
    """
    return db.query(micro_msg.Session).order_by(micro_msg.Session.nOrder.desc()).all()


@router.get("/msgs", response_model=List[schemas.MsgWithSenderWxId])
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
    print('talker_id is:' + str(talker_id))
    # 再根据id查询消息列表
    msgs = db.query(msg.Msg).filter_by(TalkerId=talker_id).order_by(msg.Msg.localId.desc()).offset(
        (page - 1) * size).limit(size)
    results = []
    for n in msgs:
        nmsg = schemas.MsgWithSenderWxId(**n.__dict__)
        proto_msg = deserialize_proto_message(n.BytesExtra)
        for tv_type in proto_msg.TVMsg:
            if tv_type.Type == 1:
                nmsg.WxId = tv_type.TypeValue
        results.append(nmsg)
    return results


def deserialize_proto_message(byte_array):
    proto_msg = msg_pb2.ProtoMsg()
    proto_msg.ParseFromString(byte_array)
    return proto_msg
