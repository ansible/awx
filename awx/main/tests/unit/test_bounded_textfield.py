from importlib import import_module
from unittest import mock

import pytest

from django.core.exceptions import ValidationError
from django.db import models
from django.test import override_settings
from django.test.utils import isolate_apps

from rest_framework import serializers

from ansible_base.lib.fields import BoundedTextField, SQLServerMaxLengthValidator

from awx.main import checks as awx_checks
from awx.main.models.rbac import Role, RoleAncestorEntry


def _vendor(name):
    """Return a stand-in database connection that reports the given vendor."""
    return mock.Mock(vendor=name)


class TestBoundedTextField:
    """Column type, migration serialization, and bound validation of BoundedTextField."""

    def test_db_type_postgres_is_text(self):
        """PostgreSQL keeps the plain text column type."""
        field = BoundedTextField(sql_server_max_length=255)
        connection = mock.Mock(vendor='postgresql', data_types={'TextField': 'text'})
        connection.ops.quote_name = lambda n: n
        assert field.db_type(connection) == 'text'

    def test_db_type_mssql_is_nvarchar(self):
        """SQL Server gets nvarchar sized to the bound."""
        assert BoundedTextField(sql_server_max_length=255).db_type(_vendor('microsoft')) == 'nvarchar(255)'

    def test_deconstruct_round_trip(self):
        """deconstruct() keeps the bound and leaves out the implied validator."""
        field = BoundedTextField(null=True, unique=True, sql_server_max_length=64)
        name, path, args, kwargs = field.deconstruct()
        assert path == 'ansible_base.lib.fields.BoundedTextField'
        assert kwargs['sql_server_max_length'] == 64
        assert 'validators' not in kwargs  # the bound validator is implied, not serialized into migrations
        clone = BoundedTextField(*args, **kwargs)
        assert clone.sql_server_max_length == 64
        assert clone.unique
        assert clone.null

    def test_sql_server_max_length_is_required(self):
        """The field cannot be built without a bound."""
        with pytest.raises(TypeError):
            BoundedTextField()

    @pytest.mark.parametrize('bound', [0, 4001, None, True, 1.5, '255'])
    def test_bound_out_of_range_is_e003(self, bound):
        """Invalid bounds report ansible_base.E003 instead of crashing checks."""
        field = BoundedTextField(sql_server_max_length=bound)
        field.name = 'f'
        with mock.patch.object(models.TextField, 'check', return_value=[]):
            errors = field.check()
        assert [e.id for e in errors] == ['ansible_base.E003']

    @pytest.mark.parametrize('bound', [1, 4000])
    def test_bound_in_range_is_clean(self, bound):
        """Bounds at either end of the valid range report no errors."""
        field = BoundedTextField(sql_server_max_length=bound)
        with mock.patch.object(models.TextField, 'check', return_value=[]):
            assert field.check() == []


class TestSQLServerMaxLengthValidator:
    """SQLServerMaxLengthValidator enforcement per database vendor."""

    def test_not_enforced_on_postgres(self):
        """Over-length values are accepted on PostgreSQL."""
        with mock.patch('ansible_base.lib.fields.connection', _vendor('postgresql')):
            SQLServerMaxLengthValidator(3)('x' * 100)

    def test_enforced_on_mssql(self):
        """Over-length values are rejected on SQL Server with code max_length."""
        validator = SQLServerMaxLengthValidator(3)
        with mock.patch('ansible_base.lib.fields.connection', _vendor('microsoft')):
            validator('abc')
            with pytest.raises(ValidationError) as exc:
                validator('abcd')
        assert exc.value.code == 'max_length'

    def test_counts_utf16_code_units(self):
        """Characters outside the BMP count as two UTF-16 code units."""
        validator = SQLServerMaxLengthValidator(2)
        with mock.patch('ansible_base.lib.fields.connection', _vendor('microsoft')):
            validator('éé')  # two BMP characters fit
            with pytest.raises(ValidationError):
                validator('\U0001f600x')  # a surrogate pair is two code units, plus one

    def test_field_carries_validator(self):
        """The field attaches a validator with its own bound."""
        field = BoundedTextField(sql_server_max_length=10)
        assert any(isinstance(v, SQLServerMaxLengthValidator) and v.sql_server_max_length == 10 for v in field.validators)

    def test_drf_model_serializer_picks_up_validator(self):
        """DRF ModelSerializer fields inherit the validator without serializer changes."""

        class Meta:
            """Serialize only Role.singleton_name."""

            model = Role
            fields = ['singleton_name']

        serializer_class = type('RoleSerializer', (serializers.ModelSerializer,), {'Meta': Meta})
        field = serializer_class().fields['singleton_name']
        assert any(isinstance(v, SQLServerMaxLengthValidator) for v in field.validators)


