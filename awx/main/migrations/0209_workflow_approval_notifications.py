from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0185_previous_migration_name_here'),  # Replace with actual latest migration file name
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