from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
from app.models.favorite import Config, FavItems, FavDataItem
from db.wx_db import get_session_local


def get_db(path):
    session_local = get_session_local(path)
    db = session_local()
    return db


def decrypt_AES(cipher_text, key, iv):
    # 将 base64 编码的密文解码为字节
    cipher_text_bytes = base64.b64decode(cipher_text)

    # 创建 AES 解密器
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # 解密并去除填充
    decrypted_data = unpad(cipher.decrypt(cipher_text_bytes), AES.block_size)

    # 返回解密后的数据
    return decrypted_data.decode('utf-8')


