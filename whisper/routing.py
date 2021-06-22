from django.conf.urls import url

from . import consumers


websocket_urlpatterns = [
    url(r'^ws/chat/unread-messages/$', consumers.UnreadChatMessagesConsumer.as_asgi()),
    url(r'^ws/chat/(?P<room_slug>[^/]+)/$', consumers.ChatConsumer.as_asgi()),
]
