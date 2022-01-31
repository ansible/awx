# Python
import pytest
from unittest import mock
from contextlib import contextmanager

from awx.main.models import Credential, UnifiedJob, Instance
from awx.main.tests.factories import (
    create_organization,
    create_job_template,
    create_instance,
    create_instance_group,
    create_notification_template,
    create_survey_spec,
    create_workflow_job_template,
)

from django.core.cache import cache
from django.conf import settings


def pytest_addoption(parser):
    parser.addoption("--genschema", action="store_true", default=False, help="execute schema validator")


def pytest_configure(config):
    import sys

    sys._called_from_test = True


def pytest_unconfigure(config):
    import sys

    del sys._called_from_test


@pytest.fixture
def mock_access():
    @contextmanager
    def access_given_class(TowerClass):
        try:
            mock_instance = mock.MagicMock(__name__='foobar')
            MockAccess = mock.MagicMock(return_value=mock_instance)
            the_patch = mock.patch.dict('awx.main.access.access_registry', {TowerClass: MockAccess}, clear=False)
            the_patch.__enter__()
            yield mock_instance
        finally:
            the_patch.__exit__()

    return access_given_class


@pytest.fixture
def job_template_factory():
    return create_job_template


@pytest.fixture
def organization_factory():
    return create_organization


@pytest.fixture
def notification_template_factory():
    return create_notification_template


@pytest.fixture
def survey_spec_factory():
    return create_survey_spec


@pytest.fixture
def instance_factory():
    return create_instance


@pytest.fixture
def instance_group_factory():
    return create_instance_group


@pytest.fixture
def controlplane_instance_group(instance_factory, instance_group_factory):
    """There always has to be a controlplane instancegroup and at least one instance in it"""
    return create_instance_group(settings.DEFAULT_CONTROL_PLANE_QUEUE_NAME, create_instance('hybrid-1', node_type='hybrid', capacity=500))


@pytest.fixture
def default_instance_group(instance_factory, instance_group_factory):
    return create_instance_group("default", instances=[create_instance("hostA", node_type='execution')])


@pytest.fixture
def control_instance():
    '''Control instance in the controlplane automatic IG'''
    inst = create_instance('control-1', node_type='control', capacity=500)
    return inst


@pytest.fixture
def control_instance_low_capacity():
    '''Control instance in the controlplane automatic IG that has low capacity'''
    inst = create_instance('control-1', node_type='control', capacity=5)
    return inst


@pytest.fixture
def execution_instance():
    '''Execution node in the automatic default IG'''
    ig = create_instance_group('default')
    inst = create_instance('receptor-1', node_type='execution', capacity=500)
    ig.instances.add(inst)
    return inst


@pytest.fixture
def hybrid_instance():
    '''Hybrid node in the default controlplane IG'''
    inst = create_instance('hybrid-1', node_type='hybrid', capacity=500)
    return inst


@pytest.fixture
def job_template_with_survey_passwords_factory(job_template_factory):
    def rf(persisted):
        "Returns job with linked JT survey with password survey questions"
        objects = job_template_factory(
            'jt',
            organization='org1',
            survey=[
                {'variable': 'submitter_email', 'type': 'text', 'default': 'foobar@redhat.com'},
                {'variable': 'secret_key', 'default': '6kQngg3h8lgiSTvIEb21', 'type': 'password'},
                {'variable': 'SSN', 'type': 'password'},
            ],
            persisted=persisted,
        )
        return objects.job_template

    return rf


@pytest.fixture
def job_with_secret_key_unit(job_with_secret_key_factory):
    return job_with_secret_key_factory(persisted=False)


@pytest.fixture
def workflow_job_template_factory():
    return create_workflow_job_template


@pytest.fixture
def job_template_with_survey_passwords_unit(job_template_with_survey_passwords_factory):
    return job_template_with_survey_passwords_factory(persisted=False)


@pytest.fixture
def mock_cache():
    class MockCache(object):
        cache = {}

        def get(self, key, default=None):
            return self.cache.get(key, default)

        def set(self, key, value, timeout=60):
            self.cache[key] = value

        def delete(self, key):
            del self.cache[key]

    return MockCache()


def pytest_runtest_teardown(item, nextitem):
    # clear Django cache at the end of every test ran
    # NOTE: this should not be memcache (as it is deprecated), nor should it be redis.
    # This is a local test cache, so we want every test to start with an empty cache
    cache.clear()


@pytest.fixture(scope='session', autouse=True)
def mock_external_credential_input_sources():
    # Credential objects query their related input sources on initialization.
    # We mock that behavior out of credentials by default unless we need to
    # test it explicitly.
    with mock.patch.object(Credential, 'dynamic_input_fields', new=[]) as _fixture:
        yield _fixture


@pytest.fixture(scope='session', autouse=True)
def mock_has_unpartitioned_events():
    # has_unpartitioned_events determines if there are any events still
    # left in the old, unpartitioned job events table. In order to work,
    # this method looks up when the partition migration occurred. When
    # Django's unit tests run, however, there will be no record of the migration.
    # We mock this out to circumvent the migration query.
    with mock.patch.object(UnifiedJob, 'has_unpartitioned_events', new=False) as _fixture:
        yield _fixture


@pytest.fixture(scope='session', autouse=True)
def mock_get_event_queryset_no_job_created():
    """
    SQLite friendly since partitions aren't supported. Do not add the faked job_created field to the filter. If we do, it will result in an sql query for the
    job_created field. That field does not actually exist in a non-partition scenario.
    """

    def event_qs(self):
        kwargs = {self.event_parent_key: self.id}
        return self.event_class.objects.filter(**kwargs)

    with mock.patch.object(UnifiedJob, 'get_event_queryset', lambda self: event_qs(self)) as _fixture:
        yield _fixture


@pytest.fixture
def mock_me():
    me_mock = mock.MagicMock(return_value=Instance(id=1, hostname=settings.CLUSTER_HOST_ID, uuid='00000000-0000-0000-0000-000000000000'))
    with mock.patch.object(Instance.objects, 'me', me_mock):
        yield
