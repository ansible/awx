from awx.main.models import Organization


def migrate_org_admin_to_use(apps):
    for org in Organization.objects.prefetch_related('admin_role__members').iterator():
        igs = list(org.instance_groups.all())
        if not igs:
            continue
        for admin in org.admin_role.members.filter(is_superuser=False):
            for ig in igs:
                ig.use_role.members.add(admin)
