# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

from contextlib import contextmanager

from django_pglocks import advisory_lock as django_pglocks_advisory_lock
from django.db import connection


@contextmanager
def advisory_lock(*args, lock_session_timeout_milliseconds=0, **kwargs):
    if connection.vendor == 'postgresql':
        cur = None
        idle_in_transaction_session_timeout = None
        idle_session_timeout = None
        if lock_session_timeout_milliseconds > 0:
            with connection.cursor() as cur:
                idle_in_transaction_session_timeout = cur.execute('SHOW idle_in_transaction_session_timeout').fetchone()[0]
                idle_session_timeout = cur.execute('SHOW idle_session_timeout').fetchone()[0]
                cur.execute(f"SET idle_in_transaction_session_timeout = {lock_session_timeout_milliseconds}")
                cur.execute(f"SET idle_session_timeout = {lock_session_timeout_milliseconds}")
        with django_pglocks_advisory_lock(*args, **kwargs) as internal_lock:
            yield internal_lock
            if lock_session_timeout_milliseconds > 0:
                with connection.cursor() as cur:
                    cur.execute(f"SET idle_in_transaction_session_timeout = {idle_in_transaction_session_timeout}")
                    cur.execute(f"SET idle_session_timeout = {idle_session_timeout}")
    else:
        yield True
