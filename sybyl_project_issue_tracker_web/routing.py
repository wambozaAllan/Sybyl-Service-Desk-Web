from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from chat.consumers import ChatConsumer2
from project_management.consumers import ChatConsumer

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('chatRoom/<client_id>/', ChatConsumer2),
            path('groupChat/<project_forum_id>,<msg_id>,<chatstate>/', ChatConsumer),
        ])
    ),
})
