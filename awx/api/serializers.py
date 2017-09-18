# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import copy
import json
import logging
import re
import six
import urllib
from collections import OrderedDict
from dateutil import rrule

# PyYAML
import yaml

# Django
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError as DjangoValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.utils.timezone import now
from django.utils.functional import cached_property

# Django REST Framework
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import fields
from rest_framework import serializers
from rest_framework import validators
from rest_framework.utils.serializer_helpers import ReturnList

# Django-Polymorphic
from polymorphic.models import PolymorphicModel

# AWX
from awx.main.constants import SCHEDULEABLE_PROVIDERS, ANSI_SGR_PATTERN
from awx.main.models import * # noqa
from awx.main.access import get_user_capabilities
from awx.main.fields import ImplicitRoleField
from awx.main.utils import (
    get_type_for_model, get_model_for_type, timestamp_apiformat,
    camelcase_to_underscore, getattrd, parse_yaml_or_json,
    has_model_field_prefetched)
from awx.main.utils.filters import SmartFilter

from awx.main.validators import vars_validate_or_raise

from awx.conf.license import feature_enabled
from awx.api.versioning import reverse, get_request_version
from awx.api.fields import BooleanNullField, CharNullField, ChoiceNullField, VerbatimField

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
                                           'inventory_sources_with_failures',
                                           'organization_id',
                                           'kind',
                                           'insights_credential_id',),
    'host': DEFAULT_SUMMARY_FIELDS + ('has_active_failures',
                                      'has_inventory_sources'),
    'group': DEFAULT_SUMMARY_FIELDS + ('has_active_failures',
                                       'total_hosts',
                                       'hosts_with_active_failures',
                                       'total_groups',
                                       'groups_with_active_failures',
                                       'has_inventory_sources'),
    'project': DEFAULT_SUMMARY_FIELDS + ('status', 'scm_type'),
    'source_project': DEFAULT_SUMMARY_FIELDS + ('status', 'scm_type'),
    'project_update': DEFAULT_SUMMARY_FIELDS + ('status', 'failed',),
    'credential': DEFAULT_SUMMARY_FIELDS + ('kind', 'cloud', 'credential_type_id'),
    'vault_credential': DEFAULT_SUMMARY_FIELDS + ('kind', 'cloud', 'credential_type_id'),
    'job': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'elapsed'),
    'job_template': DEFAULT_SUMMARY_FIELDS,
    'workflow_job_template': DEFAULT_SUMMARY_FIELDS,
    'workflow_job': DEFAULT_SUMMARY_FIELDS,
    'schedule': DEFAULT_SUMMARY_FIELDS + ('next_run',),
    'unified_job_template': DEFAULT_SUMMARY_FIELDS + ('unified_job_type',),
    'last_job': DEFAULT_SUMMARY_FIELDS + ('finished', 'status', 'failed', 'license_error'),
    'last_job_host_summary': DEFAULT_SUMMARY_FIELDS + ('failed',),
    'last_update': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
    'current_update': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
    'current_job': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
    'inventory_source': ('source', 'last_updated', 'status'),
    'custom_inventory_script': DEFAULT_SUMMARY_FIELDS,
    'source_script': ('name', 'description'),
    'role': ('id', 'role_field'),
    'notification_template': DEFAULT_SUMMARY_FIELDS,
    'instance_group': {'id', 'name', 'controller_id'},
    'insights_credential': DEFAULT_SUMMARY_FIELDS,
}


def reverse_gfk(content_object, request):
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
        camelcase_to_underscore(content_object.__class__.__name__): content_object.get_absolute_url(request=request)
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
        summary_fields = ()
        summarizable_fields = ()

    # add the URL and related resources
    type           = serializers.SerializerMethodField()
    url            = serializers.SerializerMethodField()
    related        = serializers.SerializerMethodField('_get_related')
    summary_fields = serializers.SerializerMethodField('_get_summary_fields')

    # make certain fields read only
    created       = serializers.SerializerMethodField()
    modified      = serializers.SerializerMethodField()

    @property
    def version(self):
        """
        The request version component of the URL as an integer i.e., 1 or 2
        """
        return get_request_version(self.context.get('request'))

    def get_type(self, obj):
        return get_type_for_model(self.Meta.model)

    def get_types(self):
        return [self.get_type(None)]

    def get_type_choices(self):
        type_name_map = {
            'job': _('Playbook Run'),
            'ad_hoc_command': _('Command'),
            'project_update': _('SCM Update'),
            'inventory_update': _('Inventory Sync'),
            'system_job': _('Management Job'),
            'workflow_job': _('Workflow Job'),
            'workflow_job_template': _('Workflow Template'),
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
            return self.reverse('api:user_detail', kwargs={'pk': obj.pk})
        else:
            return obj.get_absolute_url(request=self.context.get('request'))

    def filter_field_metadata(self, fields, method):
        """
        Filter field metadata based on the request method.
        This it intended to be extended by subclasses.
        """
        return fields

    def _get_related(self, obj):
        return {} if obj is None else self.get_related(obj)

    def _generate_named_url(self, url_path, obj, node):
        url_units = url_path.split('/')
        named_url = node.generate_named_url(obj)
        url_units[4] = named_url
        return '/'.join(url_units)

    def get_related(self, obj):
        res = OrderedDict()
        view = self.context.get('view', None)
        if view and (hasattr(view, 'retrieve') or view.request.method == 'POST') and \
                type(obj) in settings.NAMED_URL_GRAPH:
            original_url = self.get_url(obj)
            if not original_url.startswith('/api/v1'):
                res['named_url'] = self._generate_named_url(
                    original_url, obj, settings.NAMED_URL_GRAPH[type(obj)]
                )
        if getattr(obj, 'created_by', None):
            res['created_by'] = self.reverse('api:user_detail', kwargs={'pk': obj.created_by.pk})
        if getattr(obj, 'modified_by', None):
            res['modified_by'] = self.reverse('api:user_detail', kwargs={'pk': obj.modified_by.pk})
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
                if fk == 'project' and (isinstance(obj, InventorySource) or
                                        isinstance(obj, Project)):
                    continue

                fkval = getattr(obj, fk, None)
                if fkval is None:
                    continue
                if fkval == obj:
                    continue
                summary_fields[fk] = OrderedDict()
                for field in related_fields:
                    if field == 'credential_type_id' and fk == 'credential' and self.version < 2:  # TODO: remove version check in 3.3
                        continue

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
        roles = {}
        for field in obj._meta.get_fields():
            if type(field) is ImplicitRoleField:
                roles[field.name] = role_summary_fields_generator(obj, field.name)
        if len(roles) > 0:
            summary_fields['object_roles'] = roles

        # Advance display of RBAC capabilities
        if hasattr(self, 'show_capabilities'):
            view = self.context.get('view', None)
            parent_obj = None
            if view and hasattr(view, 'parent_model') and hasattr(view, 'get_parent_object'):
                parent_obj = view.get_parent_object()
            if view and view.request and view.request.user:
                user_capabilities = get_user_capabilities(
                    view.request.user, obj, method_list=self.show_capabilities, parent_obj=parent_obj)
                if user_capabilities:
                    summary_fields['user_capabilities'] = user_capabilities

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

    def reverse(self, *args, **kwargs):
        kwargs['request'] = self.context.get('request')
        return reverse(*args, **kwargs)


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
        fields = ('*', 'last_job_run', 'last_job_failed',
                  'next_job_run', 'status')

    def get_related(self, obj):
        res = super(UnifiedJobTemplateSerializer, self).get_related(obj)
        if obj.current_job:
            res['current_job'] = obj.current_job.get_absolute_url(request=self.context.get('request'))
        if obj.last_job:
            res['last_job'] = obj.last_job.get_absolute_url(request=self.context.get('request'))
        if obj.next_schedule:
            res['next_schedule'] = obj.next_schedule.get_absolute_url(request=self.context.get('request'))
        return res

    def get_types(self):
        if type(self) is UnifiedJobTemplateSerializer:
            return ['project', 'inventory_source', 'job_template', 'system_job_template', 'workflow_job_template',]
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
            elif isinstance(obj, SystemJobTemplate):
                serializer_class = SystemJobTemplateSerializer
            elif isinstance(obj, WorkflowJobTemplate):
                serializer_class = WorkflowJobTemplateSerializer
        if serializer_class:
            serializer = serializer_class(instance=obj, context=self.context)
            return serializer.to_representation(obj)
        else:
            return super(UnifiedJobTemplateSerializer, self).to_representation(obj)


class UnifiedJobSerializer(BaseSerializer):
    show_capabilities = ['start', 'delete']

    result_stdout = serializers.SerializerMethodField()

    class Meta:
        model = UnifiedJob
        fields = ('*', 'unified_job_template', 'launch_type', 'status',
                  'failed', 'started', 'finished', 'elapsed', 'job_args',
                  'job_cwd', 'job_env', 'job_explanation', 'result_stdout',
                  'execution_node', 'result_traceback')
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
            return ['project_update', 'inventory_update', 'job', 'ad_hoc_command', 'system_job', 'workflow_job',]
        else:
            return super(UnifiedJobSerializer, self).get_types()

    def get_related(self, obj):
        res = super(UnifiedJobSerializer, self).get_related(obj)
        if obj.unified_job_template:
            res['unified_job_template'] = obj.unified_job_template.get_absolute_url(request=self.context.get('request'))
        if obj.schedule:
            res['schedule'] = obj.schedule.get_absolute_url(request=self.context.get('request'))
        if isinstance(obj, ProjectUpdate):
            res['stdout'] = self.reverse('api:project_update_stdout', kwargs={'pk': obj.pk})
        elif isinstance(obj, InventoryUpdate):
            res['stdout'] = self.reverse('api:inventory_update_stdout', kwargs={'pk': obj.pk})
        elif isinstance(obj, Job):
            res['stdout'] = self.reverse('api:job_stdout', kwargs={'pk': obj.pk})
        elif isinstance(obj, AdHocCommand):
            res['stdout'] = self.reverse('api:ad_hoc_command_stdout', kwargs={'pk': obj.pk})
        if obj.workflow_job_id:
            res['source_workflow_job'] = self.reverse('api:workflow_job_detail', kwargs={'pk': obj.workflow_job_id})
        return res

    def get_summary_fields(self, obj):
        summary_fields = super(UnifiedJobSerializer, self).get_summary_fields(obj)
        if obj.spawned_by_workflow:
            summary_fields['source_workflow_job'] = {}
            try:
                summary_obj = obj.unified_job_node.workflow_job
            except UnifiedJob.unified_job_node.RelatedObjectDoesNotExist:
                return summary_fields

            for field in SUMMARIZABLE_FK_FIELDS['job']:
                val = getattr(summary_obj, field, None)
                if val is not None:
                    summary_fields['source_workflow_job'][field] = val

        return summary_fields

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
            elif isinstance(obj, WorkflowJob):
                serializer_class = WorkflowJobSerializer
        if serializer_class:
            serializer = serializer_class(instance=obj, context=self.context)
            ret = serializer.to_representation(obj)
        else:
            ret = super(UnifiedJobSerializer, self).to_representation(obj)

        if 'elapsed' in ret:
            if obj and obj.pk and obj.started and not obj.finished:
                td = now() - obj.started
                ret['elapsed'] = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6) / (10 ** 6 * 1.0)
            ret['elapsed'] = float(ret['elapsed'])

        return ret

    def get_result_stdout(self, obj):
        obj_size = obj.result_stdout_size
        if obj_size > settings.STDOUT_MAX_BYTES_DISPLAY:
            return _("Standard Output too large to display (%(text_size)d bytes), "
                     "only download supported for sizes over %(supported_size)d bytes") % {
                'text_size': obj_size, 'supported_size': settings.STDOUT_MAX_BYTES_DISPLAY}
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
            return ['project_update', 'inventory_update', 'job', 'ad_hoc_command', 'system_job', 'workflow_job']
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
            elif isinstance(obj, WorkflowJob):
                serializer_class = WorkflowJobSerializer
        if serializer_class:
            serializer = serializer_class(instance=obj, context=self.context)
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
        if obj_size > settings.STDOUT_MAX_BYTES_DISPLAY:
            return _("Standard Output too large to display (%(text_size)d bytes), "
                     "only download supported for sizes over %(supported_size)d bytes") % {
                'text_size': obj_size, 'supported_size': settings.STDOUT_MAX_BYTES_DISPLAY}
        return obj.result_stdout

    def get_types(self):
        if type(self) is UnifiedJobStdoutSerializer:
            return ['project_update', 'inventory_update', 'job', 'ad_hoc_command', 'system_job']
        else:
            return super(UnifiedJobStdoutSerializer, self).get_types()


