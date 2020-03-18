import pytest
from unittest import mock

from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from rest_framework.exceptions import ParseError

from awx.main.access import (
    BaseAccess,
    check_superuser,
    JobTemplateAccess,
    WorkflowJobTemplateAccess,
    SystemJobTemplateAccess,
    vars_are_encrypted
)

from awx.main.models import (
    Credential,
    CredentialType,
    Inventory,
    Project,
    Role,
    Organization,
)


@pytest.fixture
def user_unit():
    return User(username='rando', password='raginrando', email='rando@redhat.com')


class TestRelatedFieldAccess:
    @pytest.fixture
    def resource_good(self, mocker):
        good_role = mocker.MagicMock(__contains__=lambda self, user: True)
        return mocker.MagicMock(related=mocker.MagicMock(admin_role=good_role),
                                admin_role=good_role)

    @pytest.fixture
    def resource_bad(self, mocker):
        bad_role = mocker.MagicMock(__contains__=lambda self, user: False)
        return mocker.MagicMock(related=mocker.MagicMock(admin_role=bad_role),
                                admin_role=bad_role)

    @pytest.fixture
    def access(self, user_unit):
        return BaseAccess(user_unit)

    def test_new_optional_fail(self, access, resource_bad, mocker):
        """
        User tries to create a new resource, but lacks permission
        to the related resource they provided
        """
        data = {'related': resource_bad}
        assert not access.check_related('related', mocker.MagicMock, data)

    def test_new_with_bad_data(self, access, mocker):
        data = {'related': 3.1415}
        with pytest.raises(ParseError):
            access.check_related('related', mocker.MagicMock(), data)

    def test_new_mandatory_fail(self, access, mocker):
        access.user.is_superuser = False
        assert not access.check_related(
            'related', mocker.MagicMock, {}, mandatory=True)
        assert not access.check_related(
            'related', mocker.MagicMock, {'resource': None}, mandatory=True)

    def test_existing_no_op(self, access, resource_bad, mocker):
        """
        User edits a resource, but does not change related field
        lack of access to related field does not block action
        """
        data = {'related': resource_bad.related}
        assert access.check_related(
            'related', mocker.MagicMock, data, obj=resource_bad)
        assert access.check_related(
            'related', mocker.MagicMock, {}, obj=resource_bad)

    def test_existing_required_access(self, access, resource_bad, mocker):
        # no-op actions, but mandatory kwarg requires check to pass
        assert not access.check_related(
            'related', mocker.MagicMock, {}, obj=resource_bad, mandatory=True)
        assert not access.check_related(
            'related', mocker.MagicMock, {'related': resource_bad.related},
            obj=resource_bad, mandatory=True)

    def test_existing_no_access_to_current(
            self, access, resource_good, resource_bad, mocker):
        """
        User gives a valid related resource (like organization), but does
        not have access to _existing_ related resource, so deny action
        """
        data = {'related': resource_good}
        assert not access.check_related(
            'related', mocker.MagicMock, data, obj=resource_bad)

    def test_existing_no_access_to_new(
            self, access, resource_good, resource_bad, mocker):
        data = {'related': resource_bad}
        assert not access.check_related(
            'related', mocker.MagicMock, data, obj=resource_good)

    def test_existing_not_allowed_to_remove(self, access, resource_bad, mocker):
        data = {'related': None}
        assert not access.check_related(
            'related', mocker.MagicMock, data, obj=resource_bad)

    def test_existing_not_null_null(self, access, mocker):
        resource = mocker.MagicMock(related=None)
        data = {'related': None}
        # Not changing anything by giving null when it is already-null
        # important for PUT requests
        assert access.check_related(
            'related', mocker.MagicMock, data, obj=resource, mandatory=True)


def test_encrypted_vars_detection():
    assert vars_are_encrypted({
        'aaa': {'b': 'c'},
        'alist': [],
        'test_var_eight': '$encrypted$UTF8$AESCBC$Z0FBQUF...==',
        'test_var_five': 'four',
    })
    assert not vars_are_encrypted({
        'aaa': {'b': 'c'},
        'alist': [],
        'test_var_five': 'four',
    })


