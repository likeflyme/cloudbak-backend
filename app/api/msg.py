import os
from collections import defaultdict
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_sys_session
from app.helper.directory_helper import get_session_dir, get_wx_dir
from app.models import micro_msg
from app.models.micro_msg import Contact, ChatRoom
from app.models.multi import msg
from app.models.multi.msg import Name2ID
from app.models.sys import SysSession
from app.schemas import schemas
from app.schemas.micro_msg import ChatRoom as ChatRoomSchema
from app.services import parse_msg
from app.services.decode_wx_pictures import decrypt_by_file_type, decrypt_file
from config.log_config import logger
from db.wx_db import wx_db_micro_msg, wx_db_msg0, get_session_local, wx_db_msg
from config.wx_config import settings as wx_settings


session_local_dict = defaultdict(lambda: None)

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
             sys_session: SysSession = Depends(get_current_sys_session)):
    """
    分页查询用户分页消息
    :param strUsrName: 微信号
    :param page: 页码
    :param size: 分页大小
    :param sys_session: 用户 session
    :return: 分页数据
    """
    logger.info(f'strUsrName: {strUsrName}')
    sl = session_local_dict[strUsrName]
    if sl is None:
        for c in range(0, wx_settings.max_msg):
            session_local = wx_db_msg(c, sys_session)
            if not session_local:
                continue
            db = session_local()
            try:
                name = db.query(Name2ID).filter_by(UsrName=strUsrName).first()
                if name:
                    session_local_dict[strUsrName] = session_local
                    sl = session_local
            finally:
                db.close()
    if not sl:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户错误，找不到数据源",
        )
    db = sl()
    try:
        # 再根据id查询消息列表
        msgs = (db.query(msg.Msg)
                .filter_by(StrTalker=strUsrName)
                .order_by(msg.Msg.localId.desc())
                .offset((page - 1) * size).limit(size))
        results = []
        # 反序列化 ByteExtra 字段
        for n in msgs:
            nmsg = parse_msg.parse(n, sys_session.id)
            results.append(nmsg)
    finally:
        db.close()
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
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    jpg_path = file_path.replace(".dat", ".jpg")
    if os.path.exists(jpg_path):
        return FileResponse(jpg_path)
    png_path = file_path.replace(".dat", ".png")
    if os.path.exists(png_path):
        return FileResponse(png_path)
    gif_path = file_path.replace(".dat", ".gif")
    if os.path.exists(gif_path):
        return FileResponse(gif_path)
    decoded_path = decrypt_file(file_path)
    if decoded_path:
        return FileResponse(decoded_path)
    raise HTTPException(status_code=404, detail="File not found")


@router.get("/chatroom-info", response_model=ChatRoomSchema)
async def get_image(chat_room_name: str, db: Session = Depends(wx_db_micro_msg)):
    return db.query(ChatRoom).filter_by(ChatRoomName=chat_room_name).first()

