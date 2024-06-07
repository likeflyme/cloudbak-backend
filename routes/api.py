from fastapi import APIRouter
from app.api import auth
from app.api import msg

router = APIRouter(prefix="/api")

router.include_router(auth.router, tags=["auth"])
router.include_router(msg.router, tags=["msg"])

