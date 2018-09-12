import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from django.template.defaultfilters import date
from django.templatetags.tz import localtime
from django.utils.timezone import now

from whisper import settings
from whisper.helpers import ChatMessageHelper
from whisper.models import Room, Message, RoomUser
from whisper.views import RoomAddMemberView


class ChatConsumer(AsyncJsonWebsocketConsumer):

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
        await self.send_json(content={
            'type': 'room_properties',
            'room_name': self.room.name,
            'room_id': self.room.pk,
            'room_slug': room_slug,
            'room_modified': date(localtime(self.room.modified), settings.DATETIME_FORMAT),
            'user_count': self.user_count,
            'is_user_to_user': self.room.is_user_to_user_room
        })

        # init room with previous messages
        for message in await self.get_room_messages():
            await self.send_json(content={
                'type': type,
                'message': str(message),
                'timestamp': date(localtime(message.created), settings.DATETIME_FORMAT),
                'username': str(message.user) if message.user is not None else None,
            })

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
    def remove_user_from_room(self, user_id):
        return RoomUser.objects.filter(user__pk=user_id, room=self.room).delete()

    @database_sync_to_async
    def get_user(self, user_id):
        return RoomUser.get_user(self.room, user_id)

    @database_sync_to_async
    def get_room_users(self):
        return RoomUser.get_users(self.room)

    @database_sync_to_async
    def add_room_users(self, user_pks):
        users = []

        user_objects = get_user_model().objects.filter(pk__in=user_pks)

        for user in user_objects:
            users.append(self.room.add_user(user))

        return users

    @database_sync_to_async
    def get_room_user(self):
        try:
            return RoomUser.objects.get(room=self.room, user=self.user)
        except ObjectDoesNotExist:
            return None

    @database_sync_to_async
    def update_room_user(self, room, user):
        RoomUser.objects.update_or_create(room=room, user=user, defaults={'last_read': now()})

    @database_sync_to_async
    def get_or_create_group_room(self, user_ids):
        user_ids.extend(list(self.room.users.all().values_list('pk', flat=True)))
        return Room.objects.get_or_create_from_users(user_ids)

    # Receive message from WebSocket
    async def receive_json(self, content):
        if self.user.is_authenticated:
            json_type = content.get('type', None)

            if json_type == 'leave_room':
                await self.remove_user_from_room(self.user.pk)
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

            elif json_type == 'room_members':
                await self.send_room_members()

            elif json_type == 'remove_member':
                user_ids = content.get('user_id', None)
                user = await self.get_user(user_ids)
                await self.remove_user_from_room(user_ids)
                dict_message = {'USER_LEFT': {'username': str(user), 'room': self.room.name, "timestamp": date(localtime(now()), settings.DATETIME_FORMAT)}}
                await ChatMessageHelper.send_message(self.room, json.dumps(dict_message))

            elif json_type == 'add_members':
                user_ids = content.get('user_ids', None)

                if user_ids is not None:
                    user_ids = list(map(int, user_ids))

                    if self.room.is_user_to_user_room:
                        new_room = await self.get_or_create_group_room(user_ids)

                        for group_name in self.groups:
                            await self.channel_layer.group_send(
                                group_name, {
                                    'type': 'new_room',
                                    'slug': new_room.slug,
                                }
                            )
                    else:
                        users = await self.add_room_users(user_ids)

                        for user in users:
                            dict_message = {'USER_JOINED': {'username': str(user.user)}}
                            await ChatMessageHelper.send_message(self.room, json.dumps(dict_message))

                        await self.send_room_members()

            else:
                text = content['message']

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

    async def send_room_members(self):
        users = await self.get_room_users()
        form_class = RoomAddMemberView.load_form_class()
        await self.send_json(content={
            'type': 'room_members',
            'form': str(form_class(room_pk=self.room.pk).as_p()),
            'members': [{
                'id': user.id,
                'name': str(user),
                'html': loader.get_template('whisper/member.html').render(
                    {'user': user, 'scope_user': self.user, 'is_user_to_user': self.room.is_user_to_user_room}
                )
            } for user in users],
        })

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send_json(content=event)

    # Receive user_typing from room group
    async def user_typing(self, event):
        # Send user_typing to WebSocket
        await self.send_json(content=event)

    # Receive room_properties from room group
    async def room_properties(self, event):
        # Send room_properties to WebSocket
        await self.send_json(content=event)

    # Receive new_room from room group
    async def new_room(self, event):
        # Send new_room to WebSocket
        await self.send_json(content=event)


class UnreadChatMessagesConsumer(AsyncJsonWebsocketConsumer):
    async def websocket_connect(self, message):
        self.user = self.scope['user']

        if self.user.is_authenticated:
            self.group_name = f'unread-chat-messages-{self.user.pk}'
            self.groups.append(self.group_name)

            await super().websocket_connect(message)

            unread_messages = await self.get_unread_messages(self.scope['user'])

            # init current socket
            await self.send_json(content=unread_messages)

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
        await self.send_json(content=unread_messages)
