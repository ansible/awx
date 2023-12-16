from unittest import mock
import inspect

import pytest

from crum import impersonate

from awx.main.models import Host, JobHostSummary, OAuth2Application, OAuth2AccessToken

from awx.api.generics import GenericAPIView

from django.db.models import ManyToManyField


@pytest.mark.django_db
def test_modified_by_not_changed(inventory):
    with impersonate(None):
        host = Host.objects.create(name='foo', inventory=inventory)
        assert host.modified_by == None
        host.variables = {'foo': 'bar'}
        with mock.patch('django.db.models.Model.save') as save_mock:
            host.save(update_fields=['variables'])
            save_mock.assert_called_once_with(update_fields=['variables'])


@pytest.mark.django_db
def test_modified_by_changed(inventory, alice):
    with impersonate(None):
        host = Host.objects.create(name='foo', inventory=inventory)
        assert host.modified_by == None
    with impersonate(alice):
        host.variables = {'foo': 'bar'}
        with mock.patch('django.db.models.Model.save') as save_mock:
            host.save(update_fields=['variables'])
            save_mock.assert_called_once_with(update_fields=['variables', 'modified_by'])
        assert host.modified_by == alice


@pytest.mark.django_db
def test_created_by(inventory, alice):
    with impersonate(alice):
        host = Host.objects.create(name='foo', inventory=inventory)
        assert host.created_by == alice
    with impersonate(None):
        host = Host.objects.create(name='bar', inventory=inventory)
        assert host.created_by == None


def get_subclasses_recursive(cls):
    ret = set()

    for sub_cls in cls.__subclasses__():
        ret.add(sub_cls)
        for sub_cls_prime in get_subclasses_recursive(sub_cls):
            ret.add(sub_cls_prime)

    return ret


@pytest.mark.django_db
def test_help_text_is_filled():
    """
    This is a catch-all test that assures that all model fields have
    help_text filled in.
    You likely encounter failures of this test if you add a new field
    or a model, this test is simply politely asking you to add help_text
    for all the fields you add.
    """
    errors = {}
    ct = 0
    total_ct = 0
    field_ct = 0
    seen_models = set()
    seen_fields = set()
    # get the models used by views so we only consider those that affect OPTIONS
    from awx.api.urls import urls  # NOQA

    for view_cls in get_subclasses_recursive(GenericAPIView):
        if not hasattr(view_cls, 'model'):
            continue
        model_cls = view_cls.model
        # Skip if seen, and skip if not a real model as some views use dynamic @property
        if (model_cls in seen_models) or (not inspect.isclass(model_cls)):
            continue
        # model exceptions:
        # host summaries are mostly Ansible-core analog fields so skip for now
        # fields from the oauth2 library that we do not define
        if issubclass(model_cls, (JobHostSummary, OAuth2AccessToken, OAuth2Application)):
            continue
        seen_models.add(model_cls)
        if model_cls._meta.app_label != 'main':
            continue
        for field in model_cls._meta.get_fields():
            if not hasattr(field, 'help_text'):
                continue
            # Start on app-specific exceptions
            # Roles are not surfaced as direct fields in any scenario
            # the _ptr are internal polymorphic fields
            if (field.name == 'id') or (field.name.endswith('_role')) or (field.name.endswith('_ptr')):
                continue
            # specific exceptions from specific libraries
            if field.name in ('polymorphic_ctype', 'tagged_items'):
                continue
            # fields not shown in serializer for other reasons
            if field.name in ('old_pk',):
                continue
            # ManyToManyField relationships are also not directly surfaced in OPTIONS
            if isinstance(field, ManyToManyField):
                continue
            field_ct += 1
            if not field.help_text:
                # De-duplicate fields
                total_ct += 1
                if field.name in seen_fields:
                    continue
                seen_fields.add(field.name)
                ct += 1
                errors.setdefault(model_cls._meta.verbose_name, [])
                errors[model_cls._meta.verbose_name].append(field.name)
    if errors:
        formatted = '\n'.join([f'{cls}: {fields}' for cls, fields in errors.items()])
        raise Exception(
            f'These fields are missing help text:\n{formatted}\n\n({field_ct} ' f'fields evaluated, {total_ct} in violation, {ct} de-duplicated violations)'
        )
