# Copyright (c) 2017 Red Hat, Inc


from django.core.management.base import BaseCommand
from django.db.models import Count

from awx.network_ui.models import Device
from pprint import pprint


class Command(BaseCommand):

    def handle(self, *args, **options):
        dups = list(Device.objects
                    .values('topology_id', 'id')
                    .annotate(Count('pk'))
                    .order_by()
                    .filter(pk__count__gt=1))
        pprint(dups)
        for dup in dups:
            del dup['pk__count']
            pprint(list(Device.objects
                        .filter(**dup)
                        .values()))
