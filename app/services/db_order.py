import array
from collections import defaultdict

from app.models.multi.msg import Msg
from app.models.sys import SysSession
from config.log_config import get_context_logger
from db.wx_db import wx_db_msg, msg_db_count

session_msg_sort = defaultdict(lambda: None)


def clear_session_msg_sort(sys_session_id):
    if sys_session_id in session_msg_sort:
        del session_msg_sort[sys_session_id]


def get_sorted_db(sys_session: SysSession):
    """
    获取消息库排序
    使用微信迁移功能或微信扩容数据库时，MSG库可能会有排序问题，通常情况下MSGx.db后x的数字越大，消息库的消息越靠近现在的时间
    但实践下某些人的库可能需要根据MSG表的CreateTime排序后确定。
    :param sys_session:
    :return:
    """
    logger = get_context_logger()
    sorted_array = session_msg_sort[sys_session.id]
    if sorted_array:
        logger.info(f"获取到缓存的库排序: {sorted_array}")
        return sorted_array
    # 查询数据库数量
    count = msg_db_count(sys_session)
    logger.info(f"数据库最大值 {count}")
    key_value_array = []
    # 查询库中消息的最大时间
    for num in range(count - 1, -1, -1):
        logger.info(f"查询库 {num}")
        wx_session_local = wx_db_msg(num, sys_session)
        wx_db = wx_session_local()
        try:
            msg = wx_db.query(Msg).order_by(Msg.CreateTime.desc(), Msg.Sequence.desc()).first()
            if msg:  # 只有查询到消息时才加入排序
                key_value_array.append({
                    "num": num,
                    "create_time": msg.CreateTime
                })
            else:
                logger.warning(f"警告：库 {num} 中没有找到消息记录，跳过。")
        finally:
            wx_db.close()
    # 排序
    key_value_array.sort(key=lambda x: x["create_time"])
    sorted_array = array.array('i', [x["num"] for x in key_value_array])
    session_msg_sort[sys_session.id] = sorted_array
    logger.info(f"生成库排序缓存：{session_msg_sort[sys_session.id]}")
    return sorted_array


def reversed_array(sys_session: SysSession):
    sorted_array = get_sorted_db(sys_session)
    return sorted_array.reverse()
