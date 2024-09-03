import os
from collections import defaultdict
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_sys_session
from app.helper.directory_helper import get_session_dir, get_decoded_media_path
from app.models import micro_msg
from app.models.micro_msg import Contact, ChatRoom, ContactHeadImgUrl
from app.models.multi import msg
from app.models.multi.media_msg import Media
from app.models.sys import SysSession
from app.schemas import schemas
from app.schemas.micro_msg import ChatRoom as ChatRoomSchema
from app.schemas.schemas import ChatMsg, ContactHeadImgUrlOut
from app.services import parse_msg
from app.services.decode_wx_media import decode_media
from app.services.decode_wx_pictures import decrypt_file
from config.log_config import logger
from db.sys_db import get_db
from db.wx_db import wx_db_micro_msg, wx_db_msg, msg_db_count, wx_db_media_msg
from app.services.db_order import get_sorted_db

session_local_dict = defaultdict(lambda: None)

router = APIRouter(
    prefix="/msg"
)


@router.get("/session", response_model=Optional[schemas.SessionBaseOut])
def red_session(strUsrName: str, db: Session = Depends(wx_db_micro_msg)):
    stmt = (
        select(micro_msg.Session, micro_msg.ContactHeadImgUrl)
        .join(micro_msg.ContactHeadImgUrl, micro_msg.Session.strUsrName == micro_msg.ContactHeadImgUrl.usrName)
        .where(micro_msg.Session.strUsrName == strUsrName)
    )
    result = db.execute(stmt).first()
    if result:
        session, img = result
        return schemas.SessionBaseOut(
            **session.__dict__,
            smallHeadImgUrl=img.smallHeadImgUrl,
            bigHeadImgUrl=img.bigHeadImgUrl,
            headImgMd5=img.headImgMd5
        )
    return None


