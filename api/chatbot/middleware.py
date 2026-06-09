import logging
import time

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class XFrameOptionsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response["X-Frame-Options"] = settings.X_FRAME_OPTIONS
        response["Content-Security-Policy"] = "frame-ancestors *"
        return response


class RequestTimingMiddleware:
    """
    Logs method, path, status, and wall-clock duration for every request.
    Supports both sync (WSGI) and async (ASGI) stacks per Django 4.1+ pattern.
    """

    async_capable = True
    sync_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        self._log(request, response, start)
        return response

    async def __acall__(self, request):
        start = time.perf_counter()
        response = await self.get_response(request)
        self._log(request, response, start)
        return response

    @staticmethod
    def _log(request, response, start):
        logger.info(
            "perf %s %s → %d %.1fms",
            request.method,
            request.path,
            response.status_code,
            (time.perf_counter() - start) * 1000,
        )
