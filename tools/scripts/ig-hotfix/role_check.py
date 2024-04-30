from collections import Counter

from awx.main.models.rbac import Role


for r in Role.objects.all():
    if not r.content_type:
        continue
    if r.id != getattr(getattr(r.content_object, r.role_field, None), 'id', None):
        rev = getattr(r.content_object, r.role_field, None)
        print(f"role.id={r.id}   '{r.content_type}' id={r.object_id} field={r.role_field} | obj.roleid={getattr(rev, 'id', None)} {getattr(rev, 'content_type', None)} {getattr(rev, 'object_id', None)} {getattr(rev, 'role_field', None)}")
