# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import copy
import json
import re
import urllib.parse

from jinja2 import sandbox, StrictUndefined
from jinja2.exceptions import UndefinedError, TemplateSyntaxError, SecurityError

# Django
from django.contrib.postgres.fields import JSONField as upstream_JSONBField
from django.core import exceptions as django_exceptions
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.signals import (
    post_save,
    post_delete,
)
from django.db.models.signals import m2m_changed
from django.db import models
from django.db.models.fields.related import lazy_related_operation
from django.db.models.fields.related_descriptors import (
    ReverseOneToOneDescriptor,
    ForwardManyToOneDescriptor,
    ManyToManyDescriptor,
    ReverseManyToOneDescriptor,
    create_forward_many_to_many_manager
)
from django.utils.encoding import smart_text
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

# jsonschema
from jsonschema import Draft4Validator, FormatChecker
import jsonschema.exceptions

# Django-JSONField
from jsonfield import JSONField as upstream_JSONField

# DRF
from rest_framework import serializers

# AWX
from awx.main.utils.filters import SmartFilter
from awx.main.utils.encryption import encrypt_value, decrypt_value, get_encryption_key
from awx.main.validators import validate_ssh_private_key
from awx.main.models.rbac import (
    batch_role_ancestor_rebuilding, Role,
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR, ROLE_SINGLETON_SYSTEM_AUDITOR
)
from awx.main.constants import ENV_BLOCKLIST
from awx.main import utils


__all__ = ['AutoOneToOneField', 'ImplicitRoleField', 'JSONField',
           'SmartFilterField', 'OrderedManyToManyField',
           'update_role_parentage_for_instance',
           'is_implicit_parent']


# Provide a (better) custom error message for enum jsonschema validation
def __enum_validate__(validator, enums, instance, schema):
    if instance not in enums:
        yield jsonschema.exceptions.ValidationError(
            _("'{value}' is not one of ['{allowed_values}']").format(
                value=instance, allowed_values="', '".join(enums))
        )


Draft4Validator.VALIDATORS['enum'] = __enum_validate__


class JSONField(upstream_JSONField):

    def db_type(self, connection):
        return 'text'

    def from_db_value(self, value, expression, connection):
        if value in {'', None} and not self.null:
            return {}
        return super(JSONField, self).from_db_value(value, expression, connection)


