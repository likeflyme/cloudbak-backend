import os
import shutil
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.dependencies.auth_dep import get_current_user
from app.schemas.sys_schemas import User
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

UPLOAD_DIRECTORY = "./uploaded_files"

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)


def save_file_chunk(file_path: str, file_chunk: UploadFile):
    with open(file_path, "ab") as f:
        shutil.copyfileobj(file_chunk.file, f)


@router.post("/upload-zip/")
async def upload_zip(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        sys_session_id: Optional[int] = Form(...),
        key: Optional[str] = Form(None),
        user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    logger.info("sys_session_id 为: " + str(sys_session_id))
    logger.info("key为: " + key)

    file_location = os.path.join(app_settings.sys_dir, data_settings.home, file.filename)
    save_file_chunk(file_location, file)

    # 获取上传文件的大小
    uploaded_file_size = os.path.getsize(file_location)

    # 如果需要判断上传是否完成，可以和客户端上传的文件大小进行比较
    if uploaded_file_size == file.file._file.seek(0, os.SEEK_END):
        logger.info("文件上传完成，大小为" + str(uploaded_file_size))

        task_obj = TaskObj(user.id, "数据库解析任务", analyze, file_location, user, sys_session_id)
        background_tasks.add_task(task_execute, task_obj)
        return {"detail": "File uploaded successfully."}
    else:
        logger.info("文件正在上传")
        return {"detail": "Upload incomplete."}


def print_name(name: str):
    logger.info("my name is : " + name)


@router.post("/do-task/")
def do_task(background_tasks: BackgroundTasks):
    logger.info("执行 do-task")
    name = "hello word"
    task_obj = TaskObj(0, "测试任务", print_name, name)
    background_tasks.add_task(task_execute, task_obj)
    logger.info("执行 do-task 结束")


@router.get("/do-decrypt/")
def de_decrypt(background_tasks: BackgroundTasks):
    file_location = "D:\\wxdec\\wx\\jianghu\\wxid_b125nd5rc59r12.zip"
    task_obj = TaskObj(1, "数据库解析任务", analyze, file_location, None, 3)
    background_tasks.add_task(task_execute, task_obj)


@router.get("/save-head-images/")
def save_head_images():
    wx_dir = "D:\\wxdec\\wx\\jianghu\\wxid_b125nd5rc59r12"
    save_header_images(wx_dir, 'jianghu', 'wxid_b125nd5rc59r12')
