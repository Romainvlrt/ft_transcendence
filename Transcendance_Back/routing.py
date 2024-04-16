from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from chat import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/system/$', consumers.SystemConsumer.as_asgi()),
    re_path(r'ws/private_chat/(?P<room_name>[a-zA-Z0-9@.+_-]+_[a-zA-Z0-9@.+_-]+)/$', consumers.PrivateChatConsumer.as_asgi()),
    re_path(r'ws/pfc/(?P<room_name>[a-zA-Z0-9@.+_-]+_[a-zA-Z0-9@.+_-]+)/$', consumers.PFCConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})