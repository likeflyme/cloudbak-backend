import os
import re
from typing import List

import lz4.block as lb
import xmltodict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, aliased

from app.dependencies.auth_dep import get_current_sys_session
from app.models import micro_msg
from app.models.hard_link_image import HardLinkImageID
from app.models.micro_msg import Contact
from app.models.multi import msg
from app.models.proto import msg_bytes_extra_pb2
from app.models.sys import SysSession
from app.schemas import schemas
from app.services.file_handler import dat_to_img
from config.app_config import settings as app_settings
from config.data_config import settings as data_settings
from config.log_config import logger
from db.wx_db import wx_db_micro_msg, wx_db_msg0

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


def clean_xml_data(xml_str):
    # 删除非XML字符
    xml_str = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u4e00-\u9fff\u3000-\u303F\uFF00-\uFFEF]', '', xml_str)
    # 删除空的CDATA节点
    xml_str = re.sub(r'<!\[CDATA\[\]\]>', '', xml_str)
    return xml_str


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
        nmsg = schemas.MsgWithExtra(**n.__dict__)
        if n.BytesExtra:
            logger.info('BytesExtra 反序列化处理')
            proto = msg_bytes_extra_pb2.BytesExtra()
            proto.ParseFromString(n.BytesExtra)
            for f3 in proto.f3:
                # 群聊消息发送者wxid
                if f3.s1 == 1:
                    nmsg.WxId = f3.s2
                # 图片缩略图
                if f3.s1 == 3:
                    nmsg.Thumb = dat_to_img(sys_session.name, f3.s2)
                # 图片原图
                if f3.s1 == 4:
                    nmsg.Image = dat_to_img(sys_session.name, f3.s2)
        if n.CompressContent:
            unzipStr = lb.decompress(n.CompressContent, uncompressed_size=0x10004)
            xml_data = unzipStr.decode('utf-8')
            compress_content_dict = xmltodict.parse(clean_xml_data(xml_data))
            nmsg.compress_content = compress_content_dict
        results.append(nmsg)
    return results


@router.get("/contact", response_model=List[schemas.ContactBase])
def red_contact(db: Session = Depends(wx_db_micro_msg)):
    return db.query(Contact).all()


@router.get("/image")
async def get_image(img_path: str, session_name: str):
    file_path = os.path.join(app_settings.sys_dir, data_settings.home, session_name, img_path)
    logger.info(file_path)
    if os.path.exists(file_path):
        return FileResponse(str(file_path))
    raise HTTPException(status_code=404, detail="File not found")
