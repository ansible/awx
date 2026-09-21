from django.conf import settings
from django.core.management.base import BaseCommand

from awx.main.tasks.system import clear_setting_cache


class Command(BaseCommand):
    help = 'Enable or disable indirect node counting.'

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--enable', action='store_true', help='Enable indirect node counting.')
        group.add_argument('--disable', action='store_true', help='Disable indirect node counting.')

    def handle(self, **options):
        enabled = options['enable']

        settings.INDIRECT_NODE_COUNTING_ENABLED = enabled
        clear_setting_cache.delay(['INDIRECT_NODE_COUNTING_ENABLED'])
        state = 'enabled' if enabled else 'disabled'
        self.stdout.write(f'Indirect node counting is {state}.')
