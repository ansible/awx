from django.db import migrations, connection
import json

_values_to_change = ['is_superuser_value', 'is_superuser_role', 'is_system_auditor_value', 'is_system_auditor_role']


def _get_setting():
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT value FROM conf_setting WHERE key= %s', ['SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR'])
        row = cursor.fetchone()
        if row == None:
            return {}
        existing_setting = row[0]

    try:
        existing_json = json.loads(existing_setting)
    except json.decoder.JSONDecodeError as e:
        print("Failed to decode existing json setting:")
        print(existing_setting)
        raise e

    return existing_json


def _set_setting(value):
    with connection.cursor() as cursor:
        cursor.execute(f'UPDATE conf_setting SET value = %s WHERE key = %s', [json.dumps(value), 'SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR'])


def forwards(app, schema_editor):
    # The Operation should use schema_editor to apply any changes it
    # wants to make to the database.
    existing_json = _get_setting()
    for key in _values_to_change:
        if existing_json.get(key, None) and isinstance(existing_json.get(key), str):
            existing_json[key] = [existing_json.get(key)]
    _set_setting(existing_json)


def backwards(app, schema_editor):
    existing_json = _get_setting()
    for key in _values_to_change:
        if existing_json.get(key, None) and not isinstance(existing_json.get(key), str):
            try:
                existing_json[key] = existing_json.get(key).pop()
            except IndexError:
                existing_json[key] = ""
    _set_setting(existing_json)


class Migration(migrations.Migration):
    dependencies = [
        ('sso', '0002_expand_provider_options'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
