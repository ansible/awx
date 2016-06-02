# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import copy
import json
import re
import logging
from collections import OrderedDict
from dateutil import rrule

# PyYAML
import yaml

# Django
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db import models
# from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.forms.models import model_to_dict

# Django REST Framework
from rest_framework.exceptions import ValidationError
from rest_framework import fields
from rest_framework import serializers
from rest_framework import validators
from rest_framework.utils.serializer_helpers import ReturnList

# Django-Polymorphic
from polymorphic import PolymorphicModel

# AWX
from awx.main.constants import SCHEDULEABLE_PROVIDERS
from awx.main.models import * # noqa
from awx.main.fields import ImplicitRoleField
from awx.main.utils import get_type_for_model, get_model_for_type, build_url, timestamp_apiformat, camelcase_to_underscore, getattrd
from awx.main.redact import REPLACE_STR
from awx.main.conf import tower_settings

from awx.api.license import feature_enabled
from awx.api.fields import BooleanNullField, CharNullField, ChoiceNullField, EncryptedPasswordField, VerbatimField

logger = logging.getLogger('awx.api.serializers')

# Fields that should be summarized regardless of object type.
DEFAULT_SUMMARY_FIELDS = ('id', 'name', 'description')# , 'created_by', 'modified_by')#, 'type')

# Keys are fields (foreign keys) where, if found on an instance, summary info
# should be added to the serialized data.  Values are a tuple of field names on
# the related object to include in the summary data (if the field is present on
# the related object).
SUMMARIZABLE_FK_FIELDS = {
    'organization': DEFAULT_SUMMARY_FIELDS,
    'user': ('id', 'username', 'first_name', 'last_name'),
    'team': DEFAULT_SUMMARY_FIELDS,
    'inventory': DEFAULT_SUMMARY_FIELDS + ('has_active_failures',
                                           'total_hosts',
                                           'hosts_with_active_failures',
                                           'total_groups',
                                           'groups_with_active_failures',
                                           'has_inventory_sources',
                                           'total_inventory_sources',
                                           'inventory_sources_with_failures'),
    'host': DEFAULT_SUMMARY_FIELDS + ('has_active_failures',
                                      'has_inventory_sources'),
    'group': DEFAULT_SUMMARY_FIELDS + ('has_active_failures',
                                       'total_hosts',
                                       'hosts_with_active_failures',
                                       'total_groups',
                                       'groups_with_active_failures',
                                       'has_inventory_sources'),
    'project': DEFAULT_SUMMARY_FIELDS + ('status',),
    'credential': DEFAULT_SUMMARY_FIELDS + ('kind', 'cloud'),
    'cloud_credential': DEFAULT_SUMMARY_FIELDS + ('kind', 'cloud'),
    'network_credential': DEFAULT_SUMMARY_FIELDS + ('kind', 'net'),
    'job': DEFAULT_SUMMARY_FIELDS + ('status', 'failed',),
    'job_template': DEFAULT_SUMMARY_FIELDS,
    'schedule': DEFAULT_SUMMARY_FIELDS + ('next_run',),
    'unified_job_template': DEFAULT_SUMMARY_FIELDS + ('unified_job_type',),
    'last_job': DEFAULT_SUMMARY_FIELDS + ('finished', 'status', 'failed', 'license_error'),
    'last_job_host_summary': DEFAULT_SUMMARY_FIELDS + ('failed',),
    'last_update': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
    'current_update': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
    'current_job': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
    'inventory_source': ('source', 'last_updated', 'status'),
    'source_script': ('name', 'description'),
    'role': ('id', 'role_field')
}


def reverse_gfk(content_object):
    '''
    Computes a reverse for a GenericForeignKey field.

    Returns a dictionary of the form
        { '<type>': reverse(<type detail>) }
    for example
        { 'organization': '/api/v1/organizations/1/' }
    '''
    if content_object is None or not hasattr(content_object, 'get_absolute_url'):
        return {}

    return {
        camelcase_to_underscore(content_object.__class__.__name__): content_object.get_absolute_url()
    }


class BaseSerializerMetaclass(serializers.SerializerMetaclass):
    '''
    Custom metaclass to enable attribute inheritance from Meta objects on
    serializer base classes.

    Also allows for inheriting or updating field lists from base class(es):

        class Meta:

            # Inherit all fields from base class.
            fields = ('*',)

            # Inherit all fields from base class and add 'foo'.
            fields = ('*', 'foo')

            # Inherit all fields from base class except 'bar'.
            fields = ('*', '-bar')

            # Define fields as 'foo' and 'bar'; ignore base class fields.
            fields = ('foo', 'bar')

            # Extra field kwargs dicts are also merged from base classes.
            extra_kwargs = {
                'foo': {'required': True},
                'bar': {'read_only': True},
            }

            # If a subclass were to define extra_kwargs as:
            extra_kwargs = {
                'foo': {'required': False, 'default': ''},
                'bar': {'label': 'New Label for Bar'},
            }

            # The resulting value of extra_kwargs would be:
            extra_kwargs = {
                'foo': {'required': False, 'default': ''},
                'bar': {'read_only': True, 'label': 'New Label for Bar'},
            }

            # Extra field kwargs cannot be removed in subclasses, only replaced.

    '''

    @staticmethod
    def _is_list_of_strings(x):
        return isinstance(x, (list, tuple)) and all([isinstance(y, basestring) for y in x])

    @staticmethod
    def _is_extra_kwargs(x):
        return isinstance(x, dict) and all([isinstance(k, basestring) and isinstance(v, dict) for k,v in x.items()])

    @classmethod
    def _update_meta(cls, base, meta, other=None):
        for attr in dir(other):
            if attr.startswith('_'):
                continue
            val = getattr(other, attr)
            meta_val = getattr(meta, attr, None)
            # Special handling for lists/tuples of strings (field names).
            if cls._is_list_of_strings(val) and cls._is_list_of_strings(meta_val or []):
                meta_val = meta_val or []
                new_vals = []
                except_vals = []
                if base: # Merge values from all bases.
                    new_vals.extend([x for x in meta_val])
                for v in val:
                    if not base and v == '*': # Inherit all values from previous base(es).
                        new_vals.extend([x for x in meta_val])
                    elif not base and v.startswith('-'): # Except these values.
                        except_vals.append(v[1:])
                    else:
                        new_vals.append(v)
                val = []
                for v in new_vals:
                    if v not in except_vals and v not in val:
                        val.append(v)
                val = tuple(val)
            # Merge extra_kwargs dicts from base classes.
            elif cls._is_extra_kwargs(val) and cls._is_extra_kwargs(meta_val or {}):
                meta_val = meta_val or {}
                new_val = {}
                if base:
                    for k,v in meta_val.items():
                        new_val[k] = copy.deepcopy(v)
                for k,v in val.items():
                    new_val.setdefault(k, {}).update(copy.deepcopy(v))
                val = new_val
            # Any other values are copied in case they are mutable objects.
            else:
                val = copy.deepcopy(val)
            setattr(meta, attr, val)

    def __new__(cls, name, bases, attrs):
        meta = type('Meta', (object,), {})
        for base in bases[::-1]:
            cls._update_meta(base, meta, getattr(base, 'Meta', None))
        cls._update_meta(None, meta, attrs.get('Meta', meta))
        attrs['Meta'] = meta
        return super(BaseSerializerMetaclass, cls).__new__(cls, name, bases, attrs)


class BaseSerializer(serializers.ModelSerializer):

    __metaclass__ = BaseSerializerMetaclass

    class Meta:
        fields = ('id', 'type', 'url', 'related', 'summary_fields', 'created',
                  'modified', 'name', 'description')
        summary_fields = () # FIXME: List of field names from this serializer that should be used when included as part of another's summary_fields.
        summarizable_fields = () # FIXME: List of field names on this serializer that should be included in summary_fields.

    # add the URL and related resources
    type           = serializers.SerializerMethodField()
    url            = serializers.SerializerMethodField()
    related        = serializers.SerializerMethodField('_get_related')
    summary_fields = serializers.SerializerMethodField('_get_summary_fields')

    # make certain fields read only
    created       = serializers.SerializerMethodField()
    modified      = serializers.SerializerMethodField()


    def get_type(self, obj):
        return get_type_for_model(self.Meta.model)

    def get_types(self):
        return [self.get_type(None)]

    def get_type_choices(self):
        type_name_map = {
            'job': 'Playbook Run',
            'ad_hoc_command': 'Command',
            'project_update': 'SCM Update',
            'inventory_update': 'Inventory Sync',
            'system_job': 'Management Job',
        }
        choices = []
        for t in self.get_types():
            name = type_name_map.get(t, force_text(get_model_for_type(t)._meta.verbose_name).title())
            choices.append((t, name))
        return choices

    def get_url(self, obj):
        if obj is None or not hasattr(obj, 'get_absolute_url'):
            return ''
        elif isinstance(obj, User):
            return reverse('api:user_detail', args=(obj.pk,))
        else:
            return obj.get_absolute_url()

    def _get_related(self, obj):
        return {} if obj is None else self.get_related(obj)

    def get_related(self, obj):
        res = OrderedDict()
        if getattr(obj, 'created_by', None):
            res['created_by'] = reverse('api:user_detail', args=(obj.created_by.pk,))
        if getattr(obj, 'modified_by', None):
            res['modified_by'] = reverse('api:user_detail', args=(obj.modified_by.pk,))
        return res

    def _get_summary_fields(self, obj):
        return {} if obj is None else self.get_summary_fields(obj)

    def get_summary_fields(self, obj):
        # Return values for certain fields on related objects, to simplify
        # displaying lists of items without additional API requests.
        summary_fields = OrderedDict()
        for fk, related_fields in SUMMARIZABLE_FK_FIELDS.items():
            try:
                # A few special cases where we don't want to access the field
                # because it results in additional queries.
                if fk == 'job' and isinstance(obj, UnifiedJob):
                    continue
                if fk == 'project' and isinstance(obj, InventorySource):
                    continue

                fkval = getattr(obj, fk, None)
                if fkval is None:
                    continue
                if fkval == obj:
                    continue
                summary_fields[fk] = OrderedDict()
                for field in related_fields:
                    fval = getattr(fkval, field, None)
                    if fval is None and field == 'type':
                        if isinstance(fkval, PolymorphicModel):
                            fkval = fkval.get_real_instance()
                        fval = get_type_for_model(fkval)
                    elif fval is None and field == 'unified_job_type' and isinstance(fkval, UnifiedJobTemplate):
                        fkval = fkval.get_real_instance()
                        fval = get_type_for_model(fkval._get_unified_job_class())
                    if fval is not None:
                        summary_fields[fk][field] = fval
            # Can be raised by the reverse accessor for a OneToOneField.
            except ObjectDoesNotExist:
                pass
        if getattr(obj, 'created_by', None):
            summary_fields['created_by'] = OrderedDict()
            for field in SUMMARIZABLE_FK_FIELDS['user']:
                summary_fields['created_by'][field] = getattr(obj.created_by, field)
        if getattr(obj, 'modified_by', None):
            summary_fields['modified_by'] = OrderedDict()
            for field in SUMMARIZABLE_FK_FIELDS['user']:
                summary_fields['modified_by'][field] = getattr(obj.modified_by, field)

        # RBAC summary fields
        request = self.context.get('request', None)
        if request and isinstance(obj, ResourceMixin) and request.user.is_authenticated():
            summary_fields['active_roles'] = obj.get_permissions(request.user)
        roles = {}
        for field in obj._meta.get_fields():
            if type(field) is ImplicitRoleField:
                role = getattr(obj, field.name)
                #roles[field.name] = RoleSerializer(data=role).to_representation(role)
                roles[field.name] = {
                    'id': role.id,
                    'name': role.name,
                    'description': role.description,
                }
        if len(roles) > 0:
            summary_fields['roles'] = roles
        return summary_fields

    def get_created(self, obj):
        if obj is None:
            return None
        elif isinstance(obj, User):
            return obj.date_joined
        elif hasattr(obj, 'created'):
            return obj.created
        return None

    def get_modified(self, obj):
        if obj is None:
            return None
        elif isinstance(obj, User):
            return obj.last_login # Not actually exposed for User.
        elif hasattr(obj, 'modified'):
            return obj.modified
        return None

    def build_standard_field(self, field_name, model_field):
        # DRF 3.3 serializers.py::build_standard_field() -> utils/field_mapping.py::get_field_kwargs() short circuits
        # when a Model's editable field is set to False. The short circuit skips choice rendering.
        #
        # This logic is to force rendering choice's on an uneditable field.
        # Note: Consider expanding this rendering for more than just choices fields
        # Note: This logic works in conjuction with
        if hasattr(model_field, 'choices') and model_field.choices:
            was_editable = model_field.editable
            model_field.editable = True

        field_class, field_kwargs = super(BaseSerializer, self).build_standard_field(field_name, model_field)
        if hasattr(model_field, 'choices') and model_field.choices:
            model_field.editable = was_editable
            if was_editable is False:
                field_kwargs['read_only'] = True

        # Pass model field default onto the serializer field if field is not read-only.
        if model_field.has_default() and not field_kwargs.get('read_only', False):
            field_kwargs['default'] = field_kwargs['initial'] = model_field.get_default()

        # Enforce minimum value of 0 for PositiveIntegerFields.
        if isinstance(model_field, (models.PositiveIntegerField, models.PositiveSmallIntegerField)) and 'choices' not in field_kwargs:
            field_kwargs['min_value'] = 0

        # Use custom boolean field that allows null and empty string as False values.
        if isinstance(model_field, models.BooleanField) and not field_kwargs.get('read_only', False):
            field_class = BooleanNullField

        # Use custom char or choice field that coerces null to an empty string.
        if isinstance(model_field, (models.CharField, models.TextField)) and not field_kwargs.get('read_only', False):
            if 'choices' in field_kwargs:
                field_class = ChoiceNullField
            else:
                field_class = CharNullField

        # Update verbosity choices from settings (for job templates, jobs, ad hoc commands).
        if field_name == 'verbosity' and 'choices' in field_kwargs:
            field_kwargs['choices'] = getattr(settings, 'VERBOSITY_CHOICES', field_kwargs['choices'])

        # Update the message used for the unique validator to use capitalized
        # verbose name; keeps unique message the same as with DRF 2.x.
        opts = self.Meta.model._meta.concrete_model._meta
        for validator in field_kwargs.get('validators', []):
            if isinstance(validator, validators.UniqueValidator):
                unique_error_message = model_field.error_messages.get('unique', None)
                if unique_error_message:
                    unique_error_message = unique_error_message % {
                        'model_name': capfirst(opts.verbose_name),
                        'field_label': capfirst(model_field.verbose_name),
                    }
                    validator.message = unique_error_message

        return field_class, field_kwargs

    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super(BaseSerializer, self).build_relational_field(field_name, relation_info)
        # Don't include choices for foreign key fields.
        field_kwargs.pop('choices', None)
        return field_class, field_kwargs

    def get_unique_together_validators(self):
        # Allow the model's full_clean method to handle the unique together validation.
        return []

    def run_validation(self, data=fields.empty):
        try:
            return super(BaseSerializer, self).run_validation(data)
        except ValidationError as exc:
            # Avoid bug? in DRF if exc.detail happens to be a list instead of a dict.
            raise ValidationError(detail=serializers.get_validation_error_detail(exc))

    def get_validation_exclusions(self, obj=None):
        # Borrowed from DRF 2.x - return model fields that should be excluded
        # from model validation.
        cls = self.Meta.model
        opts = cls._meta.concrete_model._meta
        exclusions = [field.name for field in opts.fields + opts.many_to_many]
        for field_name, field in self.fields.items():
            field_name = field.source or field_name
            if field_name not in exclusions:
                continue
            if field.read_only:
                continue
            if isinstance(field, serializers.Serializer):
                continue
            exclusions.remove(field_name)
        return exclusions

    def validate(self, attrs):
        attrs = super(BaseSerializer, self).validate(attrs)
        try:
            # Create/update a model instance and run it's full_clean() method to
            # do any validation implemented on the model class.
            exclusions = self.get_validation_exclusions(self.instance)
            obj = self.instance or self.Meta.model()
            for k,v in attrs.items():
                if k not in exclusions:
                    setattr(obj, k, v)
            obj.full_clean(exclude=exclusions)
            # full_clean may modify values on the instance; copy those changes
            # back to attrs so they are saved.
            for k in attrs.keys():
                if k not in exclusions:
                    attrs[k] = getattr(obj, k)
        except DjangoValidationError as exc:
            # DjangoValidationError may contain a list or dict; normalize into a
            # dict where the keys are the field name and the values are a list
            # of error messages, then raise as a DRF ValidationError.  DRF would
            # normally convert any DjangoValidationError to a non-field specific
            # error message; here we preserve field-specific errors raised from
            # the model's full_clean method.
            d = exc.update_error_dict({})
            for k,v in d.items():
                v = v if isinstance(v, list) else [v]
                v2 = []
                for e in v:
                    if isinstance(e, DjangoValidationError):
                        v2.extend(list(e))
                    elif isinstance(e, list):
                        v2.extend(e)
                    else:
                        v2.append(e)
                d[k] = map(force_text, v2)
            raise ValidationError(d)
        return attrs


