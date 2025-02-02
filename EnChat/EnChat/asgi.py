import os
import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "EnChat.settings")
django.setup()  # Ensure this is called before importing any Django components

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns


application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
