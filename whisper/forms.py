import json

from asgiref.sync import async_to_sync
from django import forms
from django.contrib.auth import get_user_model
from django.forms import ModelMultipleChoiceField
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from whisper.helpers import ChatMessageHelper
from whisper.models import Room, RoomUser


class RoomAddMemberForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['users']

    def __init__(self, current_user=None, *args, **kwargs):
        room_pk = kwargs.pop('room_pk', None)
        super().__init__(*args, **kwargs)
        self.current_user = current_user

        if room_pk is not None:
            self.possible_users = RoomUser.get_possible_users_to_add(room_pk)
        else:
            self.possible_users = get_user_model().objects.all()

        self.fields['users'] = ModelMultipleChoiceField(required=True, queryset=self.possible_users)

    def clean(self):
        cleaned_data = super().clean()
        users = cleaned_data.get('users', None)
        users = set(users.values_list('pk', flat=True))
        current_users = RoomUser.get_users(self.instance)
        current_users = set(current_users.values_list('id', flat=True))

        if self.instance.is_user_to_user_room and not current_users.issubset(users):
            self.add_error('users', _('Cannot remove users from user to user chat'))

        if self.current_user.pk not in users:
            self.add_error('users', _('Cannot remove yourself from chat'))

        return cleaned_data

    def save(self, commit=True):
        users = self.cleaned_data.pop('users', None)
        current_users = RoomUser.get_users(self.instance)

        if self.instance.is_user_to_user_room:
            users = list(users.values_list('pk', flat=True))
            return Room.objects.get_or_create_from_users(users)
        else:
            for current_user in current_users:
                if current_user not in users:
                    async_to_sync(ChatMessageHelper.send_message)(self.instance, json.dumps({'USER_LEFT': {'username': str(current_user)}}))
                    RoomUser.objects.filter(user=current_user, room=self.instance).delete()

            if users is not None:
                for user in users:
                    if user not in current_users:
                        RoomUser.objects.update_or_create(room=self.instance, user=user, defaults={'last_read': now()})
                        async_to_sync(ChatMessageHelper.send_message)(self.instance, json.dumps({'USER_JOINED': {'username': str(user)}}))

            return super().save(commit)