class EmptySerializer(serializers.Serializer):
    pass

class BaseFactSerializer(BaseSerializer):

    __metaclass__ = BaseSerializerMetaclass

    def get_fields(self):
        ret = super(BaseFactSerializer, self).get_fields()
        if 'module' in ret:
            # TODO: the values_list may pull in a LOT of entries before the distinct is called
            modules = Fact.objects.all().values_list('module', flat=True).distinct()
            choices = [(o, o.title()) for o in modules]
            ret['module'] = serializers.ChoiceField(choices=choices, read_only=True, required=False)
        return ret

class UnifiedJobTemplateSerializer(BaseSerializer):

    class Meta:
        model = UnifiedJobTemplate
        fields = ('*', 'last_job_run', 'last_job_failed', 'has_schedules',
                  'next_job_run', 'status')

    def get_related(self, obj):
        res = super(UnifiedJobTemplateSerializer, self).get_related(obj)
        if obj.current_job:
            res['current_job'] = obj.current_job.get_absolute_url()
        if obj.last_job:
            res['last_job'] = obj.last_job.get_absolute_url()
        if obj.next_schedule:
            res['next_schedule'] = obj.next_schedule.get_absolute_url()
        return res

    def get_types(self):
        if type(self) is UnifiedJobTemplateSerializer:
            return ['project', 'inventory_source', 'job_template', 'system_job_template']
        else:
            return super(UnifiedJobTemplateSerializer, self).get_types()

    def to_representation(self, obj):
        serializer_class = None
        if type(self) is UnifiedJobTemplateSerializer:
            if isinstance(obj, Project):
                serializer_class = ProjectSerializer
            elif isinstance(obj, InventorySource):
                serializer_class = InventorySourceSerializer
            elif isinstance(obj, JobTemplate):
                serializer_class = JobTemplateSerializer
        if serializer_class:
            serializer = serializer_class(instance=obj)
            return serializer.to_representation(obj)
        else:
            return super(UnifiedJobTemplateSerializer, self).to_representation(obj)


class UnifiedJobSerializer(BaseSerializer):

    result_stdout = serializers.SerializerMethodField()

    class Meta:
        model = UnifiedJob
        fields = ('*', 'unified_job_template', 'launch_type', 'status',
                  'failed', 'started', 'finished', 'elapsed', 'job_args',
                  'job_cwd', 'job_env', 'job_explanation', 'result_stdout',
                  'result_traceback')
        extra_kwargs = {
            'unified_job_template': {
                'source': 'unified_job_template_id',
                'label': 'unified job template',
            },
            'job_env': {
                'read_only': True,
                'label': 'job_env',
            }
        }

    def get_types(self):
        if type(self) is UnifiedJobSerializer:
            return ['project_update', 'inventory_update', 'job', 'ad_hoc_command', 'system_job']
        else:
            return super(UnifiedJobSerializer, self).get_types()

    def get_related(self, obj):
        res = super(UnifiedJobSerializer, self).get_related(obj)
        if obj.unified_job_template:
            res['unified_job_template'] = obj.unified_job_template.get_absolute_url()
        if obj.schedule:
            res['schedule'] = obj.schedule.get_absolute_url()
        if isinstance(obj, ProjectUpdate):
            res['stdout'] = reverse('api:project_update_stdout', args=(obj.pk,))
        elif isinstance(obj, InventoryUpdate):
            res['stdout'] = reverse('api:inventory_update_stdout', args=(obj.pk,))
        elif isinstance(obj, Job):
            res['stdout'] = reverse('api:job_stdout', args=(obj.pk,))
        elif isinstance(obj, AdHocCommand):
            res['stdout'] = reverse('api:ad_hoc_command_stdout', args=(obj.pk,))
        return res

    def to_representation(self, obj):
        serializer_class = None
        if type(self) is UnifiedJobSerializer:
            if isinstance(obj, ProjectUpdate):
                serializer_class = ProjectUpdateSerializer
            elif isinstance(obj, InventoryUpdate):
                serializer_class = InventoryUpdateSerializer
            elif isinstance(obj, Job):
                serializer_class = JobSerializer
            elif isinstance(obj, AdHocCommand):
                serializer_class = AdHocCommandSerializer
            elif isinstance(obj, SystemJob):
                serializer_class = SystemJobSerializer
        if serializer_class:
            serializer = serializer_class(instance=obj)
            ret = serializer.to_representation(obj)
        else:
            ret = super(UnifiedJobSerializer, self).to_representation(obj)
        if 'elapsed' in ret:
            ret['elapsed'] = float(ret['elapsed'])
        return ret

    def get_result_stdout(self, obj):
        obj_size = obj.result_stdout_size
        if obj_size > tower_settings.STDOUT_MAX_BYTES_DISPLAY:
            return "Standard Output too large to display (%d bytes), only download supported for sizes over %d bytes" % (obj_size,
                                                                                                                         tower_settings.STDOUT_MAX_BYTES_DISPLAY)
        return obj.result_stdout


class UnifiedJobListSerializer(UnifiedJobSerializer):

    class Meta:
        fields = ('*', '-job_args', '-job_cwd', '-job_env', '-result_traceback', '-result_stdout')

    def get_field_names(self, declared_fields, info):
        field_names = super(UnifiedJobListSerializer, self).get_field_names(declared_fields, info)
        # Meta multiple inheritance and -field_name options don't seem to be
        # taking effect above, so remove the undesired fields here.
        return tuple(x for x in field_names if x not in ('job_args', 'job_cwd', 'job_env', 'result_traceback', 'result_stdout'))

    def get_types(self):
        if type(self) is UnifiedJobListSerializer:
            return ['project_update', 'inventory_update', 'job', 'ad_hoc_command', 'system_job']
        else:
            return super(UnifiedJobListSerializer, self).get_types()

    def to_representation(self, obj):
        serializer_class = None
        if type(self) is UnifiedJobListSerializer:
            if isinstance(obj, ProjectUpdate):
                serializer_class = ProjectUpdateListSerializer
            elif isinstance(obj, InventoryUpdate):
                serializer_class = InventoryUpdateListSerializer
            elif isinstance(obj, Job):
                serializer_class = JobListSerializer
            elif isinstance(obj, AdHocCommand):
                serializer_class = AdHocCommandListSerializer
            elif isinstance(obj, SystemJob):
                serializer_class = SystemJobListSerializer
        if serializer_class:
            serializer = serializer_class(instance=obj)
            ret = serializer.to_representation(obj)
        else:
            ret = super(UnifiedJobListSerializer, self).to_representation(obj)
        if 'elapsed' in ret:
            ret['elapsed'] = float(ret['elapsed'])
        return ret


class UnifiedJobStdoutSerializer(UnifiedJobSerializer):

    result_stdout = serializers.SerializerMethodField()

    class Meta:
        fields = ('result_stdout',)

    def get_result_stdout(self, obj):
        obj_size = obj.result_stdout_size
        if obj_size > tower_settings.STDOUT_MAX_BYTES_DISPLAY:
            return "Standard Output too large to display (%d bytes), only download supported for sizes over %d bytes" % (obj_size,
                                                                                                                         tower_settings.STDOUT_MAX_BYTES_DISPLAY)
        return obj.result_stdout

    def get_types(self):
        if type(self) is UnifiedJobStdoutSerializer:
            return ['project_update', 'inventory_update', 'job', 'ad_hoc_command', 'system_job']
        else:
            return super(UnifiedJobStdoutSerializer, self).get_types()

    # TODO: Needed?
    #def to_representation(self, obj):
    #    ret = super(UnifiedJobStdoutSerializer, self).to_representation(obj)
    #    return ret.get('result_stdout', '')


