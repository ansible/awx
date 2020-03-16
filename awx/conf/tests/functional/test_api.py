import pytest
from unittest import mock

from rest_framework import serializers

from awx.api.versioning import reverse
from awx.main.utils.encryption import decrypt_field
from awx.conf import fields
from awx.conf.registry import settings_registry
from awx.conf.models import Setting
from awx.sso import fields as sso_fields


@pytest.fixture
def dummy_setting():
    class context_manager(object):
        def __init__(self, name, **kwargs):
            self.name = name
            self.kwargs = kwargs

        def __enter__(self):
            settings_registry.register(self.name, **(self.kwargs))

        def __exit__(self, *args):
            settings_registry.unregister(self.name)

    return context_manager


@pytest.fixture
def dummy_validate():
    class context_manager(object):
        def __init__(self, category_slug, func):
            self.category_slug = category_slug
            self.func = func

        def __enter__(self):
            settings_registry.register_validate(self.category_slug, self.func)

        def __exit__(self, *args):
            settings_registry.unregister_validate(self.category_slug)

    return context_manager


@pytest.mark.django_db
def test_non_admin_user_does_not_see_categories(api_request, dummy_setting, normal_user):
    with dummy_setting(
        'FOO_BAR',
        field_class=fields.IntegerField,
        category='FooBar',
        category_slug='foobar'
    ):
        response = api_request(
            'get',
            reverse('api:setting_category_list',
                    kwargs={'version': 'v2'})
        )
        assert response.data['results']
        response = api_request(
            'get',
            reverse('api:setting_category_list',
                    kwargs={'version': 'v2'}),
            user=normal_user
        )
        assert not response.data['results']


@pytest.mark.django_db
def test_setting_singleton_detail_retrieve(api_request, dummy_setting):
    with dummy_setting(
        'FOO_BAR_1',
        field_class=fields.IntegerField,
        category='FooBar',
        category_slug='foobar'
    ), dummy_setting(
        'FOO_BAR_2',
        field_class=fields.IntegerField,
        category='FooBar',
        category_slug='foobar'
    ):
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        assert response.status_code == 200
        assert 'FOO_BAR_1' in response.data and response.data['FOO_BAR_1'] is None
        assert 'FOO_BAR_2' in response.data and response.data['FOO_BAR_2'] is None


@pytest.mark.django_db
def test_setting_singleton_detail_invalid_retrieve(api_request, dummy_setting, normal_user):
    with dummy_setting(
        'FOO_BAR_1',
        field_class=fields.IntegerField,
        category='FooBar',
        category_slug='foobar'
    ), dummy_setting(
        'FOO_BAR_2',
        field_class=fields.IntegerField,
        category='FooBar',
        category_slug='foobar'
    ):
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'barfoo'})
        )
        assert response.status_code == 404
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'}),
            user = normal_user
        )
        assert response.status_code == 403


@pytest.mark.django_db
def test_setting_signleton_retrieve_hierachy(api_request, dummy_setting):
    with dummy_setting(
        'FOO_BAR',
        field_class=fields.IntegerField,
        default=0,
        category='FooBar',
        category_slug='foobar'
    ):
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        assert response.data['FOO_BAR'] == 0
        s = Setting(key='FOO_BAR', value=1)
        s.save()
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        assert response.data['FOO_BAR'] == 1


@pytest.mark.django_db
def test_setting_singleton_retrieve_readonly(api_request, dummy_setting):
    with dummy_setting(
        'FOO_BAR',
        field_class=fields.IntegerField,
        read_only=True,
        default=2,
        category='FooBar',
        category_slug='foobar'
    ):
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        assert response.data['FOO_BAR'] == 2


@pytest.mark.django_db
def test_setting_singleton_update(api_request, dummy_setting):
    with dummy_setting(
        'FOO_BAR',
        field_class=fields.IntegerField,
        category='FooBar',
        category_slug='foobar'
    ), mock.patch('awx.conf.views.handle_setting_changes'):
        api_request(
            'patch',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'}),
            data={'FOO_BAR': 3}
        )
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        assert response.data['FOO_BAR'] == 3
        api_request(
            'patch',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'}),
            data={'FOO_BAR': 4}
        )
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        assert response.data['FOO_BAR'] == 4