class UserSerializer(BaseSerializer):

    password = serializers.CharField(required=False, default='', write_only=True,
                                     help_text=_('Write-only field used to change the password.'))
    ldap_dn = serializers.CharField(source='profile.ldap_dn', read_only=True)
    external_account = serializers.SerializerMethodField(help_text=_('Set if the account is managed by an external service'))
    is_system_auditor = serializers.BooleanField(default=False)
    show_capabilities = ['edit', 'delete']

    class Meta:
        model = User
        fields = ('*', '-name', '-description', '-modified',
                  'username', 'first_name', 'last_name',
                  'email', 'is_superuser', 'is_system_auditor', 'password', 'ldap_dn', 'external_account')

    def to_representation(self, obj):  # TODO: Remove in 3.3
        ret = super(UserSerializer, self).to_representation(obj)
        ret.pop('password', None)
        if obj and type(self) is UserSerializer or self.version == 1:
            ret['auth'] = obj.social_auth.values('provider', 'uid')
        return ret

    def get_validation_exclusions(self, obj=None):
        ret = super(UserSerializer, self).get_validation_exclusions(obj)
        ret.append('password')
        return ret

    def validate_password(self, value):
        if not self.instance and value in (None, ''):
            raise serializers.ValidationError(_('Password required for new User.'))
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
        if (getattr(settings, 'RADIUS_SERVER', None) or
                getattr(settings, 'TACACSPLUS_HOST', None)) and obj.enterprise_auth.all():
            new_password = None
        if new_password:
            obj.set_password(new_password)
            obj.save(update_fields=['password'])
        elif not obj.password:
            obj.set_unusable_password()
            obj.save(update_fields=['password'])

    def get_external_account(self, obj):
        account_type = None
        if getattr(settings, 'AUTH_LDAP_SERVER_URI', None) and feature_enabled('ldap'):
            try:
                if obj.pk and obj.profile.ldap_dn and not obj.has_usable_password():
                    account_type = "ldap"
            except AttributeError:
                pass
        if (getattr(settings, 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', None) or
                getattr(settings, 'SOCIAL_AUTH_GITHUB_KEY', None) or
                getattr(settings, 'SOCIAL_AUTH_GITHUB_ORG_KEY', None) or
                getattr(settings, 'SOCIAL_AUTH_GITHUB_TEAM_KEY', None) or
                getattr(settings, 'SOCIAL_AUTH_SAML_ENABLED_IDPS', None)) and obj.social_auth.all():
            account_type = "social"
        if (getattr(settings, 'RADIUS_SERVER', None) or
                getattr(settings, 'TACACSPLUS_HOST', None)) and obj.enterprise_auth.all():
            account_type = "enterprise"
        return account_type

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
            teams                  = self.reverse('api:user_teams_list',               kwargs={'pk': obj.pk}),
            organizations          = self.reverse('api:user_organizations_list',       kwargs={'pk': obj.pk}),
            admin_of_organizations = self.reverse('api:user_admin_of_organizations_list', kwargs={'pk': obj.pk}),
            projects               = self.reverse('api:user_projects_list',            kwargs={'pk': obj.pk}),
            credentials            = self.reverse('api:user_credentials_list',         kwargs={'pk': obj.pk}),
            roles                  = self.reverse('api:user_roles_list',               kwargs={'pk': obj.pk}),
            activity_stream        = self.reverse('api:user_activity_stream_list',     kwargs={'pk': obj.pk}),
            access_list            = self.reverse('api:user_access_list',              kwargs={'pk': obj.pk}),
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
                    raise serializers.ValidationError(_('Unable to change %s on user managed by LDAP.') % field_name)
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
    show_capabilities = ['edit', 'delete']

    class Meta:
        model = Organization
        fields = ('*',)

    def get_related(self, obj):
        res = super(OrganizationSerializer, self).get_related(obj)
        res.update(dict(
            projects    = self.reverse('api:organization_projects_list',       kwargs={'pk': obj.pk}),
            inventories = self.reverse('api:organization_inventories_list',    kwargs={'pk': obj.pk}),
            workflow_job_templates = self.reverse('api:organization_workflow_job_templates_list', kwargs={'pk': obj.pk}),
            users       = self.reverse('api:organization_users_list',          kwargs={'pk': obj.pk}),
            admins      = self.reverse('api:organization_admins_list',         kwargs={'pk': obj.pk}),
            teams       = self.reverse('api:organization_teams_list',          kwargs={'pk': obj.pk}),
            credentials = self.reverse('api:organization_credential_list',     kwargs={'pk': obj.pk}),
            activity_stream = self.reverse('api:organization_activity_stream_list', kwargs={'pk': obj.pk}),
            notification_templates = self.reverse('api:organization_notification_templates_list', kwargs={'pk': obj.pk}),
            notification_templates_any = self.reverse('api:organization_notification_templates_any_list', kwargs={'pk': obj.pk}),
            notification_templates_success = self.reverse('api:organization_notification_templates_success_list', kwargs={'pk': obj.pk}),
            notification_templates_error = self.reverse('api:organization_notification_templates_error_list', kwargs={'pk': obj.pk}),
            object_roles = self.reverse('api:organization_object_roles_list', kwargs={'pk': obj.pk}),
            access_list = self.reverse('api:organization_access_list', kwargs={'pk': obj.pk}),
            instance_groups = self.reverse('api:organization_instance_groups_list', kwargs={'pk': obj.pk}),
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
                  'scm_clean', 'scm_delete_on_update', 'credential', 'timeout',)

    def get_related(self, obj):
        res = super(ProjectOptionsSerializer, self).get_related(obj)
        if obj.credential:
            res['credential'] = self.reverse('api:credential_detail',
                                             kwargs={'pk': obj.credential.pk})
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
    show_capabilities = ['start', 'schedule', 'edit', 'delete']

    class Meta:
        model = Project
        fields = ('*', 'organization', 'scm_delete_on_next_update', 'scm_update_on_launch',
                  'scm_update_cache_timeout', 'scm_revision',) + \
                 ('last_update_failed', 'last_updated')  # Backwards compatibility
        read_only_fields = ('scm_delete_on_next_update',)

    def get_related(self, obj):
        res = super(ProjectSerializer, self).get_related(obj)
        res.update(dict(
            teams = self.reverse('api:project_teams_list', kwargs={'pk': obj.pk}),
            playbooks = self.reverse('api:project_playbooks', kwargs={'pk': obj.pk}),
            inventory_files = self.reverse('api:project_inventories', kwargs={'pk': obj.pk}),
            update = self.reverse('api:project_update_view', kwargs={'pk': obj.pk}),
            project_updates = self.reverse('api:project_updates_list', kwargs={'pk': obj.pk}),
            scm_inventory_sources = self.reverse('api:project_scm_inventory_sources', kwargs={'pk': obj.pk}),
            schedules = self.reverse('api:project_schedules_list', kwargs={'pk': obj.pk}),
            activity_stream = self.reverse('api:project_activity_stream_list', kwargs={'pk': obj.pk}),
            notification_templates_any = self.reverse('api:project_notification_templates_any_list', kwargs={'pk': obj.pk}),
            notification_templates_success = self.reverse('api:project_notification_templates_success_list', kwargs={'pk': obj.pk}),
            notification_templates_error = self.reverse('api:project_notification_templates_error_list', kwargs={'pk': obj.pk}),
            access_list = self.reverse('api:project_access_list', kwargs={'pk': obj.pk}),
            object_roles = self.reverse('api:project_object_roles_list', kwargs={'pk': obj.pk}),
        ))
        if obj.organization:
            res['organization'] = self.reverse('api:organization_detail',
                                               kwargs={'pk': obj.organization.pk})
        # Backwards compatibility.
        if obj.current_update:
            res['current_update'] = self.reverse('api:project_update_detail',
                                                 kwargs={'pk': obj.current_update.pk})
        if obj.last_update:
            res['last_update'] = self.reverse('api:project_update_detail',
                                              kwargs={'pk': obj.last_update.pk})
        return res

    def to_representation(self, obj):
        ret = super(ProjectSerializer, self).to_representation(obj)
        if 'scm_revision' in ret and obj.scm_type == '':
            ret['scm_revision'] = ''
        return ret

    def validate(self, attrs):
        def get_field_from_model_or_attrs(fd):
            return attrs.get(fd, self.instance and getattr(self.instance, fd) or None)

        organization = None
        if 'organization' in attrs:
            organization = attrs['organization']
        elif self.instance:
            organization = self.instance.organization

        view = self.context.get('view', None)
        if not organization and not view.request.user.is_superuser:
            # Only allow super users to create orgless projects
            raise serializers.ValidationError(_('Organization is missing'))
        elif get_field_from_model_or_attrs('scm_type') == '':
            for fd in ('scm_update_on_launch', 'scm_delete_on_update', 'scm_clean'):
                if get_field_from_model_or_attrs(fd):
                    raise serializers.ValidationError({fd: _('Update options must be set to false for manual projects.')})
        return super(ProjectSerializer, self).validate(attrs)


class ProjectPlaybooksSerializer(ProjectSerializer):

    playbooks = serializers.SerializerMethodField(help_text=_('Array of playbooks available within this project.'))

    class Meta:
        model = Project
        fields = ('playbooks',)

    def get_playbooks(self, obj):
        return obj.playbook_files if obj.scm_type else obj.playbooks

    @property
    def data(self):
        ret = super(ProjectPlaybooksSerializer, self).data
        ret = ret.get('playbooks', [])
        return ReturnList(ret, serializer=self)


class ProjectInventoriesSerializer(ProjectSerializer):

    inventory_files = serializers.ReadOnlyField(help_text=_(
        'Array of inventory files and directories available within this project, '
        'not comprehensive.'))

    class Meta:
        model = Project
        fields = ('inventory_files',)

    @property
    def data(self):
        ret = super(ProjectInventoriesSerializer, self).data
        ret = ret.get('inventory_files', [])
        return ReturnList(ret, serializer=self)


class ProjectUpdateViewSerializer(ProjectSerializer):

    can_update = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_update',)


class ProjectUpdateSerializer(UnifiedJobSerializer, ProjectOptionsSerializer):

    class Meta:
        model = ProjectUpdate
        fields = ('*', 'project', 'job_type')

    def get_related(self, obj):
        res = super(ProjectUpdateSerializer, self).get_related(obj)
        res.update(dict(
            project = self.reverse('api:project_detail', kwargs={'pk': obj.project.pk}),
            cancel = self.reverse('api:project_update_cancel', kwargs={'pk': obj.pk}),
            scm_inventory_updates = self.reverse('api:project_update_scm_inventory_updates', kwargs={'pk': obj.pk}),
            notifications = self.reverse('api:project_update_notifications_list', kwargs={'pk': obj.pk}),
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
        return vars_validate_or_raise(value)


class InventorySerializer(BaseSerializerWithVariables):
    show_capabilities = ['edit', 'delete', 'adhoc']

    class Meta:
        model = Inventory
        fields = ('*', 'organization', 'kind', 'host_filter', 'variables', 'has_active_failures',
                  'total_hosts', 'hosts_with_active_failures', 'total_groups',
                  'groups_with_active_failures', 'has_inventory_sources',
                  'total_inventory_sources', 'inventory_sources_with_failures',
                  'insights_credential', 'pending_deletion',)

    def get_related(self, obj):
        res = super(InventorySerializer, self).get_related(obj)
        res.update(dict(
            hosts         = self.reverse('api:inventory_hosts_list',        kwargs={'pk': obj.pk}),
            groups        = self.reverse('api:inventory_groups_list',       kwargs={'pk': obj.pk}),
            root_groups   = self.reverse('api:inventory_root_groups_list',  kwargs={'pk': obj.pk}),
            variable_data = self.reverse('api:inventory_variable_data',     kwargs={'pk': obj.pk}),
            script        = self.reverse('api:inventory_script_view',       kwargs={'pk': obj.pk}),
            tree          = self.reverse('api:inventory_tree_view',         kwargs={'pk': obj.pk}),
            inventory_sources = self.reverse('api:inventory_inventory_sources_list', kwargs={'pk': obj.pk}),
            update_inventory_sources = self.reverse('api:inventory_inventory_sources_update', kwargs={'pk': obj.pk}),
            activity_stream = self.reverse('api:inventory_activity_stream_list', kwargs={'pk': obj.pk}),
            job_templates = self.reverse('api:inventory_job_template_list', kwargs={'pk': obj.pk}),
            ad_hoc_commands = self.reverse('api:inventory_ad_hoc_commands_list', kwargs={'pk': obj.pk}),
            access_list = self.reverse('api:inventory_access_list',         kwargs={'pk': obj.pk}),
            object_roles = self.reverse('api:inventory_object_roles_list', kwargs={'pk': obj.pk}),
            instance_groups = self.reverse('api:inventory_instance_groups_list', kwargs={'pk': obj.pk}),
        ))
        if obj.insights_credential:
            res['insights_credential'] = self.reverse('api:credential_detail', kwargs={'pk': obj.insights_credential.pk})
        if obj.organization:
            res['organization'] = self.reverse('api:organization_detail', kwargs={'pk': obj.organization.pk})
        return res

    def to_representation(self, obj):
        ret = super(InventorySerializer, self).to_representation(obj)
        if obj is not None and 'organization' in ret and not obj.organization:
            ret['organization'] = None
        return ret

    def validate_host_filter(self, host_filter):
        if host_filter:
            try:
                SmartFilter().query_from_string(host_filter)
            except RuntimeError, e:
                raise models.base.ValidationError(e)
        return host_filter

    def validate(self, attrs):
        kind = None
        if 'kind' in attrs:
            kind = attrs['kind']
        elif self.instance:
            kind = self.instance.kind

        host_filter = None
        if 'host_filter' in attrs:
            host_filter = attrs['host_filter']
        elif self.instance:
            host_filter = self.instance.host_filter

        if kind == 'smart' and not host_filter:
            raise serializers.ValidationError({'host_filter': _(
                'Smart inventories must specify host_filter')})
        return super(InventorySerializer, self).validate(attrs)


# TODO: Remove entire serializer in 3.3, replace with normal serializer
class InventoryDetailSerializer(InventorySerializer):

    def get_fields(self):
        fields = super(InventoryDetailSerializer, self).get_fields()
        if self.version == 1:
            fields['can_run_ad_hoc_commands'] = serializers.SerializerMethodField()
        return fields

    def get_can_run_ad_hoc_commands(self, obj):
        view = self.context.get('view', None)
        return bool(obj and view and view.request and view.request.user and view.request.user.can_access(Inventory, 'run_ad_hoc_commands', obj))


class InventoryScriptSerializer(InventorySerializer):

    class Meta:
        fields = ()


class HostSerializer(BaseSerializerWithVariables):
    show_capabilities = ['edit', 'delete']

    class Meta:
        model = Host
        fields = ('*', 'inventory', 'enabled', 'instance_id', 'variables',
                  'has_active_failures', 'has_inventory_sources', 'last_job',
                  'last_job_host_summary', 'insights_system_id')
        read_only_fields = ('last_job', 'last_job_host_summary', 'insights_system_id',)

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
            variable_data = self.reverse('api:host_variable_data',   kwargs={'pk': obj.pk}),
            groups        = self.reverse('api:host_groups_list',     kwargs={'pk': obj.pk}),
            all_groups    = self.reverse('api:host_all_groups_list', kwargs={'pk': obj.pk}),
            job_events    = self.reverse('api:host_job_events_list',  kwargs={'pk': obj.pk}),
            job_host_summaries = self.reverse('api:host_job_host_summaries_list', kwargs={'pk': obj.pk}),
            activity_stream = self.reverse('api:host_activity_stream_list', kwargs={'pk': obj.pk}),
            inventory_sources = self.reverse('api:host_inventory_sources_list', kwargs={'pk': obj.pk}),
            smart_inventories = self.reverse('api:host_smart_inventories_list', kwargs={'pk': obj.pk}),
            ad_hoc_commands = self.reverse('api:host_ad_hoc_commands_list', kwargs={'pk': obj.pk}),
            ad_hoc_command_events = self.reverse('api:host_ad_hoc_command_events_list', kwargs={'pk': obj.pk}),
            fact_versions = self.reverse('api:host_fact_versions_list', kwargs={'pk': obj.pk}),
        ))
        if self.version > 1:
            res['insights'] = self.reverse('api:host_insights', kwargs={'pk': obj.pk})
        if obj.inventory:
            res['inventory'] = self.reverse('api:inventory_detail', kwargs={'pk': obj.inventory.pk})
        if obj.last_job:
            res['last_job'] = self.reverse('api:job_detail', kwargs={'pk': obj.last_job.pk})
        if obj.last_job_host_summary:
            res['last_job_host_summary'] = self.reverse('api:job_host_summary_detail', kwargs={'pk': obj.last_job_host_summary.pk})
        if self.version > 1:
            res.update(dict(
                ansible_facts = self.reverse('api:host_ansible_facts_detail', kwargs={'pk': obj.pk}),
            ))
        return res

    def get_summary_fields(self, obj):
        d = super(HostSerializer, self).get_summary_fields(obj)
        try:
            d['last_job']['job_template_id'] = obj.last_job.job_template.id
            d['last_job']['job_template_name'] = obj.last_job.job_template.name
        except (KeyError, AttributeError):
            pass
        if has_model_field_prefetched(obj, 'groups'):
            group_list = sorted([{'id': g.id, 'name': g.name} for g in obj.groups.all()], key=lambda x: x['id'])[:5]
        else:
            group_list = [{'id': g.id, 'name': g.name} for g in obj.groups.all().order_by('id')[:5]]
        group_cnt = obj.groups.count()
        d.setdefault('groups', {'count': group_cnt, 'results': group_list})
        d.setdefault('recent_jobs', [{
            'id': j.job.id,
            'name': j.job.job_template.name if j.job.job_template is not None else "",
            'status': j.job.status,
            'finished': j.job.finished,
        } for j in obj.job_host_summaries.select_related('job__job_template').order_by('-created')[:5]])
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
                raise serializers.ValidationError(_(u'Invalid port specification: %s') % force_text(port))
        return name, port

    def validate_name(self, value):
        name = force_text(value or '')
        # Validate here only, update in main validate method.
        host, port = self._get_host_port_from_name(name)
        return value

    def validate_inventory(self, value):
        if value.kind == 'smart':
            raise serializers.ValidationError({"detail": _("Cannot create Host for Smart Inventory")})
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
                    raise serializers.ValidationError({'variables': _('Must be valid JSON or YAML.')})

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


class AnsibleFactsSerializer(BaseSerializer):
    class Meta:
        model = Host

    def to_representation(self, obj):
        return obj.ansible_facts


class GroupSerializer(BaseSerializerWithVariables):

    class Meta:
        model = Group
        fields = ('*', 'inventory', 'variables', 'has_active_failures',
                  'total_hosts', 'hosts_with_active_failures', 'total_groups',
                  'groups_with_active_failures', 'has_inventory_sources')

    @property
    def show_capabilities(self):  # TODO: consolidate in 3.3
        if self.version == 1:
            return ['copy', 'edit', 'start', 'schedule', 'delete']
        else:
            return ['copy', 'edit', 'delete']

    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super(GroupSerializer, self).build_relational_field(field_name, relation_info)
        # Inventory is read-only unless creating a new group.
        if self.instance and field_name == 'inventory':
            field_kwargs['read_only'] = True
            field_kwargs.pop('queryset', None)
        return field_class, field_kwargs

    def get_summary_fields(self, obj):  # TODO: remove in 3.3
        summary_fields = super(GroupSerializer, self).get_summary_fields(obj)
        if self.version == 1:
            try:
                inv_src = obj.deprecated_inventory_source
                summary_fields['inventory_source'] = {}
                for field in SUMMARIZABLE_FK_FIELDS['inventory_source']:
                    fval = getattr(inv_src, field, None)
                    if fval is not None:
                        summary_fields['inventory_source'][field] = fval
            except Group.deprecated_inventory_source.RelatedObjectDoesNotExist:
                pass
        return summary_fields

    def get_related(self, obj):
        res = super(GroupSerializer, self).get_related(obj)
        res.update(dict(
            variable_data = self.reverse('api:group_variable_data',   kwargs={'pk': obj.pk}),
            hosts         = self.reverse('api:group_hosts_list',      kwargs={'pk': obj.pk}),
            potential_children = self.reverse('api:group_potential_children_list',   kwargs={'pk': obj.pk}),
            children      = self.reverse('api:group_children_list',   kwargs={'pk': obj.pk}),
            all_hosts     = self.reverse('api:group_all_hosts_list',  kwargs={'pk': obj.pk}),
            job_events    = self.reverse('api:group_job_events_list',   kwargs={'pk': obj.pk}),
            job_host_summaries = self.reverse('api:group_job_host_summaries_list', kwargs={'pk': obj.pk}),
            activity_stream = self.reverse('api:group_activity_stream_list', kwargs={'pk': obj.pk}),
            inventory_sources = self.reverse('api:group_inventory_sources_list', kwargs={'pk': obj.pk}),
            ad_hoc_commands = self.reverse('api:group_ad_hoc_commands_list', kwargs={'pk': obj.pk}),
        ))
        if self.version == 1:  # TODO: remove in 3.3
            try:
                res['inventory_source'] = self.reverse('api:inventory_source_detail',
                                                       kwargs={'pk': obj.deprecated_inventory_source.pk})
            except Group.deprecated_inventory_source.RelatedObjectDoesNotExist:
                pass
        if obj.inventory:
            res['inventory'] = self.reverse('api:inventory_detail', kwargs={'pk': obj.inventory.pk})
        return res

    def create(self, validated_data):  # TODO: remove in 3.3
        instance = super(GroupSerializer, self).create(validated_data)
        if self.version == 1:  # TODO: remove in 3.3
            manual_src = InventorySource(deprecated_group=instance, inventory=instance.inventory)
            manual_src.v1_group_name = instance.name
            manual_src.save()
        return instance

    def validate_name(self, value):
        if value in ('all', '_meta'):
            raise serializers.ValidationError(_('Invalid group name.'))
        return value

    def validate_inventory(self, value):
        if value.kind == 'smart':
            raise serializers.ValidationError({"detail": _("Cannot create Group for Smart Inventory")})
        return value

    def to_representation(self, obj):
        ret = super(GroupSerializer, self).to_representation(obj)
        if obj is not None and 'inventory' in ret and not obj.inventory:
            ret['inventory'] = None
        return ret


class GroupTreeSerializer(GroupSerializer):

    children = serializers.SerializerMethodField()

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
        return parse_yaml_or_json(ret.get('variables', '') or '{}')

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
    show_capabilities = ['edit', 'delete']

    class Meta:
        model = CustomInventoryScript
        fields = ('*', "script", "organization")

    def validate_script(self, value):
        if not value.startswith("#!"):
            raise serializers.ValidationError(_('Script must begin with a hashbang sequence: i.e.... #!/usr/bin/env python'))
        return value

    def to_representation(self, obj):
        ret = super(CustomInventoryScriptSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        request = self.context.get('request', None)
        if request.user not in obj.admin_role and \
           not request.user.is_superuser and \
           not request.user.is_system_auditor and \
           not (obj.organization is not None and request.user in obj.organization.auditor_role):
            ret['script'] = None
        return ret

    def get_related(self, obj):
        res = super(CustomInventoryScriptSerializer, self).get_related(obj)
        res.update(dict(
            object_roles = self.reverse('api:inventory_script_object_roles_list', kwargs={'pk': obj.pk}),
        ))

        if obj.organization:
            res['organization'] = self.reverse('api:organization_detail', kwargs={'pk': obj.organization.pk})
        return res


class InventorySourceOptionsSerializer(BaseSerializer):

    class Meta:
        fields = ('*', 'source', 'source_path', 'source_script', 'source_vars', 'credential',
                  'source_regions', 'instance_filters', 'group_by', 'overwrite', 'overwrite_vars',
                  'timeout', 'verbosity')

    def get_related(self, obj):
        res = super(InventorySourceOptionsSerializer, self).get_related(obj)
        if obj.credential:
            res['credential'] = self.reverse('api:credential_detail',
                                             kwargs={'pk': obj.credential.pk})
        if obj.source_script:
            res['source_script'] = self.reverse('api:inventory_script_detail', kwargs={'pk': obj.source_script.pk})
        return res

    def validate_source_vars(self, value):
        ret = vars_validate_or_raise(value)
        for env_k in parse_yaml_or_json(value):
            if env_k in settings.INV_ENV_VARIABLE_BLACKLIST:
                raise serializers.ValidationError(_("`{}` is a prohibited environment variable".format(env_k)))
        return ret

    def validate(self, attrs):
        # TODO: Validate source, validate source_regions
        errors = {}

        source = attrs.get('source', self.instance and self.instance.source or '')
        source_script = attrs.get('source_script', self.instance and self.instance.source_script or '')
        if source == 'custom':
            if source_script is None or source_script == '':
                errors['source_script'] = _("If 'source' is 'custom', 'source_script' must be provided.")
            else:
                try:
                    if not self.instance:
                        dest_inventory = attrs.get('inventory', None)
                        if not dest_inventory:
                            errors['inventory'] = _("Must provide an inventory.")
                    else:
                        dest_inventory = self.instance.inventory
                    if dest_inventory and source_script.organization != dest_inventory.organization:
                        errors['source_script'] = _("The 'source_script' does not belong to the same organization as the inventory.")
                except Exception:
                    errors['source_script'] = _("'source_script' doesn't exist.")
                    logger.exception('Problem processing source_script validation.')

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
    show_capabilities = ['start', 'schedule', 'edit', 'delete']
    group = serializers.SerializerMethodField(
        help_text=_('Automatic group relationship, will be removed in 3.3'))

    class Meta:
        model = InventorySource
        fields = ('*', 'name', 'inventory', 'update_on_launch', 'update_cache_timeout',
                  'source_project', 'update_on_project_update') + \
                 ('last_update_failed', 'last_updated', 'group') # Backwards compatibility.

    def get_related(self, obj):
        res = super(InventorySourceSerializer, self).get_related(obj)
        res.update(dict(
            update = self.reverse('api:inventory_source_update_view', kwargs={'pk': obj.pk}),
            inventory_updates = self.reverse('api:inventory_source_updates_list', kwargs={'pk': obj.pk}),
            schedules = self.reverse('api:inventory_source_schedules_list', kwargs={'pk': obj.pk}),
            activity_stream = self.reverse('api:inventory_source_activity_stream_list', kwargs={'pk': obj.pk}),
            hosts = self.reverse('api:inventory_source_hosts_list', kwargs={'pk': obj.pk}),
            groups = self.reverse('api:inventory_source_groups_list', kwargs={'pk': obj.pk}),
            notification_templates_any = self.reverse('api:inventory_source_notification_templates_any_list', kwargs={'pk': obj.pk}),
            notification_templates_success = self.reverse('api:inventory_source_notification_templates_success_list', kwargs={'pk': obj.pk}),
            notification_templates_error = self.reverse('api:inventory_source_notification_templates_error_list', kwargs={'pk': obj.pk}),
        ))
        if obj.inventory:
            res['inventory'] = self.reverse('api:inventory_detail', kwargs={'pk': obj.inventory.pk})
        if obj.source_project_id is not None:
            res['source_project'] = self.reverse('api:project_detail', kwargs={'pk': obj.source_project.pk})
        # Backwards compatibility.
        if obj.current_update:
            res['current_update'] = self.reverse('api:inventory_update_detail',
                                                 kwargs={'pk': obj.current_update.pk})
        if obj.last_update:
            res['last_update'] = self.reverse('api:inventory_update_detail',
                                              kwargs={'pk': obj.last_update.pk})
        if self.version == 1:  # TODO: remove in 3.3
            if obj.deprecated_group:
                res['group'] = self.reverse('api:group_detail', kwargs={'pk': obj.deprecated_group.pk})
        return res

    def get_fields(self):  # TODO: remove in 3.3
        fields = super(InventorySourceSerializer, self).get_fields()
        if self.version > 1:
            fields.pop('group', None)
        return fields

    def get_summary_fields(self, obj):  # TODO: remove in 3.3
        summary_fields = super(InventorySourceSerializer, self).get_summary_fields(obj)
        if self.version == 1 and obj.deprecated_group_id:
            g = obj.deprecated_group
            summary_fields['group'] = {}
            for field in SUMMARIZABLE_FK_FIELDS['group']:
                fval = getattr(g, field, None)
                if fval is not None:
                    summary_fields['group'][field] = fval
        return summary_fields

    def get_group(self, obj):  # TODO: remove in 3.3
        if obj.deprecated_group:
            return obj.deprecated_group.id
        return None

    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super(InventorySourceSerializer, self).build_relational_field(field_name, relation_info)
        # SCM Project and inventory are read-only unless creating a new inventory.
        if self.instance and field_name == 'inventory':
            field_kwargs['read_only'] = True
            field_kwargs.pop('queryset', None)
        return field_class, field_kwargs

    def to_representation(self, obj):
        ret = super(InventorySourceSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        if 'inventory' in ret and not obj.inventory:
            ret['inventory'] = None
        return ret

    def validate_source_project(self, value):
        if value and value.scm_type == '':
            raise serializers.ValidationError(_("Cannot use manual project for SCM-based inventory."))
        return value

    def validate_source(self, value):
        if value == '':
            raise serializers.ValidationError(_(
                "Manual inventory sources are created automatically when a group is created in the v1 API."))
        return value

    def validate_update_on_project_update(self, value):
        if value and self.instance and self.instance.schedules.exists():
            raise serializers.ValidationError(_("Setting not compatible with existing schedules."))
        return value

    def validate_inventory(self, value):
        if value and value.kind == 'smart':
            raise serializers.ValidationError({"detail": _("Cannot create Inventory Source for Smart Inventory")})
        return value

    def validate(self, attrs):
        def get_field_from_model_or_attrs(fd):
            return attrs.get(fd, self.instance and getattr(self.instance, fd) or None)

        if get_field_from_model_or_attrs('source') != 'scm':
            redundant_scm_fields = filter(
                lambda x: attrs.get(x, None),
                ['source_project', 'source_path', 'update_on_project_update']
            )
            if redundant_scm_fields:
                raise serializers.ValidationError(
                    {"detail": _("Cannot set %s if not SCM type." % ' '.join(redundant_scm_fields))}
                )

        return super(InventorySourceSerializer, self).validate(attrs)


class InventorySourceUpdateSerializer(InventorySourceSerializer):

    can_update = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_update',)


class InventoryUpdateSerializer(UnifiedJobSerializer, InventorySourceOptionsSerializer):

    class Meta:
        model = InventoryUpdate
        fields = ('*', 'inventory_source', 'license_error', 'source_project_update')

    def get_related(self, obj):
        res = super(InventoryUpdateSerializer, self).get_related(obj)
        res.update(dict(
            inventory_source = self.reverse('api:inventory_source_detail', kwargs={'pk': obj.inventory_source.pk}),
            cancel = self.reverse('api:inventory_update_cancel', kwargs={'pk': obj.pk}),
            notifications = self.reverse('api:inventory_update_notifications_list', kwargs={'pk': obj.pk}),
        ))
        if obj.source_project_update_id:
            res['source_project_update'] = self.reverse('api:project_update_detail',
                                                        kwargs={'pk': obj.source_project_update.pk})
        return res


class InventoryUpdateListSerializer(InventoryUpdateSerializer, UnifiedJobListSerializer):

    pass


class InventoryUpdateCancelSerializer(InventoryUpdateSerializer):

    can_cancel = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_cancel',)


class TeamSerializer(BaseSerializer):
    show_capabilities = ['edit', 'delete']

    class Meta:
        model = Team
        fields = ('*', 'organization')

    def get_related(self, obj):
        res = super(TeamSerializer, self).get_related(obj)
        res.update(dict(
            projects     = self.reverse('api:team_projects_list',    kwargs={'pk': obj.pk}),
            users        = self.reverse('api:team_users_list',       kwargs={'pk': obj.pk}),
            credentials  = self.reverse('api:team_credentials_list', kwargs={'pk': obj.pk}),
            roles        = self.reverse('api:team_roles_list',       kwargs={'pk': obj.pk}),
            object_roles        = self.reverse('api:team_object_roles_list',       kwargs={'pk': obj.pk}),
            activity_stream = self.reverse('api:team_activity_stream_list', kwargs={'pk': obj.pk}),
            access_list  = self.reverse('api:team_access_list',      kwargs={'pk': obj.pk}),
        ))
        if obj.organization:
            res['organization'] = self.reverse('api:organization_detail',   kwargs={'pk': obj.organization.pk})
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

        if obj.object_id:
            content_object = obj.content_object
            if hasattr(content_object, 'username'):
                ret['summary_fields']['resource_name'] = obj.content_object.username
            if hasattr(content_object, 'name'):
                ret['summary_fields']['resource_name'] = obj.content_object.name
            content_model = obj.content_type.model_class()
            ret['summary_fields']['resource_type'] = get_type_for_model(content_model)
            ret['summary_fields']['resource_type_display_name'] = content_model._meta.verbose_name.title()

        ret.pop('created')
        ret.pop('modified')
        return ret

    def get_related(self, obj):
        ret = super(RoleSerializer, self).get_related(obj)
        ret['users'] = self.reverse('api:role_users_list', kwargs={'pk': obj.pk})
        ret['teams'] = self.reverse('api:role_teams_list', kwargs={'pk': obj.pk})
        try:
            if obj.content_object:
                ret.update(reverse_gfk(obj.content_object, self.context.get('request')))
        except AttributeError:
            # AttributeError's happen if our content_object is pointing at
            # a model that no longer exists. This is dirty data and ideally
            # doesn't exist, but in case it does, let's not puke.
            pass
        return ret


class RoleSerializerWithParentAccess(RoleSerializer):
    show_capabilities = ['unattach']


class ResourceAccessListElementSerializer(UserSerializer):
    show_capabilities = []  # Clear fields from UserSerializer parent class

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
        obj = self.context['view'].get_parent_object()
        if self.context['view'].request is not None:
            requesting_user = self.context['view'].request.user
        else:
            requesting_user = None

        if 'summary_fields' not in ret:
            ret['summary_fields'] = {}

        def format_role_perm(role):
            role_dict = { 'id': role.id, 'name': role.name, 'description': role.description}
            try:
                role_dict['resource_name'] = role.content_object.name
                role_dict['resource_type'] = get_type_for_model(role.content_type.model_class())
                role_dict['related'] = reverse_gfk(role.content_object, self.context.get('request'))
            except AttributeError:
                pass
            if role.content_type is not None:
                role_dict['user_capabilities'] = {'unattach': requesting_user.can_access(
                    Role, 'unattach', role, user, 'members', data={}, skip_sub_obj_read_check=False)}
            else:
                # Singleton roles should not be managed from this view, as per copy/edit rework spec
                role_dict['user_capabilities'] = {'unattach': False}
            return { 'role': role_dict, 'descendant_roles': get_roles_on_resource(obj, role)}

        def format_team_role_perm(naive_team_role, permissive_role_ids):
            ret = []
            team_role = naive_team_role
            if naive_team_role.role_field == 'admin_role':
                team_role = naive_team_role.content_object.member_role
            for role in team_role.children.filter(id__in=permissive_role_ids).all():
                role_dict = {
                    'id': role.id,
                    'name': role.name,
                    'description': role.description,
                    'team_id': team_role.object_id,
                    'team_name': team_role.content_object.name,
                    'team_organization_name': team_role.content_object.organization.name,
                }
                if role.content_type is not None:
                    role_dict['resource_name'] = role.content_object.name
                    role_dict['resource_type'] = get_type_for_model(role.content_type.model_class())
                    role_dict['related'] = reverse_gfk(role.content_object, self.context.get('request'))
                    role_dict['user_capabilities'] = {'unattach': requesting_user.can_access(
                        Role, 'unattach', role, team_role, 'parents', data={}, skip_sub_obj_read_check=False)}
                else:
                    # Singleton roles should not be managed from this view, as per copy/edit rework spec
                    role_dict['user_capabilities'] = {'unattach': False}
                ret.append({ 'role': role_dict, 'descendant_roles': get_roles_on_resource(obj, team_role)})
            return ret

        team_content_type = ContentType.objects.get_for_model(Team)
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
            + [y for x in (format_team_role_perm(r, direct_permissive_role_ids) for r in direct_team_roles.distinct()) for y in x] \
            + [y for x in (format_team_role_perm(r, all_permissive_role_ids) for r in indirect_team_roles.distinct()) for y in x]

        ret['summary_fields']['indirect_access'] \
            = [format_role_perm(r) for r in indirect_access_roles.distinct()]

        return ret


class CredentialTypeSerializer(BaseSerializer):
    show_capabilities = ['edit', 'delete']
    managed_by_tower = serializers.ReadOnlyField()

    class Meta:
        model = CredentialType
        fields = ('*', 'kind', 'name', 'managed_by_tower', 'inputs',
                  'injectors')

    def validate(self, attrs):
        if self.instance and self.instance.managed_by_tower:
            raise PermissionDenied(
                detail=_("Modifications not allowed for managed credential types")
            )
        if self.instance and self.instance.credentials.exists():
            if 'inputs' in attrs and attrs['inputs'] != self.instance.inputs:
                raise PermissionDenied(
                    detail= _("Modifications to inputs are not allowed for credential types that are in use")
                )
        ret = super(CredentialTypeSerializer, self).validate(attrs)

        if 'kind' in attrs and attrs['kind'] not in ('cloud', 'net'):
            raise serializers.ValidationError({
                "kind": _("Must be 'cloud' or 'net', not %s") % attrs['kind']
            })

        fields = attrs.get('inputs', {}).get('fields', [])
        for field in fields:
            if field.get('ask_at_runtime', False):
                raise serializers.ValidationError({"inputs": _("'ask_at_runtime' is not supported for custom credentials.")})

        return ret

    def get_related(self, obj):
        res = super(CredentialTypeSerializer, self).get_related(obj)
        res['credentials'] = self.reverse(
            'api:credential_type_credential_list',
            kwargs={'pk': obj.pk}
        )
        res['activity_stream'] = self.reverse(
            'api:credential_type_activity_stream_list',
            kwargs={'pk': obj.pk}
        )
        return res

    def to_representation(self, data):
        value = super(CredentialTypeSerializer, self).to_representation(data)

        # translate labels and help_text for credential fields "managed by Tower"
        if value.get('managed_by_tower'):
            for field in value.get('inputs', {}).get('fields', []):
                field['label'] = _(field['label'])
                if 'help_text' in field:
                    field['help_text'] = _(field['help_text'])
        return value

    def filter_field_metadata(self, fields, method):
        # API-created/modified CredentialType kinds are limited to
        # `cloud` and `net`
        if method in ('PUT', 'POST'):
            fields['kind']['choices'] = filter(
                lambda choice: choice[0] in ('cloud', 'net'),
                fields['kind']['choices']
            )
        return fields


# TODO: remove when API v1 is removed
@six.add_metaclass(BaseSerializerMetaclass)
class V1CredentialFields(BaseSerializer):

    class Meta:
        model = Credential
        fields = ('*', 'kind', 'cloud', 'host', 'username',
                  'password', 'security_token', 'project', 'domain',
                  'ssh_key_data', 'ssh_key_unlock', 'become_method',
                  'become_username', 'become_password', 'vault_password',
                  'subscription', 'tenant', 'secret', 'client', 'authorize',
                  'authorize_password')

    def build_field(self, field_name, info, model_class, nested_depth):
        if field_name in V1Credential.FIELDS:
            return self.build_standard_field(field_name,
                                             V1Credential.FIELDS[field_name])
        return super(V1CredentialFields, self).build_field(field_name, info, model_class, nested_depth)


@six.add_metaclass(BaseSerializerMetaclass)
class V2CredentialFields(BaseSerializer):

    class Meta:
        model = Credential
        fields = ('*', 'credential_type', 'inputs')


class CredentialSerializer(BaseSerializer):
    show_capabilities = ['edit', 'delete']

    class Meta:
        model = Credential
        fields = ('*', 'organization')

    def get_fields(self):
        fields = super(CredentialSerializer, self).get_fields()

        # TODO: remove when API v1 is removed
        if self.version == 1:
            fields.update(V1CredentialFields().get_fields())
        else:
            fields.update(V2CredentialFields().get_fields())
        return fields

    def to_representation(self, data):
        value = super(CredentialSerializer, self).to_representation(data)

        # TODO: remove when API v1 is removed
        if self.version == 1:
            if value.get('kind') == 'vault':
                value['kind'] = 'ssh'
            for field in V1Credential.PASSWORD_FIELDS:
                if field in value and force_text(value[field]).startswith('$encrypted$'):
                    value[field] = '$encrypted$'

        if 'inputs' in value:
            value['inputs'] = data.display_inputs()
        return value

    def get_related(self, obj):
        res = super(CredentialSerializer, self).get_related(obj)

        if obj.organization:
            res['organization'] = self.reverse('api:organization_detail', kwargs={'pk': obj.organization.pk})

        res.update(dict(
            activity_stream = self.reverse('api:credential_activity_stream_list', kwargs={'pk': obj.pk}),
            access_list = self.reverse('api:credential_access_list', kwargs={'pk': obj.pk}),
            object_roles = self.reverse('api:credential_object_roles_list', kwargs={'pk': obj.pk}),
            owner_users = self.reverse('api:credential_owner_users_list', kwargs={'pk': obj.pk}),
            owner_teams = self.reverse('api:credential_owner_teams_list', kwargs={'pk': obj.pk}),
        ))

        # TODO: remove when API v1 is removed
        if self.version > 1:
            res.update(dict(
                credential_type = self.reverse('api:credential_type_detail', kwargs={'pk': obj.credential_type.pk}),
            ))

        parents = [role for role in obj.admin_role.parents.all() if role.object_id is not None]
        if parents:
            res.update({parents[0].content_type.name:parents[0].content_object.get_absolute_url(self.context.get('request'))})
        elif len(obj.admin_role.members.all()) > 0:
            user = obj.admin_role.members.all()[0]
            res.update({'user': self.reverse('api:user_detail', kwargs={'pk': user.pk})})

        return res

    def get_summary_fields(self, obj):
        summary_dict = super(CredentialSerializer, self).get_summary_fields(obj)
        summary_dict['owners'] = []

        for user in obj.admin_role.members.all():
            summary_dict['owners'].append({
                'id': user.pk,
                'type': 'user',
                'name': user.username,
                'description': ' '.join([user.first_name, user.last_name]),
                'url': self.reverse('api:user_detail', kwargs={'pk': user.pk}),
            })

        for parent in [role for role in obj.admin_role.parents.all() if role.object_id is not None]:
            summary_dict['owners'].append({
                'id': parent.content_object.pk,
                'type': camelcase_to_underscore(parent.content_object.__class__.__name__),
                'name': parent.content_object.name,
                'description': parent.content_object.description,
                'url': parent.content_object.get_absolute_url(self.context.get('request')),
            })

        return summary_dict

    def get_validation_exclusions(self, obj=None):
        # CredentialType is now part of validation; legacy v1 fields (e.g.,
        # 'username', 'password') in JSON POST payloads use the
        # CredentialType's inputs definition to determine their validity
        ret = super(CredentialSerializer, self).get_validation_exclusions(obj)
        for field in ('credential_type', 'inputs'):
            if field in ret:
                ret.remove(field)
        return ret

    def to_internal_value(self, data):
        # TODO: remove when API v1 is removed
        if 'credential_type' not in data:
            # If `credential_type` is not provided, assume the payload is a
            # v1 credential payload that specifies a `kind` and a flat list
            # of field values
            #
            # In this scenario, we should automatically detect the proper
            # CredentialType based on the provided values
            kind = data.get('kind', 'ssh')
            credential_type = CredentialType.from_v1_kind(kind, data)
            if credential_type is None:
                raise serializers.ValidationError({"kind": _('"%s" is not a valid choice' % kind)})
            data['credential_type'] = credential_type.pk
            value = OrderedDict(
                {'credential_type': credential_type}.items() +
                super(CredentialSerializer, self).to_internal_value(data).items()
            )

            # Make a set of the keys in the POST/PUT payload
            # - Subtract real fields (name, organization, inputs)
            # - Subtract virtual v1 fields defined on the determined credential
            #   type (username, password, etc...)
            # - Any leftovers are invalid for the determined credential type
            valid_fields = set(super(CredentialSerializer, self).get_fields().keys())
            valid_fields.update(V2CredentialFields().get_fields().keys())
            valid_fields.update(['kind', 'cloud'])

            for field in set(data.keys()) - valid_fields - set(credential_type.defined_fields):
                if data.get(field):
                    raise serializers.ValidationError(
                        {"detail": _("'%s' is not a valid field for %s") % (field, credential_type.name)}
                    )
            value.pop('kind', None)
            return value
        return super(CredentialSerializer, self).to_internal_value(data)

    def validate_credential_type(self, credential_type):
        if self.instance and credential_type.pk != self.instance.credential_type.pk:
            raise ValidationError(
                _('You cannot change the credential type of the credential, as it may break the functionality'
                  ' of the resources using it.'),
            )
        return credential_type


class CredentialSerializerCreate(CredentialSerializer):

    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False, default=None, write_only=True, allow_null=True,
        help_text=_('Write-only field used to add user to owner role. If provided, '
                    'do not give either team or organization. Only valid for creation.'))
    team = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        required=False, default=None, write_only=True, allow_null=True,
        help_text=_('Write-only field used to add team to owner role. If provided, '
                    'do not give either user or organization. Only valid for creation.'))
    organization = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        required=False, default=None, allow_null=True,
        help_text=_('Inherit permissions from organization roles. If provided on creation, '
                    'do not give either user or team.'))

    class Meta:
        model = Credential
        fields = ('*', 'user', 'team')

    def validate(self, attrs):
        owner_fields = set()
        for field in ('user', 'team', 'organization'):
            if field in attrs:
                if attrs[field]:
                    owner_fields.add(field)
                else:
                    attrs.pop(field)
        if not owner_fields:
            raise serializers.ValidationError({"detail": _("Missing 'user', 'team', or 'organization'.")})

        if attrs.get('team'):
            attrs['organization'] = attrs['team'].organization

        try:
            return super(CredentialSerializerCreate, self).validate(attrs)
        except ValidationError as e:
            # TODO: remove when API v1 is removed
            # If we have an `inputs` error on `/api/v1/`:
            # {'inputs': {'username': [...]}}
            # ...instead, send back:
            # {'username': [...]}
            if self.version == 1 and isinstance(e.detail.get('inputs'), dict):
                e.detail = e.detail['inputs']
                raise e
            else:
                raise

    def create(self, validated_data):
        user = validated_data.pop('user', None)
        team = validated_data.pop('team', None)

        # If our payload contains v1 credential fields, translate to the new
        # model
        # TODO: remove when API v1 is removed
        if self.version == 1:
            for attr in (
                set(V1Credential.FIELDS) & set(validated_data.keys())  # set intersection
            ):
                validated_data.setdefault('inputs', {})
                value = validated_data.pop(attr)
                if value:
                    validated_data['inputs'][attr] = value
        credential = super(CredentialSerializerCreate, self).create(validated_data)

        if user:
            credential.admin_role.members.add(user)
        if team:
            if not credential.organization or team.organization.id != credential.organization.id:
                raise serializers.ValidationError({"detail": _("Credential organization must be set and match before assigning to a team")})
            credential.admin_role.parents.add(team.admin_role)
            credential.use_role.parents.add(team.member_role)
        return credential


class UserCredentialSerializerCreate(CredentialSerializerCreate):

    class Meta:
        model = Credential
        fields = ('*', '-team', '-organization')


class TeamCredentialSerializerCreate(CredentialSerializerCreate):

    class Meta:
        model = Credential
        fields = ('*', '-user', '-organization')


class OrganizationCredentialSerializerCreate(CredentialSerializerCreate):

    class Meta:
        model = Credential
        fields = ('*', '-user', '-team')


class LabelsListMixin(object):

    def _summary_field_labels(self, obj):
        label_list = [{'id': x.id, 'name': x.name} for x in obj.labels.all()[:10]]
        if has_model_field_prefetched(obj, 'labels'):
            label_ct = len(obj.labels.all())
        else:
            if len(label_list) < 10:
                label_ct = len(label_list)
            else:
                label_ct = obj.labels.count()
        return {'count': label_ct, 'results': label_list}

    def get_summary_fields(self, obj):
        res = super(LabelsListMixin, self).get_summary_fields(obj)
        res['labels'] = self._summary_field_labels(obj)
        return res


# TODO: remove when API v1 is removed
@six.add_metaclass(BaseSerializerMetaclass)
class V1JobOptionsSerializer(BaseSerializer):

    class Meta:
        model = Credential
        fields = ('*', 'cloud_credential', 'network_credential')

    V1_FIELDS = {
        'cloud_credential': models.PositiveIntegerField(blank=True, null=True, default=None),
        'network_credential': models.PositiveIntegerField(blank=True, null=True, default=None)
    }

    def build_field(self, field_name, info, model_class, nested_depth):
        if field_name in self.V1_FIELDS:
            return self.build_standard_field(field_name,
                                             self.V1_FIELDS[field_name])
        return super(V1JobOptionsSerializer, self).build_field(field_name, info, model_class, nested_depth)


class JobOptionsSerializer(LabelsListMixin, BaseSerializer):

    class Meta:
        fields = ('*', 'job_type', 'inventory', 'project', 'playbook',
                  'credential', 'vault_credential', 'forks', 'limit',
                  'verbosity', 'extra_vars', 'job_tags',  'force_handlers',
                  'skip_tags', 'start_at_task', 'timeout', 'use_fact_cache',)

    def get_fields(self):
        fields = super(JobOptionsSerializer, self).get_fields()

        # TODO: remove when API v1 is removed
        if self.version == 1 and 'credential' in self.Meta.fields:
            fields.update(V1JobOptionsSerializer().get_fields())
        return fields

    def get_related(self, obj):
        res = super(JobOptionsSerializer, self).get_related(obj)
        res['labels'] = self.reverse('api:job_template_label_list', kwargs={'pk': obj.pk})
        if obj.inventory:
            res['inventory'] = self.reverse('api:inventory_detail', kwargs={'pk': obj.inventory.pk})
        if obj.project:
            res['project'] = self.reverse('api:project_detail', kwargs={'pk': obj.project.pk})
        if obj.credential:
            res['credential'] = self.reverse('api:credential_detail', kwargs={'pk': obj.credential.pk})
        if obj.vault_credential:
            res['vault_credential'] = self.reverse('api:credential_detail', kwargs={'pk': obj.vault_credential.pk})
        if self.version > 1:
            if isinstance(obj, UnifiedJobTemplate):
                res['extra_credentials'] = self.reverse(
                    'api:job_template_extra_credentials_list',
                    kwargs={'pk': obj.pk}
                )
            elif isinstance(obj, UnifiedJob):
                res['extra_credentials'] = self.reverse('api:job_extra_credentials_list', kwargs={'pk': obj.pk})
        else:
            cloud_cred = obj.cloud_credential
            if cloud_cred:
                res['cloud_credential'] = self.reverse('api:credential_detail', kwargs={'pk': cloud_cred})
            net_cred = obj.network_credential
            if net_cred:
                res['network_credential'] = self.reverse('api:credential_detail', kwargs={'pk': net_cred})

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
        if 'vault_credential' in ret and not obj.vault_credential:
            ret['vault_credential'] = None
        if self.version == 1 and 'credential' in self.Meta.fields:
            ret['cloud_credential'] = obj.cloud_credential
            ret['network_credential'] = obj.network_credential
        return ret

    def create(self, validated_data):
        deprecated_fields = {}
        for key in ('cloud_credential', 'network_credential'):
            if key in validated_data:
                deprecated_fields[key] = validated_data.pop(key)
        obj = super(JobOptionsSerializer, self).create(validated_data)
        if self.version == 1 and deprecated_fields:  # TODO: remove in 3.3
            self._update_deprecated_fields(deprecated_fields, obj)
        return obj

    def update(self, obj, validated_data):
        deprecated_fields = {}
        for key in ('cloud_credential', 'network_credential'):
            if key in validated_data:
                deprecated_fields[key] = validated_data.pop(key)
        obj = super(JobOptionsSerializer, self).update(obj, validated_data)
        if self.version == 1 and deprecated_fields:  # TODO: remove in 3.3
            self._update_deprecated_fields(deprecated_fields, obj)
        return obj

    def _update_deprecated_fields(self, fields, obj):
        for key, existing in (
            ('cloud_credential', obj.cloud_credentials),
            ('network_credential', obj.network_credentials),
        ):
            if key in fields:
                for cred in existing:
                    obj.extra_credentials.remove(cred)
                if fields[key]:
                    obj.extra_credentials.add(fields[key])
        obj.save()

    def validate(self, attrs):
        v1_credentials = {}
        view = self.context.get('view', None)
        if self.version == 1:  # TODO: remove in 3.3
            for attr, kind, error in (
                ('cloud_credential', 'cloud', _('You must provide a cloud credential.')),
                ('network_credential', 'net', _('You must provide a network credential.'))
            ):
                if attr in attrs:
                    v1_credentials[attr] = None
                    pk = attrs.pop(attr)
                    if pk:
                        cred = v1_credentials[attr] = Credential.objects.get(pk=pk)
                        if cred.credential_type.kind != kind:
                            raise serializers.ValidationError({attr: error})
                        if (not view) or (not view.request) or (view.request.user not in cred.use_role):
                            raise PermissionDenied()

        if 'project' in self.fields and 'playbook' in self.fields:
            project = attrs.get('project', self.instance and self.instance.project or None)
            playbook = attrs.get('playbook', self.instance and self.instance.playbook or '')
            if not project:
                raise serializers.ValidationError({'project': _('This field is required.')})
            if project and project.scm_type and playbook and force_text(playbook) not in project.playbook_files:
                raise serializers.ValidationError({'playbook': _('Playbook not found for project.')})
            if project and not project.scm_type and playbook and force_text(playbook) not in project.playbooks:
                raise serializers.ValidationError({'playbook': _('Playbook not found for project.')})
            if project and not playbook:
                raise serializers.ValidationError({'playbook': _('Must select playbook for project.')})

        ret = super(JobOptionsSerializer, self).validate(attrs)
        ret.update(v1_credentials)
        return ret


class JobTemplateMixin(object):
    '''
    Provide recent jobs and survey details in summary_fields
    '''

    def _recent_jobs(self, obj):
        if hasattr(obj, 'workflow_jobs'):
            job_mgr = obj.workflow_jobs
        else:
            job_mgr = obj.jobs
        return [{'id': x.id, 'status': x.status, 'finished': x.finished}
                for x in job_mgr.all().order_by('-created')[:10]]

    def get_summary_fields(self, obj):
        d = super(JobTemplateMixin, self).get_summary_fields(obj)
        if obj.survey_spec is not None and ('name' in obj.survey_spec and 'description' in obj.survey_spec):
            d['survey'] = dict(title=obj.survey_spec['name'], description=obj.survey_spec['description'])
        d['recent_jobs'] = self._recent_jobs(obj)

        # TODO: remove in 3.3
        if self.version == 1 and 'vault_credential' in d:
            if d['vault_credential'].get('kind','') == 'vault':
                d['vault_credential']['kind'] = 'ssh'

        return d


class JobTemplateSerializer(JobTemplateMixin, UnifiedJobTemplateSerializer, JobOptionsSerializer):
    show_capabilities = ['start', 'schedule', 'copy', 'edit', 'delete']

    status = serializers.ChoiceField(choices=JobTemplate.JOB_TEMPLATE_STATUS_CHOICES, read_only=True, required=False)

    class Meta:
        model = JobTemplate
        fields = ('*', 'host_config_key', 'ask_diff_mode_on_launch', 'ask_variables_on_launch', 'ask_limit_on_launch', 'ask_tags_on_launch',
                  'ask_skip_tags_on_launch', 'ask_job_type_on_launch', 'ask_verbosity_on_launch', 'ask_inventory_on_launch',
                  'ask_credential_on_launch', 'survey_enabled', 'become_enabled', 'diff_mode',
                  'allow_simultaneous')

    def get_related(self, obj):
        res = super(JobTemplateSerializer, self).get_related(obj)
        res.update(dict(
            jobs = self.reverse('api:job_template_jobs_list', kwargs={'pk': obj.pk}),
            schedules = self.reverse('api:job_template_schedules_list', kwargs={'pk': obj.pk}),
            activity_stream = self.reverse('api:job_template_activity_stream_list', kwargs={'pk': obj.pk}),
            launch = self.reverse('api:job_template_launch', kwargs={'pk': obj.pk}),
            notification_templates_any = self.reverse('api:job_template_notification_templates_any_list', kwargs={'pk': obj.pk}),
            notification_templates_success = self.reverse('api:job_template_notification_templates_success_list', kwargs={'pk': obj.pk}),
            notification_templates_error = self.reverse('api:job_template_notification_templates_error_list', kwargs={'pk': obj.pk}),
            access_list = self.reverse('api:job_template_access_list',      kwargs={'pk': obj.pk}),
            survey_spec = self.reverse('api:job_template_survey_spec', kwargs={'pk': obj.pk}),
            labels = self.reverse('api:job_template_label_list', kwargs={'pk': obj.pk}),
            object_roles = self.reverse('api:job_template_object_roles_list', kwargs={'pk': obj.pk}),
            instance_groups = self.reverse('api:job_template_instance_groups_list', kwargs={'pk': obj.pk}),
        ))
        if obj.host_config_key:
            res['callback'] = self.reverse('api:job_template_callback', kwargs={'pk': obj.pk})
        return res

    def validate(self, attrs):
        def get_field_from_model_or_attrs(fd):
            return attrs.get(fd, self.instance and getattr(self.instance, fd) or None)

        inventory = get_field_from_model_or_attrs('inventory')
        credential = get_field_from_model_or_attrs('credential')
        vault_credential = get_field_from_model_or_attrs('vault_credential')
        project = get_field_from_model_or_attrs('project')

        prompting_error_message = _("Must either set a default value or ask to prompt on launch.")
        if project is None:
            raise serializers.ValidationError({'project': _("Job types 'run' and 'check' must have assigned a project.")})
        elif all([
            credential is None,
            vault_credential is None,
            not get_field_from_model_or_attrs('ask_credential_on_launch'),
        ]):
            raise serializers.ValidationError({'credential': prompting_error_message})
        elif inventory is None and not get_field_from_model_or_attrs('ask_inventory_on_launch'):
            raise serializers.ValidationError({'inventory': prompting_error_message})

        return super(JobTemplateSerializer, self).validate(attrs)

    def validate_extra_vars(self, value):
        return vars_validate_or_raise(value)

    def get_summary_fields(self, obj):
        summary_fields = super(JobTemplateSerializer, self).get_summary_fields(obj)
        if 'pk' in self.context['view'].kwargs and self.version > 1:  # TODO: remove version check in 3.3
            extra_creds = []
            for cred in obj.extra_credentials.all():
                extra_creds.append({
                    'id': cred.pk,
                    'name': cred.name,
                    'description': cred.description,
                    'kind': cred.kind,
                    'credential_type_id': cred.credential_type_id
                })
            summary_fields['extra_credentials'] = extra_creds
        return summary_fields



class JobSerializer(UnifiedJobSerializer, JobOptionsSerializer):

    passwords_needed_to_start = serializers.ReadOnlyField()
    ask_diff_mode_on_launch = serializers.ReadOnlyField()
    ask_variables_on_launch = serializers.ReadOnlyField()
    ask_limit_on_launch = serializers.ReadOnlyField()
    ask_skip_tags_on_launch = serializers.ReadOnlyField()
    ask_tags_on_launch = serializers.ReadOnlyField()
    ask_job_type_on_launch = serializers.ReadOnlyField()
    ask_verbosity_on_launch = serializers.ReadOnlyField()
    ask_inventory_on_launch = serializers.ReadOnlyField()
    ask_credential_on_launch = serializers.ReadOnlyField()
    artifacts = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = ('*', 'job_template', 'passwords_needed_to_start', 'ask_diff_mode_on_launch',
                  'ask_variables_on_launch', 'ask_limit_on_launch', 'ask_tags_on_launch', 'ask_skip_tags_on_launch',
                  'ask_job_type_on_launch', 'ask_verbosity_on_launch', 'ask_inventory_on_launch',
                  'ask_credential_on_launch', 'allow_simultaneous', 'artifacts', 'scm_revision',
                  'instance_group', 'diff_mode')

    def get_related(self, obj):
        res = super(JobSerializer, self).get_related(obj)
        res.update(dict(
            job_events  = self.reverse('api:job_job_events_list', kwargs={'pk': obj.pk}),
            job_host_summaries = self.reverse('api:job_job_host_summaries_list', kwargs={'pk': obj.pk}),
            activity_stream = self.reverse('api:job_activity_stream_list', kwargs={'pk': obj.pk}),
            notifications = self.reverse('api:job_notifications_list', kwargs={'pk': obj.pk}),
            labels = self.reverse('api:job_label_list', kwargs={'pk': obj.pk}),
        ))
        if obj.job_template:
            res['job_template'] = self.reverse('api:job_template_detail',
                                               kwargs={'pk': obj.job_template.pk})
        if (obj.can_start or True) and self.version == 1:  # TODO: remove in 3.3
            res['start'] = self.reverse('api:job_start', kwargs={'pk': obj.pk})
        if obj.can_cancel or True:
            res['cancel'] = self.reverse('api:job_cancel', kwargs={'pk': obj.pk})
        if obj.project_update:
            res['project_update'] = self.reverse('api:project_update_detail', kwargs={'pk': obj.project_update.pk})
        res['relaunch'] = self.reverse('api:job_relaunch', kwargs={'pk': obj.pk})
        return res

    def get_artifacts(self, obj):
        if obj:
            return obj.display_artifacts()
        return {}

    def to_internal_value(self, data):
        # When creating a new job and a job template is specified, populate any
        # fields not provided in data from the job template.
        if not self.instance and isinstance(data, dict) and data.get('job_template', False):
            try:
                job_template = JobTemplate.objects.get(pk=data['job_template'])
            except JobTemplate.DoesNotExist:
                raise serializers.ValidationError({'job_template': _('Invalid job template.')})
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
        if 'extra_vars' in ret:
            ret['extra_vars'] = obj.display_extra_vars()
        return ret

    def get_summary_fields(self, obj):
        summary_fields = super(JobSerializer, self).get_summary_fields(obj)
        if 'pk' in self.context['view'].kwargs and self.version > 1:  # TODO: remove version check in 3.3
            extra_creds = []
            for cred in obj.extra_credentials.all():
                extra_creds.append({
                    'id': cred.pk,
                    'name': cred.name,
                    'description': cred.description,
                    'kind': cred.kind,
                    'credential_type_id': cred.credential_type_id
                })
            summary_fields['extra_credentials'] = extra_creds
        return summary_fields


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
            raise serializers.ValidationError(dict(credential=[_("Credential not found or deleted.")]))
        if obj.project is None:
            raise serializers.ValidationError(dict(errors=[_("Job Template Project is missing or undefined.")]))
        if obj.inventory is None or obj.inventory.pending_deletion:
            raise serializers.ValidationError(dict(errors=[_("Job Template Inventory is missing or undefined.")]))
        attrs = super(JobRelaunchSerializer, self).validate(attrs)
        return attrs


class AdHocCommandSerializer(UnifiedJobSerializer):

    class Meta:
        model = AdHocCommand
        fields = ('*', 'job_type', 'inventory', 'limit', 'credential',
                  'module_name', 'module_args', 'forks', 'verbosity', 'extra_vars',
                  'become_enabled', 'diff_mode', '-unified_job_template', '-description')
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
            module_name_choices = [(x, x) for x in settings.AD_HOC_COMMANDS]
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
            res['inventory'] = self.reverse('api:inventory_detail', kwargs={'pk': obj.inventory.pk})
        if obj.credential:
            res['credential'] = self.reverse('api:credential_detail', kwargs={'pk': obj.credential.pk})
        res.update(dict(
            events  = self.reverse('api:ad_hoc_command_ad_hoc_command_events_list', kwargs={'pk': obj.pk}),
            activity_stream = self.reverse('api:ad_hoc_command_activity_stream_list', kwargs={'pk': obj.pk}),
            notifications = self.reverse('api:ad_hoc_command_notifications_list', kwargs={'pk': obj.pk}),
        ))
        res['cancel'] = self.reverse('api:ad_hoc_command_cancel', kwargs={'pk': obj.pk})
        res['relaunch'] = self.reverse('api:ad_hoc_command_relaunch', kwargs={'pk': obj.pk})
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
            jobs = self.reverse('api:system_job_template_jobs_list', kwargs={'pk': obj.pk}),
            schedules = self.reverse('api:system_job_template_schedules_list', kwargs={'pk': obj.pk}),
            launch = self.reverse('api:system_job_template_launch', kwargs={'pk': obj.pk}),
            notification_templates_any = self.reverse('api:system_job_template_notification_templates_any_list', kwargs={'pk': obj.pk}),
            notification_templates_success = self.reverse('api:system_job_template_notification_templates_success_list', kwargs={'pk': obj.pk}),
            notification_templates_error = self.reverse('api:system_job_template_notification_templates_error_list', kwargs={'pk': obj.pk}),

        ))
        return res


