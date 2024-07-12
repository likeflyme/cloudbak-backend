import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_sys_session
from app.helper.directory_helper import get_session_dir
from app.models import micro_msg
from app.models.micro_msg import Contact, ChatRoom
from app.models.multi import msg
from app.models.sys import SysSession
from app.schemas import schemas
from app.schemas.micro_msg import ChatRoom as ChatRoomSchema
from app.services import parse_msg
from config.app_config import settings as app_settings
from config.data_config import settings as data_settings
from config.log_config import logger
from db.wx_db import wx_db_micro_msg, wx_db_msg0

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


@router.get("/msg_by_svr_id", response_model=schemas.MsgWithExtra)
def red_msg_by_svr_id(svr_id: int,
                      db: Session = Depends(wx_db_msg0),
                      sys_session: SysSession = Depends(get_current_sys_session)):
    result = db.query(msg.Msg).filter_by(MsgSvrID=svr_id).first()
    if result:
        return parse_msg.parse(result, sys_session.name)
    return None


@router.get("/msgs", response_model=List[schemas.MsgWithExtra])
def red_msgs(strUsrName: str,
             page: int = 1,
             size: int = 20,
             db: Session = Depends(wx_db_msg0),
             sys_session: SysSession = Depends(get_current_sys_session)):
    """
    分页查询用户分页消息
    :param strUsrName: 微信号
    :param page: 页码
    :param size: 分页大小
    :param db: 数据库
    :return: 分页数据
    """
    logger.info(f'strUsrName: {strUsrName}')
    # 先根据 strUsrName 在 Name2ID 表中查询 id
    names = db.query(msg.Name2ID).all()
    talker_id = 1
    for name in names:
        if name.UsrName == strUsrName:
            break
        talker_id = talker_id + 1
    logger.info(f'TalkerId: {talker_id}')
    # 再根据id查询消息列表
    msgs = (db.query(msg.Msg)
            .filter_by(TalkerId=talker_id)
            .order_by(msg.Msg.localId.desc())
            .offset((page - 1) * size).limit(size))
    results = []
    # 反序列化 ByteExtra 字段
    for n in msgs:
        nmsg = parse_msg.parse(n, sys_session.id)
        results.append(nmsg)
    return results


@router.get("/contact", response_model=List[schemas.ContactBase])
def red_contact(db: Session = Depends(wx_db_micro_msg)):
    return db.query(Contact).filter(Contact.NickName != "").all()


@router.get("/contact-split", response_model=List[schemas.ContactBase])
def red_contact(page: int = 1,
                size: int = 20,
                ChatRoomType: int = 0,
                db: Session = Depends(wx_db_micro_msg)):
    return (db.query(Contact)
            .filter(Contact.NickName != "", Contact.Type != 0, Contact.ChatRoomType == ChatRoomType)
            .order_by(Contact.NickName.asc())
            .offset((page - 1) * size).limit(size))


@router.get("/image")
async def get_image(img_path: str, session_id: int):
    file_path = os.path.join(get_session_dir(session_id), img_path)
    logger.info(file_path)
    if os.path.exists(file_path):
        return FileResponse(str(file_path))
    raise HTTPException(status_code=404, detail="File not found")


@router.get("/chatroom-info", response_model=ChatRoomSchema)
async def get_image(chat_room_name: str, db: Session = Depends(wx_db_micro_msg)):
    return db.query(ChatRoom).filter_by(ChatRoomName=chat_room_name).first()

