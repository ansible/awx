# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
import re
from dateutil.relativedelta import relativedelta
from datetime import datetime
from optparse import make_option

# Django
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

# AWX
from awx.fact.models.fact import * # noqa

OLDER_THAN = 'older_than'
GRANULARITY = 'granularity'

class CleanupFacts(object):
    def __init__(self):
        self.timestamp = None

    # Find all with timestamp < older_than
    # Start search at < older_than, stop search at oldest entry
    #   Find all factVersion < pivot && > (pivot - granularity) grouped by host sorted by time descending (because it's indexed this way)
    #   foreach group
    #       Delete all except LAST entry (or Delete all except the FIRST entry, it's an arbitrary decision)
    #   
    #   pivot -= granularity
    # group by host 
    def cleanup(self, older_than_abs, granularity):
        fact_oldest = FactVersion.objects.all().order_by('timestamp').first()
        if not fact_oldest:
            return 0

        total = 0
        date_pivot = older_than_abs
        while date_pivot > fact_oldest.timestamp:
            date_pivot_next = date_pivot - granularity
            kv = {
                'timestamp__lte': date_pivot,
                'timestamp__gt': date_pivot_next,
            }
            version_objs = FactVersion.objects.filter(**kv).order_by('-timestamp')

            # Transform array -> {host_id} = [<fact_version>, <fact_version>, ...]
            # TODO: If this set gets large then we can use mongo to transform the data set for us.
            host_ids = {}
            for obj in version_objs:
                k = obj.host.id
                if k not in host_ids:
                    host_ids[k] = []
                host_ids[k].append(obj)

            for k in host_ids:
                ids = [fact.id for fact in host_ids[k]]
                fact_ids = [fact.fact.id for fact in host_ids[k]]
                # Remove 1 entry
                ids.pop()
                fact_ids.pop()
                # delete the rest
                count = FactVersion.objects.filter(id__in=ids).delete()
                # FIXME: if this crashes here then we are inconsistent
                count = Fact.objects.filter(id__in=fact_ids).delete()
                total += count

            date_pivot = date_pivot_next
        return total

    '''
    older_than and granularity are of type relativedelta
    '''
    def run(self, older_than, granularity):
        t = datetime.now()
        deleted_count = self.cleanup(t - older_than, granularity)
        print("Deleted %d facts." % deleted_count)

class Command(BaseCommand):
    help = 'Cleanup facts. For each host older than the value specified, keep one fact scan for each time window (granularity).'
    option_list = BaseCommand.option_list + (
        make_option('--older_than',
                    dest='older_than',
                    default=None,
                    help='Specify the relative time to consider facts older than (w)eek (d)ay or (y)ear (i.e. 5d, 2w, 1y).'),
        make_option('--granularity',
                    dest='granularity',
                    default=None,
                    help='Window duration to group same hosts by for deletion (w)eek (d)ay or (y)ear (i.e. 5d, 2w, 1y).'),)

    def __init__(self):
        super(Command, self).__init__()

    def string_time_to_timestamp(self, time_string):
        units = {
            'y': 'years',
            'd': 'days', 
            'w': 'weeks',
            'm': 'months'
        }
        try:
            match = re.match(r'(?P<value>[0-9]+)(?P<unit>.*)', time_string)
            group = match.groupdict()
            kv = {}
            units_verbose = units[group['unit']]
            kv[units_verbose]= int(group['value'])
            return relativedelta(**kv)
        except (KeyError, TypeError, AttributeError):
            return None

    @transaction.atomic
    def handle(self, *args, **options):
        cleanup_facts = CleanupFacts()
        if not all([options[GRANULARITY], options[OLDER_THAN]]):
            raise CommandError('Both --granularity and --older_than are required.')

        older_than = self.string_time_to_timestamp(options[OLDER_THAN])
        granularity = self.string_time_to_timestamp(options[GRANULARITY])

        if older_than is None:
            raise CommandError('--older_than invalid value "%s"' % options[OLDER_THAN])
        if granularity is None:
            raise CommandError('--granularity invalid value "%s"' % options[GRANULARITY])

        cleanup_facts.run(older_than, granularity)

