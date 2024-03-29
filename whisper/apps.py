import django_rq
from django.apps import AppConfig
from django.conf import settings
try:
    # older Django
    from django.utils.translation import ugettext_lazy as _
except ImportError:
    # Django >= 3
    from django.utils.translation import gettext_lazy as _

from whisper.cron import notify_about_unread_messages


class ChatConfig(AppConfig):
    name = 'whisper'
    verbose_name = _('Chat')

    def schedule_jobs(self):
        try:
            import django_rq
            scheduler = django_rq.get_scheduler('cron')

            # Cron task to check status of companies
            scheduler.cron(
                "*/5 * * * *",  # Run every 5 minutes
                func=notify_about_unread_messages,
                timeout=settings.RQ_QUEUES['cron']['DEFAULT_TIMEOUT']
            )
        except ImportError:
            # django RQ couldn't be imported, the email notifications won't work
            pass
        except KeyError:
            # 'cron' not found in RQ queues
            # TODO: create whistle setting for this
            pass
