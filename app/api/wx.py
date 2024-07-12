import os
import shutil
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_user
from app.models.sys import SysSession
from app.schemas.sys_schemas import User, CreateSysSessionSchema, SysSessionSchema
from app.services.analyze import analyze
from app.services.save_head_images import save_header_images
from app.services.sys_task_maker import TaskObj, task_execute
from config.app_config import settings as app_settings
from config.data_config import settings as data_settings
from config.log_config import logger
from db.sys_db import get_db

router = APIRouter(
    prefix="/wx"
)


def save_file_chunk(file_path: str, file_chunk: UploadFile):
    with open(file_path, "ab") as f:
        shutil.copyfileobj(file_chunk.file, f)


@router.post("/create-session", response_model=SysSessionSchema)
def create_session(sys_session_in: CreateSysSessionSchema,
                   user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    sys_session = SysSession(**sys_session_in.__dict__)
    sys_session.owner_id = user.id
    db.add(sys_session)
    db.commit()
    return sys_session


@router.post("/upload-zip/")
async def upload_zip(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        sys_session_id: Optional[int] = Form(...),
        db: Session = Depends(get_db)
):
    logger.info("sys_session_id 为: " + str(sys_session_id))

    file_location = os.path.join(app_settings.sys_dir, data_settings.home, file.filename)
    save_file_chunk(file_location, file)

    # 获取上传文件的大小
    uploaded_file_size = os.path.getsize(file_location)

    # 判断文件上传完成
    if uploaded_file_size == file.file._file.seek(0, os.SEEK_END):
        logger.info("文件上传完成，大小为" + str(uploaded_file_size))
        sys_session = db.query(SysSession).filter_by(id=sys_session_id).first()
        task_obj = TaskObj(sys_session.owner_id, "数据库解析任务", analyze, file_location, sys_session_id)
        background_tasks.add_task(task_execute, task_obj)
        return {"detail": "File uploaded successfully."}
    else:
        logger.info("文件正在上传")
        return {"detail": "Upload incomplete."}


@router.get("/do-decrypt/")
def de_decrypt(background_tasks: BackgroundTasks):
    file_location = "D:\\wxdec\\wx\\jianghu\\wxid_b125nd5rc59r12.zip"
    task_obj = TaskObj(1, "数据库解析任务", analyze, file_location, None, 3)
    background_tasks.add_task(task_execute, task_obj)


@router.get("/save-head-images/")
def save_head_images():
    wx_dir = "D:\\wxdec\\wx\\jianghu\\wxid_b125nd5rc59r12"
    save_header_images(wx_dir, 'jianghu', 'wxid_b125nd5rc59r12')