class UserSerializer(BaseSerializer):

    password = serializers.CharField(required=False, default='', write_only=True,
                                     help_text='Write-only field used to change the password.')
    ldap_dn = serializers.CharField(source='profile.ldap_dn', read_only=True)
    is_system_auditor = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = ('*', '-name', '-description', '-modified',
                  '-summary_fields', 'username', 'first_name', 'last_name',
                  'email', 'is_superuser', 'is_system_auditor', 'password', 'ldap_dn')

    def to_representation(self, obj):
        ret = super(UserSerializer, self).to_representation(obj)
        ret.pop('password', None)
        if obj:
            ret['auth'] = obj.social_auth.values('provider', 'uid')
        return ret

    def get_validation_exclusions(self, obj=None):
        ret = super(UserSerializer, self).get_validation_exclusions(obj)
        ret.append('password')
        return ret

    def validate_password(self, value):
        if not self.instance and value in (None, ''):
            raise serializers.ValidationError('Password required for new User.')
        return value

    def _update_password(self, obj, new_password):
        # For now we're not raising an error, just not saving password for
        # users managed by LDAP who already have an unusable password set.
        if getattr(settings, 'AUTH_LDAP_SERVER_URI', None) and feature_enabled('ldap'):
            try:
                if obj.pk and obj.profile.ldap_dn and not obj.has_usable_password():
                    new_password = None
            except AttributeError:
                pass
        if (getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', None) or
                getattr(settings, 'SOCIAL_AUTH_GITHUB_KEY', None) or
                getattr(settings, 'SOCIAL_AUTH_GITHUB_ORG_KEY', None) or
                getattr(settings, 'SOCIAL_AUTH_GITHUB_TEAM_KEY', None) or
                getattr(settings, 'SOCIAL_AUTH_SAML_ENABLED_IDPS', None)) and obj.social_auth.all():
            new_password = None
        if new_password:
            obj.set_password(new_password)
            obj.save(update_fields=['password'])
        elif not obj.password:
            obj.set_unusable_password()
            obj.save(update_fields=['password'])

    def create(self, validated_data):
        new_password = validated_data.pop('password', None)
        obj = super(UserSerializer, self).create(validated_data)
        self._update_password(obj, new_password)
        return obj

    def update(self, obj, validated_data):
        new_password = validated_data.pop('password', None)
        obj = super(UserSerializer, self).update(obj, validated_data)
        self._update_password(obj, new_password)
        return obj

    def get_related(self, obj):
        res = super(UserSerializer, self).get_related(obj)
        res.update(dict(
            teams                  = reverse('api:user_teams_list',               args=(obj.pk,)),
            organizations          = reverse('api:user_organizations_list',       args=(obj.pk,)),
            admin_of_organizations = reverse('api:user_admin_of_organizations_list', args=(obj.pk,)),
            projects               = reverse('api:user_projects_list',            args=(obj.pk,)),
            credentials            = reverse('api:user_credentials_list',         args=(obj.pk,)),
            roles                  = reverse('api:user_roles_list',               args=(obj.pk,)),
            activity_stream        = reverse('api:user_activity_stream_list',     args=(obj.pk,)),
            access_list            = reverse('api:user_access_list',              args=(obj.pk,)),
        ))
        return res

    def _validate_ldap_managed_field(self, value, field_name):
        if not getattr(settings, 'AUTH_LDAP_SERVER_URI', None) or not feature_enabled('ldap'):
            return value
        try:
            is_ldap_user = bool(self.instance and self.instance.profile.ldap_dn)
        except AttributeError:
            is_ldap_user = False
        if is_ldap_user:
            ldap_managed_fields = ['username']
            ldap_managed_fields.extend(getattr(settings, 'AUTH_LDAP_USER_ATTR_MAP', {}).keys())
            ldap_managed_fields.extend(getattr(settings, 'AUTH_LDAP_USER_FLAGS_BY_GROUP', {}).keys())
            if field_name in ldap_managed_fields:
                if value != getattr(self.instance, field_name):
                    raise serializers.ValidationError('Unable to change %s on user managed by LDAP.' % field_name)
        return value

    def validate_username(self, value):
        return self._validate_ldap_managed_field(value, 'username')

    def validate_first_name(self, value):
        return self._validate_ldap_managed_field(value, 'first_name')

    def validate_last_name(self, value):
        return self._validate_ldap_managed_field(value, 'last_name')

    def validate_email(self, value):
        return self._validate_ldap_managed_field(value, 'email')

    def validate_is_superuser(self, value):
        return self._validate_ldap_managed_field(value, 'is_superuser')


class OrganizationSerializer(BaseSerializer):

    class Meta:
        model = Organization
        fields = ('*',)

    def get_related(self, obj):
        res = super(OrganizationSerializer, self).get_related(obj)
        res.update(dict(
            projects    = reverse('api:organization_projects_list',       args=(obj.pk,)),
            inventories = reverse('api:organization_inventories_list',    args=(obj.pk,)),
            users       = reverse('api:organization_users_list',          args=(obj.pk,)),
            admins      = reverse('api:organization_admins_list',         args=(obj.pk,)),
            teams       = reverse('api:organization_teams_list',          args=(obj.pk,)),
            credentials = reverse('api:organization_credential_list',     args=(obj.pk,)),
            activity_stream = reverse('api:organization_activity_stream_list', args=(obj.pk,)),
            notification_templates = reverse('api:organization_notification_templates_list', args=(obj.pk,)),
            notification_templates_any = reverse('api:organization_notification_templates_any_list', args=(obj.pk,)),
            notification_templates_success = reverse('api:organization_notification_templates_success_list', args=(obj.pk,)),
            notification_templates_error = reverse('api:organization_notification_templates_error_list', args=(obj.pk,)),
            roles = reverse('api:organization_roles_list', args=(obj.pk,)),
            access_list = reverse('api:organization_access_list', args=(obj.pk,)),
        ))
        return res

    def get_summary_fields(self, obj):
        summary_dict = super(OrganizationSerializer, self).get_summary_fields(obj)
        counts_dict = self.context.get('related_field_counts', None)
        if counts_dict is not None and summary_dict is not None:
            if obj.id not in counts_dict:
                summary_dict['related_field_counts'] = {
                    'inventories': 0, 'teams': 0, 'users': 0,
                    'job_templates': 0, 'admins': 0, 'projects': 0}
            else:
                summary_dict['related_field_counts'] = counts_dict[obj.id]
        return summary_dict


class ProjectOptionsSerializer(BaseSerializer):

    class Meta:
        fields = ('*', 'local_path', 'scm_type', 'scm_url', 'scm_branch',
                  'scm_clean', 'scm_delete_on_update', 'credential')

    def get_related(self, obj):
        res = super(ProjectOptionsSerializer, self).get_related(obj)
        if obj.credential:
            res['credential'] = reverse('api:credential_detail',
                                        args=(obj.credential.pk,))
        return res

    def validate(self, attrs):
        errors = {}

        # Don't allow assigning a local_path used by another project.
        # Don't allow assigning a local_path when scm_type is set.
        valid_local_paths = Project.get_local_path_choices()
        if self.instance:
            scm_type = attrs.get('scm_type', self.instance.scm_type) or u''
        else:
            scm_type = attrs.get('scm_type', u'') or u''
        if self.instance and not scm_type:
            valid_local_paths.append(self.instance.local_path)
        if scm_type:
            attrs.pop('local_path', None)
        if 'local_path' in attrs and attrs['local_path'] not in valid_local_paths:
            errors['local_path'] = 'Invalid path choice.'

        if errors:
            raise serializers.ValidationError(errors)

        return super(ProjectOptionsSerializer, self).validate(attrs)

    def to_representation(self, obj):
        ret = super(ProjectOptionsSerializer, self).to_representation(obj)
        if obj is not None and 'credential' in ret and not obj.credential:
            ret['credential'] = None
        return ret


class ProjectSerializer(UnifiedJobTemplateSerializer, ProjectOptionsSerializer):

    status = serializers.ChoiceField(choices=Project.PROJECT_STATUS_CHOICES, read_only=True)
    last_update_failed = serializers.BooleanField(read_only=True)
    last_updated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Project
        fields = ('*', 'organization', 'scm_delete_on_next_update', 'scm_update_on_launch',
                  'scm_update_cache_timeout') + \
                 ('last_update_failed', 'last_updated')  # Backwards compatibility
        read_only_fields = ('scm_delete_on_next_update',)

    def get_related(self, obj):
        res = super(ProjectSerializer, self).get_related(obj)
        res.update(dict(
            teams = reverse('api:project_teams_list', args=(obj.pk,)),
            playbooks = reverse('api:project_playbooks', args=(obj.pk,)),
            update = reverse('api:project_update_view', args=(obj.pk,)),
            project_updates = reverse('api:project_updates_list', args=(obj.pk,)),
            schedules = reverse('api:project_schedules_list', args=(obj.pk,)),
            activity_stream = reverse('api:project_activity_stream_list', args=(obj.pk,)),
            notification_templates_any = reverse('api:project_notification_templates_any_list', args=(obj.pk,)),
            notification_templates_success = reverse('api:project_notification_templates_success_list', args=(obj.pk,)),
            notification_templates_error = reverse('api:project_notification_templates_error_list', args=(obj.pk,)),
            access_list = reverse('api:project_access_list', args=(obj.pk,)),
            roles = reverse('api:project_roles_list', args=(obj.pk,)),
        ))
        if obj.organization:
            res['organization'] = reverse('api:organization_detail',
                                          args=(obj.organization.pk,))
        # Backwards compatibility.
        if obj.current_update:
            res['current_update'] = reverse('api:project_update_detail',
                                            args=(obj.current_update.pk,))
        if obj.last_update:
            res['last_update'] = reverse('api:project_update_detail',
                                         args=(obj.last_update.pk,))
        return res


class ProjectPlaybooksSerializer(ProjectSerializer):

    playbooks = serializers.ReadOnlyField(help_text='Array of playbooks available within this project.')

    class Meta:
        model = Project
        fields = ('playbooks',)

    @property
    def data(self):
        ret = super(ProjectPlaybooksSerializer, self).data
        ret = ret.get('playbooks', [])
        return ReturnList(ret, serializer=self)


class ProjectUpdateViewSerializer(ProjectSerializer):

    can_update = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_update',)


class ProjectUpdateSerializer(UnifiedJobSerializer, ProjectOptionsSerializer):

    class Meta:
        model = ProjectUpdate
        fields = ('*', 'project')

    def get_related(self, obj):
        res = super(ProjectUpdateSerializer, self).get_related(obj)
        res.update(dict(
            project = reverse('api:project_detail', args=(obj.project.pk,)),
            cancel = reverse('api:project_update_cancel', args=(obj.pk,)),
            notifications = reverse('api:project_update_notifications_list', args=(obj.pk,)),
        ))
        return res


class ProjectUpdateListSerializer(ProjectUpdateSerializer, UnifiedJobListSerializer):

    pass


class ProjectUpdateCancelSerializer(ProjectUpdateSerializer):

    can_cancel = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_cancel',)


class BaseSerializerWithVariables(BaseSerializer):

    def validate_variables(self, value):
        try:
            json.loads(value.strip() or '{}')
        except ValueError:
            try:
                yaml.safe_load(value)
            except yaml.YAMLError:
                raise serializers.ValidationError('Must be valid JSON or YAML.')
        return value


class InventorySerializer(BaseSerializerWithVariables):

    class Meta:
        model = Inventory
        fields = ('*', 'organization', 'variables', 'has_active_failures',
                  'total_hosts', 'hosts_with_active_failures', 'total_groups',
                  'groups_with_active_failures', 'has_inventory_sources',
                  'total_inventory_sources', 'inventory_sources_with_failures')

    def get_related(self, obj):
        res = super(InventorySerializer, self).get_related(obj)
        res.update(dict(
            hosts         = reverse('api:inventory_hosts_list',        args=(obj.pk,)),
            groups        = reverse('api:inventory_groups_list',       args=(obj.pk,)),
            root_groups   = reverse('api:inventory_root_groups_list',  args=(obj.pk,)),
            variable_data = reverse('api:inventory_variable_data',     args=(obj.pk,)),
            script        = reverse('api:inventory_script_view',       args=(obj.pk,)),
            tree          = reverse('api:inventory_tree_view',         args=(obj.pk,)),
            inventory_sources = reverse('api:inventory_inventory_sources_list', args=(obj.pk,)),
            activity_stream = reverse('api:inventory_activity_stream_list', args=(obj.pk,)),
            job_templates = reverse('api:inventory_job_template_list', args=(obj.pk,)),
            scan_job_templates = reverse('api:inventory_scan_job_template_list', args=(obj.pk,)),
            ad_hoc_commands = reverse('api:inventory_ad_hoc_commands_list', args=(obj.pk,)),
            access_list = reverse('api:inventory_access_list',         args=(obj.pk,)),
            roles = reverse('api:inventory_roles_list', args=(obj.pk,)),
            #single_fact = reverse('api:inventory_single_fact_view', args=(obj.pk,)),
        ))
        if obj.organization:
            res['organization'] = reverse('api:organization_detail', args=(obj.organization.pk,))
        return res

    def to_representation(self, obj):
        ret = super(InventorySerializer, self).to_representation(obj)
        if obj is not None and 'organization' in ret and not obj.organization:
            ret['organization'] = None
        return ret


class InventoryDetailSerializer(InventorySerializer):

    class Meta:
        fields = ('*', 'can_run_ad_hoc_commands')

    can_run_ad_hoc_commands = serializers.SerializerMethodField()

    def get_can_run_ad_hoc_commands(self, obj):
        view = self.context.get('view', None)
        return bool(obj and view and view.request and view.request.user and view.request.user.can_access(Inventory, 'run_ad_hoc_commands', obj))


