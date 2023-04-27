from django.core.management.base import BaseCommand

from awx.main.dispatch import pg_bus_conn
from awx.main.dispatch.queues import get_all_queues


class Command(BaseCommand):
    help = 'Listen to pg_notify messages'

    def handle(self, *args, **options):
        queues = get_all_queues()

        with pg_bus_conn(new_connection=True) as conn:
            for queue in queues:
                conn.listen(queue)

            for e in conn.events(yield_timeouts=False):
                print('')
                print(e.channel)
                print(e.pid)
                print(e.payload)
