# Generated by Django 4.2 on 2023-05-17 18:31

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0184_django_indexes'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='instancelink',
            options={'ordering': ('id',)},
        ),
        migrations.AddField(
            model_name='instance',
            name='peers_from_control_nodes',
            field=models.BooleanField(default=False, help_text='If True, control plane cluster nodes should automatically peer to it.'),
        ),
        migrations.AlterField(
            model_name='instancelink',
            name='link_state',
            field=models.CharField(
                choices=[('adding', 'Adding'), ('established', 'Established'), ('disconnected', 'Disconnected'), ('removing', 'Removing')],
                default='disconnected',
                help_text='Indicates the current life cycle stage of this peer link.',
                max_length=16,
            ),
        ),
        migrations.AddConstraint(
            model_name='instancelink',
            constraint=models.CheckConstraint(check=models.Q(('source', models.F('target')), _negated=True), name='source_and_target_can_not_be_equal'),
        ),
        migrations.AlterField(
            model_name='instance',
            name='listener_port',
            field=models.PositiveIntegerField(
                blank=True,
                default=None,
                help_text='Port that Receptor will listen for incoming connections on.',
                null=True,
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(65535)],
            ),
        ),
    ]
