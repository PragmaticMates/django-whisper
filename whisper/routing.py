from django.urls import re_path

from . import consumers


websocket_urlpatterns = [
    re_path(r'^ws/chat/unread-messages/$', consumers.UnreadChatMessagesConsumer.as_asgi()),
    re_path(r'^ws/chat/(?P<room_slug>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
]
