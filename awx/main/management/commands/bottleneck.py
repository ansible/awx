from django.core.management.base import BaseCommand
from django.db import connection

from awx.main.models import JobTemplate


class Command(BaseCommand):
    help = "Find the slowest tasks and hosts for a Job Template's most recent runs."

    def add_arguments(self, parser):
        parser.add_argument('--template', dest='jt', type=int,
                            help='ID of the Job Template to profile')
        parser.add_argument('--threshold', dest='threshold', type=float, default=30,
                            help='Only show tasks that took at least this many seconds (defaults to 30)')
        parser.add_argument('--history', dest='history', type=float, default=25,
                            help='The number of historic jobs to look at')
        parser.add_argument('--ignore', action='append', help='ignore a specific action (e.g., --ignore git)')

    def handle(self, *args, **options):
        jt = options['jt']
        threshold = options['threshold']
        history = options['history']
        ignore = options['ignore']

        print('## ' + JobTemplate.objects.get(pk=jt).name + f' (last {history} runs)\n')
        with connection.cursor() as cursor:
            cursor.execute(
                f'''
                SELECT 
                    b.id, b.job_id, b.host_name, b.created - a.created delta,
                    b.task task,
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
                        LIMIT {history}
                    )
                ORDER BY delta DESC;
                '''
            )
            slowest_events = cursor.fetchall()

        def format_td(x):
            return str(x).split('.')[0]

        fastest = dict()
        for event in slowest_events:
            _id, job_id, host, duration, task, action, playbook = event
            playbook = playbook.rsplit('/')[-1]
            if ignore and action in ignore:
                continue
            if host:
                fastest[(action, playbook)] = (_id, host, format_td(duration))

        host_counts = dict()
        warned = set()
        print(f'slowest tasks (--threshold={threshold})\n---')

        for event in slowest_events:
            _id, job_id, host, duration, task, action, playbook = event
            if ignore and action in ignore:
                continue
            if duration.total_seconds() < threshold:
                break
            playbook = playbook.rsplit('/')[-1]
            human_duration = format_td(duration)

            fastest_summary = ''
            fastest_match = fastest.get((action, playbook))
            if fastest_match[2] != human_duration and (host, action, playbook) not in warned:
                warned.add((host, action, playbook))
                fastest_summary = ' ' + self.style.WARNING(f'{fastest_match[1]} ran this in {fastest_match[2]}s at /api/v2/job_events/{fastest_match[0]}/')

            url = f'/api/v2/jobs/{job_id}/'
            print(' -- '.join([url, host, human_duration, action, task, playbook]) + fastest_summary)
            host_counts.setdefault(host, [])
            host_counts[host].append(duration)

        host_counts = sorted(host_counts.items(), key=lambda item: [e.total_seconds() for e in item[1]], reverse=True)

        print('\nslowest hosts\n---')
        for h, matches in host_counts:
            total = len(matches)
            total_seconds = sum([e.total_seconds() for e in matches])
            print(f'{h} had {total} tasks that ran longer than {threshold} second(s) for a total of {total_seconds}')

        print('')
