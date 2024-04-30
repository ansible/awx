from collections import Counter

from awx.main.models.ha import InstanceGroup
from awx.main.models.rbac import Role


for ig in InstanceGroup.objects.order_by('id'):
    for f in ('admin_role', 'use_role', 'read_role'):
        r = getattr(ig, f, None)
        print(f"id={ig.id} {f} // r.id={getattr(r, 'id', None)} {getattr(r, 'content_type', None)} {getattr(r, 'object_id', None)} {getattr(r, 'role_field', None)}")


ct = ContentType.objects.get(app_label='main', model='instancegroup')
for r in Role.objects.filter(content_type=ct).order_by('id'):
    print(f"id={r.id} instancegroup {r.object_id} {r.role_field}")
