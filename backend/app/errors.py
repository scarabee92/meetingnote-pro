"""오류 응답은 항상 {code, msg}. 코드는 15종만 쓴다."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

CODES = {
    "EMAIL_INVALID", "PASSWORD_TOO_WEAK", "TOKEN_EXPIRED", "INVITE_NOT_FOUND",
    "MEETING_NOT_FOUND", "EMAIL_DUPLICATED", "TEAM_FULL", "PAYLOAD_TOO_LARGE",
    "UNSUPPORTED_MEDIA_TYPE", "INVALID_CREDENTIALS", "UNAUTHORIZED",
    "FORBIDDEN", "OWNER_ONLY", "VALIDATION_ERROR", "NOT_FOUND",
}


class ApiError(Exception):
    def __init__(self, status: int, code: str, msg: str):
        assert code in CODES, f"정의되지 않은 오류 코드: {code}"
        self.status, self.code, self.msg = status, code, msg


def _resp(status: int, code: str, msg: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code, "msg": msg})


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api(_: Request, e: ApiError):
        return _resp(e.status, e.code, e.msg)

    @app.exception_handler(RequestValidationError)
    async def _val(_: Request, e: RequestValidationError):
        return _resp(400, "VALIDATION_ERROR", "요청 값이 올바르지 않습니다")

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, e: StarletteHTTPException):
        if e.status_code == 404:
            return _resp(404, "NOT_FOUND", "찾을 수 없습니다")
        if e.status_code in (401, 403):
            return _resp(e.status_code, "FORBIDDEN" if e.status_code == 403 else "TOKEN_EXPIRED", "권한이 없습니다")
        return _resp(e.status_code, "VALIDATION_ERROR", "요청을 처리할 수 없습니다")
