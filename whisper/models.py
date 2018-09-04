from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from whisper.managers import RoomQuerySet, MessageQuerySet


class Room(models.Model):
    slug = models.SlugField(unique=True, max_length=50)
    name = models.CharField(_('name'), max_length=200)
    users = models.ManyToManyField(to=settings.AUTH_USER_MODEL, verbose_name=_('users'), through='RoomUser')
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    objects = RoomQuerySet.as_manager()

    class Meta:
        verbose_name = _('room')
        verbose_name_plural = _('rooms')
        ordering = ('-modified',)
        default_permissions = settings.DEFAULT_PERMISSIONS

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('whisper:room_detail', args=(self.slug,))

    @property
    def group_name(self):
        return f'room_{self.id}'

    @property
    def user_groups(self):
        user_groups = []

        for member in self.member_set.all():
            user_groups.append(f'unread-chat-messages-{member.user.pk}')

        return user_groups

    def add_user(self, user):
        return RoomUser.objects.get_or_create(room=self, user=user)[0]


class RoomUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_query_name='member', related_name='member_set')
    last_read = models.DateTimeField(_('last read'), blank=True, null=True, default=None)
    last_notified = models.DateTimeField(_('last notified'), default=now)

    @staticmethod
    def get_possible_users_to_add(room):
        return get_user_model().objects.exclude(roomuser__room=room)

    @staticmethod
    def get_users(room):
        return get_user_model().objects.filter(roomuser__room=room)


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, default=None)
    text = models.TextField(_('text'))
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    objects = MessageQuerySet.as_manager()

    class Meta:
        verbose_name = _('message')
        verbose_name_plural = _('messages')
        ordering = ('created',)
        default_permissions = settings.DEFAULT_PERMISSIONS

    def __str__(self):
        return self.text

    def get_absolute_url(self):
        return self.room.get_absolute_url()
