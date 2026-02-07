from django.urls import re_path
from .consumers import CodeExecutionConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/run/(?P<session_id>[^/]+)/$",
        CodeExecutionConsumer.as_asgi()
    ),
]