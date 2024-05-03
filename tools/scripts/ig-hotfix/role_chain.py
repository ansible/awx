from collections import defaultdict
import sys

from django.contrib.contenttypes.models import ContentType

from awx.main.fields import ImplicitRoleField
from awx.main.models.rbac import Role


print("digraph G {")

for r in Role.objects.order_by('id'):
    if r.content_type is None:
        print(f'    {r.id} [shape=box,label="id={r.id}\lsingleton={r.singleton_name}\l"]')
    else:
        print(f'    {r.id} [shape=box,label="id={r.id}\lct={r.content_type}\lobject_id={r.object_id}\lrole_field={r.role_field}\l"]')

for r in Role.objects.order_by('id'):
    for p in r.parents.all():
        print(f"    {p.id} -> {r.id}")

print("}")
