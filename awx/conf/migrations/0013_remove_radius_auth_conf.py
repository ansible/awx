from django.db import migrations

RADIUS_AUTH_CONF_KEYS = [
    'RADIUS_SERVER',
    'RADIUS_PORT',
    'RADIUS_SECRET',
]


def remove_radius_auth_conf(apps, scheme_editor):
    setting = apps.get_model('conf', 'Setting')
    setting.objects.filter(key__in=RADIUS_AUTH_CONF_KEYS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('conf', '0012_remove_oidc_auth_conf'),
    ]

    operations = [
        migrations.RunPython(remove_radius_auth_conf),
    ]
