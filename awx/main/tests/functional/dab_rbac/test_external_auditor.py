import pytest

from django.apps import apps

from ansible_base.rbac.managed import SystemAuditor
from ansible_base.rbac import permission_registry

from awx.main.access import check_user_access, get_user_queryset
from awx.main.models import User, AdHocCommandEvent
from awx.api.versioning import reverse


@pytest.fixture
def ext_auditor_rd():
    info = SystemAuditor(overrides={'name': 'Alien Auditor', 'shortname': 'ext_auditor'})
    rd, _ = info.get_or_create(apps)
    return rd


@pytest.fixture
def ext_auditor(ext_auditor_rd):
    u = User.objects.create(username='external-auditor-user')
    ext_auditor_rd.give_global_permission(u)
    return u


@pytest.fixture
def obj_factory(request):
    def _rf(fixture_name):
        obj = request.getfixturevalue(fixture_name)

        # special case to make obj organization-scoped
        if obj._meta.model_name == 'executionenvironment':
            obj.organization = request.getfixturevalue('organization')
            obj.save(update_fields=['organization'])

        return obj

    return _rf


@pytest.mark.django_db
def test_access_qs_external_auditor(ext_auditor_rd, rando, job_template):
    ext_auditor_rd.give_global_permission(rando)
    jt_cls = apps.get_model('main', 'JobTemplate')
    ujt_cls = apps.get_model('main', 'UnifiedJobTemplate')
    assert job_template in jt_cls.access_qs(rando)
    assert job_template.id in jt_cls.access_ids_qs(rando)
    assert job_template.id in ujt_cls.accessible_pk_qs(rando, 'read_role')


@pytest.mark.django_db
@pytest.mark.parametrize('model', sorted(permission_registry.all_registered_models, key=lambda cls: cls._meta.model_name))
class TestExternalAuditorRoleAllModels:
    def test_access_can_read_method(self, obj_factory, model, ext_auditor, rando):
        fixture_name = model._meta.verbose_name.replace(' ', '_')
        obj = obj_factory(fixture_name)

        assert check_user_access(rando, model, 'read', obj) is False
        assert check_user_access(ext_auditor, model, 'read', obj) is True

    def test_access_get_queryset(self, obj_factory, model, ext_auditor, rando):
        fixture_name = model._meta.verbose_name.replace(' ', '_')
        obj = obj_factory(fixture_name)

        assert obj not in get_user_queryset(rando, model)
        assert obj in get_user_queryset(ext_auditor, model)

    def test_global_list(self, obj_factory, model, ext_auditor, rando, get):
        fixture_name = model._meta.verbose_name.replace(' ', '_')
        obj_factory(fixture_name)

        url = reverse(f'api:{fixture_name}_list')
        r = get(url, user=rando, expect=200)
        initial_ct = r.data['count']

        r = get(url, user=ext_auditor, expect=200)
        assert r.data['count'] == initial_ct + 1

        if fixture_name in ('job_template', 'workflow_job_template'):
            url = reverse('api:unified_job_template_list')
            r = get(url, user=rando, expect=200)
            initial_ct = r.data['count']

            r = get(url, user=ext_auditor, expect=200)
            assert r.data['count'] == initial_ct + 1

    def test_detail_view(self, obj_factory, model, ext_auditor, rando, get):
        fixture_name = model._meta.verbose_name.replace(' ', '_')
        obj = obj_factory(fixture_name)

        url = reverse(f'api:{fixture_name}_detail', kwargs={'pk': obj.pk})
        get(url, user=rando, expect=403)  # NOTE: should be 401
        get(url, user=ext_auditor, expect=200)


@pytest.mark.django_db
class TestExternalAuditorNonRoleModels:
    def test_ad_hoc_command_view(self, ad_hoc_command_factory, rando, ext_auditor, get):
        """The AdHocCommandAccess class references is_system_auditor

        this is to prove it works with other system-level view roles"""
        ad_hoc_command = ad_hoc_command_factory()
        url = reverse('api:ad_hoc_command_list')
        r = get(url, user=rando, expect=200)
        assert r.data['count'] == 0
        r = get(url, user=ext_auditor, expect=200)
        assert r.data['count'] == 1
        assert r.data['results'][0]['id'] == ad_hoc_command.id

        event = AdHocCommandEvent.objects.create(ad_hoc_command=ad_hoc_command)
        url = reverse('api:ad_hoc_command_ad_hoc_command_events_list', kwargs={'pk': ad_hoc_command.id})
        r = get(url, user=rando, expect=403)
        r = get(url, user=ext_auditor, expect=200)
        assert r.data['count'] == 1

        url = reverse('api:ad_hoc_command_event_detail', kwargs={'pk': event.id})
        r = get(url, user=rando, expect=403)
        r = get(url, user=ext_auditor, expect=200)
        assert r.data['id'] == event.id
