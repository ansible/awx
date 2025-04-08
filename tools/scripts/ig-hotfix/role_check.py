from collections import defaultdict
import json
import sys

from django.contrib.contenttypes.models import ContentType
from django.db.models.fields.related_descriptors import ManyToManyDescriptor

from awx.main.fields import ImplicitRoleField
from awx.main.models.rbac import Role


team_ct = ContentType.objects.get(app_label='main', model='team')

crosslinked = defaultdict(lambda: defaultdict(dict))
crosslinked_parents = defaultdict(list)
orphaned_roles = set()


def resolve(obj, path):
    fname, _, path = path.partition('.')
    new_obj = getattr(obj, fname, None)
    if new_obj is None:
        return set()
    if not path:
        return {
            new_obj,
        }

    if isinstance(new_obj, ManyToManyDescriptor):
        return {x for o in new_obj.all() for x in resolve(o, path)}

    return resolve(new_obj, path)


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
                sys.stderr.write(f"{cls} id={obj.id} {f.name} points to Role id={r_id}, which is not in the database.\n")
                crosslinked[ct.id][obj.id][f'{f.name}_id'] = None
                continue
            if not r:
                sys.stderr.write(f"{cls} id={obj.id} {f.name} does not have a Role object\n")
                crosslinked[ct.id][obj.id][f'{f.name}_id'] = None
                continue
            if r.content_object != obj:
                sys.stderr.write(
                    f"{cls.__name__} id={obj.id} {f.name} is pointing to a Role that is assigned to a different object: role.id={r.id} {r.content_type!r} {r.object_id} {r.role_field}\n"
                )
                crosslinked[ct.id][obj.id][f'{f.name}_id'] = None
                continue


sys.stderr.write('===================================\n')
for r in Role.objects.exclude(role_field__startswith='system_').order_by('id'):

    # The ancestor list should be a superset of both parents and implicit_parents.
    # Also, parents should be a superset of implicit_parents.
    parents = set(r.parents.values_list('id', flat=True))
    ancestors = set(r.ancestors.values_list('id', flat=True))
    implicit = set(json.loads(r.implicit_parents))

    if not implicit:
        sys.stderr.write(f"Role id={r.id} has no implicit_parents\n")
    if not parents <= ancestors:
        sys.stderr.write(f"Role id={r.id} has parents that are not in the ancestor list: {parents - ancestors}\n")
        crosslinked[r.content_type_id][r.object_id][f'{r.role_field}_id'] = r.id
    if not implicit <= parents:
        sys.stderr.write(f"Role id={r.id} has implicit_parents that are not in the parents list: {implicit - parents}\n")
        crosslinked[r.content_type_id][r.object_id][f'{r.role_field}_id'] = r.id
    if not implicit <= ancestors:
        sys.stderr.write(f"Role id={r.id} has implicit_parents that are not in the ancestor list: {implicit - ancestors}\n")
        crosslinked[r.content_type_id][r.object_id][f'{r.role_field}_id'] = r.id

    # Check that the Role's generic foreign key points to a legitimate object
    if not r.content_object:
        sys.stderr.write(f"Role id={r.id} is missing a valid content_object: {r.content_type!r} {r.object_id} {r.role_field}\n")
        orphaned_roles.add(r.id)
        continue

    # Check the resource's role field parents for consistency with Role.parents.all().
    f = r.content_object._meta.get_field(r.role_field)
    f_parent = (
        set(f.parent_role)
        if isinstance(f.parent_role, list)
        else {
            f.parent_role,
        }
    )
    dotted = {x for p in f_parent if '.' in p for x in resolve(r.content_object, p)}
    plus = set()
    for p in r.parents.all():
        if p.singleton_name:
            if f'singleton:{p.singleton_name}' not in f_parent:
                plus.add(p)
        elif p.content_type == team_ct:
            # Team has been granted this role; probably legitimate.
            if p.role_field in ('admin_role', 'member_role'):
                continue
        elif (p.content_type, p.object_id) == (r.content_type, r.object_id):
            if p.role_field not in f_parent:
                plus.add(p)
        elif p in dotted:
            continue
        else:
            plus.add(p)

    if plus:
        plus_repr = [f"{x.content_type!r} {x.object_id} {x.role_field}" for x in plus]
        sys.stderr.write(f"Role id={r.id} has cross-linked parents: {plus_repr}\n")
        crosslinked_parents[r.id].extend(x.id for x in plus)

    try:
        rev = getattr(r.content_object, r.role_field, None)
    except Role.DoesNotExist:
        sys.stderr.write(f"Role id={r.id} {r.content_type!r} {r.object_id} {r.role_field} points at an object with a broken role.\n")
        crosslinked[r.content_type_id][r.object_id][f'{r.role_field}_id'] = r.id
        continue
    if rev is None or r.id != rev.id:
        if rev and (r.content_type_id, r.object_id, r.role_field) == (rev.content_type_id, rev.object_id, rev.role_field):
            sys.stderr.write(
                f"Role id={r.id} {r.content_type!r} {r.object_id} {r.role_field} is an orphaned duplicate of Role id={rev.id}, which is actually being used by the assigned resource\n"
            )
            orphaned_roles.add(r.id)
        elif not rev:
            sys.stderr.write(f"Role id={r.id} {r.content_type!r} {r.object_id} {r.role_field} is pointing to an object currently using no role\n")
            crosslinked[r.content_type_id][r.object_id][f'{r.role_field}_id'] = r.id
        else:
            sys.stderr.write(
                f"Role id={r.id} {r.content_type!r} {r.object_id} {r.role_field} is pointing to an object using a different role: id={rev.id} {rev.content_type!r} {rev.object_id} {rev.role_field}\n"
            )
            crosslinked[r.content_type_id][r.object_id][f'{r.role_field}_id'] = r.id
        continue


