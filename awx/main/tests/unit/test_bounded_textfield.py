from importlib import import_module
from unittest import mock

import pytest

from django.core.exceptions import ValidationError
from django.db import models
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

    @pytest.mark.parametrize('bound', [0, 4001])
    def test_bound_out_of_range_is_e003(self, bound):
        """Bounds outside 1-4000 report ansible_base.E003."""
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
            fits = BoundedTextField(db_index=True, sql_server_max_length=850)
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
            'contenttypes.Wide key wide_idx needs 1708 bytes of SQL Server index key',
            'contenttypes.Wide.too_wide needs 1702 bytes of SQL Server index key',
        ]

    def test_scope_is_awx_apps_only(self):
        """The checks inspect AWX apps and leave DAB and Django apps alone."""
        labels = {m._meta.app_label for m in awx_checks._awx_models()}
        assert 'main' in labels
        assert not labels & {'dab_rbac', 'dab_resource_registry', 'auth', 'contenttypes'}
