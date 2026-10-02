from logging import getLogger
from time import perf_counter

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = getLogger(__name__)


class RequestTimingMiddleware:
    """Pure ASGI middleware logging HTTP request method, path, status, and duration."""

    def __init__(self, app: ASGIApp) -> None:
        """Initialize middleware with downstream ASGI application."""
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Intercept HTTP requests, measure duration, and log execution details."""
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        method = scope["method"]
        path = scope["path"]
        status_code = 500
        start_time = perf_counter()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self._app(scope, receive, send_wrapper)
        finally:
            duration_ms = (perf_counter() - start_time) * 1000
            logger.info(
                "request method=%s path=%s status=%s duration_ms=%.1f",
                method,
                path,
                status_code,
                duration_ms,
            )