class TestAdoptedFields:
    """AWX model fields that were switched to BoundedTextField."""

    def test_role_singleton_name(self):
        """Role.singleton_name is bounded at 255."""
        field = Role._meta.get_field('singleton_name')
        assert isinstance(field, BoundedTextField)
        assert field.db_type(_vendor('microsoft')) == 'nvarchar(255)'

    def test_role_ancestor_entry_role_field(self):
        """RoleAncestorEntry.role_field is bounded at 255."""
        field = RoleAncestorEntry._meta.get_field('role_field')
        assert isinstance(field, BoundedTextField)
        assert field.db_type(_vendor('microsoft')) == 'nvarchar(255)'

    @pytest.mark.parametrize('model_name, field_name', [('Role', 'singleton_name'), ('RoleAncestorEntry', 'role_field')])
    def test_migration_uses_dab_field(self, model_name, field_name):
        """Historical and live fields use DAB's class and serialize identically."""
        migration = import_module('awx.main.migrations.0002_squashed_v300_release')
        operation = next(op for op in migration.Migration.operations if getattr(op, 'name', None) == model_name)
        field = dict(operation.fields)[field_name]
        model = {'Role': Role, 'RoleAncestorEntry': RoleAncestorEntry}[model_name]
        live_field = model._meta.get_field(field_name)
        assert type(field) is BoundedTextField
        assert field.deconstruct()[1:] == live_field.deconstruct()[1:]