class SystemJobSerializer(UnifiedJobSerializer):

    class Meta:
        model = SystemJob
        fields = ('*', 'system_job_template', 'job_type', 'extra_vars')

    def get_related(self, obj):
        res = super(SystemJobSerializer, self).get_related(obj)
        if obj.system_job_template:
            res['system_job_template'] = self.reverse('api:system_job_template_detail',
                                                      kwargs={'pk': obj.system_job_template.pk})
            res['notifications'] = self.reverse('api:system_job_notifications_list', kwargs={'pk': obj.pk})
        if obj.can_cancel or True:
            res['cancel'] = self.reverse('api:system_job_cancel', kwargs={'pk': obj.pk})
        return res


class SystemJobCancelSerializer(SystemJobSerializer):

    can_cancel = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_cancel',)


class WorkflowJobTemplateSerializer(JobTemplateMixin, LabelsListMixin, UnifiedJobTemplateSerializer):
    show_capabilities = ['start', 'schedule', 'edit', 'copy', 'delete']

    class Meta:
        model = WorkflowJobTemplate
        fields = ('*', 'extra_vars', 'organization', 'survey_enabled', 'allow_simultaneous',)

    def get_related(self, obj):
        res = super(WorkflowJobTemplateSerializer, self).get_related(obj)
        res.update(dict(
            workflow_jobs = self.reverse('api:workflow_job_template_jobs_list', kwargs={'pk': obj.pk}),
            schedules = self.reverse('api:workflow_job_template_schedules_list', kwargs={'pk': obj.pk}),
            launch = self.reverse('api:workflow_job_template_launch', kwargs={'pk': obj.pk}),
            copy = self.reverse('api:workflow_job_template_copy', kwargs={'pk': obj.pk}),
            workflow_nodes = self.reverse('api:workflow_job_template_workflow_nodes_list', kwargs={'pk': obj.pk}),
            labels = self.reverse('api:workflow_job_template_label_list', kwargs={'pk': obj.pk}),
            activity_stream = self.reverse('api:workflow_job_template_activity_stream_list', kwargs={'pk': obj.pk}),
            notification_templates_any = self.reverse('api:workflow_job_template_notification_templates_any_list', kwargs={'pk': obj.pk}),
            notification_templates_success = self.reverse('api:workflow_job_template_notification_templates_success_list', kwargs={'pk': obj.pk}),
            notification_templates_error = self.reverse('api:workflow_job_template_notification_templates_error_list', kwargs={'pk': obj.pk}),
            access_list = self.reverse('api:workflow_job_template_access_list', kwargs={'pk': obj.pk}),
            object_roles = self.reverse('api:workflow_job_template_object_roles_list', kwargs={'pk': obj.pk}),
            survey_spec = self.reverse('api:workflow_job_template_survey_spec', kwargs={'pk': obj.pk}),
        ))
        if obj.organization:
            res['organization'] = self.reverse('api:organization_detail',   kwargs={'pk': obj.organization.pk})
        return res

    def validate_extra_vars(self, value):
        return vars_validate_or_raise(value)


