import django_rq
from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from whisper.cron import notify_about_unread_messages


class ChatConfig(AppConfig):
    name = 'whisper'
    verbose_name = _('Chat')

    def ready(self):
        self.schedule_jobs()

    def schedule_jobs(self):
        print('Scheduling chat jobs...')
        scheduler = django_rq.get_scheduler('cron')

        # Cron task to check status of companies
        scheduler.cron(
            "*/5 * * * *",  # Run every 5 minutes
            func=notify_about_unread_messages,
            timeout=settings.RQ_QUEUES['cron']['DEFAULT_TIMEOUT']
        )
