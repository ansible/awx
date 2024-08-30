import pytest

from django_test_migrations.plan import all_migrations, nodes_to_tuples
from django.utils.timezone import now

"""
Most tests that live in here can probably be deleted at some point. They are mainly
for a developer. When AWX versions that users upgrade from falls out of support that
is when migration tests can be deleted. This is also a good time to squash. Squashing
will likely mess with the tests that live here.

The smoke test should be kept in here. The smoke test ensures that our migrations
continue to work when sqlite is the backing database (vs. the default DB of postgres).
"""


@pytest.mark.django_db
class TestMigrationSmoke:
    def test_happy_path(self, migrator):
        """
        This smoke test runs all the migrations.

        Example of how to use django-test-migration to invoke particular migration(s)
        while weaving in object creation and assertions.

        Note that this is more than just an example. It is a smoke test because it runs ALL
        the migrations. Our "normal" unit tests subvert the migrations running because it is slow.
        """
        migration_nodes = all_migrations('default')
        migration_tuples = nodes_to_tuples(migration_nodes)
        final_migration = migration_tuples[-1]

        migrator.apply_initial_migration(('main', None))
        # I just picked a newish migration at the time of writing this.
        # If someone from the future finds themselves here because the are squashing migrations
        # it is fine to change the 0180_... below to some other newish migration
        intermediate_state = migrator.apply_tested_migration(('main', '0180_add_hostmetric_fields'))

        Instance = intermediate_state.apps.get_model('main', 'Instance')
        # Create any old object in the database
        Instance.objects.create(hostname='foobar', node_type='control')

        final_state = migrator.apply_tested_migration(final_migration)
        Instance = final_state.apps.get_model('main', 'Instance')
        assert Instance.objects.filter(hostname='foobar').count() == 1

    def test_receptor_address(self, migrator):
        old_state = migrator.apply_initial_migration(('main', '0188_add_bitbucket_dc_webhook'))
        Instance = old_state.apps.get_model('main', 'Instance')
        for i in range(3):
            Instance.objects.create(hostname=f'foobar{i}', node_type='hop')
        foo = Instance.objects.create(hostname='foo', node_type='execution', listener_port=1234)
        bar = Instance.objects.create(hostname='bar', node_type='execution', listener_port=None)
        bar.peers.add(foo)

        new_state = migrator.apply_tested_migration(
            ('main', '0189_inbound_hop_nodes'),
        )
        Instance = new_state.apps.get_model('main', 'Instance')
        ReceptorAddress = new_state.apps.get_model('main', 'ReceptorAddress')

        # We can now test how our migration worked, new field is there:
        assert ReceptorAddress.objects.filter(address='foo', port=1234).count() == 1
        assert not ReceptorAddress.objects.filter(address='bar').exists()

        bar = Instance.objects.get(hostname='bar')
        fooaddr = ReceptorAddress.objects.get(address='foo')

        bar_peers = bar.peers.all()
        assert len(bar_peers) == 1
        assert fooaddr in bar_peers

    def test_migrate_DAB_RBAC(self, migrator):
        old_state = migrator.apply_initial_migration(('main', '0190_alter_inventorysource_source_and_more'))
        Organization = old_state.apps.get_model('main', 'Organization')
        Team = old_state.apps.get_model('main', 'Team')
        User = old_state.apps.get_model('auth', 'User')

        org = Organization.objects.create(name='arbitrary-org', created=now(), modified=now())
        user = User.objects.create(username='random-user')
        org.read_role.members.add(user)
        org.member_role.members.add(user)

        team = Team.objects.create(name='arbitrary-team', organization=org, created=now(), modified=now())
        team.member_role.members.add(user)

        new_state = migrator.apply_tested_migration(
            ('main', '0192_custom_roles'),
        )

        RoleUserAssignment = new_state.apps.get_model('dab_rbac', 'RoleUserAssignment')
        assert RoleUserAssignment.objects.filter(user=user.id, object_id=org.id).exists()
        assert RoleUserAssignment.objects.filter(user=user.id, role_definition__name='Controller Organization Member', object_id=org.id).exists()
        assert RoleUserAssignment.objects.filter(user=user.id, role_definition__name='Controller Team Member', object_id=team.id).exists()

        # Regression testing for bug that comes from current vs past models mismatch
        RoleDefinition = new_state.apps.get_model('dab_rbac', 'RoleDefinition')
        assert not RoleDefinition.objects.filter(name='Organization Organization Admin').exists()
        # Test special cases in managed role creation
        assert not RoleDefinition.objects.filter(name='Organization Team Admin').exists()
        assert not RoleDefinition.objects.filter(name='Organization InstanceGroup Admin').exists()

        # Test that a removed EE model permission has been deleted
        new_state = migrator.apply_tested_migration(
            ('main', '0195_EE_permissions'),
        )
        DABPermission = new_state.apps.get_model('dab_rbac', 'DABPermission')
        assert not DABPermission.objects.filter(codename='view_executionenvironment').exists()
