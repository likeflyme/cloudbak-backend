import os
import re
import lz4.block as lb
import xmltodict

from app.helper.directory_helper import get_session_dir
from app.models.multi.msg import Msg
from app.models.proto import msg_bytes_extra_pb2
from app.schemas.schemas import MsgWithExtra
from app.services.file_handler import dat_to_img


def clean_xml_data(xml_str):
    # 删除非XML字符
    xml_str = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u4e00-\u9fff\u3000-\u303F\uFF00-\uFFEF]', '', xml_str)
    # 删除空的CDATA节点
    xml_str = re.sub(r'<!\[CDATA\[\]\]>', '', xml_str)
    return xml_str


def parse(msg: Msg, session_id: int, db_no: int):
    nmsg = MsgWithExtra(**msg.__dict__)
    nmsg.MsgSvrIDStr = str(msg.MsgSvrID)
    nmsg.DbNo = db_no
    if msg.BytesExtra:
        proto = msg_bytes_extra_pb2.BytesExtra()
        proto.ParseFromString(msg.BytesExtra)
        for f3 in proto.f3:
            # 群聊消息发送者wxid
            if f3.s1 == 1:
                nmsg.WxId = f3.s2
            # 图片缩略图
            if f3.s1 == 3:
                # nmsg.Thumb = dat_to_img(session_id, f3.s2)
                if f3.s2:
                    img_path = f3.s2.replace("\\", "/")
                    nmsg.Thumb = img_path
            # 图片原图
            if f3.s1 == 4:
                # nmsg.Image = dat_to_img(session_id, f3.s2)
                if f3.s2:
                    img_path = f3.s2.replace("\\", "/")
                    file_path = os.path.join(get_session_dir(session_id), img_path)
                    if os.path.exists(file_path):
                        nmsg.Image = img_path
    if msg.CompressContent:
        unzipStr = lb.decompress(msg.CompressContent, uncompressed_size=0x10004)
        xml_data = unzipStr.decode('utf-8')
        compress_content_dict = xmltodict.parse(clean_xml_data(xml_data))
        nmsg.compress_content = compress_content_dict
    return nmsg
