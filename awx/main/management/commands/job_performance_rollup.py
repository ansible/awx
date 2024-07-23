# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Django
from django.core.management.base import BaseCommand
from django.db import connection

import json
import re


class Command(BaseCommand):
    """
    Emits some simple statistics suitable for external monitoring
    """

    help = 'Run queries that provide an overview of the performance of the system over a given period of time'

    def add_arguments(self, parser):
        parser.add_argument('--since', action='store', dest='days', type=str, default="1", help='Max days to look back to for data')
        parser.add_argument('--limit', action='store', dest='limit', type=str, default="10", help='Max number of records for database queries (LIMIT)')

    def execute_query(self, query):
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()
        return rows

    def jsonify(self, title, keys, values, query):
        result = []
        query = re.sub('\n', ' ', query)
        query = re.sub('\s{2,}', ' ', query)
        for value in values:
            result.append(dict(zip(keys, value)))
        return {title: result, 'count': len(values), 'query': query}

    def jobs_pending_duration(self, days, limit):
        """Return list of jobs sorted by time in pending within configured number of days (within limit)"""
        query = f"""
            SELECT name, id AS job_id, unified_job_template_id, created, started - created AS pending_duration
            FROM main_unifiedjob 
            WHERE finished IS NOT null 
            AND started IS NOT null 
            AND cancel_flag IS NOT true 
            AND created > NOW() - INTERVAL '{days} days' 
            AND started - created > INTERVAL '0 seconds' 
            ORDER BY pending_duration DESC
            LIMIT {limit};"""
        values = self.execute_query(query)
        return self.jsonify(
            title='completed_or_started_jobs_by_pending_duration',
            keys=('job_name', 'job_id', 'unified_job_template_id', 'job_created', 'pending_duration'),
            values=values,
            query=query,
        )

    def times_of_day_pending_more_than_X_min(self, days, limit, minutes_pending):
        """Return list of jobs sorted by time in pending within configured number of days (within limit)"""
        query = f"""
            SELECT
                date_trunc('hour', created) as day_and_hour,
                COUNT(created) as count_jobs_pending_greater_than_{minutes_pending}_min
            FROM main_unifiedjob
            WHERE started IS NOT NULL
            AND started - created > INTERVAL '{minutes_pending} minutes'
            AND created > NOW() - INTERVAL '{days} days' 
            GROUP BY date_trunc('hour', created)
            ORDER BY count_jobs_pending_greater_than_{minutes_pending}_min DESC
            LIMIT {limit};"""
        values = self.execute_query(query)
        return self.jsonify(
            title=f'times_of_day_pending_more_than_{minutes_pending}',
            keys=('day_and_hour', f'count_jobs_pending_more_than_{minutes_pending}_min'),
            values=values,
            query=query,
        )

    def pending_jobs_details(self, days, limit):
        """Return list of jobs that are in pending and list details such as reasons they may be blocked, within configured number of days and limit."""
        query = f"""
            SELECT DISTINCT ON(A.id) A.name, A.id, A.unified_job_template_id, A.created, NOW() - A.created as pending_duration, F.allow_simultaneous, B.current_job_id as current_ujt_job, I.to_unifiedjob_id as dependency_job_id, A.dependencies_processed 
            FROM main_unifiedjob A
            LEFT JOIN (
                SELECT C.id, C.current_job_id FROM main_unifiedjobtemplate as C
                ) B
                ON A.unified_job_template_id = B.id
                LEFT JOIN main_job F ON A.id = F.unifiedjob_ptr_id
                LEFT JOIN (
                    SELECT * FROM main_unifiedjob_dependent_jobs as G
                    RIGHT JOIN main_unifiedjob H ON G.to_unifiedjob_id = H.id
                    ) I 
                ON A.id = I.from_unifiedjob_id
            WHERE A.status = 'pending'
            AND A.created > NOW() - INTERVAL '{days} days'
            ORDER BY id DESC
            LIMIT {limit};"""
        values = self.execute_query(query)
        return self.jsonify(
            title='pending_jobs_details',
            keys=(
                'job_name',
                'job_id',
                'unified_job_template_id',
                'job_created',
                'pending_duration',
                'allow_simultaneous',
                'current_ujt_job',
                'dependency_job_id',
                'dependencies_processed',
            ),
            values=values,
            query=query,
        )

    def jobs_by_FUNC_event_processing_time(self, func, days, limit):
        """Return list of jobs sorted by MAX job event procesing time within configured number of days (within limit)"""
        if func not in ('MAX', 'MIN', 'AVG', 'SUM'):
            raise RuntimeError('Only able to asses job events grouped by job with MAX, MIN, AVG, SUM functions')

        query = f"""SELECT job_id, {func}(A.modified - A.created) as job_event_processing_delay_{func}, B.name, B.created, B.finished, B.controller_node, B.execution_node
            FROM main_jobevent A
                RIGHT JOIN (
                SELECT id, created, name, finished, controller_node, execution_node FROM
                main_unifiedjob
                WHERE created > NOW() - INTERVAL '{days} days'
                AND created IS NOT null
                AND finished IS NOT null
                AND id IS NOT null
                AND name IS NOT null
                ) B
                ON A.job_id=B.id
            WHERE A.job_id is not null
            GROUP BY job_id, B.name, B.created, B.finished, B.controller_node, B.execution_node
            ORDER BY job_event_processing_delay_{func} DESC
            LIMIT {limit};"""
        values = self.execute_query(query)
        return self.jsonify(
            title=f'jobs_by_{func}_event_processing',
            keys=('job_id', f'{func}_job_event_processing_delay', 'job_name', 'job_created_time', 'job_finished_time', 'controller_node', 'execution_node'),
            values=values,
            query=query,
        )

    def handle(self, *args, **options):
        items = []
        for func in ('MAX', 'MIN', 'AVG'):
            items.append(self.jobs_by_FUNC_event_processing_time(func, options['days'], options['limit']))
        items.append(self.jobs_pending_duration(options['days'], options['limit']))
        items.append(self.pending_jobs_details(options['days'], options['limit']))
        items.append(self.times_of_day_pending_more_than_X_min(options['days'], options['limit'], minutes_pending=10))
        self.stdout.write(json.dumps(items, indent=4, sort_keys=True, default=str))
