import awx.main.fields
import django.db.models.deletion
from django.db import migrations

IMPLICIT_ROLE_FIELDS = [
    # Credential
    ('credential', 'admin_role', ['singleton:system_administrator', 'organization.credential_admin_role']),
    ('credential', 'use_role', ['admin_role']),
    ('credential', 'read_role', ['singleton:system_auditor', 'organization.auditor_role', 'use_role', 'admin_role']),
    # InstanceGroup
    ('instancegroup', 'admin_role', ['singleton:system_administrator']),
    ('instancegroup', 'use_role', ['admin_role']),
    ('instancegroup', 'read_role', ['singleton:system_auditor', 'use_role', 'admin_role']),
    # Inventory
    ('inventory', 'admin_role', 'organization.inventory_admin_role'),
    ('inventory', 'update_role', 'admin_role'),
    ('inventory', 'adhoc_role', 'admin_role'),
    ('inventory', 'use_role', 'adhoc_role'),
    ('inventory', 'read_role', ['organization.auditor_role', 'update_role', 'use_role', 'admin_role']),
    # JobTemplate
    ('jobtemplate', 'admin_role', ['organization.job_template_admin_role']),
    ('jobtemplate', 'execute_role', ['admin_role', 'organization.execute_role']),
    ('jobtemplate', 'read_role', ['organization.auditor_role', 'inventory.organization.auditor_role', 'execute_role', 'admin_role']),
    # Organization
    ('organization', 'admin_role', 'singleton:system_administrator'),
    ('organization', 'execute_role', 'admin_role'),
    ('organization', 'project_admin_role', 'admin_role'),
    ('organization', 'inventory_admin_role', 'admin_role'),
    ('organization', 'credential_admin_role', 'admin_role'),
    ('organization', 'workflow_admin_role', 'admin_role'),
    ('organization', 'notification_admin_role', 'admin_role'),
    ('organization', 'job_template_admin_role', 'admin_role'),
    ('organization', 'execution_environment_admin_role', 'admin_role'),
    ('organization', 'auditor_role', 'singleton:system_auditor'),
    ('organization', 'member_role', ['admin_role']),
    (
        'organization',
        'read_role',
        [
            'member_role',
            'auditor_role',
            'execute_role',
            'project_admin_role',
            'inventory_admin_role',
            'workflow_admin_role',
            'notification_admin_role',
            'credential_admin_role',
            'job_template_admin_role',
            'approval_role',
            'execution_environment_admin_role',
        ],
    ),
    ('organization', 'approval_role', 'admin_role'),
    # Project
    ('project', 'admin_role', ['organization.project_admin_role', 'singleton:system_administrator']),
    ('project', 'use_role', 'admin_role'),
    ('project', 'update_role', 'admin_role'),
    ('project', 'read_role', ['organization.auditor_role', 'singleton:system_auditor', 'use_role', 'update_role']),
    # Team
    ('team', 'admin_role', 'organization.admin_role'),
    ('team', 'member_role', 'admin_role'),
    ('team', 'read_role', ['organization.auditor_role', 'member_role']),
    # WorkflowJobTemplate
    ('workflowjobtemplate', 'admin_role', ['singleton:system_administrator', 'organization.workflow_admin_role']),
    ('workflowjobtemplate', 'execute_role', ['admin_role', 'organization.execute_role']),
    ('workflowjobtemplate', 'read_role', ['singleton:system_auditor', 'organization.auditor_role', 'execute_role', 'admin_role', 'approval_role']),
    ('workflowjobtemplate', 'approval_role', ['organization.approval_role', 'admin_role']),
]


class Migration(migrations.Migration):
    """Set db_index=False on all ImplicitRoleField ForeignKeys.

    These FK indexes on legacy *_role_id columns have zero scans after
    the DAB RBAC migration (0192+) and add unnecessary write/VACUUM
    overhead.  Changing db_index on the field definition keeps Django's
    migration state in sync with the database.
    """

    dependencies = [
        ('main', '0205_add_ordering_to_instancegroup_and_workflow_nodes'),
    ]

    operations = [
        migrations.AlterField(
            model_name=model,
            name=field,
            field=awx.main.fields.ImplicitRoleField(
                db_index=False,
                editable=False,
                null='True',
                on_delete=django.db.models.deletion.SET_NULL,
                parent_role=parent_role,
                related_name='+',
                to='main.role',
            ),
        )
        for model, field, parent_role in IMPLICIT_ROLE_FIELDS
    ]
