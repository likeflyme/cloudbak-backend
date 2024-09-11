# exception_handlers.py

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from config.log_config import logger


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error occurred: {exc.detail}")
    if exc.status_code == 404:
        raise exc
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail},
        )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error occurred: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"message": "Validation error", "errors": exc.errors()},
    )


async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": f"Internal server error, {str(exc)}"},
    )
