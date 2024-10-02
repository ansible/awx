from django.db import migrations

TACACS_PLUS_AUTH_CONF_KEYS = [
    'TACACSPLUS_HOST',
    'TACACSPLUS_PORT',
    'TACACSPLUS_SECRET',
    'TACACSPLUS_SESSION_TIMEOUT',
    'TACACSPLUS_AUTH_PROTOCOL',
    'TACACSPLUS_REM_ADDR',
]


def remove_tacacs_plus_auth_conf(apps, scheme_editor):
    setting = apps.get_model('conf', 'Setting')
    setting.objects.filter(key__in=TACACS_PLUS_AUTH_CONF_KEYS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('conf', '0010_change_to_JSONField'),
    ]

    operations = [
        migrations.RunPython(remove_tacacs_plus_auth_conf),
    ]
