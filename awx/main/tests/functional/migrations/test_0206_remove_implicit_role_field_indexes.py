from importlib import import_module

from django.db import migrations


class TestRemoveImplicitRoleFieldIndexes:
    """Test migration 0206_remove_implicit_role_field_indexes."""

    def setup_method(self):
        self.migration_module = import_module('awx.main.migrations.0206_remove_implicit_role_field_indexes')

    def test_migration_dependencies(self):
        Migration = self.migration_module.Migration
        assert ('main', '0205_add_ordering_to_instancegroup_and_workflow_nodes') in Migration.dependencies

    def test_migration_uses_alter_field(self):
        Migration = self.migration_module.Migration
        for op in Migration.operations:
            assert isinstance(op, migrations.AlterField)

    def test_migration_targets_correct_field_count(self):
        assert len(self.migration_module.IMPLICIT_ROLE_FIELDS) == 38

    def test_all_altered_fields_disable_db_index(self):
        Migration = self.migration_module.Migration
        for op in Migration.operations:
            assert op.field.db_index is False

    def test_does_not_target_dab_rbac_fields(self):
        Migration = self.migration_module.Migration
        for op in Migration.operations:
            assert 'dab_rbac' not in op.model_name

    def test_covers_all_model_tables(self):
        expected_models = {
            'credential',
            'instancegroup',
            'inventory',
            'jobtemplate',
            'organization',
            'project',
            'team',
            'workflowjobtemplate',
        }
        actual_models = {model for model, _, _ in self.migration_module.IMPLICIT_ROLE_FIELDS}
        assert actual_models == expected_models

    def test_field_class_sets_db_index_false(self):
        """Verify the field class itself defaults to db_index=False."""
        from awx.main.fields import ImplicitRoleField

        field = ImplicitRoleField(parent_role='test')
        assert field.db_index is False
