import traceback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

"""
    Custom middleware to catch unhandled exceptions globally
    and return clean JSON error responses with logs.
"""
class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)

        except HTTPException as http_exc:
            # Known HTTPException — return clean JSON
            error_log = {
                "method": request.method,
                "path": request.url.path,
                "status": http_exc.status_code,
                "detail": http_exc.detail
            }
            print(f"[HTTP_ERROR] {error_log}")
            return JSONResponse(
                status_code=http_exc.status_code,
                content={"detail": http_exc.detail},
            )

        except Exception as exc:
            # Unexpected error — log traceback for debugging
            tb = traceback.format_exc()

            error_log = {
                "method": request.method,
                "path": request.url.path,
                "status": 500,
                "error": str(exc),
                "trace": tb,
            }
            print(f"[SERVER_ERROR] {error_log}")

            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
            )