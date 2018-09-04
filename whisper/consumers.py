import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from django.template.defaultfilters import date
from django.templatetags.tz import localtime
from django.utils.timezone import now

from whisper import settings
from whisper.helpers import ChatMessageHelper
from whisper.models import Room, Message, RoomUser


class ChatConsumer(AsyncWebsocketConsumer):
    # TODO: use AsyncJsonWebsocketConsumer instead
    # https://github.com/andrewgodwin/channels-examples/blob/master/multichat/chat/consumers.py

    async def websocket_connect(self, message):
        room_slug = self.scope['url_route']['kwargs']['room_slug']

        # init variables
        self.user = self.scope['user']
        self.room = await self.get_room(room_slug)
        self.groups.append(self.room.group_name)
        type = message['type']

        # update last read flag of current room user
        if await self.get_room_user() is None:
            await ChatMessageHelper.send_message(self.room, json.dumps({'USER_JOINED': {'username': str(self.user)}}))

        await self.update_room_user(self.room, self.user)
        await super().websocket_connect(message)

        # send room properties
        self.user_count = await ChatMessageHelper.get_user_count(self.room)
        await self.send(text_data=json.dumps({
            'type': 'room_properties',
            'room_name': self.room.name,
            'room_id': self.room.pk,
            'room_slug': room_slug,
            'room_modified': date(localtime(self.room.modified), settings.DATETIME_FORMAT),
            'user_count': self.user_count
        }))

        # init room with previous messages
        for message in await self.get_room_messages():
            await self.send(text_data=json.dumps({
                'type': type,
                'message': message.text if message.user is not None else ChatMessageHelper.localized_message_from_json(message.text),
                'timestamp': date(localtime(message.created), settings.DATETIME_FORMAT),
                'username': str(message.user) if message.user is not None else None,
            }))

        await self.channel_layer.group_send(
            f'unread-chat-messages-{self.user.pk}', {
                'type': 'chat_message',
            }
        )

    @database_sync_to_async
    def get_room(self, slug):
        try:
            return Room.objects.get(slug=slug)
        except ObjectDoesNotExist:
            return Room.objects.create_from_slug(slug, self.user)

    @database_sync_to_async
    def get_room_messages(self):
        return self.room.message_set.all()

    @database_sync_to_async
    def remove_user_from_room(self):
        return RoomUser.objects.filter(user=self.user, room=self.room).delete()

    @database_sync_to_async
    def get_room_users(self):
        return RoomUser.get_users(self.room)

    @database_sync_to_async
    def get_room_user(self):
        try:
            return RoomUser.objects.get(room=self.room, user=self.user)
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def update_room_user(self, room, user):
        RoomUser.objects.update_or_create(room=room, user=user, defaults={'last_read': now()})

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        if self.user.is_authenticated:
            text_data_json = json.loads(text_data)
            json_type = text_data_json.get('type', None)

            if json_type == 'leave_room':
                await self.remove_user_from_room()
                dict_message = {'USER_LEFT': {'username': str(self.user), 'room': self.room.name, "timestamp": date(localtime(now()), settings.DATETIME_FORMAT)}}
                await ChatMessageHelper.send_message(self.room, json.dumps(dict_message))
            elif json_type == 'user_typing':

                for group_name in self.groups:
                    await self.channel_layer.group_send(
                        group_name, {
                            'type': 'user_typing',
                            'username': str(self.user),
                            'text': ChatMessageHelper.message_from_type('USER_TYPING', username=str(self.user))
                        }
                    )
            elif json_type == 'room_options':
                users = await self.get_room_users()
                print(users)

                await self.send(text_data=json.dumps({
                    'type': 'room_options',
                    'members': [{
                        'id': user.id,
                        'name': str(user),
                        'html': loader.get_template('whisper/user.html').render({'user': user})
                    } for user in users],
                }))

            else:
                text = text_data_json['message']

                # update last read flag of current room user (create if not exists)
                await self.update_room_user(self.room, self.user)

                message = Message.objects.create(
                    room=self.room,
                    user=self.user,
                    text=text
                )

                # update modified timestamp
                self.room.save()

                # Send message to room group
                for group_name in self.groups:
                    await self.channel_layer.group_send(
                        group_name, {
                            'type': 'chat_message',
                            'message': text,
                            'username': str(self.user),
                            'timestamp': date(localtime(message.created), settings.DATETIME_FORMAT)
                        }
                    )

                for group_name in self.room.user_groups:
                    await self.channel_layer.group_send(
                        group_name, {
                            'type': 'chat_message',
                        }
                    )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))

    # Receive user_typing from room group
    async def user_typing(self, event):
        # Send user_typing to WebSocket
        await self.send(text_data=json.dumps(event))

    # Receive room_properties from room group
    async def room_properties(self, event):
        # Send room_properties to WebSocket
        await self.send(text_data=json.dumps(event))


class UnreadChatMessagesConsumer(AsyncWebsocketConsumer):
    async def websocket_connect(self, message):
        self.user = self.scope['user']

        if self.user.is_authenticated:
            self.group_name = f'unread-chat-messages-{self.user.pk}'
            self.groups.append(self.group_name)

            await super().websocket_connect(message)

            unread_messages = await self.get_unread_messages(self.scope['user'])

            # init current socket
            await self.send(text_data=json.dumps(unread_messages))

    @database_sync_to_async
    def get_unread_messages(self, user):
        unread_messages = Message.objects.unread_by_user(user).count()
        unread_rooms = Room.objects.with_unread_messages(user).values('pk', 'unread_messages')

        return {
            'unread_messages': unread_messages,
            'unread_rooms': list(unread_rooms)
        }

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        unread_messages = await self.get_unread_messages(self.scope['user'])
        await self.send(text_data=json.dumps(unread_messages))
