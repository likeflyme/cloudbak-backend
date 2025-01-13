import os
import base64
import httpx
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional
from io import BytesIO


from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select, and_, union, or_
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_sys_session, get_current_user
from app.helper.contact_helper import contact_type
from app.helper.directory_helper import get_session_dir, get_decoded_media_path
from app.helper.filter_helper import convert_type
from app.models import micro_msg
from app.models.micro_msg import Contact, ChatRoom, ContactHeadImgUrl
from app.models.multi import msg
from app.models.multi.media_msg import Media
from app.models import public_msg, openim_msg, openim_contact, openim_media
from app.models.proto import cr_extra_buf_pb2
from app.models.sys import SysSession, SysUser
from app.schemas import schemas
from app.schemas.micro_msg import ChatRoom as ChatRoomSchema
from app.schemas.schemas import ChatMsg, ContactHeadImgUrlOut
from app.services import parse_msg
from app.services.db_talker import get_talker_id
from app.services.decode_wx_media import decode_media
from app.services.decode_wx_pictures import decrypt_file
from config.log_config import logger
from db.sys_db import get_db
from db.wx_db import wx_db_micro_msg, wx_db_msg, msg_db_count, wx_db_media_msg, wx_db_media_msg_by_filename, \
    wx_db_public_msg, wx_db_openim_msg, wx_db_for_conf
from app.services.db_order import get_sorted_db, reversed_array, media_msg_db_array
from config.wx_config import settings as wx_settings

session_local_dict = defaultdict(lambda: None)

router = APIRouter(
    prefix="/msg"
)


