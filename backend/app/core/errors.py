from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def _error_response(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message}},
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return _error_response(exc.code, exc.message, exc.status)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            409: "CONFLICT",
            429: "RATE_LIMITED",
        }
        code = code_map.get(exc.status_code, "HTTP_ERROR")
        message = str(exc.detail) if exc.detail else "Ошибка"
        return _error_response(code, message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(
        _: Request, exc: RequestValidationError,
    ) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else None
        message = "Ошибка валидации"
        if first:
            loc = ".".join(str(p) for p in first.get("loc", []))
            message = f"{loc}: {first.get('msg', 'некорректное значение')}"
        return _error_response("VALIDATION_ERROR", message, 422)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        return _error_response("INTERNAL_ERROR", str(exc), 500)