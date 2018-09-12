from django.conf import settings
from django.contrib.auth import get_user_model

from django.utils.translation import ugettext_lazy, ugettext

ROOM_FORM_CLASS = getattr(
    settings, 'WHISPER_ROOM_FORM_CLASS', None
)

ROOM_ADD_MEMBER_FORM_CLASS = getattr(
    settings, 'WHISPER_ROOM_ADD_MEMBER_FORM_CLASS', 'whisper.forms.RoomAddMemberForm'
)

USER_ACTIVITY_ATTRIBUTE = getattr(
    settings, 'WHISPER_USER_ACTIVITY_ATTRIBUTE', None
)

USER_INFO = getattr(
    settings, 'WHISPER_USER_INFO', lambda user: None if USER_ACTIVITY_ATTRIBUTE is None else getattr(user, USER_ACTIVITY_ATTRIBUTE)
)

CHAT_USERS = getattr(
    settings, 'WHISPER_CHAT_USERS', lambda: get_user_model().all()
)

RECENT_ROOM_THRESHOLD = getattr(
    settings, 'WHISPER_RECENT_ROOM_THRESHOLD', 7  # days
)

NOTIFY_ROOM_THRESHOLD = getattr(
    settings, 'WHISPER_NOTIFY_ROOM_THRESHOLD', 30  # minutes
)

DATETIME_FORMAT = getattr(
    settings, 'WHISPER_DATETIME_FORMAT', 'd.m.Y H:i:s'
)

MESSAGE_TYPES = getattr(
    settings, 'WHISPER_MESSAGE_TYPES',
    {
        'USER_LEFT': ugettext_lazy('{username} left room'),
        'USER_JOINED': ugettext_lazy('{username} joined room'),
        'USER_TYPING': ugettext('{username} is typing ...'),
    }
)
