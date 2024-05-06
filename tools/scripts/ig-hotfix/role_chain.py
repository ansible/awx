from collections import defaultdict
import os
import sys

from django.contrib.contenttypes.models import ContentType

from awx.main.fields import ImplicitRoleField
from awx.main.models.rbac import Role


role_id = int(os.environ.get('role'))
role = Role.objects.get(id=role_id)

all_roles = {role,}
graph = defaultdict(set)


# Role parents
new_parents = {role,}
while new_parents:
    old_parents = new_parents
    new_parents = set()
    for r in old_parents:
        new_parents |= (set(r.parents.all()) - all_roles)
        for p in r.parents.all():
            graph[p.id].add(r.id)
    all_roles |= new_parents

# Role children
new_children = {role,}
while new_children:
    old_children = new_children
    new_children = set()
    for r in old_children:
        new_children |= (set(r.children.all()) - all_roles)
        for c in r.children.all():
            graph[r.id].add(c.id)
    all_roles |= new_children


print("digraph G {")

for r in sorted(all_roles, key=lambda x: x.id):
    if r.content_type is None:
        print(f'    {r.id} [shape=box,label="id={r.id}\lsingleton={r.singleton_name}\l"]')
    else:
        print(f'    {r.id} [shape=box,label="id={r.id}\lct={r.content_type}\lobject_id={r.object_id}\lrole_field={r.role_field}\l"]')

print()
for p_id, children in sorted(graph.items()):
    for c_id in children:
        print(f"    {p_id} -> {c_id}")

print("}")
