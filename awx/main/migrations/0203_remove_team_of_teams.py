import logging

from django.db import migrations

from awx.main.migrations._dab_rbac import consolidate_indirect_user_roles

logger = logging.getLogger('awx.main.migrations')


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0202_convert_controller_role_definitions'),
    ]
    # The DAB RBAC app makes substantial model changes which by change-ordering comes after this
    # not including run_before might sometimes work but this enforces a more strict and stable order
    # for both applying migrations forwards and backwards
    run_before = [("dab_rbac", "0004_remote_permissions_additions")]

    operations = [
        migrations.RunPython(consolidate_indirect_user_roles, migrations.RunPython.noop),
    ]