@router.get("/sessions", response_model=List[schemas.SessionBaseOut])
def red_sessions(page: int = 1, size: int = 20, db: Session = Depends(wx_db_micro_msg)):
    """
    查询会话分页列表
    :param page:
    :param size:
    :param db:
    :return:
    """
    stmt = (
        select(micro_msg.Session, micro_msg.ContactHeadImgUrl)
        .join(micro_msg.ContactHeadImgUrl, micro_msg.Session.strUsrName == micro_msg.ContactHeadImgUrl.usrName)
        .where(micro_msg.Session.strUsrName.notlike("gh_%"))
        .where(micro_msg.Session.strUsrName.notlike("@%"))
        .order_by(micro_msg.Session.nOrder.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    results = db.execute(stmt).all()
    return [
        schemas.SessionBaseOut(
            **session.__dict__,
            smallHeadImgUrl=contact_head_img_url.smallHeadImgUrl,
            bigHeadImgUrl=contact_head_img_url.bigHeadImgUrl,
            headImgMd5=contact_head_img_url.headImgMd5
        )
        for session, contact_head_img_url in results
    ]


@router.get("/msg_by_svr_id", response_model=Optional[schemas.MsgWithExtra])
def red_msg_by_svr_id(svr_id: int,
                      db_no: int,
                      sys_session: SysSession = Depends(get_current_sys_session)):
    session_local = wx_db_msg(db_no, sys_session)
    db = session_local()
    result = db.query(msg.Msg).filter_by(MsgSvrID=svr_id).first()
    if result:
        return parse_msg.parse(result, sys_session.id, db_no)
    return None


@router.get("/msgs", response_model=ChatMsg)
def red_msgs(strUsrName: str,
             page: int = 1,
             size: int = 20,
             start: Optional[int] = 0,
             dbNo: Optional[int] = None,
             micro_db: Session = Depends(wx_db_micro_msg),
             sys_session: SysSession = Depends(get_current_sys_session)):
    """
    分页查询用户分页消息
    :param micro_db:
    :param strUsrName: 微信号
    :param page: 页码
    :param size: 分页大小
    :param start: 数据库起始偏移值
    :param dbNo: 数据库编号
    :param sys_session: 用户 session
    :return: 分页数据
    """
    logger.info(f'strUsrName: {strUsrName}')
    current_db_no = 0
    db_array = get_sorted_db(sys_session)
    if dbNo == -1:
        dbNo = len(db_array) - 1
        logger.info(f"数据库最大值 {dbNo}")

    results = []
    # 跨库查询
    for num in range(dbNo, -1, -1):
        db_sequence = db_array[num]
        logger.info(f"查询库 {db_sequence}")
        session_local = wx_db_msg(db_sequence, sys_session)
        db = session_local()
        logger.info(f"已查询的数据量 {len(results)}")
        query_size = size - len(results)
        logger.info(f"查询量 {query_size}")
        logger.info(f"起始偏移 {start}")
        current_db_no = num
        logger.info(f"当前库索引 {current_db_no}")
        try:
            # 再根据id查询消息列表
            msgs = (db.query(msg.Msg)
                    .filter_by(StrTalker=strUsrName)
                    .order_by(msg.Msg.CreateTime.desc(), msg.Msg.Sequence.desc())
                    .offset((page - 1) * size + start).limit(query_size))
            logger.info(str(msgs.statement.compile(compile_kwargs={"literal_binds": True})))
            # 反序列化 ByteExtra 字段
            m = msgs.all()
            logger.info(f"数据量 {len(m)}")
            personal_send = select_contact(micro_db, sys_session.wx_id)
            personal_receive = select_contact(micro_db, strUsrName)
            # 数据转换
            for n in m:
                nmsg = parse_msg.parse(n, sys_session.id, num)
                results.append(nmsg)
                # 群聊
                if strUsrName.endswith("@chatroom"):
                    if nmsg.WxId:
                        contact_data = select_contact(micro_db, nmsg.WxId)
                        if contact_data:
                            nmsg.Remark = contact_data.Remark
                            nmsg.NickName = contact_data.NickName
                            nmsg.smallHeadImgUrl = contact_data.smallHeadImgUrl
                            nmsg.bigHeadImgUrl = contact_data.bigHeadImgUrl
                    else:
                        if nmsg.IsSender == 1 and personal_send:
                            nmsg.Remark = personal_send.Remark
                            nmsg.NickName = personal_send.NickName
                            nmsg.smallHeadImgUrl = personal_send.smallHeadImgUrl
                            nmsg.bigHeadImgUrl = personal_send.bigHeadImgUrl
                # 私聊
                else:
                    if nmsg.IsSender == 1 and personal_send:
                        nmsg.Remark = personal_send.Remark
                        nmsg.NickName = personal_send.NickName
                        nmsg.smallHeadImgUrl = personal_send.smallHeadImgUrl
                        nmsg.bigHeadImgUrl = personal_send.bigHeadImgUrl
                    elif nmsg.IsSender == 0 and personal_receive:
                        nmsg.Remark = personal_receive.Remark
                        nmsg.NickName = personal_receive.NickName
                        nmsg.smallHeadImgUrl = personal_receive.smallHeadImgUrl
                        nmsg.bigHeadImgUrl = personal_receive.bigHeadImgUrl

            if len(results) >= size:
                if len(m) < size:
                    start = len(m)
                    logger.info(f"查询结束，设置起始偏移为 {start}")
                break
            # 修改起始偏移
            start = 0
            # 重置页码
            logger.info(f"当前库数据不够一页 {size}，重置页码为 1，继续查询下一个库")
            page = 1
        finally:
            db.close()
    data = {
        "dbNo": current_db_no,
        "start": start,
        "msgs": results
    }
    return data


def select_contact(micro_db: Session, wxId: str):
    contact = micro_db.query(Contact).filter_by(UserName=wxId).first()
    if contact:
        data = schemas.ContactWithHeadImg(**contact.__dict__)
        if contact.head_img_url:
            data.smallHeadImgUrl = contact.head_img_url.smallHeadImgUrl
            data.bigHeadImgUrl = contact.head_img_url.bigHeadImgUrl
        return data
    img = micro_db.query(ContactHeadImgUrl).filter_by(usrName=wxId).first()
    if img:
        if img.contact:
            data = schemas.ContactWithHeadImg(**img.contact.__dict__)
            data.smallHeadImgUrl = img.smallHeadImgUrl
            data.bigHeadImgUrl = img.bigHeadImgUrl
        else:
            data = schemas.ContactWithHeadImg(**img.__dict__)
        return data

def select_contact_with_img(micro_db, wxId):
    contact = micro_db.execute(select(micro_msg.Contact).where(micro_msg.Contact.UserName == wxId)).first()
    img = micro_db.execute(select(micro_msg.ContactHeadImgUrl).where(micro_msg.ContactHeadImgUrl.usrName == wxId)).first()
    return contact, img



@router.get("/contact", response_model=List[schemas.ContactBase])
def red_contact(db: Session = Depends(wx_db_micro_msg)):
    return db.query(Contact).filter(Contact.NickName != "").all()


@router.get("/contact-split", response_model=List[schemas.ContactWithHeadImg])
def red_contact(page: int = 1,
                size: int = 20,
                ChatRoomType: int = 0,
                db: Session = Depends(wx_db_micro_msg)):
    if ChatRoomType == 0:
        stmt = (
            select(micro_msg.Contact, micro_msg.ContactHeadImgUrl)
            .join(micro_msg.ContactHeadImgUrl, micro_msg.Contact.UserName == micro_msg.ContactHeadImgUrl.usrName)
            .where(micro_msg.Contact.UserName.notlike("%@chatroom"))
            .where(~micro_msg.Contact.Type.in_([0, 1, 2, 4]))
            .order_by(micro_msg.Contact.NickName.asc())
            .offset((page - 1) * size)
            .limit(size)
        )
    else:
        stmt = (
            select(micro_msg.Contact, micro_msg.ContactHeadImgUrl)
            .join(micro_msg.ContactHeadImgUrl, micro_msg.Contact.UserName == micro_msg.ContactHeadImgUrl.usrName)
            .where(micro_msg.Contact.UserName.like("%@chatroom"))
            .where(
                and_(
                    micro_msg.Contact.NickName.isnot(None),
                    micro_msg.Contact.NickName != ""
                )
            )
            .order_by(micro_msg.Contact.NickName.asc())
            .offset((page - 1) * size)
            .limit(size)
        )

    results = db.execute(stmt).all()
    return [
        schemas.ContactWithHeadImg(
            **contact.__dict__,
            smallHeadImgUrl=contact_head_img_url.smallHeadImgUrl,
            bigHeadImgUrl=contact_head_img_url.bigHeadImgUrl,
            headImgMd5=contact_head_img_url.headImgMd5
        )
        for contact, contact_head_img_url in results
    ]


@router.get("/image")
async def get_image(img_path: str, session_id: int):
    img_path = img_path.replace("\\", '/')
    base_dir = get_session_dir(session_id)
    file_path = os.path.join(base_dir, img_path)
    logger.info(file_path)

    # 确保 file_path 是 base_dir 的子路径
    abs_file_path = os.path.abspath(file_path)
    abs_base_dir = os.path.abspath(base_dir)

    if not abs_file_path.startswith(abs_base_dir):
        raise HTTPException(status_code=403, detail="Invalid path")

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


@router.get("/media")
async def get_media(
        MsgSvrID: str,
        session_id: int,
        db_no: int,
        db: Session = Depends(get_db)):
    sys_session = db.query(SysSession).filter_by(id=session_id).first()
    media_folder = get_decoded_media_path(sys_session)
    mp3_name = os.path.join(media_folder, f"{MsgSvrID}.mp3")
    if os.path.exists(mp3_name):
        return FileResponse(mp3_name)
    else:
        session_local = wx_db_media_msg(db_no, sys_session)
        media_db = session_local()
        media = media_db.query(Media).filter_by(Reserved0=MsgSvrID).first()
        if media:
            mp3_name = decode_media(media_folder, MsgSvrID, media.Buf)
            return FileResponse(mp3_name)
    raise HTTPException(status_code=404, detail="File not found")


@router.get("/file")
async def get_file(path: str, session_id: int):
    file_path = path.replace("\\", '/')
    base_dir = get_session_dir(session_id)
    file_path = os.path.join(base_dir, file_path)
    logger.info(file_path)

    # 确保 file_path 是 base_dir 的子路径
    abs_file_path = os.path.abspath(file_path)
    abs_base_dir = os.path.abspath(base_dir)

    if not abs_file_path.startswith(abs_base_dir):
        raise HTTPException(status_code=403, detail="Invalid path")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)


@router.get("/video")
async def get_video(video_path: str, session_id: int):
    video_path = video_path.replace("\\", '/')
    base_dir = get_session_dir(session_id)
    file_path = os.path.join(get_session_dir(session_id), video_path)
    logger.info(file_path)

    # 确保 file_path 是 base_dir 的子路径
    abs_file_path = os.path.abspath(file_path)
    abs_base_dir = os.path.abspath(base_dir)

    if not abs_file_path.startswith(abs_base_dir):
        raise HTTPException(status_code=403, detail="Invalid path")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="video/mp4")


