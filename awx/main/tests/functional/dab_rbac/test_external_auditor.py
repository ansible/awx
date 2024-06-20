import pytest

from django.apps import apps

from ansible_base.rbac.managed import SystemAuditor
from ansible_base.rbac import permission_registry

from awx.main.access import check_user_access, get_user_queryset
from awx.api.versioning import reverse


@pytest.fixture
def ext_auditor_rd():
    info = SystemAuditor(overrides={'name': 'Alien Auditor', 'shortname': 'ext_auditor'})
    rd, _ = info.get_or_create(apps)
    return rd


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
@pytest.mark.parametrize('model', permission_registry.all_registered_models)
class TestExternalAuditorRole:
    def test_access_can_read_method(self, obj_factory, model, ext_auditor_rd, rando):
        fixture_name = model._meta.verbose_name.replace(' ', '_')
        obj = obj_factory(fixture_name)

        assert check_user_access(rando, model, 'read', obj) is False
        ext_auditor_rd.give_global_permission(rando)
        assert check_user_access(rando, model, 'read', obj) is True

    def test_access_get_queryset(self, obj_factory, model, ext_auditor_rd, rando):
        fixture_name = model._meta.verbose_name.replace(' ', '_')
        obj = obj_factory(fixture_name)

        assert obj not in get_user_queryset(rando, model)
        ext_auditor_rd.give_global_permission(rando)
        assert obj in get_user_queryset(rando, model)

    def test_global_list(self, obj_factory, model, ext_auditor_rd, rando, get):
        fixture_name = model._meta.verbose_name.replace(' ', '_')
        obj_factory(fixture_name)

        url = reverse(f'api:{fixture_name}_list')
        r = get(url, user=rando, expect=200)
        initial_ct = r.data['count']

        ext_auditor_rd.give_global_permission(rando)
        r = get(url, user=rando, expect=200)
        assert r.data['count'] == initial_ct + 1

    def test_detail_view(self, obj_factory, model, ext_auditor_rd, rando, get):
        fixture_name = model._meta.verbose_name.replace(' ', '_')
        obj = obj_factory(fixture_name)

        url = reverse(f'api:{fixture_name}_detail', kwargs={'pk': obj.pk})
        r = get(url, user=rando, expect=403)  # TODO: should be 401

        ext_auditor_rd.give_global_permission(rando)
        r = get(url, user=rando, expect=200)


# TODO: test non-RBAC models, jobs, ad hoc commands, etc.
