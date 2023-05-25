import logging

from awx.main.models import Organization

logger = logging.getLogger('awx.main.migrations')


def migrate_org_admin_to_use(apps, schema_editor):
    logger.info('Initiated migration from Org admin to use role')
    roles_added = 0
    for org in Organization.objects.prefetch_related('admin_role__members').iterator(chunk_size=1000):
        igs = list(org.instance_groups.all())
        if not igs:
            continue
        for admin in org.admin_role.members.filter(is_superuser=False):
            for ig in igs:
                ig.use_role.members.add(admin)
                roles_added += 1
    if roles_added:
        logger.info(f'Migration converted {roles_added} from organization admin to use role')