@pytest.fixture
def job_template_with_ids(job_template_factory):
    # Create non-persisted objects with IDs to send to job_template_factory
    ssh_type = CredentialType(kind='ssh')
    credential = Credential(id=1, pk=1, name='testcred', credential_type=ssh_type)

    net_type = CredentialType(kind='net')
    net_cred = Credential(id=2, pk=2, name='testnetcred', credential_type=net_type)

    cloud_type = CredentialType(kind='aws')
    cloud_cred = Credential(id=3, pk=3, name='testcloudcred', credential_type=cloud_type)

    inv = Inventory(id=11, pk=11, name='testinv')
    proj = Project(id=14, pk=14, name='testproj')

    jt_objects = job_template_factory(
        'testJT', project=proj, inventory=inv, credential=credential,
        cloud_credential=cloud_cred, network_credential=net_cred,
        persisted=False)
    jt = jt_objects.job_template
    jt.organization = Organization(id=1, pk=1, name='fooOrg')
    return jt


def test_superuser(mocker):
    user = mocker.MagicMock(spec=User, id=1, is_superuser=True)
    access = BaseAccess(user)

    can_add = check_superuser(BaseAccess.can_add)
    assert can_add(access, None) is True


def test_not_superuser(mocker):
    user = mocker.MagicMock(spec=User, id=1, is_superuser=False)
    access = BaseAccess(user)

    can_add = check_superuser(BaseAccess.can_add)
    assert can_add(access, None) is False


def test_jt_existing_values_are_nonsensitive(job_template_with_ids, user_unit):
    """Assure that permission checks are not required if submitted data is
    identical to what the job template already has."""

    data = model_to_dict(job_template_with_ids, exclude=['unifiedjobtemplate_ptr'])
    access = JobTemplateAccess(user_unit)

    assert access.changes_are_non_sensitive(job_template_with_ids, data)


def test_change_jt_sensitive_data(job_template_with_ids, mocker, user_unit):
    """Assure that can_add is called with all ForeignKeys."""

    class RoleReturnsTrue(Role):
        class Meta:
            proxy = True
            
        def __contains__(self, accessor):
            return True

    job_template_with_ids.admin_role = RoleReturnsTrue()
    job_template_with_ids.organization.job_template_admin_role = RoleReturnsTrue()

    inv2 = Inventory()
    inv2.use_role = RoleReturnsTrue()
    data = {'inventory': inv2}

    access = JobTemplateAccess(user_unit)

    assert not access.changes_are_non_sensitive(job_template_with_ids, data)

    job_template_with_ids.inventory.use_role = RoleReturnsTrue()
    job_template_with_ids.project.use_role = RoleReturnsTrue()
    assert access.can_change(job_template_with_ids, data)


def mock_raise_none(self, add_host=False, feature=None, check_expiration=True):
    return None


def test_jt_can_add_bad_data(user_unit):
    "Assure that no server errors are returned if we call JT can_add with bad data"
    access = JobTemplateAccess(user_unit)
    assert not access.can_add({'asdf': 'asdf'})


class TestWorkflowAccessMethods:
    @pytest.fixture
    def workflow(self, workflow_job_template_factory):
        objects = workflow_job_template_factory('test_workflow', persisted=False)
        return objects.workflow_job_template

    def test_workflow_can_add(self, workflow, user_unit):
        organization = Organization(name='test-org')
        workflow.organization = organization
        organization.workflow_admin_role = Role()

        def mock_get_object(Class, **kwargs):
            if Class == Organization:
                return organization
            else:
                raise Exception('Item requested has not been mocked')

        access = WorkflowJobTemplateAccess(user_unit)
        with mock.patch('awx.main.models.rbac.Role.__contains__', return_value=True):
            with mock.patch('awx.main.access.get_object_or_400', mock_get_object):
                assert access.can_add({'organization': 1})



def test_user_capabilities_method():
    """Unit test to verify that the user_capabilities method will defer
    to the appropriate sub-class methods of the access classes.
    Note that normal output is True/False, but a string is returned
    in these tests to establish uniqueness.
    """

    class FooAccess(BaseAccess):
        def can_change(self, obj, data):
            return 'bar'

        def can_copy(self, obj):
            return 'foo'

    user = User(username='auser')
    foo_access = FooAccess(user)
    foo = object()
    foo_capabilities = foo_access.get_user_capabilities(foo, ['edit', 'copy'])
    assert foo_capabilities == {
        'edit': 'bar',
        'copy': 'foo'
    }


def test_system_job_template_can_start(mocker):
    user = mocker.MagicMock(spec=User, id=1, is_system_auditor=True, is_superuser=False)
    assert user.is_system_auditor
    access = SystemJobTemplateAccess(user)
    assert not access.can_start(None)

    user.is_superuser = True
    access = SystemJobTemplateAccess(user)
    assert access.can_start(None)
