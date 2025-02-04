from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class XFrameOptionsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response["X-Frame-Options"] = settings.X_FRAME_OPTIONS
        response["Content-Security-Policy"] = "frame-ancestors *"
        return response