@router.get("/session", response_model=Optional[schemas.SessionBaseOut])
def red_session(strUsrName: str, db: Session = Depends(wx_db_micro_msg)):
    stmt = (
        select(micro_msg.Session, micro_msg.ContactHeadImgUrl, micro_msg.Contact)
        .join(micro_msg.ContactHeadImgUrl, micro_msg.Session.strUsrName == micro_msg.ContactHeadImgUrl.usrName,
              isouter=True)
        .join(micro_msg.Contact, micro_msg.Session.strUsrName == micro_msg.Contact.UserName, isouter=True)
        .where(micro_msg.Session.strUsrName == strUsrName)
    )
    result = db.execute(stmt).first()
    if result:
        session, img, contact = result
        return schemas.SessionBaseOut(
            **session.__dict__,
            smallHeadImgUrl=getattr(img, 'smallHeadImgUrl', None),
            bigHeadImgUrl=getattr(img, 'bigHeadImgUrl', None),
            headImgMd5=getattr(img, 'headImgMd5', None),
            Remark=getattr(contact, 'Remark', None)
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
        select(micro_msg.Session, micro_msg.ContactHeadImgUrl, micro_msg.Contact)
        .join(micro_msg.ContactHeadImgUrl, micro_msg.Session.strUsrName == micro_msg.ContactHeadImgUrl.usrName,
              isouter=True)
        .join(micro_msg.Contact, micro_msg.Session.strUsrName == micro_msg.Contact.UserName, isouter=True)
        # .where(micro_msg.Session.strUsrName.notlike("gh_%"))
        # .where(micro_msg.Session.strUsrName.notlike("@%"))
        # .where(micro_msg.Session.strUsrName.notlike("%@openim"))
        # .where(micro_msg.Session.strUsrName != "notifymessage")
        # .where(micro_msg.Session.strUsrName != "fmessage")
        # .where(micro_msg.Session.strUsrName != "qqmail")
        .order_by(micro_msg.Session.nOrder.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    results = db.execute(stmt).all()
    return [
        schemas.SessionBaseOut(
            **session.__dict__,
            smallHeadImgUrl=getattr(img, 'smallHeadImgUrl', None),
            bigHeadImgUrl=getattr(img, 'bigHeadImgUrl', None),
            headImgMd5=getattr(img, 'headImgMd5', None),
            Remark=getattr(contact, 'Remark', None)
        )
        for session, img, contact in results
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


@router.get("/msgs-all", response_model=ChatMsg)
def msgs_all(strUsrName: str,
             page: int = 1,
             size: int = 20,
             start: Optional[int] = 0,
             dbNo: Optional[int] = None,
             micro_db: Session = Depends(wx_db_micro_msg),
             sys_session: SysSession = Depends(get_current_sys_session)):
    # 判断用户查询消息用户类型
    # 0-Multi, 正常 Multi 目录的消息
    # 1-publicMsg, 公众号等公共服务
    # 2-OpenIMMsg, 企业用户
    tp = contact_type(strUsrName, sys_session)

    if tp == 1:
        return gh_msgs(strUsrName, page, size, start, dbNo, sys_session)
    elif tp == 2:
        return openim_msgs(strUsrName, page, size, start, dbNo, sys_session)
    else:
        return red_msgs(strUsrName, page, size, start, dbNo, micro_db, sys_session)


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
    logger.info(f"库排序 {db_array}")
    if dbNo == -1:
        dbNo = len(db_array) - 1
        logger.info(f"数据库最大值 {dbNo}")

    results = []
    # 跨库查询
    for num in range(dbNo, -1, -1):
        db_sequence = db_array[num]
        logger.info(f"查询库 {db_sequence}")
        session_local = wx_db_msg(db_sequence, sys_session)
        # 没有这个库则继续
        if session_local is None:
            logger.info(f"库 {db_sequence} 不存在，继续查询下一个库")
            continue
        db = session_local()
        logger.info(f"已查询的数据量 {len(results)}")
        query_size = size - len(results)
        logger.info(f"查询量 {query_size}")
        logger.info(f"起始偏移 {start}")
        current_db_no = num
        logger.info(f"当前库索引 {current_db_no}")
        try:
            talker_id = get_talker_id(sys_session, db_sequence, strUsrName)
            logger.info(f"TalkerId: {talker_id}")
            # 再根据id查询消息列表
            stmt = (select(msg.Msg).where(msg.Msg.TalkerId == talker_id)
                    .order_by(msg.Msg.Sequence.desc())
                    .offset((page - 1) * size + start).limit(query_size))
            logger.info(f"query sql: {stmt}")
            msgs = db.execute(stmt).all()
            logger.info(f"数据量 {len(msgs)}")
            # 数据转换
            msgs = parseMsg(msgs, micro_db, sys_session, strUsrName, num)
            for m in msgs:
                results.append(m)
            if len(results) >= size:
                if len(msgs) < size:
                    start = len(msgs)
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



@router.get("/msgs-filter", response_model=ChatMsg)
def red_msgs_filter(strUsrName: str,
             page: int = 1,
             size: int = 20,
             start: Optional[int] = 0,
             dbNo: Optional[int] = None,
             filterType: Optional[int] = 0,
             filterDay: Optional[str] = None,
             filterUser: Optional[str] = None,
             filterText: Optional[str] = None,
             filterMode: Optional[int] = 0,
             micro_db: Session = Depends(wx_db_micro_msg),
             sys_session: SysSession = Depends(get_current_sys_session)):
    """
    分页查询用户分页消息
    :param filterMode: 搜索模式，-1，向后加载，0初次，1-向前加载
    :param filterText: 搜索文本
    :param filterUser: 搜索群用户微信id
    :param filterDay: 搜索时间，格式yyyy/MM/dd
    :param filterType: 搜索类型
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
    if filterMode == -1:
        db_array = db_array[::-1]
        logger.info(f"反向模式, 库排序 {db_array}")
    if dbNo == -1:
        dbNo = len(db_array) - 1
        logger.info(f"数据库最大值 {dbNo}")

    results = []
    # 跨库查询
    for num in range(dbNo, -1, -1):
        db_sequence = db_array[num]
        logger.info(f"查询库 {db_sequence}")
        session_local = wx_db_msg(db_sequence, sys_session)
        # 没有这个库则继续
        if session_local is None:
            logger.info(f"库 {db_sequence} 不存在，继续查询下一个库")
            continue
        db = session_local()
        logger.info(f"已查询的数据量 {len(results)}")
        query_size = size - len(results)
        logger.info(f"查询量 {query_size}")
        logger.info(f"起始偏移 {start}")
        current_db_no = num
        logger.info(f"当前库索引 {current_db_no}")
        try:
            # 再根据id查询消息列表
            logger.info(f"offset: {(page - 1) * size + start}, limit: {query_size}")
            talker_id = get_talker_id(sys_session, db_sequence, strUsrName)
            logger.info(f"TalkerId: {talker_id}")
            stmt = (select(msg.Msg).where(msg.Msg.TalkerId == talker_id)
                    .offset((page - 1) * size + start).limit(query_size))
            tm_stmt = None
            # 添加查询条件
            if filterType != 0:
                # 按日期查询
                if filterType == 7 and filterDay:
                    # 将 yyyyMMdd 转换为 datetime 对象
                    date = datetime.strptime(filterDay, "%Y%m%d")
                    # 当天开始时间
                    start_of_day = datetime(date.year, date.month, date.day)
                    # 当天结束时间（23:59:59）
                    end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)

                    # 转换为时间戳（秒级）
                    end_timestamp = int(end_of_day.timestamp())
                    logger.info(f"时间戳: {end_timestamp}")
                    if filterMode == 0 or filterMode == 1:
                        tm_stmt = stmt.where(msg.Msg.CreateTime <= end_timestamp).order_by(msg.Msg.Sequence.desc())
                    else:
                        tm_stmt = stmt.where(msg.Msg.CreateTime > end_timestamp).order_by(msg.Msg.Sequence.asc())
                else:
                    type_list = convert_type(filterType)
                    logger.info(f"query types {type_list}")
                    if type_list is None:
                        logger.warn(f"query type is {filterType} but convert type and sub type not found")
                    or_conditions = [and_(msg.Msg.Type == t[0], msg.Msg.SubType == t[1]) for t in type_list]
                    stmt = stmt.where(or_(*or_conditions))
            if filterText is not None:
                if filterType == 0:
                    stmt = stmt.where(msg.Msg.StrContent.contains(filterText))
            stmt = stmt.order_by(msg.Msg.Sequence.desc())
            if filterType == 7:
                logger.info(f"query sql: {tm_stmt}")
                msgs = db.execute(tm_stmt).all()
            else:
                logger.info(f"query sql: {stmt}")
                msgs = db.execute(stmt).all()
            logger.info(f"数据量 {len(msgs)}")
            # 数据转换
            msgs = parseMsg(msgs, micro_db, sys_session, strUsrName, num)
            for m in msgs:
                results.append(m)
            if len(results) >= size:
                if len(msgs) < size:
                    start = len(msgs)
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


@router.get("/msgs-by-local-id", response_model=ChatMsg)
def red_msgs_by_local_id(strUsrName: str,
             localId: int,
             CreateTime: int,
             Sequence: int,
             page: int = 1,
             size: int = 20,
             start: Optional[int] = 0,
             dbNo: Optional[int] = None,
             filterMode: int = 0,
             micro_db: Session = Depends(wx_db_micro_msg),
             sys_session: SysSession = Depends(get_current_sys_session)):
    """
    分页查询用户分页消息
    :param localId: 消息id
    :param CreateTime:
    :param Sequence:
    :param micro_db:
    :param strUsrName: 微信号
    :param page: 页码
    :param size: 分页大小
    :param start: 数据库起始偏移值
    :param filterMode: 查询模式
    :param dbNo: 数据库编号
    :param sys_session: 用户 session
    :return: 分页数据
    """
    logger.info(f'strUsrName: {strUsrName}')
    current_db_no = 0
    db_array = get_sorted_db(sys_session)
    if filterMode == -1:
        db_array = db_array[::-1]
        logger.info(f"反向模式, 库排序 {db_array}")
    if dbNo == -1:
        dbNo = len(db_array) - 1
        logger.info(f"数据库最大值 {dbNo}")

    results = []
    # 跨库查询
    for num in range(dbNo, -1, -1):
        db_sequence = db_array[num]
        logger.info(f"查询库 {db_sequence}")
        session_local = wx_db_msg(db_sequence, sys_session)
        # 没有这个库则继续
        if session_local is None:
            logger.info(f"库 {db_sequence} 不存在，继续查询下一个库")
            continue
        db = session_local()
        logger.info(f"已查询的数据量 {len(results)}")
        query_size = size - len(results)
        logger.info(f"查询量 {query_size}")
        logger.info(f"起始偏移 {start}")
        current_db_no = num
        logger.info(f"当前库索引 {current_db_no}")
        try:
            # 再根据id查询消息列表
            logger.info(f"offset: {(page - 1) * size + start}, limit: {query_size}")
            talker_id = get_talker_id(sys_session, db_sequence, strUsrName)
            logger.info(f"TalkerId: {talker_id}")
            stmt = (select(msg.Msg).where(msg.Msg.TalkerId == talker_id)
                    .offset((page - 1) * size + start).limit(query_size))
            # 查询模式
            if filterMode >= 0:
                stmt = stmt.where(msg.Msg.CreateTime <= CreateTime).order_by(msg.Msg.Sequence.desc())
            else:
                stmt = stmt.where(msg.Msg.CreateTime > CreateTime).order_by(msg.Msg.Sequence.asc())
            logger.info(f"query sql: {stmt}")
            msgs = db.execute(stmt).all()
            logger.info(f"数据量 {len(msgs)}")
            # 数据转换
            msgs = parseMsg(msgs, micro_db, sys_session, strUsrName, num)
            for m in msgs:
                results.append(m)
            if len(results) >= size:
                if len(msgs) < size:
                    start = len(msgs)
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


def gh_msgs(strUsrName: str,
            page: int = 1,
            size: int = 20,
            start: Optional[int] = 0,
            dbNo: Optional[int] = None,
            sys_session: SysSession = Depends(get_current_sys_session)):
    """
    分页查询用户分页消息
    :param public_db:
    :param strUsrName: 微信号
    :param page: 页码
    :param size: 分页大小
    :param start: 数据库起始偏移值
    :param dbNo: 数据库编号
    :param sys_session: 用户 session
    :return: 分页数据
    """
    logger.info(f'strUsrName: {strUsrName}')
    stmt = (select(public_msg.Msg).where(public_msg.Msg.StrTalker == strUsrName)
            .order_by(public_msg.Msg.Sequence.desc())
            .offset((page - 1) * size + start).limit(size))
    logger.info(f"query sql: {stmt}")
    pb_db = wx_db_for_conf(wx_settings.db_public_msg, sys_session)()
    try:
        msgs = pb_db.execute(stmt).all()
        results = []
        for r in msgs:
            nmsg = parse_msg.parse(r[0], sys_session.id, dbNo)
            results.append(nmsg)
        data = {
            "dbNo": 0,
            "start": 0,
            "msgs": results
        }
        return data
    finally:
        pb_db.close()


def openim_msgs(strUsrName: str,
            page: int = 1,
            size: int = 20,
            start: Optional[int] = 0,
            dbNo: Optional[int] = None,
            sys_session: SysSession = Depends(get_current_sys_session)):
    """
    分页查询用户分页消息
    :param openimmsg_db:
    :param strUsrName: 微信号
    :param page: 页码
    :param size: 分页大小
    :param start: 数据库起始偏移值
    :param dbNo: 数据库编号
    :param sys_session: 用户 session
    :return: 分页数据
    """
    logger.info(f'strUsrName: {strUsrName}')
    stmt = (select(openim_msg.Msg).where(openim_msg.Msg.strTalker == strUsrName)
            .order_by(openim_msg.Msg.sequence.desc())
            .offset((page - 1) * size + start).limit(size))
    logger.info(f"query sql: {stmt}")
    openimmsg_db = wx_db_for_conf(wx_settings.db_openim_msg, sys_session)()
    try:
        msgs = openimmsg_db.execute(stmt).all()
        results = []
        for r in msgs:
            m = r[0]
            # openim_msg.Msg 转 msg.Msg
            normal_msg = msg.Msg(localId=m.localId, TalkerId=m.talkerId, MsgSvrID=m.MsgSvrID, Type=m.type,
                                 IsSender=m.IsSender, CreateTime=m.CreateTime, Sequence=m.sequence, StatusEx=m.StatusEx,
                                 FlagEx=m.FlagEx, Status=m.Status, StrTalker=m.strTalker, StrContent=m.StrContent,
                                 BytesExtra=m.BytesExtra, BytesTrans=m.BytesTrans)
            nmsg = parse_msg.parse(normal_msg, sys_session.id, dbNo)
            results.append(nmsg)
        data = {
            "dbNo": 0,
            "start": 0,
            "msgs": results
        }
        return data
    finally:
        openimmsg_db.close()


def parseMsg(msgs, micro_db: Session, sys_session: SysSession, strUsrName: str, dbNo: int):
    personal_send = select_contact(micro_db, sys_session.wx_id)
    personal_receive = select_contact(micro_db, strUsrName)
    results = []
    for r in msgs:
        # 反序列化 ByteExtra 字段
        nmsg = parse_msg.parse(r[0], sys_session.id, dbNo)
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
    return results


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
    img = micro_db.execute(
        select(micro_msg.ContactHeadImgUrl).where(micro_msg.ContactHeadImgUrl.usrName == wxId)).first()
    return contact, img


@router.get("/contact", response_model=List[schemas.ContactBase])
def red_contact(db: Session = Depends(wx_db_micro_msg)):
    return db.query(Contact).filter(Contact.NickName != "").all()


@router.get("/contact-split", response_model=List[schemas.ContactWithHeadImg])
def red_contact(page: int = 1,
                size: int = 20,
                search: str = None,
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
    if search:
        stmt = stmt.where(or_(
            micro_msg.Contact.NickName.like(f"%{search}%"),
            micro_msg.Contact.Remark.like(f"%{search}%"),
            micro_msg.Contact.Alias.like(f"%{search}%"),
            micro_msg.Contact.PYInitial.like(f"%{search}%"),
            micro_msg.Contact.QuanPin.like(f"%{search}%"),
            micro_msg.Contact.RemarkPYInitial.like(f"%{search}%"),
            micro_msg.Contact.RemarkQuanPin.like(f"%{search}%"),
        ))

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


@router.get("/contact-search")
async def contact_search(search: str,
                       user: SysUser = Depends(get_current_user),
                       db: Session = Depends(wx_db_micro_msg)):
    base_stmt = (
        select(micro_msg.Contact, micro_msg.ContactHeadImgUrl)
        .join(micro_msg.ContactHeadImgUrl, micro_msg.Contact.UserName == micro_msg.ContactHeadImgUrl.usrName)
        .where(or_(
            micro_msg.Contact.NickName.like(f"%{search}%"),
            micro_msg.Contact.Remark.like(f"%{search}%"),
            micro_msg.Contact.Alias.like(f"%{search}%"),
            micro_msg.Contact.PYInitial.like(f"%{search}%"),
            micro_msg.Contact.QuanPin.like(f"%{search}%"),
            micro_msg.Contact.RemarkPYInitial.like(f"%{search}%"),
            micro_msg.Contact.RemarkQuanPin.like(f"%{search}%"),
        ))
    )

    contact_stmt = base_stmt.where(micro_msg.Contact.UserName.notlike("%@chatroom"))

    chatroom_stmt = base_stmt.where(micro_msg.Contact.UserName.like("%@chatroom"))

    contact_result = db.execute(contact_stmt).all()
    logger.info(f"query: {contact_stmt}")
    chatroom_result = db.execute(chatroom_stmt).all()
    return {
        'contacts': [
            schemas.ContactWithHeadImg(
                **contact.__dict__,
                smallHeadImgUrl=contact_head_img_url.smallHeadImgUrl,
                bigHeadImgUrl=contact_head_img_url.bigHeadImgUrl,
                headImgMd5=contact_head_img_url.headImgMd5
            )
            for contact, contact_head_img_url in contact_result
        ],
        'chatrooms': [
            schemas.ContactWithHeadImg(
                **contact.__dict__,
                smallHeadImgUrl=contact_head_img_url.smallHeadImgUrl,
                bigHeadImgUrl=contact_head_img_url.bigHeadImgUrl,
                headImgMd5=contact_head_img_url.headImgMd5
            )
            for contact, contact_head_img_url in chatroom_result
        ]
    }


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
        strUsrName: str,
        MsgSvrID: str,
        session_id: int,
        db_no: int = 0,
        db: Session = Depends(get_db)):
    sys_session = db.query(SysSession).filter_by(id=session_id).first()
    media_folder = get_decoded_media_path(sys_session)
    mp3_name = os.path.join(media_folder, f"{MsgSvrID}.mp3")
    logger.info(f"mp3: {mp3_name}")
    if os.path.exists(mp3_name):
        logger.info("存在，直接返回该数据")
        return FileResponse(mp3_name)
    else:
        # 需要判断是否是openim消息
        ctp = contact_type(strUsrName, sys_session)
        if ctp == 2:
            # openim 查询OpenIMContact
            oc_db = wx_db_for_conf(wx_settings.db_openim_media, sys_session)()
            try:
                media = oc_db.query(openim_media.Media).filter_by(Reserved0=MsgSvrID).first()
                logger.info(f"{media}")
                if media and media.Buf:
                    logger.info("查询到 media，准备生成 mp3 文件")
                    mp3_name = decode_media(media_folder, MsgSvrID, media.Buf)
                    logger.info(f"生成成功，{mp3_name}")
                    return FileResponse(mp3_name)
                else:
                    logger.info("库中不存在 media 记录或 media 记录不存在 Buf 值")
            finally:
                oc_db.close()
        else:
            logger.info("不存在，临时生成")
            db_array = media_msg_db_array(sys_session)
            for filename in db_array:
                session_local = wx_db_media_msg_by_filename(filename, sys_session)
                media_db = session_local()
                try:
                    media = media_db.query(Media).filter_by(Reserved0=MsgSvrID).first()
                    logger.info(f"{media}")
                    if media and media.Buf:
                        logger.info("查询到 media，准备生成 mp3 文件")
                        mp3_name = decode_media(media_folder, MsgSvrID, media.Buf)
                        logger.info(f"生成成功，{mp3_name}")
                        return FileResponse(mp3_name)
                    else:
                        logger.info("库中不存在 media 记录或 media 记录不存在 Buf 值")
                finally:
                    media_db.close()
    logger.info("没有获取到数据，返回 404")
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


@router.get("/chatroom", response_model=Optional[ChatRoomSchema])
async def get_chatroom_info(chat_room_name: str, db: Session = Depends(wx_db_micro_msg)):
    chat_room = db.query(ChatRoom).filter_by(ChatRoomName=chat_room_name).one()
    out = ChatRoomSchema(**chat_room.__dict__)
    if chat_room.RoomData:
        room_data = cr_extra_buf_pb2.RoomData()
        room_data.ParseFromString(chat_room.RoomData)
        out.ChatRoomMembers = []
        for u in room_data.users:
            if u.name and u.name.strip():
                out.ChatRoomMembers.append({
                    "userName": u.id,
                    "remark": u.name
                })
    return out


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
        # 查询Contact左表为主，outerjoin右表
        contact_query = (
            select(
                micro_msg.Contact.UserName,
                micro_msg.Contact.NickName,
                micro_msg.Contact.Remark,
                micro_msg.ContactHeadImgUrl.smallHeadImgUrl,
                micro_msg.ContactHeadImgUrl.bigHeadImgUrl,
                micro_msg.ContactHeadImgUrl.headImgMd5
            )
            .outerjoin(
                micro_msg.ContactHeadImgUrl,
                micro_msg.Contact.UserName == micro_msg.ContactHeadImgUrl.usrName
            )
            .where(micro_msg.Contact.UserName.in_(user_name_list))
        )

        # 查询ContactHeadImgUrl右表为主，outerjoin左表
        contact_img_query = (
            select(
                micro_msg.Contact.UserName,
                micro_msg.Contact.NickName,
                micro_msg.Contact.Remark,
                micro_msg.ContactHeadImgUrl.smallHeadImgUrl,
                micro_msg.ContactHeadImgUrl.bigHeadImgUrl,
                micro_msg.ContactHeadImgUrl.headImgMd5
            )
            .outerjoin(
                micro_msg.Contact,
                micro_msg.ContactHeadImgUrl.usrName == micro_msg.Contact.UserName
            )
            .where(micro_msg.ContactHeadImgUrl.usrName.in_(user_name_list))
        )

        # 使用union合并两者的查询结果，自动去重
        stmt = union(contact_query, contact_img_query)
        results = db.execute(stmt).all()
        out.ContactList = [
            schemas.ContactWithHeadImg(
                UserName=user_name,
                NickName=nick_name,
                Remark=remark,
                smallHeadImgUrl=small_head_img_url,
                bigHeadImgUrl=big_head_img_url,
                headImgMd5=head_img_md5
            )
            for user_name, nick_name, remark, small_head_img_url, big_head_img_url, head_img_md5 in results
        ]
    if chat_room.RoomData:
        room_data = cr_extra_buf_pb2.RoomData()
        room_data.ParseFromString(chat_room.RoomData)
        out.ChatRoomMembers = []
        for u in room_data.users:
            if u.name and u.name.strip():
                out.ChatRoomMembers.append({
                    "userName": u.id,
                    "remark": u.name
                })
    return out


@router.get("/head-image", response_model=Optional[ContactHeadImgUrlOut])
async def get_head_image(usrName: str, db: Session = Depends(wx_db_micro_msg)):
    return db.query(ContactHeadImgUrl).filter_by(usrName=usrName).first()


@router.get("/image-proxy", response_model=Optional[ContactHeadImgUrlOut])
async def get_head_image(encoded_url: str, request: Request):
    """
        图片代理接口，用于请求 Base64 编码的图片 URL，并将图片数据返回给调用方。

        参数:
        - encoded_url: Base64 编码的图片 URL。
        """
    # 解码 Base64 URL
    try:
        decoded_url = base64.b64decode(encoded_url).decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Base64 URL")

    # 使用 httpx 请求图片数据
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(decoded_url)
            response.raise_for_status()
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"Error fetching the image: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Error from the image server")

    # 确保返回的是图片内容
    content_type = response.headers.get("Content-Type", "")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="The URL does not point to an image")

    # 将图片数据流返回给调用方
    return StreamingResponse(
        BytesIO(response.content),
        media_type=content_type
    )
