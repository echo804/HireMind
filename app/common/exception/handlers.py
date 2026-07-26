"""Global exception handlers"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.common.exception.error_code import ErrorCode
from app.common.result import Result


class BusinessException(Exception):
    """Business exception with error code"""
    def __init__(self, error_code: ErrorCode, message: str = ""):
        self.error_code = error_code
        self.message = message or error_code.name
        super().__init__(self.message)


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers"""
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        return JSONResponse(status_code=200, content=Result.error(code=exc.error_code.value, message=exc.message).model_dump())

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=200, content=Result.error(code=ErrorCode.INTERNAL_ERROR.value, message=str(exc) or "internal error").model_dump())
