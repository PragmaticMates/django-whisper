from django import template
from django.contrib.auth import get_user_model

register = template.Library()


@register.simple_tag(takes_context=True)
def room_slug(context, subject):
    request = context['request']

    if isinstance(subject, get_user_model()):
        if not request.user.is_authenticated:
            return None

        users_pks = [subject.pk, request.user.pk]
        users_pks = sorted(users_pks)
        users_pks = list(map(str, users_pks))
        return 'users-{}'.format('-'.join(users_pks))

    model_name = subject.__class__.__name__.lower()
    return f'{model_name}-{subject.pk}'
