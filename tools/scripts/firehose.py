#! /usr/bin/env awx-python

#
# !!! READ BEFORE POINTING THIS AT YOUR FOOT !!!
#
# This script attempts to connect to an AWX database and insert (by default)
# a billion main_jobevent rows as screamingly fast as possible.
#
# tl;dr for best results, feed it high IOPS.
#
# this script exists *solely* for the purpose of generating *test* data very
# quickly; do *not* point this at a production installation or you *will* be
# very unhappy
#
# Before running this script, you should give postgres *GOBS* of memory
# and disk so it can create indexes and constraints as quickly as possible.
# In fact, it's probably not smart to attempt this on anything less than 8 core,
# 32GB of RAM, and tens of thousands of IOPS.
#
# Also, a billion events is a *lot* of data; make sure you've
# provisioned *at least* 750GB of disk space
#
# if you want this script to complete in a few hours, a good starting point
# is something like m5.4xlarge w/ 1TB provisioned IOPS SSD (io1)
#

import argparse
import datetime
import itertools
import json
import multiprocessing
import pkg_resources
import random
import subprocess
import sys
from io import StringIO
from time import time
from uuid import uuid4

import psycopg2

from django import setup as setup_django
from django.db import connection
from django.db.models.sql import InsertQuery
from django.utils.timezone import now

db = json.loads(
    subprocess.check_output(
        ['awx-manage', 'print_settings', 'DATABASES', '--format', 'json']
    )
)
name = db['DATABASES']['default']['NAME']
user = db['DATABASES']['default']['USER']
pw = db['DATABASES']['default']['PASSWORD']
host = db['DATABASES']['default']['HOST']

dsn = f'dbname={name} user={user} password={pw} host={host}'

u = str(uuid4())

STATUS_OPTIONS = ('successful', 'failed', 'error', 'canceled')

EVENT_OPTIONS = ('runner_on_ok', 'runner_on_failed', 'runner_on_changed', 'runner_on_skipped', 'runner_on_unreachable')

MODULE_OPTIONS = ('yup', 'stonchronize', 'templotz', 'deboog')


class YieldedRows(StringIO):

    def __init__(self, job_id, rows, created_stamp, modified_stamp, *args, **kwargs):
        self.rows = rows
        self.rowlist = []
        for (event, module) in itertools.product(EVENT_OPTIONS, MODULE_OPTIONS):
            event_data_json = {
                "task_action": module,
                "name": "Do a {} thing".format(module),
                "task": "Do a {} thing".format(module)
            }
            row = "\t".join([
                f"{created_stamp}",
                f"{modified_stamp}",
                event,
                json.dumps(event_data_json),
                str(event in ('runner_on_failed', 'runner_on_unreachable')),
                str(event == 'runner_on_changed'),
                "localhost",
                "Example Play",
                "Hello World",
                "",
                "0",
                "1",
                job_id,
                u,
                "",
                "1",
                "hello_world.yml",
                "0",
                "X",
                "1",
            ]) + '\n'
            self.rowlist.append(row)

    def read(self, x):
        if self.rows <= 0:
            self.close()
            return ''
        self.rows -= 1000
        return self.rowlist[random.randrange(len(self.rowlist))] * 1000


def firehose(job, count, created_stamp, modified_stamp):
    conn = psycopg2.connect(dsn)
    f = YieldedRows(job, count, created_stamp, modified_stamp)
    with conn.cursor() as cursor:
        cursor.copy_expert((
            'COPY '
            'main_jobevent('
            'created, modified, event, event_data, failed, changed, '
            'host_name, play, role, task, counter, host_id, job_id, uuid, '
            'parent_uuid, end_line, playbook, start_line, stdout, verbosity'
            ') '
            'FROM STDIN'
        ), f, size=1024 * 1000)
    conn.commit()
    conn.close()


def cleanup(sql):
    print(sql)
    conn = psycopg2.connect(dsn)
    with conn.cursor() as cursor:
        cursor.execute(sql)
    conn.commit()
    conn.close()


def generate_jobs(jobs, batch_size, time_delta):
    print(f'inserting {jobs} job(s)')
    sys.path.insert(0, pkg_resources.get_distribution('awx').module_path)
    from awx import prepare_env
    prepare_env()
    setup_django()

    from awx.main.models import UnifiedJob, Job, JobTemplate
    fields = list(set(Job._meta.fields) - set(UnifiedJob._meta.fields))
    job_field_names = set([f.attname for f in fields])
    # extra unified job field names from base class
    for field_name in ('name', 'created_by_id', 'modified_by_id'):
        job_field_names.add(field_name)
    jt_count = JobTemplate.objects.count()

    def make_batch(N, jt_pos=0):
        jt = None
        while not jt:
            try:
                jt = JobTemplate.objects.all()[jt_pos % jt_count]
            except IndexError as e:
                # seems to happen every now and then due to some race condition
                print('Warning: IndexError on {} JT, error: {}'.format(
                    jt_pos % jt_count, e
                ))
            jt_pos += 1
        jt_defaults = dict(
            (f.attname, getattr(jt, f.attname))
            for f in JobTemplate._meta.get_fields()
            if f.concrete and f.attname in job_field_names and getattr(jt, f.attname)
        )
        jt_defaults['job_template_id'] = jt.pk
        jt_defaults['unified_job_template_id'] = jt.pk  # populated by save method

        jobs = [
            Job(
                status=STATUS_OPTIONS[i % len(STATUS_OPTIONS)],
                started=now() - time_delta, created=now() - time_delta, modified=now() - time_delta, finished=now() - time_delta,
                elapsed=0., **jt_defaults)
            for i in range(N)
        ]
        ujs = UnifiedJob.objects.bulk_create(jobs)
        query = InsertQuery(Job)
        query.insert_values(fields, ujs)
        with connection.cursor() as cursor:
            query, params = query.sql_with_params()[0]
            cursor.execute(query, params)
        return ujs[-1], jt_pos

    i = 1
    jt_pos = 0
    s = time()
    while jobs > 0:
        s_loop = time()
        print('running batch {}, runtime {}'.format(i, time() - s))
        created, jt_pos = make_batch(min(jobs, batch_size), jt_pos)
        print('took {}'.format(time() - s_loop))
        i += 1
        jobs -= batch_size
    return created


