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


def _http_status(code: int) -> int:
    """Map error code to HTTP status"""
    if code == ErrorCode.BAD_REQUEST:
        return 400
    if code == ErrorCode.UNAUTHORIZED:
        return 401
    if code == ErrorCode.FORBIDDEN:
        return 403
    if code in (ErrorCode.NOT_FOUND, ErrorCode.RESUME_NOT_FOUND,
                ErrorCode.INTERVIEW_SESSION_NOT_FOUND, ErrorCode.KNOWLEDGE_BASE_NOT_FOUND,
                ErrorCode.SCHEDULE_NOT_FOUND, ErrorCode.VOICE_SESSION_NOT_FOUND):
        return 404
    if code == ErrorCode.RESUME_DUPLICATE or code == ErrorCode.SCHEDULE_CONFLICT:
        return 409
    if code == ErrorCode.STORAGE_FILE_TOO_LARGE:
        return 413
    if code == ErrorCode.STORAGE_INVALID_TYPE:
        return 415
    return 500


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers"""
    @app.exception_handler(BusinessException)
    async def business_exception_handler(request: Request, exc: BusinessException):
        status = _http_status(exc.error_code.value)
        return JSONResponse(
            status_code=status,
            content=Result.error(code=exc.error_code.value, message=exc.message).model_dump(),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=Result.error(
                code=ErrorCode.INTERNAL_ERROR.value,
                message=str(exc) or "internal error",
            ).model_dump(),
        )
