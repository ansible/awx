#!/usr/bin/env python
"""Compare query strategies for RoleEvaluation to understand why
iterating full model instances is slow vs values_list."""
import os
import sys
import time

import django

base_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))

if base_dir not in sys.path:
    sys.path.insert(1, base_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "awx.settings.development")
django.setup()

# Monkey-patch out websocket notifications
import awx.main.consumers  # noqa: E402
import awx.main.models.inventory  # noqa: E402

_noop = lambda *a, **kw: None
awx.main.consumers.emit_channel_notification = _noop
awx.main.models.inventory.emit_channel_notification = _noop

from ansible_base.rbac.models import ObjectRole, RoleEvaluation  # noqa: E402
from awx.main.models import Organization  # noqa: E402

ORG_NAME = "perf-test-org"


def main():
    org = Organization.objects.get(name=ORG_NAME)

    # Find the org admin role with the most permission_partials
    org_roles = ObjectRole.objects.filter(
        object_id=org.pk,
        content_type__model='organization',
    )
    role = max(org_roles, key=lambda r: r.permission_partials.count())
    total = role.permission_partials.count()
    print(f"Testing with object-role pk={role.pk}, {total} permission_partials\n")

    # 1) Full model instances via .all()
    start = time.perf_counter()
    partials = {}
    for pp in role.permission_partials.all():
        partials[pp.obj_perm_id()] = pp
    elapsed = time.perf_counter() - start
    print(f"1) .all() full model instances:      {elapsed:.4f}s  ({len(partials)} rows)")

    # 2) Full model instances via .iterator() (less memory, same instantiation)
    start = time.perf_counter()
    partials2 = {}
    for pp in role.permission_partials.iterator():
        partials2[pp.obj_perm_id()] = pp
    elapsed = time.perf_counter() - start
    print(f"2) .iterator() full model instances:  {elapsed:.4f}s  ({len(partials2)} rows)")

    # 3) values_list to get the same 3-tuple without model instantiation
    start = time.perf_counter()
    tuples = set(role.permission_partials.values_list('codename', 'content_type_id', 'object_id'))
    elapsed = time.perf_counter() - start
    print(f"3) values_list (3 fields, as set):    {elapsed:.4f}s  ({len(tuples)} rows)")

    # 4) values_list but iterated into a dict (to mimic needing delete IDs)
    start = time.perf_counter()
    partials4 = {}
    for row in role.permission_partials.values_list('id', 'codename', 'content_type_id', 'object_id'):
        partials4[(row[1], row[2], row[3])] = row[0]
    elapsed = time.perf_counter() - start
    print(f"4) values_list (4 fields, as dict):   {elapsed:.4f}s  ({len(partials4)} rows)")

    # 5) values (dict rows, no model instantiation)
    start = time.perf_counter()
    partials5 = {}
    for row in role.permission_partials.values('id', 'codename', 'content_type_id', 'object_id'):
        partials5[(row['codename'], row['content_type_id'], row['object_id'])] = row['id']
    elapsed = time.perf_counter() - start
    print(f"5) .values() dict rows:               {elapsed:.4f}s  ({len(partials5)} rows)")

    # 6) Raw SQL via cursor for baseline
    from django.db import connection

    start = time.perf_counter()
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, codename, content_type_id, object_id " "FROM dab_rbac_roleevaluation WHERE role_id = %s", [role.pk])
        partials6 = {}
        for row in cursor.fetchall():
            partials6[(row[1], row[2], row[3])] = row[0]
    elapsed = time.perf_counter() - start
    print(f"6) Raw SQL cursor:                    {elapsed:.4f}s  ({len(partials6)} rows)")


if __name__ == "__main__":
    main()
