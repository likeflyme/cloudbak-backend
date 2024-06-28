import time

from db.sys_db import SessionLocal
from app.models.sys import SysTask
from config.log_config import logger

task_running = 2  # 任务执行中
task_success = 0  # 任务执行完成
task_fail = 1  # 任务执行失败


class TaskObj:
    def __init__(self, owner_id, name, func, *args):
        self.owner_id = owner_id
        self.name = name
        self.func = func
        self.args = args


class TaskExecutionError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"TaskExecutionError: {self.message}"


def task_execute(obj: TaskObj):
    start_time = time.time()
    logger.info("执行任务：" + obj.name)
    db = SessionLocal()
    task = SysTask(name=obj.name, owner_id=obj.owner_id, state=task_running)
    try:
        db.add(task)
        db.commit()
        db.refresh(task)
        # 调用函数
        try:
            obj.func(*obj.args)
            task.state = task_success
        except TaskExecutionError as e:
            task.state = task_fail
            task.detail = e.message
        except Exception as e:
            task.state = task_fail
            task.detail = "Unexpect Error, Please check out system log file"
            logger.error("任务中函数执行未知异常", e)
    except Exception as e:
        logger.error("任务执行未知异常", e)
    finally:
        # 更新时间
        task.update_time = time.time()
        db.commit()
        db.close()
        end_time = time.time()
        # 计算执行时间，单位为秒
        execution_time = end_time - start_time
        # 转换为毫秒
        execution_time_ms = execution_time * 1000
        logger.info(f'任务执行完成，花费时间: {execution_time_ms}ms')
