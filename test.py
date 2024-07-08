import os.path
import subprocess

import lz4.block as lb

from app.models.proto import msg_img_pb2, test_pb2
from db.sys_db import SessionLocal
from db.wx_db import get_session_local
from app.models.sys import SysUser, SysSession
from app.dependencies.auth_dep import pwd_context
from config.app_config import settings as app_settings
from app.models.multi.msg import Msg

msg0_db_path = os.path.join(app_settings.sys_dir, 'wx\\jianghu\\wxid_b125nd5rc59r12\\Msg\\Multi\\decoded_MSG0.db')


def create_user():
    """
    创建新用户
    :return:
    """
    session = SessionLocal()

    try:
        password = pwd_context.hash('secret')
        user = SysUser(username='admin', password=password, nickname='nickname', state=1)
        session.add(user)
        session.commit()

        sys_session = SysSession(name='mmxc', wx_id='wxid_x1j6ne5cnl8r19', wx_acct_name='MMXC', owner_id=user.id)
        session.add(sys_session)
        session.commit()
    finally:
        session.close()


def decrypt_yinyong():
    db_path = os.path.join(app_settings.sys_dir, 'wx\\jianghu\\wxid_b125nd5rc59r12\\Msg\\Multi\\decoded_MSG0.db')
    session_local = get_session_local(db_path)
    db = session_local()
    try:
        msg = db.query(Msg).filter_by(localId=63504).first()
        print(msg)
        if msg:
            unzipStr = lb.decompress(msg.BytesExtra, uncompressed_size=0x10004)
            text = unzipStr.decode('utf-8')
            print(text)
    finally:
        db.close()


def decode_protobuf_img(data):
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



# session_local = get_session_local(msg0_db_path)
# db = session_local()
# try:
#     msg = db.query(Msg).filter_by(localId=63504).first()
#     if msg:
#         out = decode_protobuf_img(msg.BytesExtra)
#         print(out)
#         new_message = msg_img_pb2.MyMessage()
#         new_message.ParseFromString(msg.BytesExtra)
#
#         print(f"Field 1: {new_message.field_1}")
#         print(f"Field 2: {new_message.field_2}")
#         print(f"Msg Source - Bizflag: {new_message.msg_source.bizflag}")
#         print(f"Msg Source - UUID: {new_message.msg_source.uuid}")
#         print(f"Msg Source - FR: {new_message.msg_source.alnode.fr}")
#         print(f"Field 4: {new_message.field_4}")
#         print(f"Field 5: {new_message.field_5}")
# finally:
#     db.close()


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

    out = decode_protobuf_img(serialized_data)

    print(out)


generate_proto()



