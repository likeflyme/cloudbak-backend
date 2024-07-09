import os.path
import subprocess

import lz4.block as lb

from app.models.proto import test_pb2, msg_bytes_extra_pb2
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
        msg = db.query(Msg).filter_by(localId=63360).first()
        print(msg)
        if msg:

            print(decode_protobuf(msg.BytesExtra))

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


deserialize_img()

