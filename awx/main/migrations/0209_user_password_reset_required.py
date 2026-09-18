from django.db import migrations


def _column_names(schema_editor, table):
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        if table not in connection.introspection.table_names(cursor):
            return None
        return {col.name for col in connection.introspection.get_table_description(cursor, table)}


def add_password_reset_required(apps, schema_editor):
    """Add password_reset_required column on Django's auth_user table."""
    columns = _column_names(schema_editor, 'auth_user')
    if columns is None or 'password_reset_required' in columns:
        return

    vendor = schema_editor.connection.vendor
    if vendor == 'postgresql':
        schema_editor.execute(
            'ALTER TABLE auth_user ADD COLUMN password_reset_required boolean DEFAULT false NOT NULL;'
        )
    elif vendor == 'sqlite':
        schema_editor.execute(
            'ALTER TABLE auth_user ADD COLUMN password_reset_required bool NOT NULL DEFAULT 0;'
        )
    else:
        schema_editor.execute(
            'ALTER TABLE auth_user ADD COLUMN password_reset_required bool NOT NULL DEFAULT 0;'
        )


def remove_password_reset_required(apps, schema_editor):
    columns = _column_names(schema_editor, 'auth_user')
    if columns is None or 'password_reset_required' not in columns:
        return
    schema_editor.execute('ALTER TABLE auth_user DROP COLUMN password_reset_required;')


class Migration(migrations.Migration):
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('main', '0208_fix_system_auditor_migration'),
    ]

    operations = [
        migrations.RunPython(add_password_reset_required, remove_password_reset_required),
    ]