def generate_events(events, job, time_delta):
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()
    print('removing indexes and constraints')
    created_time = datetime.datetime.today() - time_delta - datetime.timedelta(seconds=5)
    modified_time = datetime.datetime.today() - time_delta
    created_stamp = created_time.strftime("%Y-%m-%d %H:%M:%S")
    modified_stamp = modified_time.strftime("%Y-%m-%d %H:%M:%S")
    # get all the indexes for main_jobevent
    try:
        # disable WAL to drastically increase write speed
        # we're not doing replication, and the goal of this script is to just
        # insert data as quickly as possible without concern for the risk of
        # data loss on crash
        # see: https://www.compose.com/articles/faster-performance-with-unlogged-tables-in-postgresql/
        cursor.execute('ALTER TABLE main_jobevent SET UNLOGGED')

        cursor.execute("SELECT indexname, indexdef FROM pg_indexes WHERE tablename='main_jobevent' AND indexname != 'main_jobevent_pkey1';")
        indexes = cursor.fetchall()

        cursor.execute(
            "SELECT conname, contype, pg_catalog.pg_get_constraintdef(r.oid, true) as condef FROM pg_catalog.pg_constraint r WHERE r.conrelid = 'main_jobevent'::regclass AND conname != 'main_jobevent_pkey1';"  # noqa
        )
        constraints = cursor.fetchall()

        # drop all indexes for speed
        for indexname, indexdef in indexes:
            cursor.execute(f'DROP INDEX IF EXISTS {indexname}')
            print(f'DROP INDEX IF EXISTS {indexname}')
        for conname, contype, condef in constraints:
            cursor.execute(f'ALTER TABLE main_jobevent DROP CONSTRAINT IF EXISTS {conname}')
            print(f'ALTER TABLE main_jobevent DROP CONSTRAINT IF EXISTS {conname}')
        conn.commit()

        print(f'attaching {events} events to job {job}')
        cores = multiprocessing.cpu_count()
        workers = []

        num_procs = min(cores, events)
        num_events = events // num_procs
        if num_events <= 1:
            num_events = events

        for i in range(num_procs):
            p = multiprocessing.Process(target=firehose, args=(job, num_events, created_stamp, modified_stamp))
            p.daemon = True
            workers.append(p)

        for w in workers:
            w.start()

        for w in workers:
            w.join()

        workers = []

        print('generating unique start/end line counts')
        cursor.execute('CREATE SEQUENCE IF NOT EXISTS firehose_seq;')
        cursor.execute('CREATE SEQUENCE IF NOT EXISTS firehose_line_seq MINVALUE 0;')
        cursor.execute('ALTER SEQUENCE firehose_seq RESTART WITH 1;')
        cursor.execute('ALTER SEQUENCE firehose_line_seq RESTART WITH 0;')
        cursor.execute("SELECT nextval('firehose_line_seq')")
        conn.commit()

        cursor.execute(
            "UPDATE main_jobevent SET "
            "counter=nextval('firehose_seq')::integer,"
            "start_line=nextval('firehose_line_seq')::integer,"
            "end_line=currval('firehose_line_seq')::integer + 2 "
            f"WHERE job_id={job}"
        )
        conn.commit()
    finally:
        # restore all indexes
        print(datetime.datetime.utcnow().isoformat())
        print('restoring indexes and constraints (this may take awhile)')

        workers = []
        for indexname, indexdef in indexes:
            p = multiprocessing.Process(target=cleanup, args=(indexdef,))
            p.daemon = True
            workers.append(p)

        for w in workers:
            w.start()

        for w in workers:
            w.join()

        for conname, contype, condef in constraints:
            if contype == 'c':
                # if there are any check constraints, don't add them back
                # (historically, these are > 0 checks, which are basically
                # worthless, because Ansible doesn't emit counters, line
                # numbers, verbosity, etc... < 0)
                continue
            sql = f'ALTER TABLE main_jobevent ADD CONSTRAINT {conname} {condef}'
            cleanup(sql)
    conn.close()
    print(datetime.datetime.utcnow().isoformat())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--jobs', type=int, help='Number of jobs to create.',
        default=1000000) # 1M by default
    parser.add_argument(
        '--events', type=int, help='Number of events to create.',
        default=1000000000) # 1B by default
    parser.add_argument(
        '--batch-size', type=int, help='Number of jobs to create in a single batch.',
        default=1000)
    parser.add_argument(
        '--days-delta', type=int, help='Number of days old to create the events. Defaults to 0.',
        default=0)
    parser.add_argument(
        '--hours-delta', type=int, help='Number of hours old to create the events. Defaults to 1.',
        default=1)
    params = parser.parse_args()
    jobs = params.jobs
    time_delta = params.days_delta, params.hours_delta
    time_delta = datetime.timedelta(days=time_delta[0], hours=time_delta[1], seconds=0)
    events = params.events
    batch_size = params.batch_size
    print(datetime.datetime.utcnow().isoformat())
    created = generate_jobs(jobs, batch_size=batch_size, time_delta=time_delta)
    generate_events(events, str(created.pk), time_delta)
