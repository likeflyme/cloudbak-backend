import os
import shutil
from typing import Optional, List

from fastapi import APIRouter, UploadFile, File, Form

from app.helper.directory_helper import get_wx_dir_directly
from config.log_config import logger
from pathlib import Path

router = APIRouter(
    prefix="/task"
)


@router.get("/task/")
async def upload_zip(
        size: int = 20,
        page: int = 1):
    return None