class JSONBField(upstream_JSONBField):
    def get_prep_lookup(self, lookup_type, value):
        if isinstance(value, str) and value == "null":
            return 'null'
        return super(JSONBField, self).get_prep_lookup(lookup_type, value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if connection.vendor == 'sqlite':
            # sqlite (which we use for tests) does not support jsonb;
            return json.dumps(value, cls=DjangoJSONEncoder)
        return super(JSONBField, self).get_db_prep_value(
            value, connection, prepared
        )

    def from_db_value(self, value, expression, connection):
        # Work around a bug in django-jsonfield
        # https://bitbucket.org/schinckel/django-jsonfield/issues/57/cannot-use-in-the-same-project-as-djangos
        if isinstance(value, str):
            return json.loads(value)
        return value

# Based on AutoOneToOneField from django-annoying:
# https://bitbucket.org/offline/django-annoying/src/a0de8b294db3/annoying/fields.py


class AutoSingleRelatedObjectDescriptor(ReverseOneToOneDescriptor):
    """Descriptor for access to the object from its related class."""

    def __get__(self, instance, instance_type=None):
        try:
            return super(AutoSingleRelatedObjectDescriptor, self).__get__(instance, instance_type)
        except self.related.related_model.DoesNotExist:
            obj = self.related.related_model(**{self.related.field.name: instance})
            obj.save()
            return obj


class AutoOneToOneField(models.OneToOneField):
    """OneToOneField that creates related object if it doesn't exist."""

    def contribute_to_related_class(self, cls, related):
        setattr(cls, related.get_accessor_name(),
                AutoSingleRelatedObjectDescriptor(related))


def resolve_role_field(obj, field):
    ret = []

    field_components = field.split('.', 1)
    if hasattr(obj, field_components[0]):
        obj = getattr(obj, field_components[0])
    else:
        return []

    if obj is None:
        return []

    if len(field_components) == 1:
        # use extremely generous duck typing to accomidate all possible forms
        # of the model that may be used during various migrations
        if obj._meta.model_name != 'role' or obj._meta.app_label != 'main':
            raise Exception(smart_text('{} refers to a {}, not a Role'.format(field, type(obj))))
        ret.append(obj.id)
    else:
        if type(obj) is ManyToManyDescriptor:
            for o in obj.all():
                ret += resolve_role_field(o, field_components[1])
        else:
            ret += resolve_role_field(obj, field_components[1])

    return ret


def is_implicit_parent(parent_role, child_role):
    '''
    Determine if the parent_role is an implicit parent as defined by
    the model definition. This does not include any role parents that
    might have been set by the user.
    '''
    if child_role.content_object is None:
        # The only singleton implicit parent is the system admin being
        # a parent of the system auditor role
        return bool(
            child_role.singleton_name == ROLE_SINGLETON_SYSTEM_AUDITOR and
            parent_role.singleton_name == ROLE_SINGLETON_SYSTEM_ADMINISTRATOR
        )
    # Get the list of implicit parents that were defined at the class level.
    implicit_parents = getattr(
        child_role.content_object.__class__, child_role.role_field
    ).field.parent_role
    if type(implicit_parents) != list:
        implicit_parents = [implicit_parents]

    # Check to see if the role matches any in the implicit parents list
    for implicit_parent_path in implicit_parents:
        if implicit_parent_path.startswith('singleton:'):
            # Singleton role isn't an object role, `singleton_name` uniquely identifies it
            if parent_role.is_singleton() and parent_role.singleton_name == implicit_parent_path[10:]:
                return True
        else:
            # Walk over multiple related objects to obtain the implicit parent
            related_obj = child_role.content_object
            for next_field in implicit_parent_path.split('.'):
                related_obj = getattr(related_obj, next_field)
                if related_obj is None:
                    break
            if related_obj and parent_role == related_obj:
                return True
    return False


def update_role_parentage_for_instance(instance):
    '''update_role_parentage_for_instance
    updates the parents listing for all the roles
    of a given instance if they have changed
    '''
    parents_removed = set()
    parents_added = set()
    for implicit_role_field in getattr(instance.__class__, '__implicit_role_fields'):
        cur_role = getattr(instance, implicit_role_field.name)
        original_parents = set(json.loads(cur_role.implicit_parents))
        new_parents = implicit_role_field._resolve_parent_roles(instance)
        removals = original_parents - new_parents
        if removals:
            cur_role.parents.remove(*list(removals))
            parents_removed.add(cur_role.pk)
        additions = new_parents - original_parents
        if additions:
            cur_role.parents.add(*list(additions))
            parents_added.add(cur_role.pk)
        new_parents_list = list(new_parents)
        new_parents_list.sort()
        new_parents_json = json.dumps(new_parents_list)
        if cur_role.implicit_parents != new_parents_json:
            cur_role.implicit_parents = new_parents_json
            cur_role.save(update_fields=['implicit_parents'])
    return (parents_added, parents_removed)


class ImplicitRoleDescriptor(ForwardManyToOneDescriptor):
    pass


class ImplicitRoleField(models.ForeignKey):
    """Implicitly creates a role entry for a resource"""

    def __init__(self, parent_role=None, *args, **kwargs):
        self.parent_role = parent_role

        kwargs.setdefault('to', 'Role')
        kwargs.setdefault('related_name', '+')
        kwargs.setdefault('null', 'True')
        kwargs.setdefault('editable', False)
        kwargs.setdefault('on_delete', models.CASCADE)
        super(ImplicitRoleField, self).__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(ImplicitRoleField, self).deconstruct()
        kwargs['parent_role'] = self.parent_role
        return name, path, args, kwargs

    def contribute_to_class(self, cls, name):
        super(ImplicitRoleField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, ImplicitRoleDescriptor(self))

        if not hasattr(cls, '__implicit_role_fields'):
            setattr(cls, '__implicit_role_fields', [])
        getattr(cls, '__implicit_role_fields').append(self)

        post_save.connect(self._post_save, cls, True, dispatch_uid='implicit-role-post-save')
        post_delete.connect(self._post_delete, cls, True, dispatch_uid='implicit-role-post-delete')

        function = lambda local, related, field: self.bind_m2m_changed(field, related, local)
        lazy_related_operation(function, cls, "self", field=self)

    def bind_m2m_changed(self, _self, _role_class, cls):
        if not self.parent_role:
            return

        field_names = self.parent_role
        if type(field_names) is not list:
            field_names = [field_names]

        for field_name in field_names:

            if field_name.startswith('singleton:'):
                continue

            field_name, sep, field_attr = field_name.partition('.')
            # Non existent fields will occur if ever a parent model is
            # moved inside a migration, needed for job_template_organization_field
            # migration in particular
            # consistency is assured by unit test awx.main.tests.functional
            field = getattr(cls, field_name, None)

            if field and type(field) is ReverseManyToOneDescriptor or \
               type(field) is ManyToManyDescriptor:

                if '.' in field_attr:
                    raise Exception('Referencing deep roles through ManyToMany fields is unsupported.')

                if type(field) is ReverseManyToOneDescriptor:
                    sender = field.through
                else:
                    sender = field.related.through

                reverse = type(field) is ManyToManyDescriptor
                m2m_changed.connect(self.m2m_update(field_attr, reverse), sender, weak=False)

    def m2m_update(self, field_attr, _reverse):
        def _m2m_update(instance, action, model, pk_set, reverse, **kwargs):
            if action == 'post_add' or action == 'pre_remove':
                if _reverse:
                    reverse = not reverse

                if reverse:
                    for pk in pk_set:
                        obj = model.objects.get(pk=pk)
                        if action == 'post_add':
                            getattr(instance, field_attr).children.add(getattr(obj, self.name))
                        if action == 'pre_remove':
                            getattr(instance, field_attr).children.remove(getattr(obj, self.name))

                else:
                    for pk in pk_set:
                        obj = model.objects.get(pk=pk)
                        if action == 'post_add':
                            getattr(instance, self.name).parents.add(getattr(obj, field_attr))
                        if action == 'pre_remove':
                            getattr(instance, self.name).parents.remove(getattr(obj, field_attr))
        return _m2m_update


    def _post_save(self, instance, created, *args, **kwargs):
        Role_ = utils.get_current_apps().get_model('main', 'Role')
        ContentType_ = utils.get_current_apps().get_model('contenttypes', 'ContentType')
        ct_id = ContentType_.objects.get_for_model(instance).id

        Model = utils.get_current_apps().get_model('main', instance.__class__.__name__)
        latest_instance = Model.objects.get(pk=instance.pk)

        with batch_role_ancestor_rebuilding():
            # Create any missing role objects
            missing_roles = []
            for implicit_role_field in getattr(latest_instance.__class__, '__implicit_role_fields'):
                cur_role = getattr(latest_instance, implicit_role_field.name, None)
                if cur_role is None:
                    missing_roles.append(
                        Role_(
                            role_field=implicit_role_field.name,
                            content_type_id=ct_id,
                            object_id=latest_instance.id
                        )
                    )

            if len(missing_roles) > 0:
                Role_.objects.bulk_create(missing_roles)
                updates = {}
                role_ids = []
                for role in Role_.objects.filter(content_type_id=ct_id, object_id=latest_instance.id):
                    setattr(latest_instance, role.role_field, role)
                    updates[role.role_field] = role.id
                    role_ids.append(role.id)
                type(latest_instance).objects.filter(pk=latest_instance.pk).update(**updates)
                Role.rebuild_role_ancestor_list(role_ids, [])

            update_role_parentage_for_instance(latest_instance)
            instance.refresh_from_db()


    def _resolve_parent_roles(self, instance):
        if not self.parent_role:
            return set()

        paths = self.parent_role if type(self.parent_role) is list else [self.parent_role]
        parent_roles = set()

        for path in paths:
            if path.startswith("singleton:"):
                singleton_name = path[10:]
                Role_ = utils.get_current_apps().get_model('main', 'Role')
                qs = Role_.objects.filter(singleton_name=singleton_name)
                if qs.count() >= 1:
                    role = qs[0]
                else:
                    role = Role_.objects.create(singleton_name=singleton_name, role_field=singleton_name)
                parents = [role.id]
            else:
                parents = resolve_role_field(instance, path)

            for parent in parents:
                parent_roles.add(parent)
        return parent_roles

    def _post_delete(self, instance, *args, **kwargs):
        role_ids = []
        for implicit_role_field in getattr(instance.__class__, '__implicit_role_fields'):
            role_ids.append(getattr(instance, implicit_role_field.name + '_id'))

        Role_ = utils.get_current_apps().get_model('main', 'Role')
        child_ids = [x for x in Role_.parents.through.objects.filter(to_role_id__in=role_ids).distinct().values_list('from_role_id', flat=True)]
        Role_.objects.filter(id__in=role_ids).delete()
        Role.rebuild_role_ancestor_list([], child_ids)


class SmartFilterField(models.TextField):
    def get_prep_value(self, value):
        # Change any false value to none.
        # https://docs.python.org/2/library/stdtypes.html#truth-value-testing
        if not value:
            return None
        value = urllib.parse.unquote(value)
        try:
            SmartFilter().query_from_string(value)
        except RuntimeError as e:
            raise models.base.ValidationError(e)
        return super(SmartFilterField, self).get_prep_value(value)


class JSONSchemaField(JSONBField):
    """
    A JSONB field that self-validates against a defined JSON schema
    (http://json-schema.org).  This base class is intended to be overwritten by
    defining `self.schema`.
    """

    format_checker = FormatChecker()

    # If an empty {} is provided, we still want to perform this schema
    # validation
    empty_values = (None, '')

    def get_default(self):
        return copy.deepcopy(super(JSONBField, self).get_default())

    def schema(self, model_instance):
        raise NotImplementedError()

    def validate(self, value, model_instance):
        super(JSONSchemaField, self).validate(value, model_instance)
        errors = []
        for error in Draft4Validator(
            self.schema(model_instance),
            format_checker=self.format_checker
        ).iter_errors(value):
            if error.validator == 'pattern' and 'error' in error.schema:
                error.message = error.schema['error'].format(instance=error.instance)
            elif error.validator == 'type':
                expected_type = error.validator_value
                if expected_type == 'object':
                    expected_type = 'dict'
                if error.path:
                    error.message = _(
                        '{type} provided in relative path {path}, expected {expected_type}'
                    ).format(path=list(error.path), type=type(error.instance).__name__,
                             expected_type=expected_type)
                else:
                    error.message = _(
                        '{type} provided, expected {expected_type}'
                    ).format(path=list(error.path), type=type(error.instance).__name__,
                             expected_type=expected_type)
            elif error.validator == 'additionalProperties' and hasattr(error, 'path'):
                error.message = _(
                    'Schema validation error in relative path {path} ({error})'
                ).format(path=list(error.path), error=error.message)
            errors.append(error)

        if errors:
            raise django_exceptions.ValidationError(
                [e.message for e in errors],
                code='invalid',
                params={'value': value},
            )


@JSONSchemaField.format_checker.checks('vault_id')
def format_vault_id(value):
    if '@' in value:
        raise jsonschema.exceptions.FormatError('@ is not an allowed character')
    return True


@JSONSchemaField.format_checker.checks('ssh_private_key')
def format_ssh_private_key(value):
    # Sanity check: GCE, in particular, provides JSON-encoded private
    # keys, which developers will be tempted to copy and paste rather
    # than JSON decode.
    #
    # These end in a unicode-encoded final character that gets double
    # escaped due to being in a Python 2 bytestring, and that causes
    # Python's key parsing to barf. Detect this issue and correct it.
    if not value or value == '$encrypted$':
        return True
    if r'\u003d' in value:
        value = value.replace(r'\u003d', '=')
    try:
        validate_ssh_private_key(value)
    except django_exceptions.ValidationError as e:
        raise jsonschema.exceptions.FormatError(e.message)
    return True


@JSONSchemaField.format_checker.checks('url')
def format_url(value):
    try:
        parsed = urllib.parse.urlparse(value)
    except Exception as e:
        raise jsonschema.exceptions.FormatError(str(e))
    if parsed.scheme == '':
        raise jsonschema.exceptions.FormatError(
            'Invalid URL: Missing url scheme (http, https, etc.)'
        )
    if parsed.netloc == '':
        raise jsonschema.exceptions.FormatError(
            'Invalid URL: {}'.format(value)
        )
    return True


class DynamicCredentialInputField(JSONSchemaField):
    """
    Used to validate JSON for
    `awx.main.models.credential:CredentialInputSource().metadata`.

    Metadata for input sources is represented as a dictionary e.g.,
    {'secret_path': '/kv/somebody', 'secret_key': 'password'}

    For the data to be valid, the keys of this dictionary should correspond
    with the metadata field (and datatypes) defined in the associated
    target CredentialType e.g.,
    """

    def schema(self, credential_type):
        # determine the defined fields for the associated credential type
        properties = {}
        for field in credential_type.inputs.get('metadata', []):
            field = field.copy()
            properties[field['id']] = field
            if field.get('choices', []):
                field['enum'] = list(field['choices'])[:]
        return {
            'type': 'object',
            'properties': properties,
            'additionalProperties': False,
        }

    def validate(self, value, model_instance):
        if not isinstance(value, dict):
            return super(DynamicCredentialInputField, self).validate(value, model_instance)

        super(JSONSchemaField, self).validate(value, model_instance)
        credential_type = model_instance.source_credential.credential_type
        errors = {}
        for error in Draft4Validator(
            self.schema(credential_type),
            format_checker=self.format_checker
        ).iter_errors(value):
            if error.validator == 'pattern' and 'error' in error.schema:
                error.message = error.schema['error'].format(instance=error.instance)
            if 'id' not in error.schema:
                # If the error is not for a specific field, it's specific to
                # `inputs` in general
                raise django_exceptions.ValidationError(
                    error.message,
                    code='invalid',
                    params={'value': value},
                )
            errors[error.schema['id']] = [error.message]

        defined_metadata = [field.get('id') for field in credential_type.inputs.get('metadata', [])]
        for field in credential_type.inputs.get('required', []):
            if field in defined_metadata and not value.get(field, None):
                errors[field] = [_('required for %s') % (
                    credential_type.name
                )]

        if errors:
            raise serializers.ValidationError({
                'metadata': errors
            })


class CredentialInputField(JSONSchemaField):
    """
    Used to validate JSON for
    `awx.main.models.credential:Credential().inputs`.

    Input data for credentials is represented as a dictionary e.g.,
    {'api_token': 'abc123', 'api_secret': 'SECRET'}

    For the data to be valid, the keys of this dictionary should correspond
    with the field names (and datatypes) defined in the associated
    CredentialType e.g.,

    {
        'fields': [{
            'id': 'api_token',
            'label': 'API Token',
            'type': 'string'
        }, {
            'id': 'api_secret',
            'label': 'API Secret',
            'type': 'string'
        }]
    }
    """

    def schema(self, model_instance):
        # determine the defined fields for the associated credential type
        properties = {}
        for field in model_instance.credential_type.inputs.get('fields', []):
            field = field.copy()
            properties[field['id']] = field
            if field.get('choices', []):
                field['enum'] = list(field['choices'])[:]
        return {
            'type': 'object',
            'properties': properties,
            'dependencies': model_instance.credential_type.inputs.get('dependencies', {}),
            'additionalProperties': False,
        }

    def validate(self, value, model_instance):
        # decrypt secret values so we can validate their contents (i.e.,
        # ssh_key_data format)

        if not isinstance(value, dict):
            return super(CredentialInputField, self).validate(value,
                                                              model_instance)

        # Backwards compatability: in prior versions, if you submit `null` for
        # a credential field value, it just considers the value an empty string
        for unset in [key for key, v in model_instance.inputs.items() if not v]:
            default_value = model_instance.credential_type.default_for_field(unset)
            if default_value is not None:
                model_instance.inputs[unset] = default_value

        decrypted_values = {}
        for k, v in value.items():
            if all([
                k in model_instance.credential_type.secret_fields,
                v != '$encrypted$',
                model_instance.pk
            ]):
                if not isinstance(model_instance.inputs.get(k), str):
                    raise django_exceptions.ValidationError(
                        _('secret values must be of type string, not {}').format(type(v).__name__),
                        code='invalid',
                        params={'value': v},
                    )
                decrypted_values[k] = utils.decrypt_field(model_instance, k)
            else:
                decrypted_values[k] = v

        # don't allow secrets with $encrypted$ on new object creation
        if not model_instance.pk:
            for field in model_instance.credential_type.secret_fields:
                if value.get(field) == '$encrypted$':
                    raise serializers.ValidationError({
                        self.name: [f'$encrypted$ is a reserved keyword, and cannot be used for {field}.']
                    })

        super(JSONSchemaField, self).validate(decrypted_values, model_instance)
        errors = {}
        for error in Draft4Validator(
            self.schema(model_instance),
            format_checker=self.format_checker
        ).iter_errors(decrypted_values):
            if error.validator == 'pattern' and 'error' in error.schema:
                error.message = error.schema['error'].format(instance=error.instance)
            if error.validator == 'dependencies':
                # replace the default error messaging w/ a better i18n string
                # I wish there was a better way to determine the parameters of
                # this validation failure, but the exception jsonschema raises
                # doesn't include them as attributes (just a hard-coded error
                # string)
                match = re.search(
                    # 'foo' is a dependency of 'bar'
                    r"'"         # apostrophe
                    r"([^']+)"   # one or more non-apostrophes (first group)
                    r"'[\w ]+'"  # one or more words/spaces
                    r"([^']+)",  # second group
                    error.message,
                )
                if match:
                    label, extraneous = match.groups()
                    if error.schema['properties'].get(label):
                        label = error.schema['properties'][label]['label']
                    errors[extraneous] = [
                        _('cannot be set unless "%s" is set') % label
                    ]
                    continue
            if 'id' not in error.schema:
                # If the error is not for a specific field, it's specific to
                # `inputs` in general
                raise django_exceptions.ValidationError(
                    error.message,
                    code='invalid',
                    params={'value': value},
                )
            errors[error.schema['id']] = [error.message]

        defined_fields = model_instance.credential_type.defined_fields

        # `ssh_key_unlock` requirements are very specific and can't be
        # represented without complicated JSON schema
        if (
                model_instance.credential_type.managed_by_tower is True and
                'ssh_key_unlock' in defined_fields
        ):

            # in order to properly test the necessity of `ssh_key_unlock`, we
            # need to know the real value of `ssh_key_data`; for a payload like:
            # {
            #   'ssh_key_data': '$encrypted$',
            #   'ssh_key_unlock': 'do-you-need-me?',
            # }
            # ...we have to fetch the actual key value from the database
            if model_instance.pk and model_instance.inputs.get('ssh_key_data') == '$encrypted$':
                model_instance.inputs['ssh_key_data'] = model_instance.__class__.objects.get(
                    pk=model_instance.pk
                ).inputs.get('ssh_key_data')

            if model_instance.has_encrypted_ssh_key_data and not value.get('ssh_key_unlock'):
                errors['ssh_key_unlock'] = [_('must be set when SSH key is encrypted.')]
            
            if all([
                model_instance.inputs.get('ssh_key_data'),
                value.get('ssh_key_unlock'),
                not model_instance.has_encrypted_ssh_key_data,
                'ssh_key_data' not in errors
            ]):
                errors['ssh_key_unlock'] = [_('should not be set when SSH key is not encrypted.')]

        if errors:
            raise serializers.ValidationError({
                'inputs': errors
            })


class CredentialTypeInputField(JSONSchemaField):
    """
    Used to validate JSON for
    `awx.main.models.credential:CredentialType().inputs`.
    """

    def schema(self, model_instance):
        return {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'required': {
                    'type': 'array',
                    'items': {'type': 'string'}
                },
                'fields':  {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'type': {'enum': ['string', 'boolean']},
                            'format': {'enum': ['ssh_private_key', 'url']},
                            'choices': {
                                'type': 'array',
                                'minItems': 1,
                                'items': {'type': 'string'},
                                'uniqueItems': True
                            },
                            'id': {
                                'type': 'string',
                                'pattern': '^[a-zA-Z_]+[a-zA-Z0-9_]*$',
                                'error': '{instance} is an invalid variable name',
                            },
                            'label': {'type': 'string'},
                            'help_text': {'type': 'string'},
                            'multiline': {'type': 'boolean'},
                            'secret': {'type': 'boolean'},
                            'ask_at_runtime': {'type': 'boolean'},
                            'default': {},
                        },
                        'additionalProperties': False,
                        'required': ['id', 'label'],
                    }
                }
            }
        }

    def validate(self, value, model_instance):
        if isinstance(value, dict) and 'dependencies' in value and \
                not model_instance.managed_by_tower:
            raise django_exceptions.ValidationError(
                _("'dependencies' is not supported for custom credentials."),
                code='invalid',
                params={'value': value},
            )

        super(CredentialTypeInputField, self).validate(
            value, model_instance
        )

        ids = {}
        for field in value.get('fields', []):
            id_ = field.get('id')
            if id_ == 'tower':
                raise django_exceptions.ValidationError(
                    _('"tower" is a reserved field name'),
                    code='invalid',
                    params={'value': value},
                )

            if id_ in ids:
                raise django_exceptions.ValidationError(
                    _('field IDs must be unique (%s)' % id_),
                    code='invalid',
                    params={'value': value},
                )
            ids[id_] = True

            if 'type' not in field:
                # If no type is specified, default to string
                field['type'] = 'string'

            if 'default' in field:
                default = field['default']
                _type = {'string': str, 'boolean': bool}[field['type']]
                if type(default) != _type:
                    raise django_exceptions.ValidationError(
                        _('{} is not a {}').format(default, field['type'])
                    )

            for key in ('choices', 'multiline', 'format', 'secret',):
                if key in field and field['type'] != 'string':
                    raise django_exceptions.ValidationError(
                        _('{sub_key} not allowed for {element_type} type ({element_id})'.format(
                            sub_key=key, element_type=field['type'], element_id=field['id'])),
                        code='invalid',
                        params={'value': value},
                    )