class InventoryScriptSerializer(InventorySerializer):

    class Meta:
        fields = ()


class HostSerializer(BaseSerializerWithVariables):

    class Meta:
        model = Host
        fields = ('*', 'inventory', 'enabled', 'instance_id', 'variables',
                  'has_active_failures', 'has_inventory_sources', 'last_job',
                  'last_job_host_summary')
        read_only_fields = ('last_job', 'last_job_host_summary')

    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super(HostSerializer, self).build_relational_field(field_name, relation_info)
        # Inventory is read-only unless creating a new host.
        if self.instance and field_name == 'inventory':
            field_kwargs['read_only'] = True
            field_kwargs.pop('queryset', None)
        return field_class, field_kwargs

    def get_related(self, obj):
        res = super(HostSerializer, self).get_related(obj)
        res.update(dict(
            variable_data = reverse('api:host_variable_data',   args=(obj.pk,)),
            groups        = reverse('api:host_groups_list',     args=(obj.pk,)),
            all_groups    = reverse('api:host_all_groups_list', args=(obj.pk,)),
            job_events    = reverse('api:host_job_events_list',  args=(obj.pk,)),
            job_host_summaries = reverse('api:host_job_host_summaries_list', args=(obj.pk,)),
            activity_stream = reverse('api:host_activity_stream_list', args=(obj.pk,)),
            inventory_sources = reverse('api:host_inventory_sources_list', args=(obj.pk,)),
            ad_hoc_commands = reverse('api:host_ad_hoc_commands_list', args=(obj.pk,)),
            ad_hoc_command_events = reverse('api:host_ad_hoc_command_events_list', args=(obj.pk,)),
            fact_versions = reverse('api:host_fact_versions_list', args=(obj.pk,)),
            #single_fact = reverse('api:host_single_fact_view', args=(obj.pk,)),
        ))
        if obj.inventory:
            res['inventory'] = reverse('api:inventory_detail', args=(obj.inventory.pk,))
        if obj.last_job:
            res['last_job'] = reverse('api:job_detail', args=(obj.last_job.pk,))
        if obj.last_job_host_summary:
            res['last_job_host_summary'] = reverse('api:job_host_summary_detail', args=(obj.last_job_host_summary.pk,))
        return res

    def get_summary_fields(self, obj):
        d = super(HostSerializer, self).get_summary_fields(obj)
        try:
            d['last_job']['job_template_id'] = obj.last_job.job_template.id
            d['last_job']['job_template_name'] = obj.last_job.job_template.name
        except (KeyError, AttributeError):
            pass
        d.update({'recent_jobs': [{
            'id': j.job.id,
            'name': j.job.job_template.name if j.job.job_template is not None else "",
            'status': j.job.status,
            'finished': j.job.finished,
        } for j in obj.job_host_summaries.select_related('job__job_template').order_by('-created')[:5]]})
        return d

    def _get_host_port_from_name(self, name):
        # Allow hostname (except IPv6 for now) to specify the port # inline.
        port = None
        if name.count(':') == 1:
            name, port = name.split(':')
            try:
                port = int(port)
                if port < 1 or port > 65535:
                    raise ValueError
            except ValueError:
                raise serializers.ValidationError(u'Invalid port specification: %s' % force_text(port))
        return name, port

    def validate_name(self, value):
        name = force_text(value or '')
        # Validate here only, update in main validate method.
        host, port = self._get_host_port_from_name(name)
        return value

    def validate(self, attrs):
        name = force_text(attrs.get('name', self.instance and self.instance.name or ''))
        host, port = self._get_host_port_from_name(name)

        if port:
            attrs['name'] = host
            variables = force_text(attrs.get('variables', self.instance and self.instance.variables or ''))
            try:
                vars_dict = json.loads(variables.strip() or '{}')
                vars_dict['ansible_ssh_port'] = port
                attrs['variables'] = json.dumps(vars_dict)
            except (ValueError, TypeError):
                try:
                    vars_dict = yaml.safe_load(variables)
                    if vars_dict is None:
                        vars_dict = {}
                    vars_dict['ansible_ssh_port'] = port
                    attrs['variables'] = yaml.dump(vars_dict)
                except (yaml.YAMLError, TypeError):
                    raise serializers.ValidationError('Must be valid JSON or YAML.')

        return super(HostSerializer, self).validate(attrs)

    def to_representation(self, obj):
        ret = super(HostSerializer, self).to_representation(obj)
        if not obj:
            return ret
        if 'inventory' in ret and not obj.inventory:
            ret['inventory'] = None
        if 'last_job' in ret and not obj.last_job:
            ret['last_job'] = None
        if 'last_job_host_summary' in ret and not obj.last_job_host_summary:
            ret['last_job_host_summary'] = None
        return ret


class GroupSerializer(BaseSerializerWithVariables):

    class Meta:
        model = Group
        fields = ('*', 'inventory', 'variables', 'has_active_failures',
                  'total_hosts', 'hosts_with_active_failures', 'total_groups',
                  'groups_with_active_failures', 'has_inventory_sources')

    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super(GroupSerializer, self).build_relational_field(field_name, relation_info)
        # Inventory is read-only unless creating a new group.
        if self.instance and field_name == 'inventory':
            field_kwargs['read_only'] = True
            field_kwargs.pop('queryset', None)
        return field_class, field_kwargs

    def get_related(self, obj):
        res = super(GroupSerializer, self).get_related(obj)
        res.update(dict(
            variable_data = reverse('api:group_variable_data',   args=(obj.pk,)),
            hosts         = reverse('api:group_hosts_list',      args=(obj.pk,)),
            potential_children = reverse('api:group_potential_children_list',   args=(obj.pk,)),
            children      = reverse('api:group_children_list',   args=(obj.pk,)),
            all_hosts     = reverse('api:group_all_hosts_list',  args=(obj.pk,)),
            job_events    = reverse('api:group_job_events_list',   args=(obj.pk,)),
            job_host_summaries = reverse('api:group_job_host_summaries_list', args=(obj.pk,)),
            activity_stream = reverse('api:group_activity_stream_list', args=(obj.pk,)),
            inventory_sources = reverse('api:group_inventory_sources_list', args=(obj.pk,)),
            ad_hoc_commands = reverse('api:group_ad_hoc_commands_list', args=(obj.pk,)),
            access_list = reverse('api:group_access_list',         args=(obj.pk,)),
            roles = reverse('api:group_roles_list', args=(obj.pk,)),
            #single_fact = reverse('api:group_single_fact_view', args=(obj.pk,)),
        ))
        if obj.inventory:
            res['inventory'] = reverse('api:inventory_detail', args=(obj.inventory.pk,))
        if obj.inventory_source:
            res['inventory_source'] = reverse('api:inventory_source_detail', args=(obj.inventory_source.pk,))
        return res

    def validate_name(self, value):
        if value in ('all', '_meta'):
            raise serializers.ValidationError('Invalid group name.')
        return value

    def to_representation(self, obj):
        ret = super(GroupSerializer, self).to_representation(obj)
        if obj is not None and 'inventory' in ret and not obj.inventory:
            ret['inventory'] = None
        return ret


class GroupTreeSerializer(GroupSerializer):

    children = serializers.SerializerMethodField('get_children')

    class Meta:
        model = Group
        fields = ('*', 'children')

    def get_children(self, obj):
        if obj is None:
            return {}
        children_qs = obj.children
        children_qs = children_qs.select_related('inventory')
        children_qs = children_qs.prefetch_related('inventory_source')
        return GroupTreeSerializer(children_qs, many=True).data


class BaseVariableDataSerializer(BaseSerializer):

    class Meta:
        fields = ('variables',)

    def to_representation(self, obj):
        if obj is None:
            return {}
        ret = super(BaseVariableDataSerializer, self).to_representation(obj)
        try:
            return json.loads(ret.get('variables', '') or '{}')
        except ValueError:
            return yaml.safe_load(ret.get('variables', ''))

    def to_internal_value(self, data):
        data = {'variables': json.dumps(data)}
        return super(BaseVariableDataSerializer, self).to_internal_value(data)


class InventoryVariableDataSerializer(BaseVariableDataSerializer):

    class Meta:
        model = Inventory


class HostVariableDataSerializer(BaseVariableDataSerializer):

    class Meta:
        model = Host


class GroupVariableDataSerializer(BaseVariableDataSerializer):

    class Meta:
        model = Group

