# Python
import uuid

# Load development settings for base variables.
from awx.settings.development import *  # NOQA

# Some things make decisions based on settings.SETTINGS_MODULE, so this is done for that
SETTINGS_MODULE = 'awx.settings.development'

# Turn off task submission, because sqlite3 does not have pg_notify
DISPATCHER_MOCK_PUBLISH = True

# Use SQLite for unit tests instead of PostgreSQL.  If the lines below are
# commented out, Django will create the test_awx-dev database in PostgreSQL to
# run unit tests.
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'unique-{}'.format(str(uuid.uuid4()))}}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'awx.sqlite3'),  # noqa
        'TEST': {
            # Test database cannot be :memory: for inventory tests.
            'NAME': os.path.join(BASE_DIR, 'awx_test.sqlite3')  # noqa
        },
    }
}

# SQLite drops multi-column indexes when it rebuilds tables during some schema
# operations, so later index-altering steps can fail while trying to remove
# indexes that no longer exist. Limit the monkeypatch to migration smoke tests
# (the `-m migration_test` target) so normal test runs remain untouched.
if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    import os

    if os.environ.get('AWX_MIGRATION_TESTS'):
        from django.db.backends.base.schema import BaseDatabaseSchemaEditor
        from django.db.backends.sqlite3.schema import DatabaseSchemaEditor as SQLiteSchemaEditor
        from django.db.migrations.operations import models as migration_operations

        _orig_delete_composed_index = SQLiteSchemaEditor._delete_composed_index
        _orig_base_delete_composed_index = BaseDatabaseSchemaEditor._delete_composed_index

        def _safe_delete_composed_index(self, model, fields, *args, **kwargs):
            try:
                return _orig_delete_composed_index(self, model, fields, *args, **kwargs)
            except ValueError as exc:
                if self.connection.vendor == 'sqlite' and (
                    "Found wrong number (0) of constraints" in str(exc) or "Found wrong number (0) of indexes" in str(exc)
                ):
                    return
                raise

        SQLiteSchemaEditor._delete_composed_index = _safe_delete_composed_index

        def _safe_base_delete_composed_index(self, model, fields, *args, **kwargs):
            try:
                return _orig_base_delete_composed_index(self, model, fields, *args, **kwargs)
            except ValueError as exc:
                if self.connection.vendor == 'sqlite' and (
                    "Found wrong number (0) of constraints" in str(exc) or "Found wrong number (0) of indexes" in str(exc)
                ):
                    return
                raise

        BaseDatabaseSchemaEditor._delete_composed_index = _safe_base_delete_composed_index

        _orig_rename_index_forwards = migration_operations.RenameIndex.database_forwards

        def _safe_rename_index_forwards(self, app_label, schema_editor, from_state, to_state):
            try:
                return _orig_rename_index_forwards(self, app_label, schema_editor, from_state, to_state)
            except ValueError as exc:
                # SQLite may have already dropped the index when rewriting the table.
                if schema_editor.connection.vendor == 'sqlite' and (
                    "Found wrong number (0) of constraints" in str(exc) or "wrong number (0) of indexes" in str(exc)
                ):
                    return
                raise

        migration_operations.RenameIndex.database_forwards = _safe_rename_index_forwards
