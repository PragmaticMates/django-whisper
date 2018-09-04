from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template import loader, TemplateDoesNotExist
from django.utils import translation
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _


def notify_about_unread_messages():
    """
    - iterate every user and check their rooms with unread and not notified messages
    """
    from whisper.models import Room, RoomUser

    notified_users = 0

    # TODO: not logged/away in only?
    for user in get_user_model().objects.all():
        unread_and_not_notified_rooms = Room.objects.unread_and_not_notified(user)

        if not unread_and_not_notified_rooms.exists():
            continue

        notify(user, unread_and_not_notified_rooms)
        notified_users += 1

        for room in unread_and_not_notified_rooms:
            member = RoomUser.objects.get(room=room, user=user)
            member.last_notified = now()
            member.save(update_fields=['last_notified'])

    return notified_users


def notify(user, rooms):
    """
    Send email notification about unread messages to room member
    """

    # activate language
    language = settings.LANGUAGE_CODE  # TODO: pick from user profile
    translation.activate(language)

    # add unread messages to room object
    for room in rooms:
        room.unread_messages = room.message_set.unread_by_user(user)

    # templates
    t = loader.get_template('whisper/mails/notification.txt')

    try:
        t_html = loader.get_template('whisper/mails/notification.html')
    except TemplateDoesNotExist:
        t_html = None

    # recipients
    recipient = user
    recipient_list = [recipient.email]

    # description
    description = _('You have unread chat messages')

    # subject
    site = get_current_site(None)

    subject = '[{}] {}'.format(
        site.name,
        description
    )

    # context
    context = {
        'subject': subject,
        'description': description,
        'recipient': recipient,
        'rooms': rooms,
    }

    # message
    message = t.render(context)
    html_message = t_html.render(context) if t_html else None

    # mail arguments
    from_email = settings.DEFAULT_FROM_EMAIL
    fail_silently = True

    send_mail(subject, message, from_email, recipient_list, html_message=html_message, fail_silently=fail_silently)