# TODO:
class WorkflowJobTemplateListSerializer(WorkflowJobTemplateSerializer):
    pass


# TODO:
class WorkflowJobSerializer(LabelsListMixin, UnifiedJobSerializer):

    class Meta:
        model = WorkflowJob
        fields = ('*', 'workflow_job_template', 'extra_vars', 'allow_simultaneous', '-execution_node',)

    def get_related(self, obj):
        res = super(WorkflowJobSerializer, self).get_related(obj)
        if obj.workflow_job_template:
            res['workflow_job_template'] = self.reverse('api:workflow_job_template_detail',
                                                        kwargs={'pk': obj.workflow_job_template.pk})
            res['notifications'] = self.reverse('api:workflow_job_notifications_list', kwargs={'pk': obj.pk})
        res['workflow_nodes'] = self.reverse('api:workflow_job_workflow_nodes_list', kwargs={'pk': obj.pk})
        res['labels'] = self.reverse('api:workflow_job_label_list', kwargs={'pk': obj.pk})
        res['activity_stream'] = self.reverse('api:workflow_job_activity_stream_list', kwargs={'pk': obj.pk})
        res['relaunch'] = self.reverse('api:workflow_job_relaunch', kwargs={'pk': obj.pk})
        if obj.can_cancel or True:
            res['cancel'] = self.reverse('api:workflow_job_cancel', kwargs={'pk': obj.pk})
        return res

    def to_representation(self, obj):
        ret = super(WorkflowJobSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        if 'extra_vars' in ret:
            ret['extra_vars'] = obj.display_extra_vars()
        return ret


# TODO:
class WorkflowJobListSerializer(WorkflowJobSerializer, UnifiedJobListSerializer):

    class Meta:
        fields = ('*', '-execution_node',)


class WorkflowJobCancelSerializer(WorkflowJobSerializer):

    can_cancel = serializers.BooleanField(read_only=True)

    class Meta:
        fields = ('can_cancel',)


class WorkflowNodeBaseSerializer(BaseSerializer):
    job_type = serializers.CharField(allow_blank=True, allow_null=True, required=False, default=None)
    job_tags = serializers.CharField(allow_blank=True, allow_null=True, required=False, default=None)
    limit = serializers.CharField(allow_blank=True, allow_null=True, required=False, default=None)
    skip_tags = serializers.CharField(allow_blank=True, allow_null=True, required=False, default=None)
    success_nodes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    failure_nodes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    always_nodes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        fields = ('*', '-name', '-description', 'id', 'url', 'related',
                  'unified_job_template', 'success_nodes', 'failure_nodes', 'always_nodes',
                  'inventory', 'credential', 'job_type', 'job_tags', 'skip_tags', 'limit', 'skip_tags')

    def get_related(self, obj):
        res = super(WorkflowNodeBaseSerializer, self).get_related(obj)
        if obj.unified_job_template:
            res['unified_job_template'] = obj.unified_job_template.get_absolute_url(self.context.get('request'))
        return res

    def validate(self, attrs):
        # char_prompts go through different validation, so remove them here
        for fd in ['job_type', 'job_tags', 'skip_tags', 'limit']:
            if fd in attrs:
                attrs.pop(fd)
        return super(WorkflowNodeBaseSerializer, self).validate(attrs)


class WorkflowJobTemplateNodeSerializer(WorkflowNodeBaseSerializer):
    class Meta:
        model = WorkflowJobTemplateNode
        fields = ('*', 'workflow_job_template',)

    def get_related(self, obj):
        res = super(WorkflowJobTemplateNodeSerializer, self).get_related(obj)
        res['success_nodes'] = self.reverse('api:workflow_job_template_node_success_nodes_list', kwargs={'pk': obj.pk})
        res['failure_nodes'] = self.reverse('api:workflow_job_template_node_failure_nodes_list', kwargs={'pk': obj.pk})
        res['always_nodes'] = self.reverse('api:workflow_job_template_node_always_nodes_list', kwargs={'pk': obj.pk})
        if obj.workflow_job_template:
            res['workflow_job_template'] = self.reverse('api:workflow_job_template_detail', kwargs={'pk': obj.workflow_job_template.pk})
        return res

    def to_internal_value(self, data):
        internal_value = super(WorkflowNodeBaseSerializer, self).to_internal_value(data)
        view = self.context.get('view', None)
        request_method = None
        if view and view.request:
            request_method = view.request.method
        if request_method in ['PATCH']:
            obj = self.instance
            char_prompts = copy.copy(obj.char_prompts)
            char_prompts.update(self.extract_char_prompts(data))
        else:
            char_prompts = self.extract_char_prompts(data)
        for fd in copy.copy(char_prompts):
            if char_prompts[fd] is None:
                char_prompts.pop(fd)
        internal_value['char_prompts'] = char_prompts
        return internal_value

    def extract_char_prompts(self, data):
        char_prompts = {}
        for fd in ['job_type', 'job_tags', 'skip_tags', 'limit']:
            # Accept null values, if given
            if fd in data:
                char_prompts[fd] = data[fd]
        return char_prompts

    def validate(self, attrs):
        if 'char_prompts' in attrs:
            if 'job_type' in attrs['char_prompts']:
                job_types = [t for t, v in JOB_TYPE_CHOICES]
                if attrs['char_prompts']['job_type'] not in job_types:
                    raise serializers.ValidationError({
                        "job_type": _("%(job_type)s is not a valid job type. The choices are %(choices)s.") % {
                            'job_type': attrs['char_prompts']['job_type'], 'choices': job_types}})
        if self.instance is None and ('workflow_job_template' not in attrs or
                                      attrs['workflow_job_template'] is None):
            raise serializers.ValidationError({
                "workflow_job_template": _("Workflow job template is missing during creation.")
            })
        ujt_obj = attrs.get('unified_job_template', None)
        if isinstance(ujt_obj, (WorkflowJobTemplate, SystemJobTemplate)):
            raise serializers.ValidationError({
                "unified_job_template": _("Cannot nest a %s inside a WorkflowJobTemplate") % ujt_obj.__class__.__name__})
        return super(WorkflowJobTemplateNodeSerializer, self).validate(attrs)


class WorkflowJobNodeSerializer(WorkflowNodeBaseSerializer):
    class Meta:
        model = WorkflowJobNode
        fields = ('*', 'job', 'workflow_job',)

    def get_related(self, obj):
        res = super(WorkflowJobNodeSerializer, self).get_related(obj)
        res['success_nodes'] = self.reverse('api:workflow_job_node_success_nodes_list', kwargs={'pk': obj.pk})
        res['failure_nodes'] = self.reverse('api:workflow_job_node_failure_nodes_list', kwargs={'pk': obj.pk})
        res['always_nodes'] = self.reverse('api:workflow_job_node_always_nodes_list', kwargs={'pk': obj.pk})
        if obj.job:
            res['job'] = obj.job.get_absolute_url(self.context.get('request'))
        if obj.workflow_job:
            res['workflow_job'] = self.reverse('api:workflow_job_detail', kwargs={'pk': obj.workflow_job.pk})
        return res


class WorkflowJobNodeListSerializer(WorkflowJobNodeSerializer):
    pass


class WorkflowJobNodeDetailSerializer(WorkflowJobNodeSerializer):
    pass


class WorkflowJobTemplateNodeDetailSerializer(WorkflowJobTemplateNodeSerializer):
    '''
    Influence the api browser sample data to not include workflow_job_template
    when editing a WorkflowNode.

    Note: I was not able to accomplish this trough the use of extra_kwargs.
    Maybe something to do with workflow_job_template being a relational field?
    '''
    def build_relational_field(self, field_name, relation_info):
        field_class, field_kwargs = super(WorkflowJobTemplateNodeDetailSerializer, self).build_relational_field(field_name, relation_info)
        if self.instance and field_name == 'workflow_job_template':
            field_kwargs['read_only'] = True
            field_kwargs.pop('queryset', None)
        return field_class, field_kwargs


class WorkflowJobTemplateNodeListSerializer(WorkflowJobTemplateNodeSerializer):
    pass


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
            job=self.reverse('api:job_detail', kwargs={'pk': obj.job.pk})))
        if obj.host is not None:
            res.update(dict(
                host=self.reverse('api:host_detail', kwargs={'pk': obj.host.pk})
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
                  'changed', 'uuid', 'parent_uuid', 'host', 'host_name', 'parent',
                  'playbook', 'play', 'task', 'role', 'stdout', 'start_line', 'end_line',
                  'verbosity')

    def get_related(self, obj):
        res = super(JobEventSerializer, self).get_related(obj)
        res.update(dict(
            job = self.reverse('api:job_detail', kwargs={'pk': obj.job_id}),
        ))
        if obj.parent_id:
            res['parent'] = self.reverse('api:job_event_detail', kwargs={'pk': obj.parent_id})
        if obj.children.exists():
            res['children'] = self.reverse('api:job_event_children_list', kwargs={'pk': obj.pk})
        if obj.host_id:
            res['host'] = self.reverse('api:host_detail', kwargs={'pk': obj.host_id})
        if obj.hosts.exists():
            res['hosts'] = self.reverse('api:job_event_hosts_list', kwargs={'pk': obj.pk})
        return res

    def get_summary_fields(self, obj):
        d = super(JobEventSerializer, self).get_summary_fields(obj)
        try:
            d['job']['job_template_id'] = obj.job.job_template.id
            d['job']['job_template_name'] = obj.job.job_template.name
        except (KeyError, AttributeError):
            pass
        return d

    def to_representation(self, obj):
        ret = super(JobEventSerializer, self).to_representation(obj)
        # Show full stdout for event detail view, truncate only for list view.
        if hasattr(self.context.get('view', None), 'retrieve'):
            return ret
        # Show full stdout for playbook_on_* events.
        if obj and obj.event.startswith('playbook_on'):
            return ret
        max_bytes = settings.EVENT_STDOUT_MAX_BYTES_DISPLAY
        if max_bytes > 0 and 'stdout' in ret and len(ret['stdout']) >= max_bytes:
            ret['stdout'] = ret['stdout'][:(max_bytes - 1)] + u'\u2026'
            set_count = 0
            reset_count = 0
            for m in ANSI_SGR_PATTERN.finditer(ret['stdout']):
                if m.string[m.start():m.end()] == u'\u001b[0m':
                    reset_count += 1
                else:
                    set_count += 1
            ret['stdout'] += u'\u001b[0m' * (set_count - reset_count)
        return ret


class AdHocCommandEventSerializer(BaseSerializer):

    event_display = serializers.CharField(source='get_event_display', read_only=True)

    class Meta:
        model = AdHocCommandEvent
        fields = ('*', '-name', '-description', 'ad_hoc_command', 'event',
                  'counter', 'event_display', 'event_data', 'failed',
                  'changed', 'uuid', 'host', 'host_name', 'stdout',
                  'start_line', 'end_line', 'verbosity')

    def get_related(self, obj):
        res = super(AdHocCommandEventSerializer, self).get_related(obj)
        res.update(dict(
            ad_hoc_command = self.reverse('api:ad_hoc_command_detail', kwargs={'pk': obj.ad_hoc_command_id}),
        ))
        if obj.host:
            res['host'] = self.reverse('api:host_detail', kwargs={'pk': obj.host.pk})
        return res

    def to_representation(self, obj):
        ret = super(AdHocCommandEventSerializer, self).to_representation(obj)
        # Show full stdout for event detail view, truncate only for list view.
        if hasattr(self.context.get('view', None), 'retrieve'):
            return ret
        max_bytes = settings.EVENT_STDOUT_MAX_BYTES_DISPLAY
        if max_bytes > 0 and 'stdout' in ret and len(ret['stdout']) >= max_bytes:
            ret['stdout'] = ret['stdout'][:(max_bytes - 1)] + u'\u2026'
            set_count = 0
            reset_count = 0
            for m in ANSI_SGR_PATTERN.finditer(ret['stdout']):
                if m.string[m.start():m.end()] == u'\u001b[0m':
                    reset_count += 1
                else:
                    set_count += 1
            ret['stdout'] += u'\u001b[0m' * (set_count - reset_count)
        return ret


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
                  'credential', 'extra_credentials', 'ask_variables_on_launch', 'ask_tags_on_launch',
                  'ask_diff_mode_on_launch', 'ask_skip_tags_on_launch', 'ask_job_type_on_launch', 'ask_limit_on_launch',
                  'ask_verbosity_on_launch', 'ask_inventory_on_launch', 'ask_credential_on_launch',
                  'survey_enabled', 'variables_needed_to_start', 'credential_needed_to_start',
                  'inventory_needed_to_start', 'job_template_data', 'defaults', 'verbosity')
        read_only_fields = (
            'ask_diff_mode_on_launch', 'ask_variables_on_launch', 'ask_limit_on_launch', 'ask_tags_on_launch',
            'ask_skip_tags_on_launch', 'ask_job_type_on_launch', 'ask_verbosity_on_launch',
            'ask_inventory_on_launch', 'ask_credential_on_launch',)
        extra_kwargs = {
            'credential': {'write_only': True,},
            'extra_credentials': {'write_only': True, 'default': [], 'allow_empty': True},
            'limit': {'write_only': True,},
            'job_tags': {'write_only': True,},
            'skip_tags': {'write_only': True,},
            'job_type': {'write_only': True,},
            'inventory': {'write_only': True,},
            'verbosity': {'write_only': True,}
        }

    # TODO: remove in 3.3
    def get_fields(self):
        ret = super(JobLaunchSerializer, self).get_fields()
        if self.version == 1:
            ret.pop('extra_credentials')
        return ret

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
        ask_for_vars_dict['vault_credential'] = False
        defaults_dict = {}
        for field in ask_for_vars_dict:
            if field in ('inventory', 'credential', 'vault_credential'):
                defaults_dict[field] = dict(
                    name=getattrd(obj, '%s.name' % field, None),
                    id=getattrd(obj, '%s.pk' % field, None))
            elif field == 'extra_credentials':
                if self.version > 1:
                    defaults_dict[field] = [
                        dict(
                            id=cred.id,
                            name=cred.name,
                            credential_type=cred.credential_type.pk
                        )
                        for cred in obj.extra_credentials.all()
                    ]
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
            if not (attrs.get(field, False) and obj._ask_for_vars_dict().get(field, False)):
                errors[field] = _("Job Template '%s' is missing or undefined.") % field

        if obj.inventory and obj.inventory.pending_deletion is True:
            errors['inventory'] = _("The inventory associated with this Job Template is being deleted.")

        if (not obj.ask_credential_on_launch) or (not attrs.get('credential', None)):
            credential = obj.credential
        else:
            credential = attrs.get('credential', None)

        # fill passwords dict with request data passwords
        for cred in (credential, obj.vault_credential):
            if cred and cred.passwords_needed:
                passwords = self.context.get('passwords')
                try:
                    for p in cred.passwords_needed:
                        passwords[p] = data[p]
                except KeyError:
                    errors.setdefault('passwords_needed_to_start', []).extend(cred.passwords_needed)

        extra_vars = attrs.get('extra_vars', {})

        if isinstance(extra_vars, basestring):
            try:
                extra_vars = json.loads(extra_vars)
            except (ValueError, TypeError):
                try:
                    extra_vars = yaml.safe_load(extra_vars)
                    assert isinstance(extra_vars, dict)
                except (yaml.YAMLError, TypeError, AttributeError, AssertionError):
                    errors['extra_vars'] = _('Must be valid JSON or YAML.')

        if not isinstance(extra_vars, dict):
            extra_vars = {}

        if self.get_survey_enabled(obj):
            validation_errors = obj.survey_variable_validation(extra_vars)
            if validation_errors:
                errors['variables_needed_to_start'] = validation_errors

        extra_cred_kinds = []
        for cred in data.get('extra_credentials', []):
            cred = Credential.objects.get(id=cred)
            if cred.credential_type.pk in extra_cred_kinds:
                errors['extra_credentials'] = _('Cannot assign multiple %s credentials.' % cred.credential_type.name)
            if cred.credential_type.kind not in ('net', 'cloud'):
                errors['extra_credentials'] = _('Extra credentials must be network or cloud.')
            extra_cred_kinds.append(cred.credential_type.pk)

        # Special prohibited cases for scan jobs
        errors.update(obj._extra_job_type_errors(data))

        if errors:
            raise serializers.ValidationError(errors)

        JT_extra_vars = obj.extra_vars
        JT_limit = obj.limit
        JT_job_type = obj.job_type
        JT_job_tags = obj.job_tags
        JT_skip_tags = obj.skip_tags
        JT_inventory = obj.inventory
        JT_credential = obj.credential
        JT_verbosity = obj.verbosity
        extra_credentials = attrs.pop('extra_credentials', None)
        attrs = super(JobLaunchSerializer, self).validate(attrs)
        obj.extra_vars = JT_extra_vars
        obj.limit = JT_limit
        obj.job_type = JT_job_type
        obj.skip_tags = JT_skip_tags
        obj.job_tags = JT_job_tags
        obj.inventory = JT_inventory
        obj.credential = JT_credential
        obj.verbosity = JT_verbosity
        if extra_credentials is not None:
            attrs['extra_credentials'] = extra_credentials
        return attrs


