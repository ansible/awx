import time
import sys

from django.db import connection
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            clear = False
            while True:
                lines = []
                for relation in (
                    'main_jobevent', 'main_inventoryupdateevent',
                    'main_projectupdateevent', 'main_adhoccommandevent'
                ):
                    lines.append(relation)
                    for label, interval in (
                        ('last minute:   ', '1 minute'),
                        ('last 5 minutes:', '5 minutes'),
                        ('last hour:     ', '1 hour'),
                    ):
                        cursor.execute(
                            f"SELECT MAX(id) - MIN(id) FROM {relation} WHERE modified > now() - '{interval}'::interval;"
                        )
                        events = cursor.fetchone()[0] or 0
                        lines.append(f'↳  {label} {events}')
                    lines.append('')
                if clear:
                    for i in range(20):
                        sys.stdout.write('\x1b[1A\x1b[2K')
                for l in lines:
                    print(l)
                clear = True
                time.sleep(.25)
