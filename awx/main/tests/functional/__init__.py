from django.db import connection
from django.db.models.signals import post_migrate
from django.apps import apps
from django.conf import settings


def app_post_migration(sender, app_config, **kwargs):
    # our usage of pytest.django+sqlite doesn't actually run real migrations,
    # so we've got to make sure the deprecated
    # `main_unifiedjob.result_stdout_text` column actually exists
    cur = connection.cursor()
    cols = cur.execute(
        'SELECT sql FROM sqlite_master WHERE tbl_name="main_unifiedjob";'
    ).fetchone()[0]
    if 'result_stdout_text' not in cols:
        cur.execute(
            'ALTER TABLE main_unifiedjob ADD COLUMN result_stdout_text TEXT'
        )


if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    post_migrate.connect(app_post_migration, sender=apps.get_app_config('main'))