class WorkflowJobLaunchSerializer(BaseSerializer):

    can_start_without_user_input = serializers.BooleanField(read_only=True)
    variables_needed_to_start = serializers.ReadOnlyField()
    survey_enabled = serializers.SerializerMethodField()
    extra_vars = VerbatimField(required=False, write_only=True)
    workflow_job_template_data = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowJobTemplate
        fields = ('can_start_without_user_input', 'extra_vars',
                  'survey_enabled', 'variables_needed_to_start',
                  'node_templates_missing', 'node_prompts_rejected',
                  'workflow_job_template_data')

    def get_survey_enabled(self, obj):
        if obj:
            return obj.survey_enabled and 'spec' in obj.survey_spec
        return False

    def get_workflow_job_template_data(self, obj):
        return dict(name=obj.name, id=obj.id, description=obj.description)

    def validate(self, attrs):
        errors = {}
        obj = self.instance

        extra_vars = attrs.get('extra_vars', {})

        if isinstance(extra_vars, basestring):
            try:
                extra_vars = json.loads(extra_vars)
            except (ValueError, TypeError):
                try:
                    extra_vars = yaml.safe_load(extra_vars)
                    assert isinstance(extra_vars, dict)
                except (yaml.YAMLError, TypeError, AttributeError, AssertionError):
                    errors['extra_vars'] = _('Must be valid JSON or YAML.')

        if not isinstance(extra_vars, dict):
            extra_vars = {}

        if self.get_survey_enabled(obj):
            validation_errors = obj.survey_variable_validation(extra_vars)
            if validation_errors:
                errors['variables_needed_to_start'] = validation_errors

        if errors:
            raise serializers.ValidationError(errors)

        WFJT_extra_vars = obj.extra_vars
        attrs = super(WorkflowJobLaunchSerializer, self).validate(attrs)
        obj.extra_vars = WFJT_extra_vars
        return attrs


