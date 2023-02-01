# Generated by Django 2.2.16 on 2021-02-15 22:02

from django.db import migrations


def reset_pod_specs(apps, schema_editor):
    InstanceGroup = apps.get_model('main', 'InstanceGroup')
    InstanceGroup.objects.update(pod_spec_override="")


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0126_executionenvironment_container_options'),
    ]

    operations = [migrations.RunPython(reset_pod_specs)]
