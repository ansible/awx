from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0205_add_ordering_to_instancegroup_and_workflow_nodes'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowapprovaltemplate',
            name='notification_templates_approvals',
            field=models.ManyToManyField(
                blank=True,
                related_name='%(class)s_notification_templates_for_approvals',
                to='main.notificationtemplate',
            ),
        ),
    ]
