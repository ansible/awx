import pytest

from django.test import TransactionTestCase

from awx.main.access import UserAccess
from awx.main.models import User, Organization, Inventory


@pytest.mark.django_db
class TestSysAuditorTransactional(TransactionTestCase):
    def rando(self):
        return User.objects.create(username='rando', password='rando', email='rando@com.com')

    def inventory(self):
        org = Organization.objects.create(name='org')
        inv = Inventory.objects.create(name='inv', organization=org)
        return inv

    def test_auditor_caching(self):
        rando = self.rando()
        with self.assertNumQueries(1):
            v = rando.is_system_auditor
        assert not v
        with self.assertNumQueries(0):
            v = rando.is_system_auditor
        assert not v

    def test_auditor_setter(self):
        rando = self.rando()
        inventory = self.inventory()
        rando.is_system_auditor = True
        assert rando in inventory.read_role

    def test_refresh_with_set(self):
        rando = self.rando()
        rando.is_system_auditor = True
        assert rando.is_system_auditor
        rando.is_system_auditor = False
        assert not rando.is_system_auditor


@pytest.mark.django_db
def test_system_auditor_is_system_auditor(system_auditor):
    assert system_auditor.is_system_auditor


@pytest.mark.django_db
def test_system_auditor_can_modify_self(system_auditor):
    access = UserAccess(system_auditor)
    assert access.can_change(obj=system_auditor, data=dict(is_system_auditor='true'))


@pytest.mark.django_db
def test_user_queryset(user):
    u = user('pete', False)

    access = UserAccess(u)
    qs = access.get_queryset()
    assert qs.count() == 1


@pytest.mark.django_db
def test_user_accessible_objects(user, organization):
    '''
    We cannot directly use accessible_objects for User model because
    both editing and read permissions are obligated to complex business logic
    '''
    admin = user('admin', False)
    u = user('john', False)
    access = UserAccess(admin)
    assert access.get_queryset().count() == 1  # can only see himself

    organization.member_role.members.add(u)
    organization.member_role.members.add(admin)
    assert access.get_queryset().count() == 2

    organization.member_role.members.remove(u)
    assert access.get_queryset().count() == 1


@pytest.mark.django_db
def test_org_admin_create_sys_auditor(org_admin):
    access = UserAccess(org_admin)
    assert not access.can_add(data=dict(
        username='new_user', password="pa$$sowrd", email="asdf@redhat.com",
        is_system_auditor='true'))


@pytest.mark.django_db
def test_org_admin_edit_sys_auditor(org_admin, alice, organization):
    organization.member_role.members.add(alice)
    access = UserAccess(org_admin)
    assert not access.can_change(obj=alice, data=dict(is_system_auditor='true'))
