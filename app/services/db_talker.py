from collections import defaultdict

from app.models.sys import SysSession
from config.log_config import get_context_logger
from db.wx_db import msg_db_count, wx_db_msg
from app.models.multi.msg import Name2ID

# 保存库对应的用户消息排序
talker_id_cache = defaultdict(lambda: None)


def get_talker_id(sys_session: SysSession, db_no: int, wx_id: str):
    db_dict = talker_id_cache[sys_session.id]
    if db_dict is None:
        init_talker(sys_session)
        return get_talker_id(sys_session, db_no, wx_id)
    wx_dict = db_dict[db_no]
    if wx_dict is None:
        return None
    return wx_dict[wx_id]


def init_talker(sys_session: SysSession):
    logger = get_context_logger()
    logger.info("初始化 talkerId")
    if sys_session.id in talker_id_cache:
        del talker_id_cache[sys_session.id]
    db_dict = defaultdict(lambda: None)
    talker_id_cache[sys_session.id] = db_dict
    # 消息库数量
    count = msg_db_count(sys_session)
    logger.info(f"数据库最大值 {count}")
    for num in range(count - 1, -1, -1):
        logger.info(f"查询库 {num}")
        wx_dict = defaultdict(lambda: None)
        db_dict[num] = wx_dict
        wx_session_local = wx_db_msg(num, sys_session)
        with wx_session_local() as wx_db:
            talkers = wx_db.query(Name2ID).all()
            for index, talker in enumerate(talkers):
                wx_dict[talker.UsrName] = index + 1



