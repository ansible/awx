import pytest
import mock

from django.contrib.contenttypes.models import ContentType

from awx.main.models.rbac import (
    Role,
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    ROLE_SINGLETON_SYSTEM_AUDITOR
)
from awx.main.models import Organization, JobTemplate, Project

from awx.main.fields import (
    ImplicitRoleField,
    is_implicit_parent
)


def apply_fake_roles(obj):
    '''
    Creates an un-saved role for all the implicit role fields on an object
    '''
    for fd in obj._meta.fields:
        if not isinstance(fd, ImplicitRoleField):
            continue
        r = Role(role_field=fd.name)
        setattr(obj, fd.name, r)
        with mock.patch('django.contrib.contenttypes.fields.GenericForeignKey.get_content_type') as mck_ct:
            mck_ct.return_value = ContentType(model=obj._meta.model_name)
            r.content_object = obj


@pytest.fixture
def system_administrator():
    return Role(
        role_field=ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
        singleton_name=ROLE_SINGLETON_SYSTEM_ADMINISTRATOR
    )


@pytest.fixture
def system_auditor():
    return Role(
        role_field=ROLE_SINGLETON_SYSTEM_AUDITOR,
        singleton_name=ROLE_SINGLETON_SYSTEM_AUDITOR
    )


@pytest.fixture
def organization():
    o = Organization(name='unit-test-org')
    apply_fake_roles(o)
    return o


@pytest.fixture
def project(organization):
    p = Project(name='unit-test-proj', organization=organization)
    apply_fake_roles(p)
    return p


@pytest.fixture
def job_template(project):
    jt = JobTemplate(name='unit-test-jt', project=project)
    apply_fake_roles(jt)
    return jt


class TestIsImplicitParent:
    '''
    Tests to confirm that `is_implicit_parent` gives the right answers
    '''
    def test_sys_admin_implicit_parent(self, organization, system_administrator):
        assert is_implicit_parent(
            parent_role=system_administrator,
            child_role=organization.admin_role
        )


    def test_admin_is_parent_of_member_role(self, organization):
        assert is_implicit_parent(
            parent_role=organization.admin_role,
            child_role=organization.member_role
        )

    def test_member_is_not_parent_of_admin_role(self, organization):
        assert not is_implicit_parent(
            parent_role=organization.member_role,
            child_role=organization.admin_role
        )

    def test_second_level_implicit_parent_role(self, job_template, organization):
        assert is_implicit_parent(
            parent_role=organization.admin_role,
            child_role=job_template.admin_role
        )

    def test_second_level_is_not_an_implicit_parent_role(self, job_template, organization):
        assert not is_implicit_parent(
            parent_role=organization.member_role,
            child_role=job_template.admin_role
        )