sys.stderr.write('===================================\n')


print(
    f"""\
from collections import Counter

from django.contrib.contenttypes.models import ContentType

from awx.main.fields import ImplicitRoleField
from awx.main.models.rbac import Role


delete_counts = Counter()
update_counts = Counter()

"""
)


print("# Resource objects that are pointing to the wrong Role.  Some of these")
print("# do not have corresponding Roles anywhere, so delete the foreign key.")
print("# For those, new Roles will be constructed upon save.\n")
print("queue = set()\n")
for ct, objs in crosslinked.items():
    print(f"cls = ContentType.objects.get(id={ct}).model_class()\n")
    for obj, kv in objs.items():
        print(f"c = cls.objects.filter(id={obj}).update(**{kv!r})")
        print("update_counts.update({cls._meta.label: c})")
        print(f"queue.add((cls, {obj}))")

print("\n# Role objects that are assigned to objects that do not exist")
for r in orphaned_roles:
    print(f"c = Role.objects.filter(id={r}).update(object_id=None)")
    print("update_counts.update({'main.Role': c})")
    print(f"_, c = Role.objects.filter(id={r}).delete()")
    print("delete_counts.update(c)")

print('\n\n')
for child, parents in crosslinked_parents.items():
    print(f"r = Role.objects.get(id={child})")
    print(f"r.parents.remove(*Role.objects.filter(id__in={parents!r}))")
    print(f"queue.add((r.content_object.__class__, r.object_id))")

print('\n\n')
print('print("Objects deleted:", dict(delete_counts.most_common()))')
print('print("Objects updated:", dict(update_counts.most_common()))')

print("\n\nfor cls, obj_id in queue:")
print("    role_fields = [f for f in cls._meta.fields if isinstance(f, ImplicitRoleField)]")
print("    obj = cls.objects.get(id=obj_id)")
print("    for f in role_fields:")
print("        r = getattr(obj, f.name, None)")
print("        if r is not None:")
print("            print(f'updating implicit parents on Role {r.id}')")
print("            r.implicit_parents = '[]'")
print("            r.save()")
print("    obj.save()")
