from datetime import timedelta

from django.apps import apps
from django.db import transaction

from whisper import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import QuerySet, Count, Q, F
from django.template.defaultfilters import title
from django.utils.timezone import now


class RoomQuerySet(QuerySet):
    def create_from_slug(self, slug, creator=None):
        room_name, users = self.get_room_name_and_users_from_slug(slug)
        room = self.update_or_create(slug=slug, defaults={'name': room_name})[0]

        from whisper.models import RoomUser
        for user in users:
            RoomUser.objects.get_or_create(room=room, user=user, defaults={'last_read': now()})

        if creator:
            RoomUser.objects.get_or_create(room=room, user=creator, defaults={'last_read': now()})

        return room

    @transaction.atomic
    def create_group(self):
        room = self.create()
        room.slug = "group-" + str(room.pk)
        room.name = "Group #" + str(room.pk)
        room.save(update_fields=['slug', 'name'])
        return room

    def get_or_create_from_users(self, user_ids):
        users_room = self.filter(slug__startswith='group').annotate(cnt=Count('users')).filter(cnt=len(user_ids))

        for user_id in user_ids:
            users_room = users_room.filter(users__pk=user_id)

        if users_room:
            return users_room.latest()
        else:
            new_room = self.create_group()

            from whisper.models import RoomUser
            for user_id in user_ids:
                RoomUser.objects.get_or_create(room=new_room, user_id=user_id, defaults={'last_read': now()})

            return new_room

    @staticmethod
    def get_room_name_and_users_from_slug(slug):
        slug_parts = slug.split('-', 1)
        subject = slug_parts[0]
        users = get_user_model().objects.none()

        if subject == 'users':
            user_pks = slug_parts[1].split('-')
            users = get_user_model().objects.filter(pk__in=user_pks)
            room_name = ' & '.join(list(map(str, users)))
        else:
            subject_pk = slug_parts[1]
            obj_name = f'#{subject_pk}'

            for model in apps.get_models():
                if subject == model.__name__.lower():
                    model_name = model._meta.verbose_name
                    obj = model.objects.get(pk=subject_pk)
                    users = obj.room_members
                    obj_name = str(obj)

            room_name = title(f'{model_name} {obj_name}')

        return room_name, users

    def rename_by_slug(self, slug, new_name, default_name=None):
        try:
            room = self.get(slug=slug)

            if room.name == default_name or default_name is None:
                room.name = new_name
                room.save(update_fields=['name'])

        except ObjectDoesNotExist:
            pass

    def of_user(self, user):
        if not user.is_authenticated:
            return self.none()

        return user.room_set.all()

    def count_unread_messages(self, user):
        if not user.is_authenticated:
            return self.none()

        return self.annotate(
            unread_messages=
                Count('message__pk',
                filter=Q(
                    Q(message__room__member__user=user, message__created__gt=F('message__room__member__last_read')),
                    ~Q(message__user=user),
                    ~Q(message__user=None),
                )
            )
        )

    def empty(self):
        return self.model.objects.filter(message__isnull=True)

    def not_empty(self):
        return self.model.objects.exclude(message__isnull=True)

    def with_unread_messages(self, user):
        if not user.is_authenticated:
            return self.none()

        return self.of_user(user).count_unread_messages(user).filter(unread_messages__gte=1)

    def recent(self, user):
        if not user.is_authenticated:
            return self.none()

        return self.of_user(user).count_unread_messages(user).filter(
            Q(unread_messages__gte=1) |
            Q(modified__gte=now() - timedelta(days=settings.RECENT_ROOM_THRESHOLD))
        )

    def unread_and_not_notified(self, user):
        """
        - unread: [member.last_read < last message created]       # notify only about unread messages
        - unsent: [member.last_notified < room modified]          # do not notify about same messages
        - dont spam: [member.last_notified < now() - threshold]   # do not spam
        - ready to send: [member.last_read < now() - threshold]   # give user enough time to read message in app
        - user inactive (user.last_seen < now() - threshold]      # send notification if user is not active

        :return: Unread messages which haven't been sent by email yet in defined time threshold
        """
        if not user.is_authenticated:
            return self.none()

        threshold_date = now() - timedelta(minutes=settings.NOTIFY_ROOM_THRESHOLD)

        query = Q(
                member__user=user,
                member__last_notified__lt=threshold_date
            ) & \
            Q(
                member__user=user,
                member__last_read__lt=threshold_date
            ) & \
            Q(
                member__user=user,
                member__last_notified__lt=F('modified')
            )

        user_activity_attribute = settings.USER_ACTIVITY_ATTRIBUTE

        if user_activity_attribute:
            query &= Q(**{f'member__user__{user_activity_attribute}__lt': threshold_date})

        return self.with_unread_messages(user).filter(query)


class MessageQuerySet(QuerySet):
    def of_room(self, room):
        return self.filter(room=room)

    def unread_by_user(self, user):
        if not user.is_authenticated:
            return self.none()

        return self \
            .exclude(Q(user=user) | Q(user=None)) \
            .filter(
                room__member__user=user,
                created__gt=F('room__member__last_read')
            )