class TestChecks:
    """The awx.E002 and awx.E004 system checks."""

    def test_awx_models_are_clean(self):
        """No AWX model violates awx.E002 or awx.E004 today, so CI catches new violations."""
        assert awx_checks.check_textfield_indexed_is_bounded(None) == []
        assert awx_checks.check_bounded_textfield_index_key_size(None) == []

    @isolate_apps('django.contrib.contenttypes')
    def test_e002_variants(self):
        """awx.E002 flags each way a plain TextField can be indexed, and skips bounded or unindexed fields."""

        class Plain(models.Model):
            """Model with TextFields indexed through every supported mechanism."""

            unique_text = models.TextField(unique=True)
            indexed_text = models.TextField(db_index=True)
            meta_indexed = models.TextField()
            expr_indexed = models.TextField()
            together = models.TextField()
            other = models.IntegerField()
            unindexed = models.TextField()
            bounded = BoundedTextField(unique=True, sql_server_max_length=10)

            class Meta:
                """Indexes by field, by descending field, by expression, and by unique_together."""

                app_label = 'contenttypes'
                indexes = [models.Index(fields=['-meta_indexed']), models.Index(models.functions.Lower('expr_indexed'), name='expr_idx')]
                unique_together = [('together', 'other')]

        with mock.patch.object(awx_checks, '_awx_models', return_value=[Plain]):
            errors = awx_checks.check_textfield_indexed_is_bounded(None)
        flagged = {e.msg.split()[0] for e in errors}
        assert {e.id for e in errors} == {'awx.E002'}
        assert flagged == {f'contenttypes.Plain.{n}' for n in ('unique_text', 'indexed_text', 'meta_indexed', 'expr_indexed', 'together')}

    @isolate_apps('django.contrib.contenttypes')
    def test_e004_single_and_composite(self):
        """awx.E004 flags single and composite keys over the 1700-byte budget, and allows keys within it."""

        class Wide(models.Model):
            """Model with bounded keys on both sides of the SQL Server index-size budget."""

            too_wide = BoundedTextField(unique=True, sql_server_max_length=851)
            fits = BoundedTextField(db_index=True, sql_server_max_length=848)
            a = BoundedTextField(sql_server_max_length=800)
            b = models.CharField(max_length=50)
            c = models.BigIntegerField()

            class Meta:
                """A composite index that mixes bounded, char, and integer columns."""

                app_label = 'contenttypes'
                indexes = [models.Index(fields=['a', 'b', 'c'], name='wide_idx')]

        with mock.patch.object(awx_checks, '_awx_models', return_value=[Wide]):
            errors = awx_checks.check_bounded_textfield_index_key_size(None)
        assert {e.id for e in errors} == {'awx.E004'}
        msgs = sorted(e.msg for e in errors)
        assert msgs == [
            'contenttypes.Wide key wide_idx needs 1712 bytes of SQL Server index key',
            'contenttypes.Wide.too_wide needs 1702 bytes of SQL Server index key',
        ]

    def test_scope_is_awx_apps_only(self):
        """The checks inspect AWX apps and leave DAB and Django apps alone."""
        labels = {m._meta.app_label for m in awx_checks._awx_models()}
        assert 'main' in labels
        assert not labels & {'dab_rbac', 'dab_resource_registry', 'auth', 'contenttypes'}

    @pytest.mark.parametrize(
        'key',
        [models.Index('role_field', name='plain_string_idx'), models.UniqueConstraint(models.F('role_field'), name='plain_f_unique')],
    )
    def test_e002_root_f_expression(self, key):
        """Positional strings and root F expressions are checked without flatten()."""
        with (
            mock.patch.object(awx_checks, '_awx_models', return_value=[Role]),
            mock.patch.object(Role._meta, 'indexes', [key] if isinstance(key, models.Index) else []),
            mock.patch.object(Role._meta, 'constraints', [key] if isinstance(key, models.UniqueConstraint) else []),
        ):
            errors = awx_checks.check_textfield_indexed_is_bounded(None)
            assert [error.id for error in errors] == ['awx.E002']
            assert 'Role.role_field' in errors[0].msg
            assert awx_checks.check_bounded_textfield_index_key_size(None) == []

    @pytest.mark.parametrize('bound', [None, True, 1.5, '255'])
    def test_e004_invalid_bound_does_not_crash(self, bound):
        """DAB's E003 owns malformed bounds; AWX's width check still completes."""
        with (
            mock.patch.object(awx_checks, '_awx_models', return_value=[Role]),
            mock.patch.object(Role._meta.get_field('singleton_name'), 'sql_server_max_length', bound),
            mock.patch.object(Role._meta, 'indexes', [models.Index('singleton_name', name='invalid_bound_idx')]),
        ):
            assert awx_checks.check_bounded_textfield_index_key_size(None) == []

    @pytest.mark.parametrize('use_tz, expected_datetime_width', [(True, 10), (False, 8)])
    def test_widths_match_mssql_django(self, use_tz, expected_datetime_width):
        """Account for char(32), datetimeoffset/datetime2, and double precision."""
        with override_settings(USE_TZ=use_tz):
            assert awx_checks._index_key_width(models.UUIDField()) == 32
            assert awx_checks._index_key_width(models.DateTimeField()) == expected_datetime_width
            assert awx_checks._index_key_width(models.DateField()) == 3
            assert awx_checks._index_key_width(models.FloatField()) == 8

    @pytest.mark.parametrize('field, bound', [(models.UUIDField(), 835), (models.DateTimeField(), 846), (models.FloatField(), 847)])
    @isolate_apps('django.contrib.contenttypes')
    def test_e004_mixed_column_widths(self, field, bound):
        """An oversized mixed key is rejected even when the text column fits alone."""

        class Mixed(models.Model):
            """A unique key avoids adding the clustered key to the width."""

            name = BoundedTextField(sql_server_max_length=bound)
            other = field

            class Meta:
                """Combine text and a fixed-width column in a unique constraint."""

                app_label = 'contenttypes'
                constraints = [models.UniqueConstraint(fields=['name', 'other'], name='mixed_unique')]

        with override_settings(USE_TZ=True), mock.patch.object(awx_checks, '_awx_models', return_value=[Mixed]):
            errors = awx_checks.check_bounded_textfield_index_key_size(None)
        assert [error.id for error in errors] == ['awx.E004']
        assert 'mixed_unique needs 1702 bytes' in errors[0].msg

    @pytest.mark.parametrize('bound, expected_errors', [(848, 0), (849, 1)])
    def test_e004_nonunique_index_includes_primary_key(self, bound, expected_errors):
        """A non-unique index carries Role's four-byte clustered primary key."""
        with (
            mock.patch.object(awx_checks, '_awx_models', return_value=[Role]),
            mock.patch.object(Role._meta.get_field('singleton_name'), 'sql_server_max_length', bound),
            mock.patch.object(Role._meta, 'indexes', [models.Index('singleton_name', name='nonunique_idx')]),
        ):
            errors = awx_checks.check_bounded_textfield_index_key_size(None)
        assert len(errors) == expected_errors
        if errors:
            assert errors[0].id == 'awx.E004'
            assert 'nonunique_idx needs 1702 bytes' in errors[0].msg

    def test_e004_field_index_includes_primary_key(self):
        """Field-level db_index follows the same clustered-key accounting."""
        field = Role._meta.get_field('singleton_name')
        with (
            mock.patch.object(awx_checks, '_awx_models', return_value=[Role]),
            mock.patch.object(field, 'sql_server_max_length', 849),
            mock.patch.object(field, 'unique', False),
        ):
            errors = awx_checks.check_bounded_textfield_index_key_size(None)
        assert [error.id for error in errors] == ['awx.E004']
        assert 'Role.singleton_name needs 1702 bytes' in errors[0].msg

    @pytest.mark.parametrize('key_type', ['field', 'constraint', 'together'])
    def test_e004_unique_key_excludes_primary_key(self, key_type):
        """Unique keys keep the clustered key in included columns outside the budget."""
        with (
            mock.patch.object(awx_checks, '_awx_models', return_value=[Role]),
            mock.patch.object(Role._meta.get_field('singleton_name'), 'sql_server_max_length', 850),
            mock.patch.object(Role._meta, 'constraints', [models.UniqueConstraint('singleton_name', name='unique_name')] if key_type == 'constraint' else []),
            mock.patch.object(Role._meta, 'unique_together', [('singleton_name',)] if key_type == 'together' else []),
        ):
            assert awx_checks.check_bounded_textfield_index_key_size(None) == []

    @pytest.mark.parametrize('bound, expected_errors', [(448, 0), (449, 1)])
    def test_e004_composite_primary_key_uses_clustered_budget(self, bound, expected_errors):
        """A composite primary key has a 900-byte budget and counts each column once."""
        with (
            mock.patch.object(awx_checks, '_awx_models', return_value=[Role]),
            mock.patch.object(Role._meta, 'pk', models.CompositePrimaryKey('singleton_name', 'id')),
            mock.patch.object(Role._meta.get_field('singleton_name'), 'sql_server_max_length', bound),
            mock.patch.object(Role._meta, 'indexes', [models.Index('singleton_name', 'id', name='pk_index')]),
        ):
            errors = awx_checks.check_bounded_textfield_index_key_size(None)
        assert len(errors) == expected_errors
        if errors:
            assert errors[0].id == 'awx.E004'
            assert 'primary key needs 902 bytes' in errors[0].msg

    def test_e002_composite_primary_key(self):
        """Plain text columns in a composite primary key must also be bounded."""
        with (
            mock.patch.object(awx_checks, '_awx_models', return_value=[Role]),
            mock.patch.object(Role._meta, 'pk', models.CompositePrimaryKey('role_field', 'id')),
        ):
            errors = awx_checks.check_textfield_indexed_is_bounded(None)
        assert [error.id for error in errors] == ['awx.E002']
        assert 'Role.role_field' in errors[0].msg

    def test_mssql_tag_registration(self):
        """AWX checks run both by default and with --tag mssql, like DAB's checks."""
        from django.core.checks.registry import registry

        for check in [awx_checks.check_textfield_indexed_is_bounded, awx_checks.check_bounded_textfield_index_key_size]:
            assert check in registry.registered_checks
            assert 'mssql' in check.tags