class NotificationTemplateSerializer(BaseSerializer):
    show_capabilities = ['edit', 'delete']

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
        if 'notification_configuration' in ret:
            ret['notification_configuration'] = obj.display_notification_configuration()
        return ret

    def get_related(self, obj):
        res = super(NotificationTemplateSerializer, self).get_related(obj)
        res.update(dict(
            test = self.reverse('api:notification_template_test', kwargs={'pk': obj.pk}),
            notifications = self.reverse('api:notification_template_notification_list', kwargs={'pk': obj.pk}),
        ))
        if obj.organization:
            res['organization'] = self.reverse('api:organization_detail', kwargs={'pk': obj.organization.pk})
        return res

    def _recent_notifications(self, obj):
        return [{'id': x.id, 'status': x.status, 'created': x.created} for x in obj.notifications.all().order_by('-created')[:5]]

    def get_summary_fields(self, obj):
        d = super(NotificationTemplateSerializer, self).get_summary_fields(obj)
        d['recent_notifications'] = self._recent_notifications(obj)
        return d

    def validate(self, attrs):
        from awx.api.views import NotificationTemplateDetail

        notification_type = None
        if 'notification_type' in attrs:
            notification_type = attrs['notification_type']
        elif self.instance:
            notification_type = self.instance.notification_type
        else:
            notification_type = None
        if not notification_type:
            raise serializers.ValidationError(_('Missing required fields for Notification Configuration: notification_type'))

        notification_class = NotificationTemplate.CLASS_FOR_NOTIFICATION_TYPE[notification_type]
        missing_fields = []
        incorrect_type_fields = []
        error_list = []
        if 'notification_configuration' not in attrs:
            return attrs
        if self.context['view'].kwargs and isinstance(self.context['view'], NotificationTemplateDetail):
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
            if field_type == "list" and len(field_val) < 1:
                error_list.append(_("No values specified for field '{}'").format(field))
                continue
            if field_type == "password" and field_val == "$encrypted$" and object_actual is not None:
                attrs['notification_configuration'][field] = object_actual.notification_configuration[field]
        if missing_fields:
            error_list.append(_("Missing required fields for Notification Configuration: {}.").format(missing_fields))
        if incorrect_type_fields:
            for type_field_error in incorrect_type_fields:
                error_list.append(_("Configuration field '{}' incorrect type, expected {}.").format(type_field_error[0],
                                                                                                    type_field_error[1]))
        if error_list:
            raise serializers.ValidationError(error_list)
        return super(NotificationTemplateSerializer, self).validate(attrs)