@router.get("/chatroom-info", response_model=Optional[ChatRoomSchema])
async def get_chatroom_info(chat_room_name: str, db: Session = Depends(wx_db_micro_msg)):
    chat_room = db.query(ChatRoom).filter_by(ChatRoomName=chat_room_name).first()
    if not chat_room:
        return None
    out = ChatRoomSchema(**chat_room.__dict__)
    contact = db.query(Contact).filter_by(UserName=chat_room_name).first()
    if contact:
        out.NickName = contact.NickName
        out.Remark = contact.Remark
    if chat_room and chat_room.UserNameList:
        user_name_list = chat_room.UserNameList.split('^G')
        stmt = (
            select(micro_msg.Contact, micro_msg.ContactHeadImgUrl)
            .join(micro_msg.ContactHeadImgUrl, micro_msg.Contact.UserName == micro_msg.ContactHeadImgUrl.usrName)
            .where(micro_msg.Contact.UserName.in_(user_name_list))
        )
        results = db.execute(stmt).all()
        out.ContactList = [
            schemas.ContactWithHeadImg(
                **contact.__dict__,
                smallHeadImgUrl=contact_head_img_url.smallHeadImgUrl,
                bigHeadImgUrl=contact_head_img_url.bigHeadImgUrl,
                headImgMd5=contact_head_img_url.headImgMd5
            )
            for contact, contact_head_img_url in results
        ]
    return out


@router.get("/head-image", response_model=ContactHeadImgUrlOut)
async def get_head_image(usrName: str, db: Session = Depends(wx_db_micro_msg)):
    return db.query(ContactHeadImgUrl).filter_by(usrName=usrName).first()

