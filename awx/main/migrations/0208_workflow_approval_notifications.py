# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""Database migration for adding node-level notification templates to WorkflowApprovalTemplate."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Adds the `notification_templates_approvals` ManyToManyField to the `WorkflowApprovalTemplate` model."""

    dependencies = [
        ('main', '0207_alter_skip_tags_to_textfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowapprovaltemplate',
            name='notification_templates_approvals',
            field=models.ManyToManyField(
                blank=True,
                help_text='Notification templates to fire for this approval node.',
                related_name='workflow_approval_templates',
                to='main.notificationtemplate',
            ),
        ),
    ]