class CustomInventoryScriptSerializer(BaseSerializer):

    script = serializers.CharField(trim_whitespace=False)

    class Meta:
        model = CustomInventoryScript
        fields = ('*', "script", "organization")

    def validate_script(self, value):
        if not value.startswith("#!"):
            raise serializers.ValidationError('Script must begin with a hashbang sequence: i.e.... #!/usr/bin/env python')
        return value

    def to_representation(self, obj):
        ret = super(CustomInventoryScriptSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        request = self.context.get('request', None)
        if request is not None and request.user is not None and not request.user.is_superuser:
            ret['script'] = None
        return ret

    def get_related(self, obj):
        res = super(CustomInventoryScriptSerializer, self).get_related(obj)
        res.update(dict(
            roles = reverse('api:inventory_script_roles_list', args=(obj.pk,)),
        ))

        if obj.organization:
            res['organization'] = reverse('api:organization_detail', args=(obj.organization.pk,))
        return res


class InventorySourceOptionsSerializer(BaseSerializer):

    class Meta:
        fields = ('*', 'source', 'source_path', 'source_script', 'source_vars', 'credential',
                  'source_regions', 'instance_filters', 'group_by', 'overwrite', 'overwrite_vars')

    def get_related(self, obj):
        res = super(InventorySourceOptionsSerializer, self).get_related(obj)
        if obj.credential:
            res['credential'] = reverse('api:credential_detail',
                                        args=(obj.credential.pk,))
        if obj.source_script:
            res['source_script'] = reverse('api:inventory_script_detail', args=(obj.source_script.pk,))
        return res

    def validate_source_vars(self, value):
        # source_env must be blank, a valid JSON or YAML dict, or ...
        # FIXME: support key=value pairs.
        try:
            json.loads((value or '').strip() or '{}')
            return value
        except ValueError:
            pass
        try:
            yaml.safe_load(value)
            return value
        except yaml.YAMLError:
            pass
        raise serializers.ValidationError('Must be valid JSON or YAML.')

    def validate(self, attrs):
        # TODO: Validate source, validate source_regions
        errors = {}

        source = attrs.get('source', self.instance and self.instance.source or '')
        source_script = attrs.get('source_script', self.instance and self.instance.source_script or '')
        if source == 'custom':
            if source_script is None or source_script == '':
                errors['source_script'] = "If 'source' is 'custom', 'source_script' must be provided."
            else:
                try:
                    if source_script.organization != self.instance.inventory.organization:
                        errors['source_script'] = "The 'source_script' does not belong to the same organization as the inventory."
                except Exception:
                    # TODO: Log
                    errors['source_script'] = "'source_script' doesn't exist."

        if errors:
            raise serializers.ValidationError(errors)

        return super(InventorySourceOptionsSerializer, self).validate(attrs)

    def to_representation(self, obj):
        ret = super(InventorySourceOptionsSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        if 'credential' in ret and not obj.credential:
            ret['credential'] = None
        return ret


class InventorySourceSerializer(UnifiedJobTemplateSerializer, InventorySourceOptionsSerializer):

    status = serializers.ChoiceField(choices=InventorySource.INVENTORY_SOURCE_STATUS_CHOICES, read_only=True)
    last_update_failed = serializers.BooleanField(read_only=True)
    last_updated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = InventorySource
        fields = ('*', 'inventory', 'group', 'update_on_launch',
                  'update_cache_timeout') + \
                 ('last_update_failed', 'last_updated') # Backwards compatibility.
        read_only_fields = ('*', 'name', 'inventory', 'group')

    def get_related(self, obj):
        res = super(InventorySourceSerializer, self).get_related(obj)
        res.update(dict(
            update = reverse('api:inventory_source_update_view', args=(obj.pk,)),
            inventory_updates = reverse('api:inventory_source_updates_list', args=(obj.pk,)),
            schedules = reverse('api:inventory_source_schedules_list', args=(obj.pk,)),
            activity_stream = reverse('api:inventory_activity_stream_list', args=(obj.pk,)),
            hosts = reverse('api:inventory_source_hosts_list', args=(obj.pk,)),
            groups = reverse('api:inventory_source_groups_list', args=(obj.pk,)),
            notification_templates_any = reverse('api:inventory_source_notification_templates_any_list', args=(obj.pk,)),
            notification_templates_success = reverse('api:inventory_source_notification_templates_success_list', args=(obj.pk,)),
            notification_templates_error = reverse('api:inventory_source_notification_templates_error_list', args=(obj.pk,)),
        ))
        if obj.inventory:
            res['inventory'] = reverse('api:inventory_detail', args=(obj.inventory.pk,))
        if obj.group:
            res['group'] = reverse('api:group_detail', args=(obj.group.pk,))
        # Backwards compatibility.
        if obj.current_update:
            res['current_update'] = reverse('api:inventory_update_detail',
                                            args=(obj.current_update.pk,))
        if obj.last_update:
            res['last_update'] = reverse('api:inventory_update_detail',
                                         args=(obj.last_update.pk,))
        return res

    def to_representation(self, obj):
        ret = super(InventorySourceSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        if 'inventory' in ret and not obj.inventory:
            ret['inventory'] = None
        if 'group' in ret and not obj.group:
            ret['group'] = None
        return ret


class InventorySourceUpdateSerializer(InventorySourceSerializer):

    can_update = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_update',)


class InventoryUpdateSerializer(UnifiedJobSerializer, InventorySourceOptionsSerializer):

    class Meta:
        model = InventoryUpdate
        fields = ('*', 'inventory_source', 'license_error')

    def get_related(self, obj):
        res = super(InventoryUpdateSerializer, self).get_related(obj)
        res.update(dict(
            inventory_source = reverse('api:inventory_source_detail', args=(obj.inventory_source.pk,)),
            cancel = reverse('api:inventory_update_cancel', args=(obj.pk,)),
            notifications = reverse('api:inventory_update_notifications_list', args=(obj.pk,)),
        ))
        return res


class InventoryUpdateListSerializer(InventoryUpdateSerializer, UnifiedJobListSerializer):

    pass


class InventoryUpdateCancelSerializer(InventoryUpdateSerializer):

    can_cancel = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_cancel',)


class TeamSerializer(BaseSerializer):

    class Meta:
        model = Team
        fields = ('*', 'organization')

    def get_related(self, obj):
        res = super(TeamSerializer, self).get_related(obj)
        res.update(dict(
            projects     = reverse('api:team_projects_list',    args=(obj.pk,)),
            users        = reverse('api:team_users_list',       args=(obj.pk,)),
            credentials  = reverse('api:team_credentials_list', args=(obj.pk,)),
            roles        = reverse('api:team_roles_list',       args=(obj.pk,)),
            activity_stream = reverse('api:team_activity_stream_list', args=(obj.pk,)),
            access_list  = reverse('api:team_access_list',      args=(obj.pk,)),
        ))
        if obj.organization:
            res['organization'] = reverse('api:organization_detail',   args=(obj.organization.pk,))
        return res

    def to_representation(self, obj):
        ret = super(TeamSerializer, self).to_representation(obj)
        if obj is not None and 'organization' in ret and not obj.organization:
            ret['organization'] = None
        return ret



class RoleSerializer(BaseSerializer):

    class Meta:
        model = Role
        read_only_fields = ('id', 'role_field', 'description', 'name')

    def to_representation(self, obj):
        ret = super(RoleSerializer, self).to_representation(obj)

        def spacify_type_name(cls):
            return re.sub(r'([a-z])([A-Z])', '\g<1> \g<2>', cls.__name__)

        if obj.object_id:
            content_object = obj.content_object
            if hasattr(content_object, 'username'):
                ret['summary_fields']['resource_name'] = obj.content_object.username
            if hasattr(content_object, 'name'):
                ret['summary_fields']['resource_name'] = obj.content_object.name
            ret['summary_fields']['resource_type'] = obj.content_type.name
            ret['summary_fields']['resource_type_display_name'] = spacify_type_name(obj.content_type.model_class())

        ret.pop('created')
        ret.pop('modified')
        return ret

    def get_related(self, obj):
        ret = super(RoleSerializer, self).get_related(obj)
        ret['users'] = reverse('api:role_users_list', args=(obj.pk,))
        ret['teams'] = reverse('api:role_teams_list', args=(obj.pk,))
        try:
            if obj.content_object:
                ret.update(reverse_gfk(obj.content_object))
        except AttributeError:
            # AttributeError's happen if our content_object is pointing at
            # a model that no longer exists. This is dirty data and ideally
            # doesn't exist, but in case it does, let's not puke.
            pass
        return ret



class ResourceAccessListElementSerializer(UserSerializer):

    def to_representation(self, user):
        '''
        With this method we derive "direct" and "indirect" access lists. Contained
        in the direct access list are all the roles the user is a member of, and
        all of the roles that are directly granted to any teams that the user is a
        member of.

        The indirect access list is a list of all of the roles that the user is
        a member of that are ancestors of any roles that grant permissions to
        the resource.
        '''
        ret = super(ResourceAccessListElementSerializer, self).to_representation(user)
        object_id = self.context['view'].object_id
        obj = self.context['view'].resource_model.objects.get(pk=object_id)

        if 'summary_fields' not in ret:
            ret['summary_fields'] = {}
        ret['summary_fields']['active_roles'] = get_roles_on_resource(obj, user)

        def format_role_perm(role):
            role_dict = { 'id': role.id, 'name': role.name, 'description': role.description}
            try:
                role_dict['resource_name'] = role.content_object.name
                role_dict['resource_type'] = role.content_type.name
                role_dict['related'] = reverse_gfk(role.content_object)
            except:
                pass
            return { 'role': role_dict, 'descendant_roles': get_roles_on_resource(obj, role)}

        def format_team_role_perm(team_role, permissive_role_ids):
            ret = []
            for role in team_role.children.filter(id__in=permissive_role_ids).all():
                role_dict = {
                    'id': role.id,
                    'name': role.name,
                    'description': role.description,
                    'team_id': team_role.object_id,
                    'team_name': team_role.content_object.name
                }
                try:
                    role_dict['resource_name'] = role.content_object.name
                    role_dict['resource_type'] = role.content_type.name
                    role_dict['related'] = reverse_gfk(role.content_object)
                except:
                    pass
                ret.append({ 'role': role_dict, 'descendant_roles': get_roles_on_resource(obj, team_role)})
            return ret

        team_content_type = ContentType.objects.get_for_model(Team)
        content_type = ContentType.objects.get_for_model(obj)


        content_type = ContentType.objects.get_for_model(obj)
        direct_permissive_role_ids = Role.objects.filter(content_type=content_type, object_id=obj.id).values_list('id', flat=True)
        all_permissive_role_ids = Role.objects.filter(content_type=content_type, object_id=obj.id).values_list('ancestors__id', flat=True)

        direct_access_roles   = user.roles \
                                    .filter(id__in=direct_permissive_role_ids).all()

        direct_team_roles     = Role.objects \
                                    .filter(content_type=team_content_type,
                                            members=user,
                                            children__in=direct_permissive_role_ids)
        if content_type == team_content_type:
            # When looking at the access list for a team, exclude the entries
            # for that team. This exists primarily so we don't list the read role
            # as a direct role when a user is a member or admin of a team
            direct_team_roles = direct_team_roles.exclude(
                children__content_type=team_content_type,
                children__object_id=obj.id
            )


        indirect_team_roles   = Role.objects \
                                    .filter(content_type=team_content_type,
                                            members=user,
                                            children__in=all_permissive_role_ids) \
                                    .exclude(id__in=direct_team_roles)

        indirect_access_roles = user.roles \
                                    .filter(id__in=all_permissive_role_ids)     \
                                    .exclude(id__in=direct_permissive_role_ids) \
                                    .exclude(id__in=direct_team_roles)          \
                                    .exclude(id__in=indirect_team_roles)

        ret['summary_fields']['direct_access'] \
            = [format_role_perm(r) for r in direct_access_roles.distinct()] \
            + [y for x in (format_team_role_perm(r, direct_permissive_role_ids) for r in direct_team_roles.distinct()) for y in x]

        ret['summary_fields']['indirect_access'] \
            = [format_role_perm(r) for r in indirect_access_roles.distinct()] \
            + [y for x in (format_team_role_perm(r, all_permissive_role_ids) for r in indirect_team_roles.distinct()) for y in x]

        return ret




class CredentialSerializer(BaseSerializer):

    # FIXME: may want to make some fields filtered based on user accessing

    class Meta:
        model = Credential
        fields = ('*', 'kind', 'cloud', 'host', 'username',
                  'password', 'security_token', 'project', 'domain',
                  'ssh_key_data', 'ssh_key_unlock',
                  'become_method', 'become_username', 'become_password',
                  'vault_password', 'subscription', 'tenant', 'secret', 'client',
                  'authorize', 'authorize_password')

    def build_standard_field(self, field_name, model_field):
        field_class, field_kwargs = super(CredentialSerializer, self).build_standard_field(field_name, model_field)
        if field_name in Credential.PASSWORD_FIELDS:
            field_class = EncryptedPasswordField
            field_kwargs['required'] = False
            field_kwargs['default'] = ''
        return field_class, field_kwargs

    def get_related(self, obj):
        res = super(CredentialSerializer, self).get_related(obj)
        res.update(dict(
            activity_stream = reverse('api:credential_activity_stream_list', args=(obj.pk,)),
            access_list = reverse('api:credential_access_list', args=(obj.pk,)),
            roles = reverse('api:credential_roles_list', args=(obj.pk,)),
        ))

        parents = obj.owner_role.parents.exclude(object_id__isnull=True)
        if parents.count() > 0:
            res.update({parents[0].content_type.name:parents[0].content_object.get_absolute_url()})
        elif obj.owner_role.members.count() > 0:
            user = obj.owner_role.members.first()
            res.update({'user': reverse('api:user_detail', args=(user.pk,))})

        return res

    def get_summary_fields(self, obj):
        summary_dict = super(CredentialSerializer, self).get_summary_fields(obj)
        summary_dict['owners'] = []

        for user in obj.owner_role.members.all():
            summary_dict['owners'].append({
                'id': user.pk,
                'name': user.username,
                'description': ' '.join([user.first_name, user.last_name]),
                'url': reverse('api:user_detail', args=(user.pk,)),
            })

        for parent in obj.owner_role.parents.exclude(object_id__isnull=True).all():
            summary_dict['owners'].append({
                'id': parent.content_object.pk,
                'name': parent.content_object.name,
                'description': parent.content_object.description,
                'url': parent.content_object.get_absolute_url(),
            })

        return summary_dict


class CredentialSerializerCreate(CredentialSerializer):

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False, default=None, write_only=True, allow_null=True,
        help_text='Write-only field used to add user to owner role. If provided, '
                  'do not give either team or organization. Only valid for creation.')
    team = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        required=False, default=None, write_only=True, allow_null=True,
        help_text='Write-only field used to add team to owner role. If provided, '
                  'do not give either user or organization. Only valid for creation.')
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        required=False, default=None, write_only=True, allow_null=True,
        help_text='Write-only field used to add organization to owner role. If provided, '
                  'do not give either team or team. Only valid for creation.')

    class Meta:
        model = Credential
        fields = ('*', 'user', 'team', 'organization')

    def create(self, validated_data):
        # Remove the user, team, and organization processed in view
        for field in ['user', 'team', 'organization']:
            validated_data.pop(field, None)
        return super(CredentialSerializer, self).create(validated_data)


