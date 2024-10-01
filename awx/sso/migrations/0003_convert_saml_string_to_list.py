from django.db import migrations, connection


class Migration(migrations.Migration):
    dependencies = [
        ('sso', '0002_expand_provider_options'),
    ]
    # NOOP, migration is kept to preserve integrity.
    operations = []
