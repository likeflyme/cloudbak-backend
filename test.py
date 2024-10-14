import os.path
import re
import subprocess
import time
from datetime import datetime

import google
import pilk
import os
import array

import lz4.block as lb

from collections import defaultdict
from app.dependencies.auth_dep import pwd_context
from app.models.micro_msg import Contact, ContactHeadImgUrl, ChatRoom
from app.models.multi.media_msg import Media
from app.models.proto import test_pb2, msg_bytes_extra_pb2, cr_extra_buf_pb2
from app.models.sys import SysUser, SysSession
from app.services.save_head_images import save_header_images, analyze_head_images
from config.app_config import settings as app_settings
from db.sys_db import SessionLocal
from db.wx_db import get_session_local, msg_db_count, wx_db_msg, media_msg_db_array
from config.log_config import logger, get_context_logger, analyze_logger
from app.models.multi.msg import Msg
from sqlalchemy import select, and_

msg0_db_path = os.path.join(app_settings.sys_dir, 'sessions\\1\\wxid_b125nd5rc59r12\\Msg\\Multi\\decoded_MSG6.db')


def decode_protobuf(data):
    """
    聊天记录图片 BytesExtra protobuf 结构
    :param data:
    :return:
    """
    process = subprocess.Popen([r'protoc', '--decode_raw'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    output = error = None
    try:
        output, error = process.communicate(data)
        if error:
            print(error)
    except OSError as e:
        print(e)
        pass
    finally:
        if process.poll() != 0:
            process.wait()
    return output


def generate_proto():
    animal = test_pb2.Animal()
    animal.title = 'dog'
    animal.age = 12
    animal.isDead = False

    child1 = test_pb2.Animal()
    child1.title = 'child1'
    child1.age = 1
    child1.isDead = False
    child1.foot.extend(['foot1', 'foot2', 'foot3'])

    child2 = test_pb2.Animal()
    child2.title = 'child2'
    child2.age = 2
    child2.isDead = True
    child2.foot.extend(['foot1', 'foot2', 'foot3'])

    animal.children.append(child1)
    animal.children.append(child2)

    animal.foot.extend(['pfoot1', 'pfoot2', 'pfoot3'])

    serialized_data = animal.SerializeToString()
    print(f"Serialized data: {serialized_data}")

    out = decode_protobuf(serialized_data)

    print(out)


def deserialize_img():
    session_local = get_session_local(msg0_db_path)
    db = session_local()
    try:
        msg = db.query(Msg).filter_by(localId=44695).first()
        print(msg)
        if msg:
            # print('-----decode protobuf-------')
            # print(decode_protobuf(msg.BytesExtra))
            # print(decode_protobuf(msg.CompressContent))

            # print('-----lz4 decompress compress content-----')
            # unzipStr = lb.decompress(msg.CompressContent, uncompressed_size=0x10004)
            # text = unzipStr.decode('utf-8')
            # print(text)
            # # print(xml_data)
            # compress_content_dict = xmltodict.parse(clean_xml_data(text))
            # print(compress_content_dict)

            be = msg_bytes_extra_pb2.BytesExtra()
            be.ParseFromString(msg.BytesExtra)

            print('print f1')
            for f1 in be.f1:
                print(f'{f1.s1}: {f1.s2}')
            print('print f3')
            for f3 in be.f3:
                print(f'{f3.s1}: {f3.s2}')
    finally:
        db.close()


def deserialize_vedio():
    session_local = get_session_local(msg0_db_path)
    db = session_local()
    try:
        # msg = db.query(Msg).filter_by(localId=3540).first()
        msg = db.query(Msg).filter_by(localId=44695).first()
        print(msg)
        if msg:
            print('-----decode protobuf-------')
            print(decode_protobuf(msg.BytesExtra))
            # print(decode_protobuf(msg.CompressContent))

            # print('-----lz4 decompress compress content-----')
            # unzipStr = lb.decompress(msg.CompressContent, uncompressed_size=0x10004)
            # text = unzipStr.decode('utf-8')
            # print(text)
            # # print(xml_data)
            # compress_content_dict = xmltodict.parse(clean_xml_data(text))
            # print(compress_content_dict)

            be = msg_bytes_extra_pb2.BytesExtra()
            be.ParseFromString(msg.BytesExtra)

            print('print f1')
            for f1 in be.f1:
                print(f'{f1.s1}: {f1.s2}')
            print('print f3')
            for f3 in be.f3:
                print(f'{f3.s1}: {f3.s2}')
    finally:
        db.close()


# 清理XML数据函数
def clean_xml_data(xml_str):
    # 删除非XML字符
    xml_str = re.sub(r'[^\x09\x0A\x0D\x20-\x7E\u4e00-\u9fff]', '', xml_str)
    # 删除空的CDATA节点
    xml_str = re.sub(r'<!\[CDATA\[\]\]>', '', xml_str)
    return xml_str


def decrypt_contact_ExtraBuf():
    db_path = os.path.join(app_settings.sys_dir, 'wx\\jianghu\\wxid_b125nd5rc59r12\\Msg\\decoded_MicroMsg.db')
    session_local = get_session_local(db_path)
    db = session_local()
    try:
        contact = db.query(Contact).filter_by(UserName='guxuefei0719').first()
        print(contact.NickName)
        if contact:
            unzipStr = lb.decompress(contact.ExtraBuf, uncompressed_size=0x10004)
            text = unzipStr.decode('utf-8')
            print(text)
    finally:
        db.close()


def decode_media(data):
    silk_mame = 'D:\\workspace\\test.silk'
    pcm_name = 'D:\\workspace\\test.pcm'
    mp3_name = 'D:\\workspace\\test.mp3'
    with open(silk_mame, 'wb') as file:
        # 将字节数组写入文件
        file.write(data)
    # silk 转 pcm
    pilk.decode(silk_mame, pcm_name, 44100)
    # pcm 转 mp3
    os.system(f"ffmpeg -y -f s16le -i {pcm_name} -ar 44100 -ac 1 {mp3_name}")


# sys_session_id = 8
# analyze_head_images(sys_session_id)

def logger_error_test(num):
    log_dir = os.path.join(app_settings.sys_dir, app_settings.log_dir, app_settings.log_task_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file_name = int(time.time() * 1000)
    log_file_path = os.path.join(str(log_dir), str(log_file_name))
    log = analyze_logger(str(log_file_name), log_file_path)

    try:
        if num == 1:
            raise Exception('test error')
    except Exception as e:
        log.error(e)


from apscheduler.schedulers.blocking import BlockingScheduler
scheduler = BlockingScheduler()


def tick():
    print('Tick! The time is: %s' % datetime.now())
    jobs = scheduler.get_jobs()
    print(len(jobs))
    for job in jobs:
        print(f'Job is ${job.id} - ${job.name}, ${job.args}')


if __name__ == '__main__':

    scheduler.add_executor('processpool')
    scheduler.add_job(tick, 'interval', seconds=3)
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


