import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_user
from app.models.sys import SysTask, SysUser
from config.app_config import settings
from db.sys_db import get_db
from app.services.analyze import analyze
from app.services.sys_task_maker import TaskObj, task_execute

from app.schemas.sys_schemas import SysTaskOut

router = APIRouter(
    prefix="/task"
)


@router.get("/", response_model=List[SysTaskOut])
async def upload_zip(
        size: int = 20,
        page: int = 1,
        db: Session = Depends(get_db),
        user: SysUser = Depends(get_current_user)):
    return db.query(SysTask).filter_by(owner_id=user.id).order_by(SysTask.id.desc()).offset((page - 1) * size).limit(size).all()


@router.get("/log")
async def get_video(task_id: int, db: Session = Depends(get_db)):
    task = db.query(SysTask).filter_by(id=task_id).one()

    if task.detail:
        log_path = os.path.join(settings.sys_dir, task.detail)
        if os.path.exists(log_path):
            return FileResponse(str(log_path), media_type="text/plain")
    raise HTTPException(status_code=404, detail="File not found")


@router.post("/single-decrypt/{sys_session_id}")
def single_decrypt(sys_session_id: int,
                   background_tasks: BackgroundTasks,
                   sys_user: SysUser = Depends(get_current_user)):
    """
    只执行一次解析任务
    :param sys_session_id:
    :param background_tasks:
    :param sys_user:
    :return:
    """
    task_obj = TaskObj(sys_user.id, "数据解析", analyze, sys_session_id)
    background_tasks.add_task(task_execute, task_obj)
