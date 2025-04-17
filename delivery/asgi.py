import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'delivery.settings')

django.setup()  # Ensure Django settings are loaded before any imports

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.chat.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(  # WebSockets require authentication middleware
        URLRouter(websocket_urlpatterns)
    ),
})
