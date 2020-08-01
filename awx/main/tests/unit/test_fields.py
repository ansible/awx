# -*- coding: utf-8 -*-
import pytest

from django.core.exceptions import ValidationError
from django.apps import apps
from django.db.models.fields.related import ForeignKey
from django.db.models.fields.related_descriptors import (
    ReverseManyToOneDescriptor,
    ForwardManyToOneDescriptor
)

from rest_framework.serializers import ValidationError as DRFValidationError

from awx.main.models import Credential, CredentialType, BaseModel
from awx.main.fields import JSONSchemaField, ImplicitRoleField, ImplicitRoleDescriptor


@pytest.mark.parametrize('schema, given, message', [
    (
        {  # immitates what the CredentialType injectors field is
            "additionalProperties": False,
            "type": "object",
            "properties": {
                "extra_vars": {
                    "additionalProperties": False,
                    "type": "object"
                }
            }
        },
        {'extra_vars': ['duck', 'horse']},
        "list provided in relative path ['extra_vars'], expected dict"
    ),
    (
        {  # immitates what the CredentialType injectors field is
            "additionalProperties": False,
            "type": "object",
        },
        ['duck', 'horse'],
        "list provided, expected dict"
    ),
])
def test_custom_error_messages(schema, given, message):
    instance = BaseModel()

    class MockFieldSubclass(JSONSchemaField):
        def schema(self, model_instance):
            return schema

    field = MockFieldSubclass()

    with pytest.raises(ValidationError) as exc:
        field.validate(given, instance)

    assert message == exc.value.error_list[0].message


@pytest.mark.parametrize('input_, valid', [
    ({}, True),
    ({'fields': []}, True),
    ({'fields': {}}, False),
    ({'fields': 123}, False),
    ({'fields': [{'id': 'username', 'label': 'Username', 'foo': 'bar'}]}, False),
    ({'fields': [{'id': 'username', 'label': 'Username'}]}, True),
    ({'fields': [{'id': 'username', 'label': 'Username', 'type': 'string'}]}, True),
    ({'fields': [{'id': 'username', 'label': 'Username', 'help_text': 1}]}, False),
    ({'fields': [{'id': 'username', 'label': 'Username', 'help_text': 'Help Text'}]}, True),  # noqa
    ({'fields': [{'id': 'username', 'label': 'Username'}, {'id': 'username', 'label': 'Username 2'}]}, False),  # noqa
    ({'fields': [{'id': '$invalid$', 'label': 'Invalid', 'type': 'string'}]}, False),  # noqa
    ({'fields': [{'id': 'password', 'label': 'Password', 'type': 'invalid-type'}]}, False),
    ({'fields': [{'id': 'ssh_key', 'label': 'SSH Key', 'type': 'string', 'format': 'ssh_private_key'}]}, True),  # noqa
    ({'fields': [{'id': 'flag', 'label': 'Some Flag', 'type': 'boolean'}]}, True),
    ({'fields': [{'id': 'flag', 'label': 'Some Flag', 'type': 'boolean', 'choices': ['a', 'b']}]}, False),
    ({'fields': [{'id': 'flag', 'label': 'Some Flag', 'type': 'boolean', 'secret': True}]}, False),
    ({'fields': [{'id': 'certificate', 'label': 'Cert', 'multiline': True}]}, True),
    ({'fields': [{'id': 'certificate', 'label': 'Cert', 'multiline': True, 'type': 'boolean'}]}, False),  # noqa
    ({'fields': [{'id': 'certificate', 'label': 'Cert', 'multiline': 'bad'}]}, False),  # noqa
    ({'fields': [{'id': 'token', 'label': 'Token', 'secret': True}]}, True),
    ({'fields': [{'id': 'token', 'label': 'Token', 'secret': 'bad'}]}, False),
    ({'fields': [{'id': 'token', 'label': 'Token', 'ask_at_runtime': True}]}, True),
    ({'fields': [{'id': 'token', 'label': 'Token', 'ask_at_runtime': 'bad'}]}, False),  # noqa
    ({'fields': [{'id': 'become_method', 'label': 'Become', 'choices': 'not-a-list'}]}, False),  # noqa
    ({'fields': [{'id': 'become_method', 'label': 'Become', 'choices': []}]}, False),
    ({'fields': [{'id': 'become_method', 'label': 'Become', 'choices': ['su', 'sudo']}]}, True),  # noqa
    ({'fields': [{'id': 'become_method', 'label': 'Become', 'choices': ['dup', 'dup']}]}, False),  # noqa
    ({'fields': [{'id': 'tower', 'label': 'Reserved!', }]}, False),  # noqa
])
def test_cred_type_input_schema_validity(input_, valid):
    type_ = CredentialType(
        kind='cloud',
        name='SomeCloud',
        managed_by_tower=True,
        inputs=input_
    )
    field = CredentialType._meta.get_field('inputs')
    if valid is False:
        with pytest.raises(ValidationError):
            field.clean(input_, type_)
    else:
        field.clean(input_, type_)


