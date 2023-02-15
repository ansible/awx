from django.core.management.base import BaseCommand
import datetime
from django.core.serializers.json import DjangoJSONEncoder
from awx.main.models.inventory import HostMetric, HostMetricSummaryMonthly
from awx.main.analytics.collectors import config
from awx.main.utils.encryption import get_encryption_key, Fernet256
from django.utils.encoding import smart_str, smart_bytes
import base64
import json
import sys
import tempfile
import tarfile
import pandas as pd

PREFERRED_ROW_COUNT = 500000


class Command(BaseCommand):
    help = 'This is for offline licensing usage'

    def host_metric_queryset(self, result, offset=0, limit=PREFERRED_ROW_COUNT):
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

    def host_metric_summary_monthly_queryset(self, result, offset=0, limit=PREFERRED_ROW_COUNT):
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

    def paginated_df(self, options, type, filter_kwargs, offset=0, limit=PREFERRED_ROW_COUNT):
        list_of_queryset = []
        if type == 'host_metric':
            result = HostMetric.objects.filter(**filter_kwargs)
            list_of_queryset = self.host_metric_queryset(result, offset, limit)
        elif type == 'host_metric_summary_monthly':
            result = HostMetricSummaryMonthly.objects.filter(**filter_kwargs)
            list_of_queryset = self.host_metric_summary_monthly_queryset(result, offset, limit)

        df = pd.DataFrame(list_of_queryset)

        if options['anonymized'] and 'hostname' in df.columns:
            key = get_encryption_key('hostname', options.get('anonymized'))
            df['hostname'] = df.apply(lambda x: self.obfuscated_hostname(key, x['hostname']), axis=1)

        return df

    def obfuscated_hostname(self, secret_sauce, hostname):
        return self.encrypt_name(secret_sauce, hostname)

    def whole_page_count(self, row_count, rows_per_file):
        whole_pages = int(row_count / rows_per_file)
        partial_page = row_count % rows_per_file
        if partial_page:
            whole_pages += 1
        return whole_pages

    def csv_for_tar(self, options, temp_dir, type, filter_kwargs, index=1, offset=0, rows_per_file=PREFERRED_ROW_COUNT):
        df = self.paginated_df(options, type, filter_kwargs, offset, rows_per_file)
        csv_file = f'{temp_dir}/{type}{index}.csv'
        arcname_file = f'{type}{index}.csv'
        df.to_csv(csv_file, index=False)
        return csv_file, arcname_file

    def config_for_tar(self, options, temp_dir):
        config_json = json.dumps(config(options.get('since')))
        config_file = f'{temp_dir}/config.json'
        arcname_file = 'config.json'
        with open(config_file, 'w') as f:
            f.write(config_json)
        return config_file, arcname_file

    def encrypt_name(self, key, value):
        value = smart_str(value)
        f = Fernet256(key)
        encrypted = f.encrypt(smart_bytes(value))
        b64data = smart_str(base64.b64encode(encrypted))
        tokens = ['$encrypted', 'UTF8', 'AESCBC', b64data]
        return '$'.join(tokens)

    def decrypt_name(self, encryption_key, value):
        raw_data = value[len('$encrypted$') :]
        # If the encrypted string contains a UTF8 marker, discard it
        utf8 = raw_data.startswith('UTF8$')
        if utf8:
            raw_data = raw_data[len('UTF8$') :]
        algo, b64data = raw_data.split('$', 1)
        if algo != 'AESCBC':
            raise ValueError('unsupported algorithm: %s' % algo)
        encrypted = base64.b64decode(b64data)
        f = Fernet256(encryption_key)
        value = f.decrypt(encrypted)
        return smart_str(value)

    def output_json(self, options, filter_kwargs):
        if not options.get('json') or options.get('json') == 'host_metric':
            result = HostMetric.objects.filter(**filter_kwargs)
            list_of_queryset = self.host_metric_queryset(result)
        elif options.get('json') == 'host_metric_summary_monthly':
            result = HostMetricSummaryMonthly.objects.filter(**filter_kwargs)
            list_of_queryset = self.host_metric_summary_monthly_queryset(result)

        json_result = json.dumps(list_of_queryset, cls=DjangoJSONEncoder)
        print(json_result)

    def output_csv(self, options, filter_kwargs):
        with tempfile.TemporaryDirectory() as temp_dir:
            if not options.get('csv') or options.get('csv') == 'host_metric':
                csv_file, _arcname_file = self.csv_for_tar(options, temp_dir, 'host_metric', filter_kwargs)
            elif options.get('csv') == 'host_metric_summary_monthly':
                csv_file, _arcname_file = self.csv_for_tar(options, temp_dir, 'host_metric_summary_monthly', filter_kwargs)
            with open(csv_file) as f:
                sys.stdout.write(f.read())

    def output_tarball(self, options, filter_kwargs, host_metric_row_count, host_metric_summary_monthly_row_count):
        tar = tarfile.open("./host_metrics.tar.gz", "w:gz")

        with tempfile.TemporaryDirectory() as temp_dir:
            if host_metric_row_count:
                csv_file, arcname_file = self.csv_for_tar(options, temp_dir, 'host_metric', filter_kwargs)
                tar.add(csv_file, arcname=arcname_file)

            if host_metric_summary_monthly_row_count:
                csv_file, arcname_file = self.csv_for_tar(options, temp_dir, 'host_metric_summary_monthly', filter_kwargs)
                tar.add(csv_file, arcname=arcname_file)

            config_file, arcname_file = self.config_for_tar(options, temp_dir)
            tar.add(config_file, arcname=arcname_file)

        tar.close()

    def output_rows_per_file(self, options, filter_kwargs, host_metric_row_count, host_metric_summary_monthly_row_count):
        rows_per_file = options.get('rows_per_file', PREFERRED_ROW_COUNT)
        tar = tarfile.open("./host_metrics.tar.gz", "w:gz")

        host_metric_whole_pages = self.whole_page_count(host_metric_row_count, rows_per_file)
        host_metric_summary_monthly_whole_pages = self.whole_page_count(host_metric_summary_monthly_row_count, rows_per_file)

        with tempfile.TemporaryDirectory() as temp_dir:
            for index in range(host_metric_whole_pages):
                offset = index * rows_per_file

                csv_file, arcname_file = self.csv_for_tar(options, temp_dir, 'host_metric', filter_kwargs, index + 1, offset, rows_per_file)
                tar.add(csv_file, arcname=arcname_file)

            for index in range(host_metric_summary_monthly_whole_pages):
                offset = index * rows_per_file

                csv_file, arcname_file = self.csv_for_tar(options, temp_dir, 'host_metric_summary_monthly', filter_kwargs, index + 1, offset, rows_per_file)
                tar.add(csv_file, arcname=arcname_file)

            config_file, arcname_file = self.config_for_tar(options, temp_dir)
            tar.add(config_file, arcname=arcname_file)

        tar.close()

    def add_arguments(self, parser):
        parser.add_argument('--since', type=datetime.datetime.fromisoformat, help='Start Date in ISO format YYYY-MM-DD')
        parser.add_argument('--until', type=datetime.datetime.fromisoformat, help='End Date in ISO format YYYY-MM-DD')
        parser.add_argument('--json', type=str, const='host_metric', nargs='?', help='Select output as JSON for host_metric or host_metric_summary_monthly')
        parser.add_argument('--csv', type=str, const='host_metric', nargs='?', help='Select output as CSV for host_metric or host_metric_summary_monthly')
        parser.add_argument('--tarball', action='store_true', help=f'Package CSV files into a tar with upto {PREFERRED_ROW_COUNT} rows')
        parser.add_argument('--anonymized', type=str, help='Anonymize hostnames with provided salt')
        parser.add_argument('--rows_per_file', type=int, help=f'Split rows in chunks of {PREFERRED_ROW_COUNT}')

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

        host_metric_row_count = HostMetric.objects.filter(**filter_kwargs).count()
        host_metric_summary_monthly_row_count = HostMetricSummaryMonthly.objects.filter(**filter_kwargs_host_metrics_summary).count()

        if (host_metric_row_count > PREFERRED_ROW_COUNT or host_metric_summary_monthly_row_count > PREFERRED_ROW_COUNT) and (
            not options.get('rows_per_file') or options.get('rows_per_file') > PREFERRED_ROW_COUNT
        ):
            print(
                f"HostMetric / HostMetricSummaryMonthly rows exceed the allowable limit of {PREFERRED_ROW_COUNT}. "
                f"Set --rows_per_file {PREFERRED_ROW_COUNT} "
                f"to split the rows in chunks of {PREFERRED_ROW_COUNT}"
            )
            return

        # if --json flag is set, output the result in json format
        if options['json']:
            self.output_json(options, filter_kwargs)
        elif options['csv']:
            self.output_csv(options, filter_kwargs)
        elif options['tarball']:
            self.output_tarball(options, filter_kwargs, host_metric_row_count, host_metric_summary_monthly_row_count)
        elif options['rows_per_file']:
            self.output_rows_per_file(options, filter_kwargs, host_metric_row_count, host_metric_summary_monthly_row_count)

        # --json flag is not set, output in plain text
        else:
            print(f"Total Number of hosts automated: {host_metric_row_count}")
            result = HostMetric.objects.filter(**filter_kwargs)
            for item in result:
                print(
                    "Hostname : {hostname} | first_automation : {first_automation} | last_automation : {last_automation}".format(
                        hostname=item.hostname, first_automation=item.first_automation, last_automation=item.last_automation
                    )
                )
        return
