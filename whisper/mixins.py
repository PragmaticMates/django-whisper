from django.core.exceptions import ObjectDoesNotExist
from django.utils.functional import cached_property

from whisper.models import Room


class ChatRoomMixin(object):
    @cached_property
    def room_members(self):
        raise NotImplementedError()

    @property
    def room_slug(self):
        raise NotImplementedError()

    @property
    def room(self):
        try:
            return Room.objects.get(slug=self.room_slug)
        except ObjectDoesNotExist:
            return None
