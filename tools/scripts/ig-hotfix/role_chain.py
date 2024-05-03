from collections import defaultdict
import os
import sys

from django.contrib.contenttypes.models import ContentType

from awx.main.fields import ImplicitRoleField
from awx.main.models.rbac import Role


r_id = int(os.environ.get('role'))
r = Role.objects.get(id=r_id)

print(r)
