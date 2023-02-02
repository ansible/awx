from django.core.management.base import BaseCommand
import datetime
from django.core.serializers.json import DjangoJSONEncoder
from awx.main.models.inventory import HostMetric
import json


class Command(BaseCommand):
    help = 'This is for offline licensing usage'

    def add_arguments(self, parser):
        parser.add_argument('--since', type=datetime.datetime.fromisoformat, help='Start Date in ISO format YYYY-MM-DD')
        parser.add_argument('--until', type=datetime.datetime.fromisoformat, help='End Date in ISO format YYYY-MM-DD')
        parser.add_argument('--json', action='store_true', help='Select output as JSON')

    def handle(self, *args, **options):
        since = options.get('since')
        until = options.get('until')

        if since is None and until is None:
            print("No Arguments received")
            return None

        if since is not None and since.tzinfo is None:
            since = since.replace(tzinfo=datetime.timezone.utc)

        if until is not None and until.tzinfo is None:
            until = until.replace(tzinfo=datetime.timezone.utc)

        filter_kwargs = {}
        if since is not None:
            filter_kwargs['last_automation__gte'] = since
        if until is not None:
            filter_kwargs['last_automation__lte'] = until

        result = HostMetric.objects.filter(**filter_kwargs)

        # if --json flag is set, output the result in json format
        if options['json']:
            list_of_queryset = list(result.values('hostname', 'first_automation', 'last_automation'))
            json_result = json.dumps(list_of_queryset, cls=DjangoJSONEncoder)
            print(json_result)

        # --json flag is not set, output in plain text
        else:
            print(f"Total Number of hosts automated: {len(result)}")
            for item in result:
                print(
                    "Hostname : {hostname} | first_automation : {first_automation} | last_automation : {last_automation}".format(
                        hostname=item.hostname, first_automation=item.first_automation, last_automation=item.last_automation
                    )
                )
        return
