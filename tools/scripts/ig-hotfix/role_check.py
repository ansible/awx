from collections import Counter

from awx.main.models.rbac import Role


print(Counter(r.id == getattr(getattr(r.content_object, r.role_field, None), 'id', None) for r in Role.objects.all() if r.content_type))
