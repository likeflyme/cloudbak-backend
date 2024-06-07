from typing import List

from fastapi import APIRouter, Depends
from fastapi_pagination import Page
from sqlalchemy.orm import Session

from app.models import micro_msg
from app.schemas import schemas
from db.wx_db import wx_db_micro_msg
from fastapi_pagination.ext.sqlalchemy import paginate

router = APIRouter(
    prefix="/msg"
)


@router.get("/sessions", response_model=Page[schemas.Session])
def red_sessions(page: int = 1, size: int = 50, db: Session = Depends(wx_db_micro_msg)):
    return paginate(db.query(micro_msg.Session).offset((page - 1) * size).limit(size))