class JobOptionsSerializer(BaseSerializer):

    class Meta:
        fields = ('*', 'job_type', 'inventory', 'project', 'playbook',
                  'credential', 'cloud_credential', 'network_credential', 'forks', 'limit',
                  'verbosity', 'extra_vars', 'job_tags',  'force_handlers',
                  'skip_tags', 'start_at_task',)

    def get_related(self, obj):
        res = super(JobOptionsSerializer, self).get_related(obj)
        res['labels'] = reverse('api:job_template_label_list', args=(obj.pk,))
        if obj.inventory:
            res['inventory'] = reverse('api:inventory_detail', args=(obj.inventory.pk,))
        if obj.project:
            res['project'] = reverse('api:project_detail', args=(obj.project.pk,))
        if obj.credential:
            res['credential'] = reverse('api:credential_detail', args=(obj.credential.pk,))
        if obj.cloud_credential:
            res['cloud_credential'] = reverse('api:credential_detail',
                                              args=(obj.cloud_credential.pk,))
        if obj.network_credential:
            res['network_credential'] = reverse('api:credential_detail',
                                                args=(obj.network_credential.pk,))
        return res

    def _summary_field_labels(self, obj):
        return {'count': obj.labels.count(), 'results': [{'id': x.id, 'name': x.name} for x in obj.labels.all().order_by('name')[:10]]}

    def get_summary_fields(self, obj):
        res = super(JobOptionsSerializer, self).get_summary_fields(obj)
        res['labels'] = self._summary_field_labels(obj)
        return res

    def to_representation(self, obj):
        ret = super(JobOptionsSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        if 'inventory' in ret and not obj.inventory:
            ret['inventory'] = None
        if 'project' in ret and not obj.project:
            ret['project'] = None
            if 'playbook' in ret:
                ret['playbook'] = ''
        if 'credential' in ret and not obj.credential:
            ret['credential'] = None
        if 'cloud_credential' in ret and not obj.cloud_credential:
            ret['cloud_credential'] = None
        if 'network_credential' in ret and not obj.network_credential:
            ret['network_credential'] = None
        return ret

    def validate(self, attrs):
        if 'project' in self.fields and 'playbook' in self.fields:
            project = attrs.get('project', self.instance and self.instance.project or None)
            playbook = attrs.get('playbook', self.instance and self.instance.playbook or '')
            job_type = attrs.get('job_type', self.instance and self.instance.job_type or None)
            if not project and job_type != PERM_INVENTORY_SCAN:
                raise serializers.ValidationError({'project': 'This field is required.'})
            if project and playbook and force_text(playbook) not in project.playbooks:
                raise serializers.ValidationError({'playbook': 'Playbook not found for project.'})
            if project and not playbook:
                raise serializers.ValidationError({'playbook': 'Must select playbook for project.'})

        return super(JobOptionsSerializer, self).validate(attrs)


class JobTemplateSerializer(UnifiedJobTemplateSerializer, JobOptionsSerializer):

    status = serializers.ChoiceField(choices=JobTemplate.JOB_TEMPLATE_STATUS_CHOICES, read_only=True, required=False)

    class Meta:
        model = JobTemplate
        fields = ('*', 'host_config_key', 'ask_variables_on_launch', 'ask_limit_on_launch',
                  'ask_tags_on_launch', 'ask_job_type_on_launch', 'ask_inventory_on_launch',
                  'ask_credential_on_launch', 'survey_enabled', 'become_enabled', 'allow_simultaneous')

    def get_related(self, obj):
        res = super(JobTemplateSerializer, self).get_related(obj)
        res.update(dict(
            jobs = reverse('api:job_template_jobs_list', args=(obj.pk,)),
            schedules = reverse('api:job_template_schedules_list', args=(obj.pk,)),
            activity_stream = reverse('api:job_template_activity_stream_list', args=(obj.pk,)),
            launch = reverse('api:job_template_launch', args=(obj.pk,)),
            notification_templates_any = reverse('api:job_template_notification_templates_any_list', args=(obj.pk,)),
            notification_templates_success = reverse('api:job_template_notification_templates_success_list', args=(obj.pk,)),
            notification_templates_error = reverse('api:job_template_notification_templates_error_list', args=(obj.pk,)),
            access_list = reverse('api:job_template_access_list',      args=(obj.pk,)),
            survey_spec = reverse('api:job_template_survey_spec', args=(obj.pk,)),
            labels = reverse('api:job_template_label_list', args=(obj.pk,)),
            roles = reverse('api:job_template_roles_list', args=(obj.pk,)),
        ))
        if obj.host_config_key:
            res['callback'] = reverse('api:job_template_callback', args=(obj.pk,))
        return res

    def _recent_jobs(self, obj):
        return [{'id': x.id, 'status': x.status, 'finished': x.finished} for x in obj.jobs.all().order_by('-created')[:10]]

    def get_summary_fields(self, obj):
        d = super(JobTemplateSerializer, self).get_summary_fields(obj)
        if obj.survey_spec is not None and ('name' in obj.survey_spec and 'description' in obj.survey_spec):
            d['survey'] = dict(title=obj.survey_spec['name'], description=obj.survey_spec['description'])
        request = self.context.get('request', None)

        # Check for conditions that would create a validation error if coppied
        validation_errors, resources_needed_to_start = obj.resource_validation_data()

        if request is None or request.user is None:
            d['can_copy'] = False
            d['can_edit'] = False
        elif request.user.is_superuser:
            d['can_copy'] = not validation_errors
            d['can_edit'] = True
        else:
            jt_data = model_to_dict(obj)
            d['can_copy'] = (not validation_errors) and request.user.can_access(JobTemplate, 'add', jt_data)
            d['can_edit'] = request.user.can_access(JobTemplate, 'change', obj, jt_data)

        d['recent_jobs'] = self._recent_jobs(obj)
        return d

    def validate(self, attrs):
        survey_enabled = attrs.get('survey_enabled', self.instance and self.instance.survey_enabled or False)
        job_type = attrs.get('job_type', self.instance and self.instance.job_type or None)
        if survey_enabled and job_type == PERM_INVENTORY_SCAN:
            raise serializers.ValidationError({'survey_enabled': 'Survey Enabled can not be used with scan jobs.'})

        return super(JobTemplateSerializer, self).validate(attrs)

    def validate_extra_vars(self, value):
        # extra_vars must be blank, a valid JSON or YAML dict, or ...
        # FIXME: support key=value pairs.
        try:
            json.loads((value or '').strip() or '{}')
            return value
        except ValueError:
            pass
        try:
            yaml.safe_load(value)
            return value
        except yaml.YAMLError:
            pass
        raise serializers.ValidationError('Must be valid JSON or YAML.')


class JobSerializer(UnifiedJobSerializer, JobOptionsSerializer):

    passwords_needed_to_start = serializers.ReadOnlyField()
    ask_variables_on_launch = serializers.ReadOnlyField()
    ask_limit_on_launch = serializers.ReadOnlyField()
    ask_tags_on_launch = serializers.ReadOnlyField()
    ask_job_type_on_launch = serializers.ReadOnlyField()
    ask_inventory_on_launch = serializers.ReadOnlyField()
    ask_credential_on_launch = serializers.ReadOnlyField()

    class Meta:
        model = Job
        fields = ('*', 'job_template', 'passwords_needed_to_start', 'ask_variables_on_launch',
                  'ask_limit_on_launch', 'ask_tags_on_launch', 'ask_job_type_on_launch',
                  'ask_inventory_on_launch', 'ask_credential_on_launch')

    def get_related(self, obj):
        res = super(JobSerializer, self).get_related(obj)
        res.update(dict(
            job_events  = reverse('api:job_job_events_list', args=(obj.pk,)),
            job_plays = reverse('api:job_job_plays_list', args=(obj.pk,)),
            job_tasks = reverse('api:job_job_tasks_list', args=(obj.pk,)),
            job_host_summaries = reverse('api:job_job_host_summaries_list', args=(obj.pk,)),
            activity_stream = reverse('api:job_activity_stream_list', args=(obj.pk,)),
            notifications = reverse('api:job_notifications_list', args=(obj.pk,)),
            labels = reverse('api:job_label_list', args=(obj.pk,)),
        ))
        if obj.job_template:
            res['job_template'] = reverse('api:job_template_detail',
                                          args=(obj.job_template.pk,))
        if obj.can_start or True:
            res['start'] = reverse('api:job_start', args=(obj.pk,))
        if obj.can_cancel or True:
            res['cancel'] = reverse('api:job_cancel', args=(obj.pk,))
        res['relaunch'] = reverse('api:job_relaunch', args=(obj.pk,))
        return res

    def to_internal_value(self, data):
        # When creating a new job and a job template is specified, populate any
        # fields not provided in data from the job template.
        if not self.instance and isinstance(data, dict) and 'job_template' in data:
            try:
                job_template = JobTemplate.objects.get(pk=data['job_template'])
            except JobTemplate.DoesNotExist:
                self._errors = {'job_template': 'Invalid job template.'}
                return
            data.setdefault('name', job_template.name)
            data.setdefault('description', job_template.description)
            data.setdefault('job_type', job_template.job_type)
            if job_template.inventory:
                data.setdefault('inventory', job_template.inventory.pk)
            if job_template.project:
                data.setdefault('project', job_template.project.pk)
                data.setdefault('playbook', job_template.playbook)
            if job_template.credential:
                data.setdefault('credential', job_template.credential.pk)
            if job_template.cloud_credential:
                data.setdefault('cloud_credential', job_template.cloud_credential.pk)
            if job_template.network_credential:
                data.setdefault('network_credential', job_template.network_credential.pk)
            data.setdefault('forks', job_template.forks)
            data.setdefault('limit', job_template.limit)
            data.setdefault('verbosity', job_template.verbosity)
            data.setdefault('extra_vars', job_template.extra_vars)
            data.setdefault('job_tags', job_template.job_tags)
            data.setdefault('force_handlers', job_template.force_handlers)
            data.setdefault('skip_tags', job_template.skip_tags)
            data.setdefault('start_at_task', job_template.start_at_task)
        return super(JobSerializer, self).to_internal_value(data)

    def to_representation(self, obj):
        ret = super(JobSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        if 'job_template' in ret and not obj.job_template:
            ret['job_template'] = None

        if obj.job_template and obj.job_template.survey_enabled:
            if 'extra_vars' in ret:
                try:
                    extra_vars = json.loads(ret['extra_vars'])
                    for key in obj.job_template.survey_password_variables():
                        if key in extra_vars:
                            extra_vars[key] = REPLACE_STR
                    ret['extra_vars'] = json.dumps(extra_vars)
                except ValueError:
                    pass
        return ret


class JobCancelSerializer(JobSerializer):

    can_cancel = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_cancel',)


class JobRelaunchSerializer(JobSerializer):

    passwords_needed_to_start = serializers.SerializerMethodField()

    class Meta:
        fields = ('passwords_needed_to_start',)

    def to_internal_value(self, data):
        obj = self.context.get('obj')
        all_data = self.to_representation(obj)
        all_data.update(data)
        ret = super(JobRelaunchSerializer, self).to_internal_value(all_data)
        return ret

    def to_representation(self, obj):
        res = super(JobRelaunchSerializer, self).to_representation(obj)
        view = self.context.get('view', None)
        if hasattr(view, '_raw_data_form_marker'):
            password_keys = dict([(p, u'') for p in self.get_passwords_needed_to_start(obj)])
            res.update(password_keys)
        return res

    def get_passwords_needed_to_start(self, obj):
        if obj:
            return obj.passwords_needed_to_start
        return ''

    def validate_passwords_needed_to_start(self, value):
        obj = self.context.get('obj')
        data = self.context.get('data')

        # Check for passwords needed
        needed = self.get_passwords_needed_to_start(obj)
        provided = dict([(field, data.get(field, '')) for field in needed])
        if not all(provided.values()):
            raise serializers.ValidationError(needed)
        return value

    def validate(self, attrs):
        obj = self.context.get('obj')
        if not obj.credential:
            raise serializers.ValidationError(dict(credential=["Credential not found or deleted."]))
        if obj.job_type != PERM_INVENTORY_SCAN and obj.project is None:
            raise serializers.ValidationError(dict(errors=["Job Template Project is missing or undefined."]))
        if obj.inventory is None:
            raise serializers.ValidationError(dict(errors=["Job Template Inventory is missing or undefined."]))
        attrs = super(JobRelaunchSerializer, self).validate(attrs)
        return attrs

class AdHocCommandSerializer(UnifiedJobSerializer):

    class Meta:
        model = AdHocCommand
        fields = ('*', 'job_type', 'inventory', 'limit', 'credential',
                  'module_name', 'module_args', 'forks', 'verbosity', 'extra_vars',
                  'become_enabled', '-unified_job_template', '-description')
        extra_kwargs = {
            'name': {
                'read_only': True,
            },
        }

    def get_field_names(self, declared_fields, info):
        field_names = super(AdHocCommandSerializer, self).get_field_names(declared_fields, info)
        # Meta multiple inheritance and -field_name options don't seem to be
        # taking effect above, so remove the undesired fields here.
        return tuple(x for x in field_names if x not in ('unified_job_template', 'description'))

    def build_standard_field(self, field_name, model_field):
        field_class, field_kwargs = super(AdHocCommandSerializer, self).build_standard_field(field_name, model_field)
        # Load module name choices dynamically from DB settings.
        if field_name == 'module_name':
            field_class = serializers.ChoiceField
            module_name_choices = [(x, x) for x in tower_settings.AD_HOC_COMMANDS]
            module_name_default = 'command' if 'command' in [x[0] for x in module_name_choices] else ''
            field_kwargs['choices'] = module_name_choices
            field_kwargs['required'] = bool(not module_name_default)
            field_kwargs['default'] = module_name_default or serializers.empty
            field_kwargs['allow_blank'] = bool(module_name_default)
            field_kwargs.pop('max_length', None)
        return field_class, field_kwargs

    def get_related(self, obj):
        res = super(AdHocCommandSerializer, self).get_related(obj)
        if obj.inventory:
            res['inventory'] = reverse('api:inventory_detail', args=(obj.inventory.pk,))
        if obj.credential:
            res['credential'] = reverse('api:credential_detail', args=(obj.credential.pk,))
        res.update(dict(
            events  = reverse('api:ad_hoc_command_ad_hoc_command_events_list', args=(obj.pk,)),
            activity_stream = reverse('api:ad_hoc_command_activity_stream_list', args=(obj.pk,)),
        ))
        res['cancel'] = reverse('api:ad_hoc_command_cancel', args=(obj.pk,))
        res['relaunch'] = reverse('api:ad_hoc_command_relaunch', args=(obj.pk,))
        return res

    def to_representation(self, obj):
        ret = super(AdHocCommandSerializer, self).to_representation(obj)
        if 'inventory' in ret and not obj.inventory:
            ret['inventory'] = None
        if 'credential' in ret and not obj.credential:
            ret['credential'] = None
        # For the UI, only module_name is returned for name, instead of the
        # longer module name + module_args format.
        if 'name' in ret:
            ret['name'] = obj.module_name
        return ret


class AdHocCommandCancelSerializer(AdHocCommandSerializer):

    can_cancel = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_cancel',)


class AdHocCommandRelaunchSerializer(AdHocCommandSerializer):

    class Meta:
        fields = ()

    def to_representation(self, obj):
        if obj:
            return dict([(p, u'') for p in obj.passwords_needed_to_start])
        else:
            return {}


class SystemJobTemplateSerializer(UnifiedJobTemplateSerializer):

    class Meta:
        model = SystemJobTemplate
        fields = ('*', 'job_type',)

    def get_related(self, obj):
        res = super(SystemJobTemplateSerializer, self).get_related(obj)
        res.update(dict(
            jobs = reverse('api:system_job_template_jobs_list', args=(obj.pk,)),
            schedules = reverse('api:system_job_template_schedules_list', args=(obj.pk,)),
            launch = reverse('api:system_job_template_launch', args=(obj.pk,)),
            notification_templates_any = reverse('api:system_job_template_notification_templates_any_list', args=(obj.pk,)),
            notification_templates_success = reverse('api:system_job_template_notification_templates_success_list', args=(obj.pk,)),
            notification_templates_error = reverse('api:system_job_template_notification_templates_error_list', args=(obj.pk,)),

        ))
        return res

class SystemJobSerializer(UnifiedJobSerializer):

    class Meta:
        model = SystemJob
        fields = ('*', 'system_job_template', 'job_type', 'extra_vars')

    def get_related(self, obj):
        res = super(SystemJobSerializer, self).get_related(obj)
        if obj.system_job_template:
            res['system_job_template'] = reverse('api:system_job_template_detail',
                                                 args=(obj.system_job_template.pk,))
            res['notifications'] = reverse('api:system_job_notifications_list', args=(obj.pk,))
        if obj.can_cancel or True:
            res['cancel'] = reverse('api:system_job_cancel', args=(obj.pk,))
        return res

class SystemJobCancelSerializer(SystemJobSerializer):

    can_cancel = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_cancel',)

class JobListSerializer(JobSerializer, UnifiedJobListSerializer):
    pass

class AdHocCommandListSerializer(AdHocCommandSerializer, UnifiedJobListSerializer):
    pass

class SystemJobListSerializer(SystemJobSerializer, UnifiedJobListSerializer):
    pass

class JobHostSummarySerializer(BaseSerializer):

    class Meta:
        model = JobHostSummary
        fields = ('*', '-name', '-description', 'job', 'host', 'host_name', 'changed',
                  'dark', 'failures', 'ok', 'processed', 'skipped', 'failed')

    def get_related(self, obj):
        res = super(JobHostSummarySerializer, self).get_related(obj)
        res.update(dict(
            job=reverse('api:job_detail', args=(obj.job.pk,))))
        if obj.host is not None:
            res.update(dict(
                host=reverse('api:host_detail', args=(obj.host.pk,))
            ))
        return res

    def get_summary_fields(self, obj):
        d = super(JobHostSummarySerializer, self).get_summary_fields(obj)
        try:
            d['job']['job_template_id'] = obj.job.job_template.id
            d['job']['job_template_name'] = obj.job.job_template.name
        except (KeyError, AttributeError):
            pass
        return d


class JobEventSerializer(BaseSerializer):

    event_display = serializers.CharField(source='get_event_display2', read_only=True)
    event_level = serializers.IntegerField(read_only=True)

    class Meta:
        model = JobEvent
        fields = ('*', '-name', '-description', 'job', 'event', 'counter',
                  'event_display', 'event_data', 'event_level', 'failed',
                  'changed', 'host', 'host_name', 'parent', 'play', 'task', 'role')

    def get_related(self, obj):
        res = super(JobEventSerializer, self).get_related(obj)
        res.update(dict(
            job = reverse('api:job_detail', args=(obj.job.pk,)),
            #children = reverse('api:job_event_children_list', args=(obj.pk,)),
        ))
        if obj.parent:
            res['parent'] = reverse('api:job_event_detail', args=(obj.parent.pk,))
        if obj.children.count():
            res['children'] = reverse('api:job_event_children_list', args=(obj.pk,))
        if obj.host:
            res['host'] = reverse('api:host_detail', args=(obj.host.pk,))
        if obj.hosts.count():
            res['hosts'] = reverse('api:job_event_hosts_list', args=(obj.pk,))
        return res

    def get_summary_fields(self, obj):
        d = super(JobEventSerializer, self).get_summary_fields(obj)
        try:
            d['job']['job_template_id'] = obj.job.job_template.id
            d['job']['job_template_name'] = obj.job.job_template.name
        except (KeyError, AttributeError):
            pass
        return d


class AdHocCommandEventSerializer(BaseSerializer):

    event_display = serializers.CharField(source='get_event_display', read_only=True)

    class Meta:
        model = AdHocCommandEvent
        fields = ('*', '-name', '-description', 'ad_hoc_command', 'event',
                  'counter', 'event_display', 'event_data', 'failed',
                  'changed', 'host', 'host_name')

    def to_internal_value(self, data):
        ret = super(AdHocCommandEventSerializer, self).to_internal_value(data)
        # AdHocCommandAdHocCommandEventsList should be the only view creating
        # AdHocCommandEvent instances, so keep the ad_hoc_command it sets, even
        # though ad_hoc_command is a read-only field.
        if 'ad_hoc_command' in data:
            ret['ad_hoc_command'] = data['ad_hoc_command']
        return ret

    def get_related(self, obj):
        res = super(AdHocCommandEventSerializer, self).get_related(obj)
        res.update(dict(
            ad_hoc_command = reverse('api:ad_hoc_command_detail', args=(obj.ad_hoc_command_id,)),
        ))
        if obj.host:
            res['host'] = reverse('api:host_detail', args=(obj.host.pk,))
        return res


class JobLaunchSerializer(BaseSerializer):

    passwords_needed_to_start = serializers.ReadOnlyField()
    can_start_without_user_input = serializers.BooleanField(read_only=True)
    variables_needed_to_start = serializers.ReadOnlyField()
    credential_needed_to_start = serializers.SerializerMethodField()
    inventory_needed_to_start = serializers.SerializerMethodField()
    survey_enabled = serializers.SerializerMethodField()
    extra_vars = VerbatimField(required=False, write_only=True)
    job_template_data = serializers.SerializerMethodField()
    defaults = serializers.SerializerMethodField()

    class Meta:
        model = JobTemplate
        fields = ('can_start_without_user_input', 'passwords_needed_to_start',
                  'extra_vars', 'limit', 'job_tags', 'skip_tags', 'job_type', 'inventory',
                  'credential', 'ask_variables_on_launch', 'ask_tags_on_launch',
                  'ask_job_type_on_launch', 'ask_limit_on_launch',
                  'ask_inventory_on_launch', 'ask_credential_on_launch',
                  'survey_enabled', 'variables_needed_to_start',
                  'credential_needed_to_start', 'inventory_needed_to_start',
                  'job_template_data', 'defaults')
        read_only_fields = ('ask_variables_on_launch', 'ask_limit_on_launch',
                            'ask_tags_on_launch', 'ask_job_type_on_launch',
                            'ask_inventory_on_launch', 'ask_credential_on_launch')
        extra_kwargs = {
            'credential': {'write_only': True,},
            'limit': {'write_only': True,},
            'job_tags': {'write_only': True,},
            'skip_tags': {'write_only': True,},
            'job_type': {'write_only': True,},
            'inventory': {'write_only': True,}
        }

    def get_credential_needed_to_start(self, obj):
        return not (obj and obj.credential)

    def get_inventory_needed_to_start(self, obj):
        return not (obj and obj.inventory)

    def get_survey_enabled(self, obj):
        if obj:
            return obj.survey_enabled and 'spec' in obj.survey_spec
        return False

    def get_defaults(self, obj):
        ask_for_vars_dict = obj._ask_for_vars_dict()
        defaults_dict = {}
        for field in ask_for_vars_dict:
            if field in ('inventory', 'credential'):
                defaults_dict[field] = dict(
                    name=getattrd(obj, '%s.name' % field, None),
                    id=getattrd(obj, '%s.pk' % field, None))
            else:
                defaults_dict[field] = getattr(obj, field)
        return defaults_dict

    def get_job_template_data(self, obj):
        return dict(name=obj.name, id=obj.id, description=obj.description)

    def validate(self, attrs):
        errors = {}
        obj = self.context.get('obj')
        data = self.context.get('data')

        for field in obj.resources_needed_to_start:
            if not (field in attrs and obj._ask_for_vars_dict().get(field, False)):
                errors[field] = "Job Template '%s' is missing or undefined." % field

        if (not obj.ask_credential_on_launch) or (not attrs.get('credential', None)):
            credential = obj.credential
        else:
            credential = attrs.get('credential', None)

        # fill passwords dict with request data passwords
        if credential and credential.passwords_needed:
            passwords = self.context.get('passwords')
            try:
                for p in credential.passwords_needed:
                    passwords[p] = data[p]
            except KeyError:
                errors['passwords_needed_to_start'] = credential.passwords_needed

        extra_vars = attrs.get('extra_vars', {})

        if isinstance(extra_vars, basestring):
            try:
                extra_vars = json.loads(extra_vars)
            except (ValueError, TypeError):
                try:
                    extra_vars = yaml.safe_load(extra_vars)
                    assert isinstance(extra_vars, dict)
                except (yaml.YAMLError, TypeError, AttributeError, AssertionError):
                    errors['extra_vars'] = 'Must be a valid JSON or YAML dictionary.'

        if not isinstance(extra_vars, dict):
            extra_vars = {}

        if self.get_survey_enabled(obj):
            validation_errors = obj.survey_variable_validation(extra_vars)
            if validation_errors:
                errors['variables_needed_to_start'] = validation_errors

        # Special prohibited cases for scan jobs
        if 'job_type' in data and obj.ask_job_type_on_launch:
            if ((obj.job_type == PERM_INVENTORY_SCAN and not data['job_type'] == PERM_INVENTORY_SCAN) or
                    (data['job_type'] == PERM_INVENTORY_SCAN and not obj.job_type == PERM_INVENTORY_SCAN)):
                errors['job_type'] = 'Can not override job_type to or from a scan job.'
        if (obj.job_type == PERM_INVENTORY_SCAN and ('inventory' in data) and obj.ask_inventory_on_launch and
                obj.inventory != data['inventory']):
            errors['inventory'] = 'Inventory can not be changed at runtime for scan jobs.'

        if errors:
            raise serializers.ValidationError(errors)

        JT_extra_vars = obj.extra_vars
        JT_limit = obj.limit
        JT_job_type = obj.job_type
        JT_job_tags = obj.job_tags
        JT_skip_tags = obj.skip_tags
        JT_inventory = obj.inventory
        JT_credential = obj.credential
        attrs = super(JobLaunchSerializer, self).validate(attrs)
        obj.extra_vars = JT_extra_vars
        obj.limit = JT_limit
        obj.job_type = JT_job_type
        obj.skip_tags = JT_skip_tags
        obj.job_tags = JT_job_tags
        obj.inventory = JT_inventory
        obj.credential = JT_credential
        return attrs

class NotificationTemplateSerializer(BaseSerializer):

    class Meta:
        model = NotificationTemplate
        fields = ('*', 'organization', 'notification_type', 'notification_configuration')

    type_map = {"string": (str, unicode),
                "int": (int,),
                "bool": (bool,),
                "list": (list,),
                "password": (str, unicode),
                "object": (dict, OrderedDict)}

    def to_representation(self, obj):
        ret = super(NotificationTemplateSerializer, self).to_representation(obj)
        for field in obj.notification_class.init_parameters:
            if field in ret['notification_configuration'] and \
               force_text(ret['notification_configuration'][field]).startswith('$encrypted$'):
                ret['notification_configuration'][field] = '$encrypted$'
        return ret

    def get_related(self, obj):
        res = super(NotificationTemplateSerializer, self).get_related(obj)
        res.update(dict(
            test = reverse('api:notification_template_test', args=(obj.pk,)),
            notifications = reverse('api:notification_template_notification_list', args=(obj.pk,)),
        ))
        if obj.organization:
            res['organization'] = reverse('api:organization_detail', args=(obj.organization.pk,))
        return res

    def _recent_notifications(self, obj):
        return [{'id': x.id, 'status': x.status, 'created': x.created} for x in obj.notifications.all().order_by('-created')[:5]]

    def get_summary_fields(self, obj):
        d = super(NotificationTemplateSerializer, self).get_summary_fields(obj)
        d['recent_notifications'] = self._recent_notifications(obj)
        return d

    def validate(self, attrs):
        notification_class = NotificationTemplate.CLASS_FOR_NOTIFICATION_TYPE[attrs['notification_type']]
        missing_fields = []
        incorrect_type_fields = []
        if 'notification_configuration' not in attrs:
            return attrs
        if self.context['view'].kwargs:
            object_actual = self.context['view'].get_object()
        else:
            object_actual = None
        for field in notification_class.init_parameters:
            if field not in attrs['notification_configuration']:
                missing_fields.append(field)
                continue
            field_val = attrs['notification_configuration'][field]
            field_type = notification_class.init_parameters[field]['type']
            expected_types = self.type_map[field_type]
            if not type(field_val) in expected_types:
                incorrect_type_fields.append((field, field_type))
                continue
            if field_type == "password" and field_val == "$encrypted$" and object_actual is not None:
                attrs['notification_configuration'][field] = object_actual.notification_configuration[field]
        error_list = []
        if missing_fields:
            error_list.append("Missing required fields for Notification Configuration: {}.".format(missing_fields))
        if incorrect_type_fields:
            for type_field_error in incorrect_type_fields:
                error_list.append("Configuration field '{}' incorrect type, expected {}.".format(type_field_error[0],
                                                                                                 type_field_error[1]))
        if error_list:
            raise serializers.ValidationError(error_list)
        return attrs

class NotificationSerializer(BaseSerializer):

    class Meta:
        model = Notification
        fields = ('*', '-name', '-description', 'notification_template', 'error', 'status', 'notifications_sent',
                  'notification_type', 'recipients', 'subject')

    def get_related(self, obj):
        res = super(NotificationSerializer, self).get_related(obj)
        res.update(dict(
            notification_template = reverse('api:notification_template_detail', args=(obj.notification_template.pk,)),
        ))
        return res

class LabelSerializer(BaseSerializer):

    class Meta:
        model = Label
        fields = ('*', '-description', 'organization')

    def get_related(self, obj):
        res = super(LabelSerializer, self).get_related(obj)
        if obj.organization:
            res['organization'] = reverse('api:organization_detail', args=(obj.organization.pk,))
        return res

class ScheduleSerializer(BaseSerializer):

    class Meta:
        model = Schedule
        fields = ('*', 'unified_job_template', 'enabled', 'dtstart', 'dtend', 'rrule', 'next_run', 'extra_data')

    def get_related(self, obj):
        res = super(ScheduleSerializer, self).get_related(obj)
        res.update(dict(
            unified_jobs = reverse('api:schedule_unified_jobs_list', args=(obj.pk,)),
        ))
        if obj.unified_job_template:
            res['unified_job_template'] = obj.unified_job_template.get_absolute_url()
        return res

    def validate_unified_job_template(self, value):
        if type(value) == InventorySource and value.source not in SCHEDULEABLE_PROVIDERS:
            raise serializers.ValidationError('Inventory Source must be a cloud resource.')
        return value

    # We reject rrules if:
    # - DTSTART is not include
    # - INTERVAL is not included
    # - SECONDLY is used
    # - TZID is used
    # - BYDAY prefixed with a number (MO is good but not 20MO)
    # - BYYEARDAY
    # - BYWEEKNO
    # - Multiple DTSTART or RRULE elements
    # - COUNT > 999
    def validate_rrule(self, value):
        rrule_value = value
        multi_by_month_day = ".*?BYMONTHDAY[\:\=][0-9]+,-*[0-9]+"
        multi_by_month = ".*?BYMONTH[\:\=][0-9]+,[0-9]+"
        by_day_with_numeric_prefix = ".*?BYDAY[\:\=][0-9]+[a-zA-Z]{2}"
        match_count = re.match(".*?(COUNT\=[0-9]+)", rrule_value)
        match_multiple_dtstart = re.findall(".*?(DTSTART\:[0-9]+T[0-9]+Z)", rrule_value)
        match_multiple_rrule = re.findall(".*?(RRULE\:)", rrule_value)
        if not len(match_multiple_dtstart):
            raise serializers.ValidationError('DTSTART required in rrule. Value should match: DTSTART:YYYYMMDDTHHMMSSZ')
        if len(match_multiple_dtstart) > 1:
            raise serializers.ValidationError('Multiple DTSTART is not supported.')
        if not len(match_multiple_rrule):
            raise serializers.ValidationError('RRULE require in rrule.')
        if len(match_multiple_rrule) > 1:
            raise serializers.ValidationError('Multiple RRULE is not supported.')
        if 'interval' not in rrule_value.lower():
            raise serializers.ValidationError('INTERVAL required in rrule.')
        if 'tzid' in rrule_value.lower():
            raise serializers.ValidationError('TZID is not supported.')
        if 'secondly' in rrule_value.lower():
            raise serializers.ValidationError('SECONDLY is not supported.')
        if re.match(multi_by_month_day, rrule_value):
            raise serializers.ValidationError('Multiple BYMONTHDAYs not supported.')
        if re.match(multi_by_month, rrule_value):
            raise serializers.ValidationError('Multiple BYMONTHs not supported.')
        if re.match(by_day_with_numeric_prefix, rrule_value):
            raise serializers.ValidationError("BYDAY with numeric prefix not supported.")
        if 'byyearday' in rrule_value.lower():
            raise serializers.ValidationError("BYYEARDAY not supported.")
        if 'byweekno' in rrule_value.lower():
            raise serializers.ValidationError("BYWEEKNO not supported.")
        if match_count:
            count_val = match_count.groups()[0].strip().split("=")
            if int(count_val[1]) > 999:
                raise serializers.ValidationError("COUNT > 999 is unsupported.")
        try:
            rrule.rrulestr(rrule_value)
        except Exception:
            # TODO: Log
            raise serializers.ValidationError("rrule parsing failed validation.")
        return value

class ActivityStreamSerializer(BaseSerializer):

    changes = serializers.SerializerMethodField()
    object_association = serializers.SerializerMethodField()

    class Meta:
        model = ActivityStream
        fields = ('*', '-name', '-description', '-created', '-modified',
                  'timestamp', 'operation', 'changes', 'object1', 'object2', 'object_association')

    def get_fields(self):
        ret = super(ActivityStreamSerializer, self).get_fields()
        for key, field in ret.items():
            if key == 'changes':
                field.help_text = 'A summary of the new and changed values when an object is created, updated, or deleted'
            if key == 'object1':
                field.help_text = ('For create, update, and delete events this is the object type that was affected. '
                                   'For associate and disassociate events this is the object type associated or disassociated with object2.')
            if key == 'object2':
                field.help_text = ('Unpopulated for create, update, and delete events. For associate and disassociate '
                                   'events this is the object type that object1 is being associated with.')
            if key == 'operation':
                field.help_text = 'The action taken with respect to the given object(s).'
        return ret

    def get_changes(self, obj):
        if obj is None:
            return {}
        try:
            return json.loads(obj.changes)
        except Exception:
            # TODO: Log
            logger.warn("Error deserializing activity stream json changes")
        return {}

    def get_object_association(self, obj):
        try:
            return obj.object_relationship_type.split(".")[-1].split("_")[1]
        except:
            pass
        return ""

    def get_related(self, obj):
        rel = {}
        if obj.actor is not None:
            rel['actor'] = reverse('api:user_detail', args=(obj.actor.pk,))
        for fk, _ in SUMMARIZABLE_FK_FIELDS.items():
            if not hasattr(obj, fk):
                continue
            allm2m = getattr(obj, fk).all()
            if allm2m.count() > 0:
                rel[fk] = []
                for thisItem in allm2m:
                    rel[fk].append(reverse('api:' + fk + '_detail', args=(thisItem.id,)))
                    if fk == 'schedule':
                        rel['unified_job_template'] = thisItem.unified_job_template.get_absolute_url()
        return rel

    def get_summary_fields(self, obj):
        summary_fields = OrderedDict()
        for fk, related_fields in SUMMARIZABLE_FK_FIELDS.items():
            try:
                if not hasattr(obj, fk):
                    continue
                allm2m = getattr(obj, fk).all()
                if allm2m.count() > 0:
                    summary_fields[fk] = []
                    for thisItem in allm2m:
                        if fk == 'job':
                            summary_fields['job_template'] = []
                            job_template_item = {}
                            job_template_fields = SUMMARIZABLE_FK_FIELDS['job_template']
                            job_template = getattr(thisItem, 'job_template', None)
                            if job_template is not None:
                                for field in job_template_fields:
                                    fval = getattr(job_template, field, None)
                                    if fval is not None:
                                        job_template_item[field] = fval
                                summary_fields['job_template'].append(job_template_item)
                        if fk == 'schedule':
                            unified_job_template = getattr(thisItem, 'unified_job_template', None)
                            if unified_job_template is not None:
                                summary_fields[get_type_for_model(unified_job_template)] = {'id': unified_job_template.id,
                                                                                            'name': unified_job_template.name}
                        thisItemDict = {}
                        if 'id' not in related_fields:
                            related_fields = related_fields + ('id',)
                        for field in related_fields:
                            fval = getattr(thisItem, field, None)
                            if fval is not None:
                                thisItemDict[field] = fval
                        summary_fields[fk].append(thisItemDict)
            except ObjectDoesNotExist:
                pass
        if obj.actor is not None:
            summary_fields['actor'] = dict(id = obj.actor.id,
                                           username = obj.actor.username,
                                           first_name = obj.actor.first_name,
                                           last_name = obj.actor.last_name)
        return summary_fields


class TowerSettingsSerializer(BaseSerializer):

    value = VerbatimField()

    class Meta:
        model = TowerSettings
        fields = ('key', 'description', 'category', 'value', 'value_type', 'user')
        read_only_fields = ('description', 'category', 'value_type', 'user')

    def __init__(self, instance=None, data=serializers.empty, **kwargs):
        if instance is None and data is not serializers.empty and 'key' in data:
            try:
                instance = TowerSettings.objects.get(key=data['key'])
            except TowerSettings.DoesNotExist:
                pass
        super(TowerSettingsSerializer, self).__init__(instance, data, **kwargs)

    def to_representation(self, obj):
        ret = super(TowerSettingsSerializer, self).to_representation(obj)
        ret['value'] = getattr(obj, 'value_converted', obj.value)
        return ret

    def to_internal_value(self, data):
        if data['key'] not in settings.TOWER_SETTINGS_MANIFEST:
            self._errors = {'key': 'Key {0} is not a valid settings key.'.format(data['key'])}
            return
        ret = super(TowerSettingsSerializer, self).to_internal_value(data)
        manifest_val = settings.TOWER_SETTINGS_MANIFEST[data['key']]
        ret['description'] = manifest_val['description']
        ret['category'] = manifest_val['category']
        ret['value_type'] = manifest_val['type']
        return ret

    def validate(self, attrs):
        manifest = settings.TOWER_SETTINGS_MANIFEST
        if attrs['key'] not in manifest:
            raise serializers.ValidationError(dict(key=["Key {0} is not a valid settings key.".format(attrs['key'])]))

        if attrs['value_type'] == 'json':
            attrs['value'] = json.dumps(attrs['value'])
        elif attrs['value_type'] == 'list':
            try:
                attrs['value'] = ','.join(map(force_text, attrs['value']))
            except TypeError:
                attrs['value'] = force_text(attrs['value'])
        elif attrs['value_type'] == 'bool':
            attrs['value'] = force_text(bool(attrs['value']))
        else:
            attrs['value'] = force_text(attrs['value'])

        return super(TowerSettingsSerializer, self).validate(attrs)


class AuthTokenSerializer(serializers.Serializer):

    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Unable to login with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password".')


class FactVersionSerializer(BaseFactSerializer):

    class Meta:
        model = Fact
        fields = ('related', 'module', 'timestamp')
        read_only_fields = ('*',)

    def get_related(self, obj):
        res = super(FactVersionSerializer, self).get_related(obj)
        params = {
            'datetime': timestamp_apiformat(obj.timestamp),
            'module': obj.module,
        }
        res['fact_view'] = build_url('api:host_fact_compare_view', args=(obj.host.pk,), get=params)
        return res

class FactSerializer(BaseFactSerializer):

    class Meta:
        model = Fact
        # TODO: Consider adding in host to the fields list ?
        fields = ('related', 'timestamp', 'module', 'facts', 'id', 'summary_fields', 'host')
        read_only_fields = ('*',)

    def get_related(self, obj):
        res = super(FactSerializer, self).get_related(obj)
        res['host'] = obj.host.get_absolute_url()
        return res

