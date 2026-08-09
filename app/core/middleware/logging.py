from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import json
import logging
import time

logger = logging.getLogger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        start = time.time()

        body = await request.body()

        async def receive():
            return {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }

        request = Request(request.scope, receive)

        try:
            request_body = json.loads(body.decode()) if body else None
        except Exception:
            request_body = body.decode(errors="ignore")

        response = await call_next(request)

        logger.info(
            f"""
Method : {request.method}
URL    : {request.url}
Body   : {request_body}
Status : {response.status_code}
Time   : {(time.time()-start)*1000:.2f} ms
"""
        )

        return response