@pytest.mark.django_db
def test_setting_singleton_update_hybriddictfield_with_forbidden(api_request, dummy_setting):
    # Some HybridDictField subclasses have a child of _Forbidden,
    # indicating that only the defined fields can be filled in.  Make
    # sure that the _Forbidden validator doesn't get used for the
    # fields.  See also https://github.com/ansible/awx/issues/4099.
    with dummy_setting(
        'FOO_BAR',
        field_class=sso_fields.SAMLOrgAttrField,
        category='FooBar',
        category_slug='foobar',
    ), mock.patch('awx.conf.views.handle_setting_changes'):
        api_request(
            'patch',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'}),
            data={'FOO_BAR': {'saml_admin_attr': 'Admins', 'saml_attr': 'Orgs'}}
        )
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        assert response.data['FOO_BAR'] == {'saml_admin_attr': 'Admins', 'saml_attr': 'Orgs'}


@pytest.mark.django_db
def test_setting_singleton_update_dont_change_readonly_fields(api_request, dummy_setting):
    with dummy_setting(
        'FOO_BAR',
        field_class=fields.IntegerField,
        read_only=True,
        default=4,
        category='FooBar',
        category_slug='foobar'
    ), mock.patch('awx.conf.views.handle_setting_changes'):
        api_request(
            'patch',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'}),
            data={'FOO_BAR': 5}
        )
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        assert response.data['FOO_BAR'] == 4


@pytest.mark.django_db
def test_setting_singleton_update_dont_change_encrypted_mark(api_request, dummy_setting):
    with dummy_setting(
        'FOO_BAR',
        field_class=fields.CharField,
        encrypted=True,
        category='FooBar',
        category_slug='foobar'
    ), mock.patch('awx.conf.views.handle_setting_changes'):
        api_request(
            'patch',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'}),
            data={'FOO_BAR': 'password'}
        )
        assert Setting.objects.get(key='FOO_BAR').value.startswith('$encrypted$')
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        assert response.data['FOO_BAR'] == '$encrypted$'
        api_request(
            'patch',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'}),
            data={'FOO_BAR': '$encrypted$'}
        )
        assert decrypt_field(Setting.objects.get(key='FOO_BAR'), 'value') == 'password'
        api_request(
            'patch',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'}),
            data={'FOO_BAR': 'new_pw'}
        )
        assert decrypt_field(Setting.objects.get(key='FOO_BAR'), 'value') == 'new_pw'


@pytest.mark.django_db
def test_setting_singleton_update_runs_custom_validate(api_request, dummy_setting, dummy_validate):

    def func_raising_exception(serializer, attrs):
        raise serializers.ValidationError('Error')

    with dummy_setting(
        'FOO_BAR',
        field_class=fields.IntegerField,
        category='FooBar',
        category_slug='foobar'
    ), dummy_validate(
        'foobar', func_raising_exception
    ), mock.patch('awx.conf.views.handle_setting_changes'):
        response = api_request(
            'patch',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'}),
            data={'FOO_BAR': 23}
        )
        assert response.status_code == 400


@pytest.mark.django_db
def test_setting_singleton_delete(api_request, dummy_setting):
    with dummy_setting(
        'FOO_BAR',
        field_class=fields.IntegerField,
        category='FooBar',
        category_slug='foobar'
    ), mock.patch('awx.conf.views.handle_setting_changes'):
        api_request(
            'delete',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        assert not response.data['FOO_BAR']


@pytest.mark.django_db
def test_setting_singleton_delete_no_read_only_fields(api_request, dummy_setting):
    with dummy_setting(
        'FOO_BAR',
        field_class=fields.IntegerField,
        read_only=True,
        default=23,
        category='FooBar',
        category_slug='foobar'
    ), mock.patch('awx.conf.views.handle_setting_changes'):
        api_request(
            'delete',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        response = api_request(
            'get',
            reverse('api:setting_singleton_detail', kwargs={'category_slug': 'foobar'})
        )
        assert response.data['FOO_BAR'] == 23

