from collections import defaultdict
import json
import sys

from django.contrib.contenttypes.models import ContentType

from awx.main.fields import ImplicitRoleField
from awx.main.models.rbac import Role


crosslinked = defaultdict(lambda: defaultdict(dict))
orphaned_roles = []


for ct in ContentType.objects.order_by('id'):
    cls = ct.model_class()
    if cls is None:
        sys.stderr.write(f"{ct!r} does not have a corresponding model class in the codebase. Skipping.\n")
        continue
    if not any(isinstance(f, ImplicitRoleField) for f in cls._meta.fields):
        continue
    for obj in cls.objects.all():
        for f in cls._meta.fields:
            if not isinstance(f, ImplicitRoleField):
                continue
            r_id = getattr(obj, f'{f.name}_id', None)
            try:
                r = getattr(obj, f.name, None)
            except Role.DoesNotExist:
                sys.stderr.write(f"{cls} id={obj.id} {f.name} points to Role id={r_id}, which is not in the database.")
                crosslinked[ct.id][obj.id][f'{f.name}_id'] = None
                continue
            if not r:
                sys.stderr.write(f"{cls} id={obj.id} {f.name} does not have a Role object\n")
                crosslinked[ct.id][obj.id][f'{f.name}_id'] = None
                continue
            if r.content_object != obj:
                sys.stderr.write(f"{cls.__name__} id={obj.id} {f.name} is pointing to a Role that is assigned to a different object: role.id={r.id} {r.content_type!r} {r.object_id} {r.role_field}\n")
                crosslinked[ct.id][obj.id][f'{f.name}_id'] = None
                continue


sys.stderr.write('===================================\n')
for r in Role.objects.exclude(role_field__startswith='system_').order_by('id'):

    # The ancestor list should be a superset of both parents and implicit_parents
    parents = set(r.parents.values_list('id', flat=True))
    ancestors = set(r.ancestors.values_list('id', flat=True))
    implicit = set(json.loads(r.implicit_parents))

    if not parents <= ancestors:
        sys.stderr.write(f"Role id={r.id} has parents that are not in the ancestor list: {parents - ancestors}\n")
    if not implicit <= ancestors:
        sys.stderr.write(f"Role id={r.id} has implicit_parents that are not in the ancestor list: {implicit - ancestors}\n")

    # Check that the Role's generic foreign key points to a legitimate object
    if not r.content_object:
        sys.stderr.write(f"Role id={r.id} is missing a valid content_object: {r.content_type!r} {r.object_id} {r.role_field}\n")
        orphaned_roles.append(r.id)
        continue
    rev = getattr(r.content_object, r.role_field, None)
    if rev is None or r.id != rev.id:
        if rev and (r.content_type_id, r.object_id, r.role_field) == (rev.content_type_id, rev.object_id, rev.role_field):
            sys.stderr.write(f"Role id={r.id} {r.content_type!r} {r.object_id} {r.role_field} is an orphaned duplicate of Role id={rev.id}, which is actually being used by the assigned resource\n")
            orphaned_roles.append(r.id)
        elif not rev:
            sys.stderr.write(f"Role id={r.id} {r.content_type!r} {r.object_id} {r.role_field} is pointing to an object currently using no role\n")
            crosslinked[r.content_type_id][r.object_id][f'{r.role_field}_id'] = r.id
        else:
            sys.stderr.write(f"Role id={r.id} {r.content_type!r} {r.object_id} {r.role_field} is pointing to an object using a different role: id={rev.id} {rev.content_type!r} {rev.object_id} {rev.role_field}\n")
            crosslinked[r.content_type_id][r.object_id][f'{r.role_field}_id'] = r.id
        continue


sys.stderr.write('===================================\n')


print(f"""\
from django.contrib.contenttypes.models import ContentType

from awx.main.models.rbac import Role

""")

print("# Role objects that are assigned to objects that do not exist")
for r in orphaned_roles:
    print(f"Role.objects.filter(id={r}).update(object_id=None)")
    print(f"Role.objects.filter(id={r}).delete()")


print("\n")
print("# Resource objects that are pointing to the wrong Role.  Some of these")
print("# do not have corresponding Roles anywhere, so delete the foreign key.")
print("# For those, new Roles will be constructed upon save.\n")
print("queue = []\n")
for ct, objs in crosslinked.items():
    print(f"cls = ContentType.objects.get(id={ct}).model_class()\n")
    for obj, kv in objs.items():
        print(f"cls.objects.filter(id={obj}).update(**{kv!r})")
        print(f"queue.append((cls, {obj}))")

print(f"\n\nfor cls, obj_id in queue:")
print(f"    obj = cls.objects.get(id=obj_id)")
print(f"    obj.save()")
