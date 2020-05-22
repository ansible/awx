import time
import sys

from django.db import connection
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            start = {}
            for relation in (
                'main_jobevent', 'main_inventoryupdateevent',
                'main_projectupdateevent', 'main_adhoccommandevent'
            ):
                cursor.execute(f"SELECT MAX(id) FROM {relation};")
                start[relation] = cursor.fetchone()[0] or 0
            clear = False
            while True:
                lines = []
                for relation in (
                    'main_jobevent', 'main_inventoryupdateevent',
                    'main_projectupdateevent', 'main_adhoccommandevent'
                ):
                    lines.append(relation)
                    minimum = start[relation]
                    cursor.execute(
                        f"SELECT MAX(id) - MIN(id) FROM {relation} WHERE id > {minimum} AND modified > now() - '1 minute'::interval;"
                    )
                    events = cursor.fetchone()[0] or 0
                    lines.append(f'↳  last minute {events}')
                    lines.append('')
                if clear:
                    for i in range(12):
                        sys.stdout.write('\x1b[1A\x1b[2K')
                for line in lines:
                    print(line)
                clear = True
                time.sleep(.25)
