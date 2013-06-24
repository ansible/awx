import sys

from django.core.management.base import BaseCommand
from django.utils.log import getLogger


logger = getLogger('django.commands')


class LoggingBaseCommand(BaseCommand):
    """
    A subclass of BaseCommand that logs run time errors to `django.commands`.
    To use this, create a management command subclassing LoggingBaseCommand:

        from django_extensions.management.base import LoggingBaseCommand

        class Command(LoggingBaseCommand):
            help = 'Test error'

            def handle(self, *args, **options):
                raise Exception


    And then define a logging handler in settings.py:

        LOGGING = {
            ... # Other stuff here

            'handlers': {
                'mail_admins': {
                    'level': 'ERROR',
                    'filters': ['require_debug_false'],
                    'class': 'django.utils.log.AdminEmailHandler'
                },
            },
            'loggers': {
                'django.commands': {
                    'handlers': ['mail_admins'],
                    'level': 'ERROR',
                    'propagate': False,
                },
            }

        }

    """

    def execute(self, *args, **options):
        try:
            super(LoggingBaseCommand, self).execute(*args, **options)
        except Exception as e:
            logger.error(e, exc_info=sys.exc_info(), extra={'status_code': 500})
            raise
