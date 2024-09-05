import array
from collections import defaultdict

from app.models.multi.msg import Msg
from app.models.sys import SysSession
from config.log_config import logger
from db.wx_db import wx_db_msg, msg_db_count

session_msg_sort = defaultdict(lambda: None)


def clear_session_msg_sort(sys_session_id):
    if sys_session_id in session_msg_sort:
        del session_msg_sort[sys_session_id]


def get_sorted_db(sys_session: SysSession):
    """
    获取消息库排序
    :param sys_session:
    :return:
    """
    sorted_array = session_msg_sort[sys_session.id]
    if sorted_array:
        logger.info(f"获取到缓存的库排序: {sorted_array}")
        return sorted_array
    # 查询数据库数量
    count = msg_db_count(sys_session)
    logger.info(f"数据库最大值 {count}")
    sorted_array = array.array('i', [0] * count)
    key_value_array = [{} for _ in range(count)]
    # 查询库中消息的最大时间
    for num in range(count - 1, -1, -1):
        logger.info(f"查询库 {num}")
        wx_session_local = wx_db_msg(num, sys_session)
        wx_db = wx_session_local()
        try:
            msg = wx_db.query(Msg).order_by(Msg.CreateTime.desc(), Msg.Sequence.desc()).first()
            key_value_array[num] = {
                "num": num,
                "create_time": msg.CreateTime
            }
        finally:
            wx_db.close()
    # 排序
    key_value_array.sort(key=lambda x: x["create_time"])
    for n in range(len(sorted_array)):
        sorted_array[n] = key_value_array[n]["num"]
    session_msg_sort[sys_session.id] = sorted_array
    logger.info(f"生成库排序缓存：{session_msg_sort[sys_session.id]}")
    return sorted_array
