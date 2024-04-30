from collections import defaultdict
import sys
import textwrap

from django.contrib.contenttypes.models import ContentType

from awx.main.fields import ImplicitRoleField
from awx.main.models.rbac import Role


crosslinked = defaultdict(dict)
orphaned_roles = []


for ct in ContentType.objects.order_by('id'):
    cls = ct.model_class()
    if not any(isinstance(f, ImplicitRoleField) for f in cls._meta.fields):
        continue
    for obj in cls.objects.all():
        for f in cls._meta.fields:
            if not isinstance(f, ImplicitRoleField):
                continue
            r = getattr(obj, f.name, None)
            if not r:
                sys.stderr.write(f"{cls} id={obj.id} {f.name} does not have a Role object\n")
                crosslinked[(ct.id, obj.id)][f.name] = None
                continue
            if r.content_object != obj:
                sys.stderr.write(f"{cls.__name__} id={obj.id} {f.name} is pointing to a Role that is assigned to a different object: role.id={r.id} {r.content_type!r} {r.object_id} {r.role_field}\n")
                crosslinked[(ct.id, obj.id)][f.name] = None
                continue


sys.stderr.write('===================================\n')
for r in Role.objects.exclude(role_field__startswith='system_').order_by('id'):
    if not r.content_object:
        sys.stderr.write(f"Role id={r.id} is missing a valid content_object: {r.content_type!r} {r.object_id} {r.role_field}\n")
        orphaned_roles.append(r.id)
        continue
    rev = getattr(r.content_object, r.role_field, None)
    if not rev:
        continue
    if r.id != rev.id:
        sys.stderr.write(f"Role id={r.id} {r.content_type!r} {r.object_id} {r.role_field} is pointing to an object using a different role: id={rev.id} {rev.content_type!r} {rev.object_id} {rev.role_field}\n")
        crosslinked[(r.content_type_id, r.object_id)][r.role_field] = r.id
        continue


sys.stderr.write('===================================\n')


print(f"""\
from django.contrib.contenttypes.models import ContentType

from awx.main.models.rbac import Role

""")

print("# Role objects that are assigned to objects that do not exist")
for r in orphaned_roles:
    print(f"Role.objects.filter(id={r}).delete()")


print("\n")
print("# Resource objects that are pointing to the wrong Role.  Some of these")
print("# do not have corresponding Roles anywhere, so delete the foreign key.")
print("# For those, new Roles will be constructed upon save.\n")
for (ct, obj), kv in crosslinked.items():
    print(f"ct = ContentType.objects.get(id={ct})")
    print(f"obj = ct.get_object_for_this_type(id={obj})")
    for f, val in kv.items():
        print(f"setattr(obj, '{f}_id', {val})")
    print(f"obj.save()\n")