class NotificationSerializer(BaseSerializer):

    class Meta:
        model = Notification
        fields = ('*', '-name', '-description', 'notification_template', 'error', 'status', 'notifications_sent',
                  'notification_type', 'recipients', 'subject')

    def get_related(self, obj):
        res = super(NotificationSerializer, self).get_related(obj)
        res.update(dict(
            notification_template = self.reverse('api:notification_template_detail', kwargs={'pk': obj.notification_template.pk}),
        ))
        return res


class LabelSerializer(BaseSerializer):

    class Meta:
        model = Label
        fields = ('*', '-description', 'organization')

    def get_related(self, obj):
        res = super(LabelSerializer, self).get_related(obj)
        if obj.organization:
            res['organization'] = self.reverse('api:organization_detail', kwargs={'pk': obj.organization.pk})
        return res


class ScheduleSerializer(BaseSerializer):
    show_capabilities = ['edit', 'delete']

    class Meta:
        model = Schedule
        fields = ('*', 'unified_job_template', 'enabled', 'dtstart', 'dtend', 'rrule', 'next_run', 'extra_data')

    def get_related(self, obj):
        res = super(ScheduleSerializer, self).get_related(obj)
        res.update(dict(
            unified_jobs = self.reverse('api:schedule_unified_jobs_list', kwargs={'pk': obj.pk}),
        ))
        if obj.unified_job_template:
            res['unified_job_template'] = obj.unified_job_template.get_absolute_url(self.context.get('request'))
        return res

    def validate_unified_job_template(self, value):
        if type(value) == InventorySource and value.source not in SCHEDULEABLE_PROVIDERS:
            raise serializers.ValidationError(_('Inventory Source must be a cloud resource.'))
        elif type(value) == Project and value.scm_type == '':
            raise serializers.ValidationError(_('Manual Project cannot have a schedule set.'))
        elif type(value) == InventorySource and value.source == 'scm' and value.update_on_project_update:
            raise serializers.ValidationError(_(
                'Inventory sources with `update_on_project_update` cannot be scheduled. '
                'Schedule its source project `{}` instead.'.format(value.source_project.name)))
        return value

    def validate_extra_data(self, value):
        if isinstance(value, dict):
            return value
        return vars_validate_or_raise(value)

    def validate(self, attrs):
        extra_data = parse_yaml_or_json(attrs.get('extra_data', {}))
        if extra_data:
            ujt = None
            if 'unified_job_template' in attrs:
                ujt = attrs['unified_job_template']
            elif self.instance:
                ujt = self.instance.unified_job_template
            if ujt and isinstance(ujt, (Project, InventorySource)):
                raise serializers.ValidationError({'extra_data': _(
                    'Projects and inventory updates cannot accept extra variables.')})
        return super(ScheduleSerializer, self).validate(attrs)

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
            raise serializers.ValidationError(_('DTSTART required in rrule. Value should match: DTSTART:YYYYMMDDTHHMMSSZ'))
        if len(match_multiple_dtstart) > 1:
            raise serializers.ValidationError(_('Multiple DTSTART is not supported.'))
        if not len(match_multiple_rrule):
            raise serializers.ValidationError(_('RRULE require in rrule.'))
        if len(match_multiple_rrule) > 1:
            raise serializers.ValidationError(_('Multiple RRULE is not supported.'))
        if 'interval' not in rrule_value.lower():
            raise serializers.ValidationError(_('INTERVAL required in rrule.'))
        if 'tzid' in rrule_value.lower():
            raise serializers.ValidationError(_('TZID is not supported.'))
        if 'secondly' in rrule_value.lower():
            raise serializers.ValidationError(_('SECONDLY is not supported.'))
        if re.match(multi_by_month_day, rrule_value):
            raise serializers.ValidationError(_('Multiple BYMONTHDAYs not supported.'))
        if re.match(multi_by_month, rrule_value):
            raise serializers.ValidationError(_('Multiple BYMONTHs not supported.'))
        if re.match(by_day_with_numeric_prefix, rrule_value):
            raise serializers.ValidationError(_("BYDAY with numeric prefix not supported."))
        if 'byyearday' in rrule_value.lower():
            raise serializers.ValidationError(_("BYYEARDAY not supported."))
        if 'byweekno' in rrule_value.lower():
            raise serializers.ValidationError(_("BYWEEKNO not supported."))
        if match_count:
            count_val = match_count.groups()[0].strip().split("=")
            if int(count_val[1]) > 999:
                raise serializers.ValidationError(_("COUNT > 999 is unsupported."))
        try:
            rrule.rrulestr(rrule_value)
        except Exception:
            raise serializers.ValidationError(_("rrule parsing failed validation."))
        return value


