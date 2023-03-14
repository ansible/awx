from django.core.management.base import BaseCommand
import datetime
from django.core.serializers.json import DjangoJSONEncoder
from awx.main.models.inventory import HostMetric, HostMetricSummaryMonthly
from awx.main.analytics.collectors import config
import json
import sys
import tempfile
import tarfile
import csv

CSV_PREFERRED_ROW_COUNT = 500000
BATCHED_FETCH_COUNT = 10000


class Command(BaseCommand):
    help = 'This is for offline licensing usage'

    def host_metric_queryset(self, result, offset=0, limit=BATCHED_FETCH_COUNT):
        list_of_queryset = list(
            result.values(
                'id',
                'hostname',
                'first_automation',
                'last_automation',
                'last_deleted',
                'automated_counter',
                'deleted_counter',
                'deleted',
                'used_in_inventories',
            ).order_by('first_automation')[offset : offset + limit]
        )

        return list_of_queryset

    def host_metric_summary_monthly_queryset(self, result, offset=0, limit=BATCHED_FETCH_COUNT):
        list_of_queryset = list(
            result.values(
                'id',
                'date',
                'license_consumed',
                'license_capacity',
                'hosts_added',
                'hosts_deleted',
                'indirectly_managed_hosts',
            ).order_by(
                'date'
            )[offset : offset + limit]
        )

        return list_of_queryset

    def paginated_db_retrieval(self, type, filter_kwargs, rows_per_file):
        offset = 0
        list_of_queryset = []
        while True:
            if type == 'host_metric':
                result = HostMetric.objects.filter(**filter_kwargs)
                list_of_queryset = self.host_metric_queryset(result, offset, rows_per_file)
            elif type == 'host_metric_summary_monthly':
                result = HostMetricSummaryMonthly.objects.filter(**filter_kwargs)
                list_of_queryset = self.host_metric_summary_monthly_queryset(result, offset, rows_per_file)

            if not list_of_queryset:
                break
            else:
                yield list_of_queryset

            offset += len(list_of_queryset)

    def controlled_db_retrieval(self, type, filter_kwargs, offset=0, fetch_count=BATCHED_FETCH_COUNT):
        if type == 'host_metric':
            result = HostMetric.objects.filter(**filter_kwargs)
            return self.host_metric_queryset(result, offset, fetch_count)
        elif type == 'host_metric_summary_monthly':
            result = HostMetricSummaryMonthly.objects.filter(**filter_kwargs)
            return self.host_metric_summary_monthly_queryset(result, offset, fetch_count)

    def write_to_csv(self, csv_file, list_of_queryset, always_header, first_write=False, mode='a'):
        with open(csv_file, mode, newline='') as output_file:
            try:
                keys = list_of_queryset[0].keys() if list_of_queryset else []
                dict_writer = csv.DictWriter(output_file, keys)
                if always_header or first_write:
                    dict_writer.writeheader()
                dict_writer.writerows(list_of_queryset)

            except Exception as e:
                print(e)

    def csv_for_tar(self, temp_dir, type, filter_kwargs, rows_per_file, always_header=True):
        for index, list_of_queryset in enumerate(self.paginated_db_retrieval(type, filter_kwargs, rows_per_file)):
            csv_file = f'{temp_dir}/{type}{index+1}.csv'
            arcname_file = f'{type}{index+1}.csv'

            first_write = True if index == 0 else False

            self.write_to_csv(csv_file, list_of_queryset, always_header, first_write, 'w')
            yield csv_file, arcname_file

    def csv_for_tar_batched_fetch(self, temp_dir, type, filter_kwargs, rows_per_file, always_header=True):
        csv_iteration = 1

        offset = 0
        rows_written_per_csv = 0
        to_fetch = BATCHED_FETCH_COUNT

        while True:
            list_of_queryset = self.controlled_db_retrieval(type, filter_kwargs, offset, to_fetch)

            if not list_of_queryset:
                break

            csv_file = f'{temp_dir}/{type}{csv_iteration}.csv'
            arcname_file = f'{type}{csv_iteration}.csv'
            self.write_to_csv(csv_file, list_of_queryset, always_header)

            offset += to_fetch
            rows_written_per_csv += to_fetch
            always_header = False

            remaining_rows_per_csv = rows_per_file - rows_written_per_csv

            if not remaining_rows_per_csv:
                yield csv_file, arcname_file

                rows_written_per_csv = 0
                always_header = True
                to_fetch = BATCHED_FETCH_COUNT
                csv_iteration += 1
            elif remaining_rows_per_csv < BATCHED_FETCH_COUNT:
                to_fetch = remaining_rows_per_csv

        if rows_written_per_csv:
            yield csv_file, arcname_file

    def config_for_tar(self, options, temp_dir):
        config_json = json.dumps(config(options.get('since')))
        config_file = f'{temp_dir}/config.json'
        arcname_file = 'config.json'
        with open(config_file, 'w') as f:
            f.write(config_json)
        return config_file, arcname_file

    def output_json(self, options, filter_kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            for csv_detail in self.csv_for_tar(temp_dir, options.get('json', 'host_metric'), filter_kwargs, BATCHED_FETCH_COUNT, True):
                csv_file = csv_detail[0]

                with open(csv_file) as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    json_result = json.dumps(rows, cls=DjangoJSONEncoder)
                    print(json_result)

    def output_csv(self, options, filter_kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            for csv_detail in self.csv_for_tar(temp_dir, options.get('csv', 'host_metric'), filter_kwargs, BATCHED_FETCH_COUNT, False):
                csv_file = csv_detail[0]
                with open(csv_file) as f:
                    sys.stdout.write(f.read())

    def output_tarball(self, options, filter_kwargs):
        always_header = True
        rows_per_file = options['rows_per_file'] or CSV_PREFERRED_ROW_COUNT

        tar = tarfile.open("./host_metrics.tar.gz", "w:gz")

        if rows_per_file <= BATCHED_FETCH_COUNT:
            csv_function = self.csv_for_tar
        else:
            csv_function = self.csv_for_tar_batched_fetch

        with tempfile.TemporaryDirectory() as temp_dir:
            for csv_detail in csv_function(temp_dir, 'host_metric', filter_kwargs, rows_per_file, always_header):
                tar.add(csv_detail[0], arcname=csv_detail[1])

            for csv_detail in csv_function(temp_dir, 'host_metric_summary_monthly', filter_kwargs, rows_per_file, always_header):
                tar.add(csv_detail[0], arcname=csv_detail[1])

            config_file, arcname_file = self.config_for_tar(options, temp_dir)
            tar.add(config_file, arcname=arcname_file)

        tar.close()

    def add_arguments(self, parser):
        parser.add_argument('--since', type=datetime.datetime.fromisoformat, help='Start Date in ISO format YYYY-MM-DD')
        parser.add_argument('--until', type=datetime.datetime.fromisoformat, help='End Date in ISO format YYYY-MM-DD')
        parser.add_argument('--json', type=str, const='host_metric', nargs='?', help='Select output as JSON for host_metric or host_metric_summary_monthly')
        parser.add_argument('--csv', type=str, const='host_metric', nargs='?', help='Select output as CSV for host_metric or host_metric_summary_monthly')
        parser.add_argument('--tarball', action='store_true', help=f'Package CSV files into a tar with upto {CSV_PREFERRED_ROW_COUNT} rows')
        parser.add_argument('--rows_per_file', type=int, help=f'Split rows in chunks of {CSV_PREFERRED_ROW_COUNT}')

    def handle(self, *args, **options):
        since = options.get('since')
        until = options.get('until')

        if since is not None and since.tzinfo is None:
            since = since.replace(tzinfo=datetime.timezone.utc)

        if until is not None and until.tzinfo is None:
            until = until.replace(tzinfo=datetime.timezone.utc)

        filter_kwargs = {}
        if since is not None:
            filter_kwargs['last_automation__gte'] = since
        if until is not None:
            filter_kwargs['last_automation__lte'] = until

        filter_kwargs_host_metrics_summary = {}
        if since is not None:
            filter_kwargs_host_metrics_summary['date__gte'] = since
        if until is not None:
            filter_kwargs_host_metrics_summary['date__lte'] = until

        if options['rows_per_file'] and options.get('rows_per_file') > CSV_PREFERRED_ROW_COUNT:
            print(f"rows_per_file exceeds the allowable limit of {CSV_PREFERRED_ROW_COUNT}.")
            return

        # if --json flag is set, output the result in json format
        if options['json']:
            self.output_json(options, filter_kwargs)
        elif options['csv']:
            self.output_csv(options, filter_kwargs)
        elif options['tarball']:
            self.output_tarball(options, filter_kwargs)

        # --json flag is not set, output in plain text
        else:
            print(f"Printing up to {BATCHED_FETCH_COUNT } automated hosts:")
            result = HostMetric.objects.filter(**filter_kwargs)
            list_of_queryset = self.host_metric_queryset(result, 0, BATCHED_FETCH_COUNT)
            for item in list_of_queryset:
                print(
                    "Hostname : {hostname} | first_automation : {first_automation} | last_automation : {last_automation}".format(
                        hostname=item['hostname'], first_automation=item['first_automation'], last_automation=item['last_automation']
                    )
                )
        return
