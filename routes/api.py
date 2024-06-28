from fastapi import APIRouter
from app.api import auth, msg, wx, user_api

router = APIRouter(prefix="/api")

router.include_router(auth.router, tags=["auth"])
router.include_router(msg.router, tags=["msg"])
router.include_router(wx.router, tags=["wx"])
router.include_router(user_api.router, tags=["user"])