class InstanceSerializer(BaseSerializer):

    consumed_capacity = serializers.SerializerMethodField()
    percent_capacity_remaining = serializers.SerializerMethodField()
    jobs_running = serializers.SerializerMethodField()

    class Meta:
        model = Instance
        fields = ("id", "type", "url", "related", "uuid", "hostname", "created", "modified",
                  "version", "capacity", "consumed_capacity", "percent_capacity_remaining", "jobs_running")

    def get_related(self, obj):
        res = super(InstanceSerializer, self).get_related(obj)
        res['jobs'] = self.reverse('api:instance_unified_jobs_list', kwargs={'pk': obj.pk})
        res['instance_groups'] = self.reverse('api:instance_instance_groups_list', kwargs={'pk': obj.pk})
        return res

    def get_consumed_capacity(self, obj):
        return obj.consumed_capacity

    def get_percent_capacity_remaining(self, obj):
        if not obj.capacity or obj.consumed_capacity == obj.capacity:
            return 0.0
        else:
            return float("{0:.2f}".format(((float(obj.capacity) - float(obj.consumed_capacity)) / (float(obj.capacity))) * 100))

    def get_jobs_running(self, obj):
        return UnifiedJob.objects.filter(execution_node=obj.hostname, status__in=('running', 'waiting',)).count()


class InstanceGroupSerializer(BaseSerializer):

    consumed_capacity = serializers.SerializerMethodField()
    percent_capacity_remaining = serializers.SerializerMethodField()
    jobs_running = serializers.SerializerMethodField()
    instances = serializers.SerializerMethodField()

    class Meta:
        model = InstanceGroup
        fields = ("id", "type", "url", "related", "name", "created", "modified", "capacity", "consumed_capacity",
                  "percent_capacity_remaining", "jobs_running", "instances", "controller")

    def get_related(self, obj):
        res = super(InstanceGroupSerializer, self).get_related(obj)
        res['jobs'] = self.reverse('api:instance_group_unified_jobs_list', kwargs={'pk': obj.pk})
        res['instances'] = self.reverse('api:instance_group_instance_list', kwargs={'pk': obj.pk})
        if obj.controller_id:
            res['controller'] = self.reverse('api:instance_group_detail', kwargs={'pk': obj.controller_id})
        return res

    def get_jobs_qs(self):
        # Store running jobs queryset in context, so it will be shared in ListView
        if 'running_jobs' not in self.context:
            self.context['running_jobs'] = UnifiedJob.objects.filter(
                status__in=('running', 'waiting'))
        return self.context['running_jobs']

    def get_capacity_dict(self):
        # Store capacity values (globally computed) in the context
        if 'capacity_map' not in self.context:
            ig_qs = None
            if self.parent:  # Is ListView:
                ig_qs = self.parent.instance
            self.context['capacity_map'] = InstanceGroup.objects.capacity_values(
                qs=ig_qs, tasks=self.get_jobs_qs(), breakdown=True)
        return self.context['capacity_map']

    def get_consumed_capacity(self, obj):
        return self.get_capacity_dict()[obj.name]['consumed_capacity']

    def get_percent_capacity_remaining(self, obj):
        if not obj.capacity:
            return 0.0
        else:
            return float("{0:.2f}".format(
                ((float(obj.capacity) - float(self.get_consumed_capacity(obj))) / (float(obj.capacity))) * 100)
            )

    def get_jobs_running(self, obj):
        jobs_qs = self.get_jobs_qs()
        return sum(1 for job in jobs_qs if job.instance_group_id == obj.id)

    def get_instances(self, obj):
        return obj.instances.count()


class ActivityStreamSerializer(BaseSerializer):

    changes = serializers.SerializerMethodField()
    object_association = serializers.SerializerMethodField()

    @cached_property
    def _local_summarizable_fk_fields(self):
        summary_dict = copy.copy(SUMMARIZABLE_FK_FIELDS)
        # Special requests
        summary_dict['group'] = summary_dict['group'] + ('inventory_id',)
        for key in summary_dict.keys():
            if 'id' not in summary_dict[key]:
                summary_dict[key] = summary_dict[key] + ('id',)
        field_list = summary_dict.items()
        # Needed related fields that are not in the default summary fields
        field_list += [
            ('workflow_job_template_node', ('id', 'unified_job_template_id')),
            ('label', ('id', 'name', 'organization_id')),
            ('notification', ('id', 'status', 'notification_type', 'notification_template_id'))
        ]
        return field_list

    class Meta:
        model = ActivityStream
        fields = ('*', '-name', '-description', '-created', '-modified',
                  'timestamp', 'operation', 'changes', 'object1', 'object2', 'object_association')

    def get_fields(self):
        ret = super(ActivityStreamSerializer, self).get_fields()
        for key, field in ret.items():
            if key == 'changes':
                field.help_text = _('A summary of the new and changed values when an object is created, updated, or deleted')
            if key == 'object1':
                field.help_text = _('For create, update, and delete events this is the object type that was affected. '
                                    'For associate and disassociate events this is the object type associated or disassociated with object2.')
            if key == 'object2':
                field.help_text = _('Unpopulated for create, update, and delete events. For associate and disassociate '
                                    'events this is the object type that object1 is being associated with.')
            if key == 'operation':
                field.help_text = _('The action taken with respect to the given object(s).')
        return ret

    def get_changes(self, obj):
        if obj is None:
            return {}
        try:
            return json.loads(obj.changes)
        except Exception:
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
            rel['actor'] = self.reverse('api:user_detail', kwargs={'pk': obj.actor.pk})
        for fk, __ in self._local_summarizable_fk_fields:
            if not hasattr(obj, fk):
                continue
            m2m_list = self._get_rel(obj, fk)
            if m2m_list:
                rel[fk] = []
                id_list = []
                for thisItem in m2m_list:
                    if getattr(thisItem, 'id', None) in id_list:
                        continue
                    id_list.append(getattr(thisItem, 'id', None))
                    if fk == 'custom_inventory_script':
                        rel[fk].append(self.reverse('api:inventory_script_detail', kwargs={'pk': thisItem.id}))
                    else:
                        rel[fk].append(self.reverse('api:' + fk + '_detail', kwargs={'pk': thisItem.id}))

                    if fk == 'schedule':
                        rel['unified_job_template'] = thisItem.unified_job_template.get_absolute_url(self.context.get('request'))
        return rel

    def _get_rel(self, obj, fk):
        related_model = ActivityStream._meta.get_field(fk).related_model
        related_manager = getattr(obj, fk)
        if issubclass(related_model, PolymorphicModel) and hasattr(obj, '_prefetched_objects_cache'):
            # HACK: manually fill PolymorphicModel caches to prevent running query multiple times
            # unnecessary if django-polymorphic issue #68 is solved
            if related_manager.prefetch_cache_name not in obj._prefetched_objects_cache:
                obj._prefetched_objects_cache[related_manager.prefetch_cache_name] = list(related_manager.all())
        return related_manager.all()

    def get_summary_fields(self, obj):
        summary_fields = OrderedDict()
        for fk, related_fields in self._local_summarizable_fk_fields:
            try:
                if not hasattr(obj, fk):
                    continue
                m2m_list = self._get_rel(obj, fk)
                if m2m_list:
                    summary_fields[fk] = []
                    for thisItem in m2m_list:
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
                raise serializers.ValidationError(_('Unable to login with provided credentials.'))
        else:
            raise serializers.ValidationError(_('Must include "username" and "password".'))


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
        res['fact_view'] = '%s?%s' % (
            reverse('api:host_fact_compare_view', kwargs={'pk': obj.host.pk}, request=self.context.get('request')),
            urllib.urlencode(params)
        )
        return res


class FactSerializer(BaseFactSerializer):

    class Meta:
        model = Fact
        # TODO: Consider adding in host to the fields list ?
        fields = ('related', 'timestamp', 'module', 'facts', 'id', 'summary_fields', 'host')
        read_only_fields = ('*',)

    def get_related(self, obj):
        res = super(FactSerializer, self).get_related(obj)
        res['host'] = obj.host.get_absolute_url(self.context.get('request'))
        return res

    def to_representation(self, obj):
        ret = super(FactSerializer, self).to_representation(obj)
        if obj is None:
            return ret
        if 'facts' in ret and isinstance(ret['facts'], six.string_types):
            ret['facts'] = json.loads(ret['facts'])
        return ret
