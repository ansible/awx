from django.db import connection
from awx.main.models import InstanceGroup

InstanceGroup.objects.filter(name__in=('green', 'yellow', 'red', 'blue')).delete()

green = InstanceGroup.objects.create(name='green')
red = InstanceGroup.objects.create(name='red')
yellow = InstanceGroup.objects.create(name='yellow')
blue = InstanceGroup.objects.create(name='blue')

for ig in InstanceGroup.objects.all():
    print((ig.id, ig.name, ig.use_role_id))

with connection.cursor() as cursor:
    cursor.execute("ALTER TABLE main_instancegroup DROP CONSTRAINT main_instancegroup_use_role_id_48ea7ecc_fk_main_rbac_roles_id")

    cursor.execute(f"UPDATE main_rbac_roles SET object_id = NULL WHERE id = {red.use_role_id}")
    cursor.execute(f"DELETE FROM main_rbac_roles_parents WHERE from_role_id = {blue.use_role_id} OR to_role_id = {blue.use_role_id}")
    cursor.execute(f"DELETE FROM main_rbac_role_ancestors WHERE ancestor_id = {blue.use_role_id} OR descendent_id = {blue.use_role_id}")
    cursor.execute(f"DELETE FROM main_rbac_roles WHERE id = {blue.use_role_id}")
    cursor.execute("UPDATE main_instancegroup SET use_role_id = NULL WHERE name = 'red'")
    cursor.execute(f"UPDATE main_instancegroup SET use_role_id = {green.use_role_id} WHERE name = 'yellow'")

    cursor.execute(
        "ALTER TABLE main_instancegroup ADD CONSTRAINT main_instancegroup_use_role_id_48ea7ecc_fk_main_rbac_roles_id FOREIGN KEY (use_role_id) REFERENCES public.main_rbac_roles(id) DEFERRABLE INITIALLY DEFERRED NOT VALID"
    )

print("=====================================")
for ig in InstanceGroup.objects.all():
    print((ig.id, ig.name, ig.use_role_id))