@pytest.mark.parametrize('injectors, valid', [
    ({}, True),
    ({'invalid-injector': {}}, False),
    ({'file': 123}, False),
    ({'file': {}}, True),
    # Uses credential inputs inside of unnamed file contents
    ({'file': {'template': '{{username}}'}}, True),
    # Uses named file
    ({'file': {'template.username': '{{username}}'}}, True),
    # Uses multiple named files
    ({'file': {'template.username': '{{username}}', 'template.password': '{{pass}}'}}, True),
    # Use of unnamed file mutually exclusive with use of named files
    ({'file': {'template': '{{username}}', 'template.password': '{{pass}}'}}, False),
    # References non-existant named file
    ({'env': {'FROM_FILE': "{{tower.filename.cert}}"}}, False),
    # References unnamed file, but a file was never defined
    ({'env': {'FROM_FILE': "{{tower.filename}}"}}, False),
    # Cannot reference tower namespace itself (what would this return??)
    ({'env': {'FROM_FILE': "{{tower}}"}}, False),
    # References filename of a named file
    ({'file': {'template.cert': '{{awx_secret}}'}, 'env': {'FROM_FILE': "{{tower.filename.cert}}"}}, True),
    # With named files, `tower.filename` is another namespace, so it cannot be referenced
    ({'file': {'template.cert': '{{awx_secret}}'}, 'env': {'FROM_FILE': "{{tower.filename}}"}}, False),
    # With an unnamed file, `tower.filename` is just the filename
    ({'file': {'template': '{{awx_secret}}'}, 'env': {'THE_FILENAME': "{{tower.filename}}"}}, True),
    ({'file': {'foo': 'bar'}}, False),
    ({'env': 123}, False),
    ({'env': {}}, True),
    ({'env': {'AWX_SECRET': '{{awx_secret}}'}}, True),
    ({'env': {'AWX_SECRET_99': '{{awx_secret}}'}}, True),
    ({'env': {'99': '{{awx_secret}}'}}, False),
    ({'env': {'AWX_SECRET=': '{{awx_secret}}'}}, False),
    ({'env': {'ANSIBLE_SETTING': '{{awx_secret}}'}}, False),
    ({'env': {'DRAGON': u'🐉'}}, False),
    ({'env': {u'🐉': 'DRAGON'}}, False),
    ({'extra_vars': 123}, False),
    ({'extra_vars': {}}, True),
    ({'extra_vars': {'hostname': '{{host}}'}}, True),
    ({'extra_vars': {'hostname_99': '{{host}}'}}, True),
    ({'extra_vars': {'99': '{{host}}'}}, False),
    ({'extra_vars': {'99=': '{{host}}'}}, False),
])
def test_cred_type_injectors_schema(injectors, valid):
    type_ = CredentialType(
        kind='cloud',
        name='SomeCloud',
        managed_by_tower=True,
        inputs={
            'fields': [
                {'id': 'username', 'type': 'string', 'label': '_'},
                {'id': 'pass', 'type': 'string', 'label': '_'},
                {'id': 'awx_secret', 'type': 'string', 'label': '_'},
                {'id': 'host', 'type': 'string', 'label': '_'},
            ]
        },
        injectors=injectors
    )
    field = CredentialType._meta.get_field('injectors')
    if valid is False:
        with pytest.raises(ValidationError):
            field.clean(injectors, type_)
    else:
        field.clean(injectors, type_)


@pytest.mark.parametrize('inputs', [
    ['must-be-a-dict'],
    {'user': 'wrong-key'},
    {'username': 1},
    {'username': 1.5},
    {'username': ['a', 'b', 'c']},
    {'username': {'a': 'b'}},
    {'flag': 1},
    {'flag': 1.5},
    {'flag': ['a', 'b', 'c']},
    {'flag': {'a': 'b'}},
    {'flag': 'some-string'},
])
def test_credential_creation_validation_failure(inputs):
    type_ = CredentialType(
        kind='cloud',
        name='SomeCloud',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': 'Username for SomeCloud',
                'type': 'string'
            },{
                'id': 'flag',
                'label': 'Some Boolean Flag',
                'type': 'boolean'
            }]
        }
    )
    cred = Credential(credential_type=type_, name="Bob's Credential",
                      inputs=inputs)
    field = cred._meta.get_field('inputs')

    with pytest.raises(Exception) as e:
        field.validate(inputs, cred)
    assert e.type in (ValidationError, DRFValidationError)


def test_implicit_role_field_parents():
    """This assures that every ImplicitRoleField only references parents
    which are relationships that actually exist
    """
    app_models = apps.get_app_config('main').get_models()
    for cls in app_models:
        for field in cls._meta.get_fields():
            if not isinstance(field, ImplicitRoleField):
                continue

            if not field.parent_role:
                continue

            field_names = field.parent_role
            if type(field_names) is not list:
                field_names = [field_names]

            for field_name in field_names:
                # this type of specification appears to have been considered
                # at some point, but does not exist in the app and would
                # need support and tests built out for it
                assert not isinstance(field_name, tuple)
                # also used to be a thing before py3 upgrade
                assert not isinstance(field_name, bytes)
                # this is always coherent
                if field_name.startswith('singleton:'):
                    continue
                # separate out parent role syntax
                field_name, sep, field_attr = field_name.partition('.')
                # now make primary assertion, that specified paths exist
                assert hasattr(cls, field_name)

                # inspect in greater depth
                second_field = cls._meta.get_field(field_name)
                second_field_descriptor = getattr(cls, field_name)
                # all supported linkage types
                assert isinstance(second_field_descriptor, (
                    ReverseManyToOneDescriptor,  # not currently used
                    ImplicitRoleDescriptor,
                    ForwardManyToOneDescriptor
                ))
                # only these links are supported
                if field_attr:
                    if isinstance(second_field_descriptor, ReverseManyToOneDescriptor):
                        assert type(second_field) is ForeignKey
                        rel_model = cls._meta.get_field(field_name).related_model
                        third_field = getattr(rel_model, field_attr)
                        # expecting for related_model.foo_role, test role field type
                        assert isinstance(third_field, ImplicitRoleDescriptor)
                else:
                    # expecting simple format of foo_role
                    assert type(second_field) is ImplicitRoleField
