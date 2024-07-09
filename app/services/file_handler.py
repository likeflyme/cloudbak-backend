import os

from config.app_config import settings as app_settings
from config.data_config import settings as data_settings


def dat_to_img(sys_session_name: str, dat_path: str):
    """
    图片文件名转原文件名
    :param sys_session_name: 系统 session name，查找路径用
    :param dat_path: 类似以下路径 wxid_b125nd5rc59r12\\\\FileStorage\\\\MsgAttach\\\\07f138ed4330857426806eeaa9aaa932\\\\Image\\\\2024-06\\\\29448b7495e275478012d1142fb6e2bf.dat
    :return: 最后的 .dat 替换为 png 或 jpg
    """
    file_path = os.path.join(app_settings.sys_dir, data_settings.home, sys_session_name, dat_path)
    jpg_path = file_path.replace('.dat', '.jpg')
    if os.path.exists(jpg_path):
        return dat_path.replace('.dat', '.jpg')
    png_path = file_path.replace('.dat', '.png')
    if os.path.exists(png_path):
        return dat_path.replace('.dat', '.png')
    return None
