from django.core.management.base import BaseCommand
from django.db import connection

from awx.main.models import JobTemplate


class Command(BaseCommand):
    help = 'Discover the slowest tasks and hosts for a specific Job Template.'

    def add_arguments(self, parser):
        parser.add_argument('--template', dest='jt', type=int,
                            help='ID of the Job Template to profile')
        parser.add_argument('--threshold', dest='threshold', type=float, default=5,
                            help='Only show tasks that took at least this many seconds (defaults to 5)')
        parser.add_argument('--ignore', action='append', help='ignore a specific action (e.g., --ignore git)')

    def handle(self, *args, **options):
        jt = options['jt']
        threshold = options['threshold']
        ignore = options['ignore']

        print('## ' + JobTemplate.objects.get(pk=jt).name + ' (last 25 runs)\n')
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                SELECT 
                    b.id, b.job_id, b.host_name, b.created - a.created delta,
                    b.event_data::json->'task_action' task_action,
                    b.event_data::json->'task_path' task_path
                FROM main_jobevent a JOIN main_jobevent b
                ON b.parent_uuid = a.parent_uuid  AND a.host_name = b.host_name
                WHERE
                    a.event = 'runner_on_start' AND
                    b.event != 'runner_on_start' AND
                    b.event != 'runner_on_skipped' AND
                    b.failed = false AND
                    a.job_id IN (
                        SELECT unifiedjob_ptr_id FROM main_job
                        WHERE job_template_id={jt}
                        ORDER BY unifiedjob_ptr_id DESC
                        LIMIT 25
                    )
                ORDER BY delta DESC;
                '''
            )
            slowest_events = cursor.fetchall()

        fastest = dict()
        for event in slowest_events:
            _id, job_id, host, duration, action, playbook = event
            playbook = playbook.rsplit('/')[-1]
            if ignore and action in ignore:
                continue
            if host:
                fastest[(action, playbook)] = (_id, host, str(duration).split('.')[0])

        host_counts = dict()
        warned = set()
        print(f'slowest tasks (--threshold={threshold})\n---')
        for event in slowest_events:
            _id, job_id, host, duration, action, playbook = event
            playbook = playbook.rsplit('/')[-1]
            if ignore and action in ignore:
                continue
            if duration.total_seconds() < threshold:
                break

            fastest_summary = ''
            fastest_match = fastest.get((action, playbook))
            if fastest_match[2] != duration.total_seconds() and (host, action, playbook) not in warned:
                warned.add((host, action, playbook))
                fastest_summary = f'  \033[93m{fastest_match[1]} ran this in {fastest_match[2]}s at /api/v2/job_events/{fastest_match[0]}/\033[0m'

            url = f'/api/v2/jobs/{job_id}/'
            human_duration = str(duration).split('.')[0]
            print(' -- '.join([url, host, human_duration, action, playbook]) + fastest_summary)
            host_counts.setdefault(host, [])
            host_counts[host].append(duration)

        host_counts = sorted(host_counts.items(), key=lambda item: [e.total_seconds() for e in item[1]], reverse=True)

        print('\nslowest hosts\n---')
        for h, matches in host_counts:
            total = len(matches)
            total_seconds = sum([e.total_seconds() for e in matches])
            print(f'{h} had {total} tasks that ran longer than {threshold} second(s) for a total of {total_seconds}')

        print('')