class CredentialTypeInjectorField(JSONSchemaField):
    """
    Used to validate JSON for
    `awx.main.models.credential:CredentialType().injectors`.
    """

    def schema(self, model_instance):
        return {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'file': {
                    'type': 'object',
                    'patternProperties': {
                        r'^template(\.[a-zA-Z_]+[a-zA-Z0-9_]*)?$': {'type': 'string'},
                    },
                    'additionalProperties': False,
                },
                'env': {
                    'type': 'object',
                    'patternProperties': {
                        # http://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap08.html
                        # In the shell command language, a word consisting solely
                        # of underscores, digits, and alphabetics from the portable
                        # character set. The first character of a name is not
                        # a digit.
                        '^[a-zA-Z_]+[a-zA-Z0-9_]*$': {
                            'type': 'string',
                            # The environment variable _value_ can be any ascii,
                            # but pexpect will choke on any unicode
                            'pattern': '^[\x00-\x7F]*$'
                        },
                    },
                    'additionalProperties': False,
                },
                'extra_vars': {
                    'type': 'object',
                    'patternProperties': {
                        # http://docs.ansible.com/ansible/playbooks_variables.html#what-makes-a-valid-variable-name
                        '^[a-zA-Z_]+[a-zA-Z0-9_]*$': {'type': 'string'},
                    },
                    'additionalProperties': False,
                },
            },
            'additionalProperties': False
        }

    def validate_env_var_allowed(self, env_var):
        if env_var.startswith('ANSIBLE_'):
            raise django_exceptions.ValidationError(
                _('Environment variable {} may affect Ansible configuration so its '
                  'use is not allowed in credentials.').format(env_var),
                code='invalid', params={'value': env_var},
            )
        if env_var in ENV_BLOCKLIST:
            raise django_exceptions.ValidationError(
                _('Environment variable {} is not allowed to be used in credentials.').format(env_var),
                code='invalid', params={'value': env_var},
            )

    def validate(self, value, model_instance):
        super(CredentialTypeInjectorField, self).validate(
            value, model_instance
        )

        # make sure the inputs are valid first
        try:
            CredentialTypeInputField().validate(model_instance.inputs, model_instance)
        except django_exceptions.ValidationError:
            # If `model_instance.inputs` itself is invalid, we can't make an
            # estimation as to whether our Jinja templates contain valid field
            # names; don't continue
            return

        # In addition to basic schema validation, search the injector fields
        # for template variables and make sure they match the fields defined in
        # the inputs
        valid_namespace = dict(
            (field, 'EXAMPLE')
            for field in model_instance.defined_fields
        )

        class ExplodingNamespace:
            def __str__(self):
                raise UndefinedError(_('Must define unnamed file injector in order to reference `tower.filename`.'))

        class TowerNamespace:
            def __init__(self):
                self.filename = ExplodingNamespace()

            def __str__(self):
                raise UndefinedError(_('Cannot directly reference reserved `tower` namespace container.'))

        valid_namespace['tower'] = TowerNamespace()

        # ensure either single file or multi-file syntax is used (but not both)
        template_names = [x for x in value.get('file', {}).keys() if x.startswith('template')]
        if 'template' in template_names:
            valid_namespace['tower'].filename = 'EXAMPLE_FILENAME'
            if len(template_names) > 1:
                raise django_exceptions.ValidationError(
                    _('Must use multi-file syntax when injecting multiple files'),
                    code='invalid',
                    params={'value': value},
                )
        elif template_names:
            for template_name in template_names:
                template_name = template_name.split('.')[1]
                setattr(valid_namespace['tower'].filename, template_name, 'EXAMPLE_FILENAME')

        for type_, injector in value.items():
            if type_ == 'env':
                for key in injector.keys():
                    self.validate_env_var_allowed(key)
            for key, tmpl in injector.items():
                try:
                    sandbox.ImmutableSandboxedEnvironment(
                        undefined=StrictUndefined
                    ).from_string(tmpl).render(valid_namespace)
                except UndefinedError as e:
                    raise django_exceptions.ValidationError(
                        _('{sub_key} uses an undefined field ({error_msg})').format(
                            sub_key=key, error_msg=e),
                        code='invalid',
                        params={'value': value},
                    )
                except SecurityError as e:
                    raise django_exceptions.ValidationError(
                        _('Encountered unsafe code execution: {}').format(e)
                    )
                except TemplateSyntaxError as e:
                    raise django_exceptions.ValidationError(
                        _('Syntax error rendering template for {sub_key} inside of {type} ({error_msg})').format(
                            sub_key=key, type=type_, error_msg=e),
                        code='invalid',
                        params={'value': value},
                    )


