import binascii
import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, aliased

from app.dependencies.auth_dep import get_current_sys_session
from app.models import micro_msg
from app.models.proto import msg_pb2
from app.models.hard_link_image import HardLinkImageAttribute, HardLinkImageID
from app.models.micro_msg import Contact
from app.models.multi import msg
from app.models.sys import SysSession
from app.schemas import schemas
from db.wx_db import wx_db_micro_msg, wx_db_msg0, wx_db_hard_link_image
from config.log_config import logger
from config.app_config import settings as app_settings
from config.data_config import settings as data_settings

router = APIRouter(
    prefix="/msg"
)

HardLinkImageID = aliased(HardLinkImageID, name='dir1')
HardLinkImageID2 = aliased(HardLinkImageID, name='dir2')

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
    msgs = db.query(msg.Msg).filter_by(TalkerId=talker_id).order_by(msg.Msg.localId.desc()).offset(
        (page - 1) * size).limit(size)
    results = []
    # 群聊反序列化 ByteExtra 字段
    if '@' in strUsrName:
        for n in msgs:
            nmsg = schemas.MsgWithSenderWxId(**n.__dict__)
            proto_msg = msg_pb2.ProtoMsg()
            proto_msg.ParseFromString(n.BytesExtra)
            for tv_type in proto_msg.TVMsg:
                if tv_type.Type == 1:
                    nmsg.WxId = tv_type.TypeValue
            results.append(nmsg)
        return results
    return msgs


@router.get("/contact", response_model=List[schemas.ContactBase])
def red_contact(db: Session = Depends(wx_db_micro_msg)):
    return db.query(Contact).all()


@router.get("/image/{md5_val}")
async def get_image(md5_value: str,
                    db: Session = Depends(wx_db_hard_link_image),
                    sys_session: SysSession = Depends(get_current_sys_session)):
    md5_blob = binascii.unhexlify(md5_value.upper())
    image = db.query(HardLinkImageAttribute).filter_by(MD5=md5_blob).first()
    logger.info(image)
    query = db.query(
        HardLinkImageAttribute.Md5Hash,
        HardLinkImageAttribute.MD5,
        HardLinkImageAttribute.FileName,
        HardLinkImageID.Dir.label('dirName1'),
        HardLinkImageID2.Dir.label('dirName2')
    ).join(
        HardLinkImageID, HardLinkImageAttribute.DirID1 == HardLinkImageID.DirID
    ).join(
        HardLinkImageID2, HardLinkImageAttribute.DirID2 == HardLinkImageID2.DirID
    ).filter(
        HardLinkImageAttribute.MD5 == md5_blob
    )
    logger.info(str(query))
    img = query.first()
    logger.info(img)
    if img:
        image_file = os.path.join(app_settings.sys_dir, data_settings.home, sys_session.name, sys_session.wx_id, md5_value)
        logger.info(f'image_file: {image_file}')
        image_file_jpg = image_file + '.jpg'
        if os.path.exists(image_file_jpg):
            return FileResponse(str(image_file_jpg))
        image_file_png = image_file + '.png'
        if os.path.exists(image_file_png):
            return FileResponse(str(image_file_png))

    raise HTTPException(status_code=404, detail="File not found")
