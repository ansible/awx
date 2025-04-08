from django.db import connection
from awx.main.models import InstanceGroup

InstanceGroup.objects.filter(name__in=('green', 'yellow', 'red')).delete()

green = InstanceGroup.objects.create(name='green')
red = InstanceGroup.objects.create(name='red')
yellow = InstanceGroup.objects.create(name='yellow')

for ig in InstanceGroup.objects.all():
    print((ig.id, ig.name, ig.use_role_id))

with connection.cursor() as cursor:
    cursor.execute("UPDATE main_instancegroup SET use_role_id = NULL WHERE name = 'red'")
    cursor.execute(f"UPDATE main_instancegroup SET use_role_id = {green.use_role_id} WHERE name = 'yellow'")

print("=====================================")
for ig in InstanceGroup.objects.all():
    print((ig.id, ig.name, ig.use_role_id))