class AskForField(models.BooleanField):
    """
    Denotes whether to prompt on launch for another field on the same template
    """
    def __init__(self, allows_field=None, **kwargs):
        super(AskForField, self).__init__(**kwargs)
        self._allows_field = allows_field

    @property
    def allows_field(self):
        if self._allows_field is None:
            try:
                return self.name[len('ask_'):-len('_on_launch')]
            except AttributeError:
                # self.name will be set by the model metaclass, not this field
                raise Exception('Corresponding allows_field cannot be accessed until model is initialized.')
        return self._allows_field


class OAuth2ClientSecretField(models.CharField):

    def get_db_prep_value(self, value, connection, prepared=False):
        return super(OAuth2ClientSecretField, self).get_db_prep_value(
            encrypt_value(value), connection, prepared
        )

    def from_db_value(self, value, expression, connection):
        if value and value.startswith('$encrypted$'):
            return decrypt_value(get_encryption_key('value', pk=None), value)
        return value


class OrderedManyToManyDescriptor(ManyToManyDescriptor):
    """
    Django doesn't seem to support:

    class Meta:
        ordering = [...]

    ...on custom through= relations for ManyToMany fields.

    Meaning, queries made _through_ the intermediary table will _not_ apply an
    ORDER_BY clause based on the `Meta.ordering` of the intermediary M2M class
    (which is the behavior we want for "ordered" many to many relations):

    https://github.com/django/django/blob/stable/1.11.x/django/db/models/fields/related_descriptors.py#L593

    This descriptor automatically sorts all queries through this relation
    using the `position` column on the M2M table.
    """

    @cached_property
    def related_manager_cls(self):
        model = self.rel.related_model if self.reverse else self.rel.model

        def add_custom_queryset_to_many_related_manager(many_related_manage_cls):
            class OrderedManyRelatedManager(many_related_manage_cls):
                def get_queryset(self):
                    return super(OrderedManyRelatedManager, self).get_queryset().order_by(
                        '%s__position' % self.through._meta.model_name
                    )

            return OrderedManyRelatedManager

        return add_custom_queryset_to_many_related_manager(
            create_forward_many_to_many_manager(
                model._default_manager.__class__,
                self.rel,
                reverse=self.reverse,
            )
        )


class OrderedManyToManyField(models.ManyToManyField):
    """
    A ManyToManyField that automatically sorts all querysets
    by a special `position` column on the M2M table
    """

    def _update_m2m_position(self, sender, **kwargs):
        if kwargs.get('action') in ('post_add', 'post_remove'):
            order_with_respect_to = None
            for field in sender._meta.local_fields:
                if (
                    isinstance(field, models.ForeignKey) and
                    isinstance(kwargs['instance'], field.related_model)
                ):
                    order_with_respect_to = field.name
            for i, ig in enumerate(sender.objects.filter(**{
                order_with_respect_to: kwargs['instance'].pk}
            )):
                if ig.position != i:
                    ig.position = i
                    ig.save()

    def contribute_to_class(self, cls, name, **kwargs):
        super(OrderedManyToManyField, self).contribute_to_class(cls, name, **kwargs)
        setattr(
            cls, name,
            OrderedManyToManyDescriptor(self.remote_field, reverse=False)
        )

        through = getattr(cls, name).through
        if isinstance(through, str) and "." not in through:
            # support lazy loading of string model names
            through = '.'.join([cls._meta.app_label, through])
        m2m_changed.connect(
            self._update_m2m_position,
            sender=through
        )
