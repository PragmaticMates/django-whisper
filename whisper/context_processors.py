from whisper import settings
from whisper.models import Room


def chat(request):
    # TODO: cache to save DB requests or use template tags in chat.html template instead

    return {
        'chat_users': settings.CHAT_USERS,
        'recent_rooms': Room.objects.recent(request.user).not_empty()
    }
