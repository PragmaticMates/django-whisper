import json
from json import JSONDecodeError
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from django.template.defaultfilters import date
from django.templatetags.tz import localtime
from whisper import settings
from whisper.models import Message


class ChatMessageHelper:
    # send system message
    @staticmethod
    async def send_message(room, text_message, sender=None):
        message = Message.objects.create(
            room=room,
            user=sender,
            text=text_message,
        )

        # update modified timestamp
        room.save()

        channel_layer = get_channel_layer()

        # Send message to room group
        await channel_layer.group_send(
            room.group_name, {
                'type': 'chat_message',
                'message': str(message),
                'username': str(sender) if sender is not None else None,
                'timestamp': date(localtime(message.created), settings.DATETIME_FORMAT)
            }
        )

        for group_name in room.user_groups:
            await channel_layer.group_send(
                group_name, {
                    'type': 'chat_message',
                }
            )

        await ChatMessageHelper.send_room_properties(room, channel_layer)

    @staticmethod
    def message_from_type(type, **params):
        message = settings.MESSAGE_TYPES.get(type, type)

        try:
            return message.format(**params) if params is not None else message
        except AttributeError:
            return message

    @staticmethod
    async def send_room_properties(room, channel_layer):
        # send room properties
        user_count = await ChatMessageHelper.get_user_count(room)
        await channel_layer.group_send(
            room.group_name, {
                'type': 'room_properties',
                'room_name': room.name,
                'room_id': room.pk,
                'user_count': user_count
            })

    @staticmethod
    @database_sync_to_async
    def get_user_count(room):
        return room.users.count()
