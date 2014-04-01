# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import json
import re
import socket
import urlparse
import logging
import os.path
from dateutil import rrule

# PyYAML
import yaml

# Django
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import BLANK_CHOICE_DASH
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.compat import get_concrete_model
from rest_framework import fields
from rest_framework import serializers

# AWX
from awx.main.models import *
from awx.main.utils import update_scm_url, get_type_for_model, get_model_for_type

logger = logging.getLogger('awx.api.serializers')

# Fields that should be summarized regardless of object type.
DEFAULT_SUMMARY_FIELDS = ('name', 'description',)

# Keys are fields (foreign keys) where, if found on an instance, summary info
# should be added to the serialized data.  Values are a tuple of field names on
# the related object to include in the summary data (if the field is present on
# the related object).
SUMMARIZABLE_FK_FIELDS = {
    'organization': DEFAULT_SUMMARY_FIELDS,
    'user': ('username', 'first_name', 'last_name'),
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
    'permission': DEFAULT_SUMMARY_FIELDS,
    'job': DEFAULT_SUMMARY_FIELDS + ('status', 'failed',),
    'job_template': DEFAULT_SUMMARY_FIELDS,
    'schedule': DEFAULT_SUMMARY_FIELDS + ('next_run',),
    'unified_job_template': DEFAULT_SUMMARY_FIELDS + ('type',),
    'last_job': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
    'last_job_host_summary': DEFAULT_SUMMARY_FIELDS + ('failed',),
    'last_update': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
    'current_update': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
    'current_job': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
    'inventory_source': ('source', 'last_updated', 'status'),
}

class ChoiceField(fields.ChoiceField):

    def __init__(self, *args, **kwargs):
        super(ChoiceField, self).__init__(*args, **kwargs)
        if not self.required:
            # Remove extra blank option if one is already present (for writable
            # field) or if present at all for read-only fields.
            if ([x[0] for x in self.choices].count(u'') > 1 or self.read_only) \
                and BLANK_CHOICE_DASH[0] in self.choices:
                self.choices = [x for x in self.choices
                                if x != BLANK_CHOICE_DASH[0]]

    def metadata(self):
        metadata = super(ChoiceField, self).metadata()
        if self.choices:
            metadata['choices'] = self.choices
        return metadata

# Monkeypatch REST framework to replace default ChoiceField used by
# ModelSerializer.
serializers.ChoiceField = ChoiceField


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

    '''

    @classmethod
    def _update_meta(self, base, meta, other=None):
        for attr in dir(other):
            if attr.startswith('_'):
                continue
            val = getattr(other, attr)
            # Special handling for lists of strings (field names).
            if isinstance(val, (list, tuple)) and all([isinstance(x, basestring) for x in val]):
                new_vals = []
                except_vals = []
                if base: # Merge values from all bases.
                    new_vals.extend([x for x in getattr(meta, attr, [])])
                for v in val:
                    if not base and v == '*': # Inherit all values from previous base(es).
                        new_vals.extend([x for x in getattr(meta, attr, [])])
                    elif not base and v.startswith('-'): # Except these values.
                        except_vals.append(v[1:])
                    else:
                        new_vals.append(v)
                val = []
                for v in new_vals:
                    if v not in except_vals and v not in val:
                        val.append(v)
            setattr(meta, attr, val)

    def __new__(cls, name, bases, attrs):
        meta = type('Meta', (object,), {})
        for base in bases[::-1]:
            cls._update_meta(base, meta, getattr(base, 'Meta', None))
        cls._update_meta(None, meta, attrs.get('Meta', meta))
        attrs['Meta'] = meta
        return super(BaseSerializerMetaclass, cls).__new__(cls, name, bases, attrs)


class BaseSerializerOptions(serializers.ModelSerializerOptions):

    def __init__(self, meta):
        super(BaseSerializerOptions, self).__init__(meta)
        self.summary_fields = getattr(meta, 'summary_fields', ())
        self.summarizable_fields = getattr(meta, 'summarizable_fields', ())


class BaseSerializer(serializers.ModelSerializer):

    __metaclass__ = BaseSerializerMetaclass
    _options_class = BaseSerializerOptions

    class Meta:
        fields = ('id', 'type', 'url', 'related', 'summary_fields', 'created',
                  'modified', 'name', 'description')
        summary_fields = () # FIXME: List of field names from this serializer that should be used when included as part of another's summary_fields.
        summarizable_fields = () # FIXME: List of field names on this serializer that should be included in summary_fields.

    # add the URL and related resources
    type           = serializers.SerializerMethodField('get_type')
    url            = serializers.SerializerMethodField('get_url')
    related        = serializers.SerializerMethodField('_get_related')
    summary_fields = serializers.SerializerMethodField('_get_summary_fields')

    # make certain fields read only
    created       = serializers.SerializerMethodField('get_created')
    modified      = serializers.SerializerMethodField('get_modified')
    active        = serializers.SerializerMethodField('get_active')

    def get_fields(self):
        opts = get_concrete_model(self.opts.model)._meta
        ret = super(BaseSerializer, self).get_fields()
        for key, field in ret.items():
            if key == 'id' and not getattr(field, 'help_text', None):
                field.help_text = 'Database ID for this %s.' % unicode(opts.verbose_name)
            elif key == 'type':
                field.help_text = 'Data type for this %s.' % unicode(opts.verbose_name)
                field.type_label = 'string'
            elif key == 'url':
                field.help_text = 'URL for this %s.' % unicode(opts.verbose_name)
                field.type_label = 'string'
            elif key == 'related':
                field.help_text = 'Data structure with URLs of related resources.'
                field.type_label = 'object'
            elif key == 'summary_fields':
                field.help_text = 'Data structure with name/description for related resources.'
                field.type_label = 'object'
            elif key == 'created':
                field.help_text = 'Timestamp when this %s was created.' % unicode(opts.verbose_name)
                field.type_label = 'datetime'
            elif key == 'modified':
                field.help_text = 'Timestamp when this %s was last modified.' % unicode(opts.verbose_name)
                field.type_label = 'datetime'
        return ret

    def get_type(self, obj):
        return get_type_for_model(self.opts.model)

    def get_types(self):
        return [self.get_type(None)]

    def get_type_choices(self):
        type_name_map = {
            'job': 'Playbook Run',
            'project_update': 'SCM Update',
            'inventory_update': 'Inventory Sync',
        }
        choices = []
        for t in self.get_types():
            name = type_name_map.get(t, unicode(get_model_for_type(t)._meta.verbose_name).title())
            choices.append((t, name))
        return choices

    def get_url(self, obj):
        if obj is None:
            return ''
        elif isinstance(obj, User):
            return reverse('api:user_detail', args=(obj.pk,))
        else:
            return obj.get_absolute_url()

    def _get_related(self, obj):
        return {} if obj is None else self.get_related(obj)

    def get_related(self, obj):
        res = SortedDict()
        if getattr(obj, 'created_by', None) and obj.created_by.is_active:
            res['created_by'] = reverse('api:user_detail', args=(obj.created_by.pk,))
        if getattr(obj, 'modified_by', None) and obj.modified_by.is_active:
            res['modified_by'] = reverse('api:user_detail', args=(obj.modified_by.pk,))
        return res

    def _get_summary_fields(self, obj):
        return {} if obj is None else self.get_summary_fields(obj)

    def get_summary_fields(self, obj):
        # Return values for certain fields on related objects, to simplify
        # displaying lists of items without additional API requests.
        summary_fields = SortedDict()
        for fk, related_fields in SUMMARIZABLE_FK_FIELDS.items():
            try:
                fkval = getattr(obj, fk, None)
                if fkval is None:
                    continue
                if fkval == obj:
                    continue
                if hasattr(fkval, 'active') and not fkval.active:
                    continue
                if hasattr(fkval, 'is_active') and not fkval.is_active:
                    continue
                summary_fields[fk] = SortedDict()
                for field in related_fields:
                    fval = getattr(fkval, field, None)
                    if fval is None and field == 'type':
                        if type(fkval) == UnifiedJobTemplate:
                            obj_actual = UnifiedJobTemplate.objects.get(id=fkval.id)
                            summary_fields[fk][field] = get_type_for_model(obj_actual._get_unified_job_class())
                        else:
                            summary_fields[fk][field] = get_type_for_model(fkval)
                    if fval is not None:
                        summary_fields[fk][field] = fval
            # Can be raised by the reverse accessor for a OneToOneField.
            except ObjectDoesNotExist:
                pass
        return summary_fields 

    def get_created(self, obj):
        if obj is None:
            return None
        elif isinstance(obj, User):
            return obj.date_joined
        else:
            return obj.created

    def get_modified(self, obj):
        if obj is None:
            return None
        elif isinstance(obj, User):
            return obj.last_login # Not actually exposed for User.
        else:
            return obj.modified

    def get_active(self, obj):
        if obj is None:
            return False
        elif isinstance(obj, User):
            return obj.is_active
        else:
            return obj.active

    def get_validation_exclusions(self, instance=None):
        # Override base class method to continue to use model validation for
        # fields (including optional ones), appears this was broken by DRF
        # 2.3.13 update.
        cls = self.opts.model
        opts = get_concrete_model(cls)._meta
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


class UnifiedJobTemplateSerializer(BaseSerializer):

    class Meta:
        model = UnifiedJobTemplate
        fields = ('*', 'last_job_run', 'last_job_failed', 'has_schedules',
                  'next_job_run', 'status')

    def get_related(self, obj):
        res = super(UnifiedJobTemplateSerializer, self).get_related(obj)
        if obj.current_job and obj.current_job.active:
            res['current_job'] = obj.current_job.get_absolute_url()
        if obj.last_job and obj.last_job.active:
            res['last_job'] = obj.last_job.get_absolute_url()
        if obj.next_schedule and obj.next_schedule.active:
            res['next_schedule'] = obj.next_schedule.get_absolute_url()
        return res

    def get_types(self):
        if type(self) is UnifiedJobTemplateSerializer:
            return ['project', 'inventory_source', 'job_template']
        else:
            return super(UnifiedJobTemplateSerializer, self).get_types()

    def to_native(self, obj):
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
            return serializer.to_native(obj)
        else:
            return super(UnifiedJobTemplateSerializer, self).to_native(obj)


class UnifiedJobSerializer(BaseSerializer):

    result_stdout = serializers.Field(source='result_stdout')

    class Meta:
        model = UnifiedJob
        fields = ('*', 'unified_job_template', 'launch_type', 'status',
                  'failed', 'started', 'finished', 'elapsed', 'job_args',
                  'job_cwd', 'job_env', 'job_explanation', 'result_stdout',
                  'result_traceback')

    def get_types(self):
        if type(self) is UnifiedJobSerializer:
            return ['project_update', 'inventory_update', 'job']
        else:
            return super(UnifiedJobSerializer, self).get_types()

    def get_related(self, obj):
        res = super(UnifiedJobSerializer, self).get_related(obj)
        if obj.unified_job_template and obj.unified_job_template.active:
            res['unified_job_template'] = obj.unified_job_template.get_absolute_url()
        if obj.schedule and obj.schedule.active:
            res['schedule'] = obj.schedule.get_absolute_url()
        return res

    def to_native(self, obj):
        serializer_class = None
        if type(self) is UnifiedJobSerializer:
            if isinstance(obj, ProjectUpdate):
                serializer_class = ProjectUpdateSerializer
            elif isinstance(obj, InventoryUpdate):
                serializer_class = InventoryUpdateSerializer
            elif isinstance(obj, Job):
                serializer_class = JobSerializer
        if serializer_class:
            serializer = serializer_class(instance=obj)
            ret = serializer.to_native(obj)
        else:
            ret = super(UnifiedJobSerializer, self).to_native(obj)
        if 'elapsed' in ret:
            ret['elapsed'] = float(ret['elapsed'])
        return ret


class UnifiedJobListSerializer(UnifiedJobSerializer):
    
    class Meta:
        exclude = ('*', 'job_args', 'job_cwd', 'job_env', 'result_traceback',
                   'result_stdout')

    def get_types(self):
       if type(self) is UnifiedJobListSerializer:
           return ['project_update', 'inventory_update', 'job']
       else:
           return super(UnifiedJobListSerializer, self).get_types()

    def to_native(self, obj):
        serializer_class = None
        if type(self) is UnifiedJobListSerializer:
            if isinstance(obj, ProjectUpdate):
                serializer_class = ProjectUpdateListSerializer
            elif isinstance(obj, InventoryUpdate):
                serializer_class = InventoryUpdateListSerializer
            elif isinstance(obj, Job):
                serializer_class = JobListSerializer
        if serializer_class:
            serializer = serializer_class(instance=obj)
            ret = serializer.to_native(obj)
        else:
            ret = super(UnifiedJobListSerializer, self).to_native(obj)
        if 'elapsed' in ret:
            ret['elapsed'] = float(ret['elapsed'])
        return ret


class BaseTaskSerializer(BaseSerializer):

    job_env = serializers.SerializerMethodField('get_job_env')

    def get_job_env(self, obj):
        job_env_d = obj.job_env
        if 'BROKER_URL' in job_env_d:
            job_env_d.pop('BROKER_URL')
        return job_env_d


class UserSerializer(BaseSerializer):

    password = serializers.WritableField(required=False, default='',
        help_text='Write-only field used to change the password.')
    ldap_dn = serializers.Field(source='profile.ldap_dn')

    class Meta:
        model = User
        fields = ('*', '-name', '-description', '-modified',
                  '-summary_fields', 'username', 'first_name', 'last_name',
                  'email', 'is_superuser', 'password', 'ldap_dn')

    def to_native(self, obj):
        ret = super(UserSerializer, self).to_native(obj)
        ret.pop('password', None)
        ret.fields.pop('password', None)
        return ret

    def get_validation_exclusions(self):
        ret = super(UserSerializer, self).get_validation_exclusions()
        ret.append('password')
        return ret

    def restore_object(self, attrs, instance=None):
        new_password = attrs.pop('password', None)
        instance = super(UserSerializer, self).restore_object(attrs, instance)
        instance._new_password = new_password
        return instance

    def save_object(self, obj, **kwargs):
        new_password = getattr(obj, '_new_password', None)
        # For now we're not raising an error, just not saving password for
        # users managed by LDAP who already have an unusable password set.
        try:
            if obj.pk and obj.profile.ldap_dn and not obj.has_usable_password():
                new_password = None
        except AttributeError:
            pass
        if new_password:
            obj.set_password(new_password)
        if not obj.password:
            obj.set_unusable_password()
        return super(UserSerializer, self).save_object(obj, **kwargs)
    
    def get_related(self, obj):
        res = super(UserSerializer, self).get_related(obj)
        res.update(dict(
            teams                  = reverse('api:user_teams_list',               args=(obj.pk,)),
            organizations          = reverse('api:user_organizations_list',       args=(obj.pk,)),
            admin_of_organizations = reverse('api:user_admin_of_organizations_list', args=(obj.pk,)),
            projects               = reverse('api:user_projects_list',            args=(obj.pk,)),
            credentials            = reverse('api:user_credentials_list',         args=(obj.pk,)),
            permissions            = reverse('api:user_permissions_list',         args=(obj.pk,)),
            activity_stream        = reverse('api:user_activity_stream_list',     args=(obj.pk,)),
        ))
        return res

    def _validate_ldap_managed_field(self, attrs, source):
        try:
            is_ldap_user = bool(self.object.profile.ldap_dn)
        except AttributeError:
            is_ldap_user = False
        if is_ldap_user:
            ldap_managed_fields = ['username']
            ldap_managed_fields.extend(getattr(settings, 'AUTH_LDAP_USER_ATTR_MAP', {}).keys())
            ldap_managed_fields.extend(getattr(settings, 'AUTH_LDAP_USER_FLAGS_BY_GROUP', {}).keys())
            if source in ldap_managed_fields and source in attrs:
                if attrs[source] != getattr(self.object, source):
                    raise serializers.ValidationError('Unable to change %s on user managed by LDAP' % source)
        return attrs

    def validate_username(self, attrs, source):
        return self._validate_ldap_managed_field(attrs, source)

    def validate_first_name(self, attrs, source):
        return self._validate_ldap_managed_field(attrs, source)

    def validate_last_name(self, attrs, source):
        return self._validate_ldap_managed_field(attrs, source)

    def validate_email(self, attrs, source):
        return self._validate_ldap_managed_field(attrs, source)

    def validate_is_superuser(self, attrs, source):
        return self._validate_ldap_managed_field(attrs, source)


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
            activity_stream = reverse('api:organization_activity_stream_list', args=(obj.pk,))
        ))
        return res


class ProjectOptionsSerializer(BaseSerializer):
    
    class Meta:
        fields = ('*', 'local_path', 'scm_type', 'scm_url', 'scm_branch',
                  'scm_clean', 'scm_delete_on_update', 'credential')

    def get_related(self, obj):
        res = super(ProjectOptionsSerializer, self).get_related(obj)
        if obj.credential and obj.credential.active:
            res['credential'] = reverse('api:credential_detail',
                                        args=(obj.credential.pk,))
        return res

    def validate_local_path(self, attrs, source):
        # Don't allow assigning a local_path used by another project.
        # Don't allow assigning a local_path when scm_type is set.
        valid_local_paths = Project.get_local_path_choices()
        if self.object:
            scm_type = attrs.get('scm_type', self.object.scm_type) or u''
        else:
            scm_type = attrs.get('scm_type', u'') or u''
        if self.object and not scm_type:
            valid_local_paths.append(self.object.local_path)
        if scm_type:
            attrs.pop(source, None)
        if source in attrs and attrs[source] not in valid_local_paths:
            raise serializers.ValidationError('Invalid path choice')
        return attrs

    def to_native(self, obj):
        ret = super(ProjectOptionsSerializer, self).to_native(obj)
        if obj is not None and 'credential' in ret and (not obj.credential or not obj.credential.active):
            ret['credential'] = None
        return ret


class ProjectSerializer(UnifiedJobTemplateSerializer, ProjectOptionsSerializer):

    playbooks = serializers.Field(source='playbooks', help_text='Array of playbooks available within this project.')
    scm_delete_on_next_update = serializers.Field(source='scm_delete_on_next_update')
    last_update_failed = serializers.Field(source='last_update_failed')
    last_updated = serializers.Field(source='last_updated')

    class Meta:
        model = Project
        fields = ('*', 'scm_delete_on_next_update', 'scm_update_on_launch',
                  'scm_update_cache_timeout') + \
                 ('last_update_failed', 'last_updated')  # Backwards compatibility

    def get_related(self, obj):
        res = super(ProjectSerializer, self).get_related(obj)
        res.update(dict(
            organizations = reverse('api:project_organizations_list', args=(obj.pk,)),
            teams = reverse('api:project_teams_list', args=(obj.pk,)),
            playbooks = reverse('api:project_playbooks', args=(obj.pk,)),
            update = reverse('api:project_update_view', args=(obj.pk,)),
            project_updates = reverse('api:project_updates_list', args=(obj.pk,)),
            schedules = reverse('api:project_schedules_list', args=(obj.pk,)),
            activity_stream = reverse('api:project_activity_stream_list', args=(obj.pk,)),
        ))
        # Backwards compatibility.
        if obj.current_update:
            res['current_update'] = reverse('api:project_update_detail',
                                            args=(obj.current_update.pk,))
        if obj.last_update:
            res['last_update'] = reverse('api:project_update_detail',
                                         args=(obj.last_update.pk,))
        return res


class ProjectPlaybooksSerializer(ProjectSerializer):

    class Meta:
        model = Project
        fields = ('playbooks',)

    def to_native(self, obj):
        ret = super(ProjectPlaybooksSerializer, self).to_native(obj)
        return ret.get('playbooks', [])


class ProjectUpdateSerializer(UnifiedJobSerializer, ProjectOptionsSerializer):

    class Meta:
        model = ProjectUpdate
        fields = ('*', 'project')

    def get_related(self, obj):
        res = super(ProjectUpdateSerializer, self).get_related(obj)
        res.update(dict(
            project = reverse('api:project_detail', args=(obj.project.pk,)),
            cancel = reverse('api:project_update_cancel', args=(obj.pk,)),
        ))
        return res


class ProjectUpdateListSerializer(ProjectUpdateSerializer, UnifiedJobListSerializer):

    pass


class BaseSerializerWithVariables(BaseSerializer):

    def validate_variables(self, attrs, source):
        try:
            json.loads(attrs.get(source, '').strip() or '{}')
        except ValueError:
            try:
                yaml.safe_load(attrs[source])
            except yaml.YAMLError:
                raise serializers.ValidationError('Must be valid JSON or YAML')
        return attrs


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
        ))
        if obj.organization and obj.organization.active:
            res['organization'] = reverse('api:organization_detail', args=(obj.organization.pk,))
        return res

    def to_native(self, obj):
        ret = super(InventorySerializer, self).to_native(obj)
        if obj is not None and 'organization' in ret and (not obj.organization or not obj.organization.active):
            ret['organization'] = None
        return ret


class HostSerializer(BaseSerializerWithVariables):

    class Meta:
        model = Host
        fields = ('*', 'inventory', 'enabled', 'instance_id', 'variables',
                  'has_active_failures', 'has_inventory_sources', 'last_job',
                  'last_job_host_summary')
        readonly_fields = ('last_job', 'last_job_host_summary')

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
        ))
        if obj.inventory and obj.inventory.active:
            res['inventory'] = reverse('api:inventory_detail', args=(obj.inventory.pk,))
        if obj.last_job and obj.last_job.active:
            res['last_job'] = reverse('api:job_detail', args=(obj.last_job.pk,))
        if obj.last_job_host_summary and obj.last_job_host_summary.job.active:
            res['last_job_host_summary'] = reverse('api:job_host_summary_detail', args=(obj.last_job_host_summary.pk,))
        return res

    def get_summary_fields(self, obj):
        d = super(HostSerializer, self).get_summary_fields(obj)
        try:
            d['last_job']['job_template_id'] = obj.last_job.job_template.id
            d['last_job']['job_template_name'] = obj.last_job.job_template.name
        except (KeyError, AttributeError):
            pass
        d['all_groups'] = [{'id': g.id, 'name': g.name} for g in obj.all_groups.all()]
        d['groups'] = [{'id': g.id, 'name': g.name} for g in obj.groups.all()]
        d['recent_jobs'] = [{'id': j.job.id, 'name': j.job.job_template.name, 'status': j.job.status} \
                            for j in obj.job_host_summaries.all().order_by('-created')[:5]]
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
                raise serializers.ValidationError('Invalid port specification: %s' % str(port))
        return name, port

    def validate_name(self, attrs, source):
        name = unicode(attrs.get(source, ''))
        # Validate here only, update in main validate method.
        host, port = self._get_host_port_from_name(name)
        #for family in (socket.AF_INET, socket.AF_INET6):
        #    try:
        #        socket.inet_pton(family, name)
        #        return attrs
        #    except socket.error:
        #        pass
        # Hostname should match the following regular expression and have at
        # last one letter in the name (to catch invalid IPv4 addresses from
        # above).
        #valid_host_re = r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'
        #if re.match(valid_host_re, name) and re.match(r'^.*?[a-zA-Z].*?$', name):
        #    return attrs
        #raise serializers.ValidationError('Invalid host name or IP')
        return attrs

    def validate(self, attrs):
        name = unicode(attrs.get('name', ''))
        host, port = self._get_host_port_from_name(name)

        if port:
            attrs['name'] = host
            if self.object:
                variables = unicode(attrs.get('variables', self.object.variables) or '')
            else:
                variables = unicode(attrs.get('variables', ''))
            try:
                vars_dict = json.loads(variables.strip() or '{}')
                vars_dict['ansible_ssh_port'] = port
                attrs['variables'] = json.dumps(vars_dict)
            except (ValueError, TypeError):
                try:
                    vars_dict = yaml.safe_load(variables)
                    vars_dict['ansible_ssh_port'] = port
                    attrs['variables'] = yaml.dump(vars_dict)
                except (yaml.YAMLError, TypeError):
                    raise serializers.ValidationError('Must be valid JSON or YAML')

        return attrs

    def to_native(self, obj):
        ret = super(HostSerializer, self).to_native(obj)
        if not obj:
            return ret
        if 'inventory' in ret and (not obj.inventory or not obj.inventory.active):
            ret['inventory'] = None
        if 'last_job' in ret and (not obj.last_job or not obj.last_job.active):
            ret['last_job'] = None
        if 'last_job_host_summary' in ret and (not obj.last_job_host_summary or not obj.last_job_host_summary.job.active):
            ret['last_job_host_summary'] = None
        return ret


class GroupSerializer(BaseSerializerWithVariables):

    class Meta:
        model = Group
        fields = ('*', 'inventory', 'variables', 'has_active_failures',
                  'total_hosts', 'hosts_with_active_failures', 'total_groups',
                  'groups_with_active_failures', 'has_inventory_sources')

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
        ))
        if obj.inventory and obj.inventory.active:
            res['inventory'] = reverse('api:inventory_detail', args=(obj.inventory.pk,))
        if obj.inventory_source:
            res['inventory_source'] = reverse('api:inventory_source_detail', args=(obj.inventory_source.pk,))
        return res

    def validate_name(self, attrs, source):
        name = attrs.get(source, '')
        if name in ('all', '_meta'):
            raise serializers.ValidationError('Invalid group name')
        return attrs

    def to_native(self, obj):
        ret = super(GroupSerializer, self).to_native(obj)
        if obj is not None and 'inventory' in ret and (not obj.inventory or not obj.inventory.active):
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
        children_qs = obj.children.filter(active=True)
        children_qs = children_qs.select_related('inventory')
        children_qs = children_qs.prefetch_related('inventory_source')
        return GroupTreeSerializer(children_qs, many=True).data


class BaseVariableDataSerializer(BaseSerializer):

    class Meta:
        fields = ('variables',)

    def to_native(self, obj):
        if obj is None:
            return {}
        ret = super(BaseVariableDataSerializer, self).to_native(obj)
        try:
            return json.loads(ret.get('variables', '') or '{}')
        except ValueError:
            return yaml.safe_load(ret.get('variables', ''))

    def from_native(self, data, files):
        data = {'variables': json.dumps(data)}
        return super(BaseVariableDataSerializer, self).from_native(data, files)


class InventoryVariableDataSerializer(BaseVariableDataSerializer):

    class Meta:
        model = Inventory


class HostVariableDataSerializer(BaseVariableDataSerializer):

    class Meta:
        model = Host


class GroupVariableDataSerializer(BaseVariableDataSerializer):

    class Meta:
        model = Group


class InventorySourceOptionsSerializer(BaseSerializer):
    
    class Meta:
        fields = ('*', 'source', 'source_path', 'source_vars', 'credential',
                  'source_regions', 'overwrite', 'overwrite_vars')

    def get_related(self, obj):
        res = super(InventorySourceOptionsSerializer, self).get_related(obj)
        if obj.credential and obj.credential.active:
            res['credential'] = reverse('api:credential_detail',
                                        args=(obj.credential.pk,))
        return res

    def validate_source(self, attrs, source):
        src = attrs.get(source, '')
        obj = self.object
        # FIXME
        return attrs

    def validate_source_vars(self, attrs, source):
        # source_env must be blank, a valid JSON or YAML dict, or ...
        # FIXME: support key=value pairs.
        try:
            json.loads(attrs.get(source, '').strip() or '{}')
            return attrs
        except ValueError:
            pass
        try:
            yaml.safe_load(attrs[source])
            return attrs
        except yaml.YAMLError:
            pass
        raise serializers.ValidationError('Must be valid JSON or YAML')

    def validate_source_regions(self, attrs, source):
        # FIXME
        return attrs

    def metadata(self):
        metadata = super(InventorySourceOptionsSerializer, self).metadata()
        field_opts = metadata.get('source_regions', {})
        field_opts['ec2_region_choices'] = self.opts.model.get_ec2_region_choices()
        field_opts['rax_region_choices'] = self.opts.model.get_rax_region_choices()
        return metadata

    def to_native(self, obj):
        ret = super(InventorySourceOptionsSerializer, self).to_native(obj)
        if obj is None:
            return ret
        if 'credential' in ret and (not obj.credential or not obj.credential.active):
            ret['credential'] = None
        return ret


class InventorySourceSerializer(UnifiedJobTemplateSerializer, InventorySourceOptionsSerializer):
    
    last_update_failed = serializers.Field(source='last_update_failed')
    last_updated = serializers.Field(source='last_updated')

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
        ))
        if obj.inventory and obj.inventory.active:
            res['inventory'] = reverse('api:inventory_detail', args=(obj.inventory.pk,))
        if obj.group and obj.group.active:
            res['group'] = reverse('api:group_detail', args=(obj.group.pk,))
        # Backwards compatibility.
        if obj.current_update:
            res['current_update'] = reverse('api:inventory_update_detail',
                                            args=(obj.current_update.pk,))
        if obj.last_update:
            res['last_update'] = reverse('api:inventory_update_detail',
                                         args=(obj.last_update.pk,))
        return res

    def to_native(self, obj):
        ret = super(InventorySourceSerializer, self).to_native(obj)
        if obj is None:
            return ret
        if 'inventory' in ret and (not obj.inventory or not obj.inventory.active):
            ret['inventory'] = None
        if 'group' in ret and (not obj.group or not obj.group.active):
            ret['group'] = None
        return ret


class InventoryUpdateSerializer(UnifiedJobSerializer, InventorySourceOptionsSerializer):

    class Meta:
        model = InventoryUpdate
        fields = ('*', 'inventory_source', 'license_error')

    def get_related(self, obj):
        res = super(InventoryUpdateSerializer, self).get_related(obj)
        res.update(dict(
            inventory_source = reverse('api:inventory_source_detail', args=(obj.inventory_source.pk,)),
            cancel = reverse('api:inventory_update_cancel', args=(obj.pk,)),
        ))
        return res


class InventoryUpdateListSerializer(InventoryUpdateSerializer, UnifiedJobListSerializer):

    pass


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
            permissions  = reverse('api:team_permissions_list', args=(obj.pk,)),
            activity_stream = reverse('api:team_activity_stream_list', args=(obj.pk,)),
        ))
        if obj.organization and obj.organization.active:
            res['organization'] = reverse('api:organization_detail',   args=(obj.organization.pk,))
        return res

    def to_native(self, obj):
        ret = super(TeamSerializer, self).to_native(obj)
        if obj is not None and 'organization' in ret and (not obj.organization or not obj.organization.active):
            ret['organization'] = None
        return ret


class PermissionSerializer(BaseSerializer):

    class Meta:
        model = Permission
        fields = ('*', 'user', 'team', 'project', 'inventory',
                  'permission_type')

    def get_related(self, obj):
        res = super(PermissionSerializer, self).get_related(obj)
        if obj.user and obj.user.is_active:
            res['user']        = reverse('api:user_detail', args=(obj.user.pk,))
        if obj.team and obj.team.active:
            res['team']        = reverse('api:team_detail', args=(obj.team.pk,))
        if obj.project and obj.project.active:
            res['project']     = reverse('api:project_detail', args=(obj.project.pk,)) 
        if obj.inventory and obj.inventory.active:
            res['inventory']   = reverse('api:inventory_detail', args=(obj.inventory.pk,))
        return res

    def validate(self, attrs):
        # Can only set either user or team.
        if attrs['user'] and attrs['team']:
            raise serializers.ValidationError('permission can only be assigned'
                                              ' to a user OR a team, not both')
        # Cannot assign admit/read/write permissions for a project.
        if attrs['permission_type'] in ('admin', 'read', 'write') and attrs['project']:
            raise serializers.ValidationError('project cannot be assigned for '
                                              'inventory-only permissions')
        # Project is required when setting deployment permissions.
        if attrs['permission_type'] in ('run', 'check') and not attrs['project']:
            raise serializers.ValidationError('project is required when '
                                              'assigning deployment permissions')
        return attrs

    def to_native(self, obj):
        ret = super(PermissionSerializer, self).to_native(obj)
        if obj is None:
            return ret
        if 'user' in ret and (not obj.user or not obj.user.is_active):
            ret['user'] = None
        if 'team' in ret and (not obj.team or not obj.team.active):
            ret['team'] = None
        if 'project' in ret and (not obj.project or not obj.project.active):
            ret['project'] = None
        if 'inventory' in ret and (not obj.inventory or not obj.inventory.active):
            ret['inventory'] = None
        return ret


class CredentialSerializer(BaseSerializer):

    # FIXME: may want to make some of these filtered based on user accessing

    password = serializers.WritableField(required=False, default='')
    ssh_key_data = serializers.WritableField(required=False, default='')
    ssh_key_unlock = serializers.WritableField(required=False, default='')
    sudo_password = serializers.WritableField(required=False, default='')
    vault_password = serializers.WritableField(required=False, default='')

    class Meta:
        model = Credential
        fields = ('*', 'user', 'team', 'kind', 'cloud', 'username',
                  'password', 'ssh_key_data', 'ssh_key_unlock',
                  'sudo_username', 'sudo_password', 'vault_password')

    def to_native(self, obj):
        ret = super(CredentialSerializer, self).to_native(obj)
        if obj is not None and 'user' in ret and (not obj.user or not obj.user.is_active):
            ret['user'] = None
        if obj is not None and 'team' in ret and (not obj.team or not obj.team.active):
            ret['team'] = None
        # Replace the actual encrypted value with the string $encrypted$.
        for field in Credential.PASSWORD_FIELDS:
            if field in ret and unicode(ret[field]).startswith('$encrypted$'):
                ret[field] = '$encrypted$'
        return ret

    def restore_object(self, attrs, instance=None):
        # If the value sent to the API startswith $encrypted$, ignore it.
        for field in Credential.PASSWORD_FIELDS:
            if unicode(attrs.get(field, '')).startswith('$encrypted$'):
                attrs.pop(field, None)
        instance = super(CredentialSerializer, self).restore_object(attrs, instance)
        return instance

    def get_related(self, obj):
        res = super(CredentialSerializer, self).get_related(obj)
        res.update(dict(
            activity_stream = reverse('api:credential_activity_stream_list', args=(obj.pk,))
        ))
        if obj.user:
            res['user'] = reverse('api:user_detail', args=(obj.user.pk,))
        if obj.team:
            res['team'] = reverse('api:team_detail', args=(obj.team.pk,))
        return res


class JobOptionsSerializer(BaseSerializer):

    class Meta:
        fields = ('*', 'job_type', 'inventory', 'project', 'playbook',
                  'credential', 'cloud_credential', 'forks', 'limit',
                  'verbosity', 'extra_vars', 'job_tags')

    def get_related(self, obj):
        res = super(JobOptionsSerializer, self).get_related(obj)
        if obj.inventory and obj.inventory.active:
            res['inventory'] = reverse('api:inventory_detail', args=(obj.inventory.pk,))
        if obj.project and obj.project.active:
            res['project'] = reverse('api:project_detail', args=(obj.project.pk,))
        if obj.credential and obj.credential.active:
            res['credential'] = reverse('api:credential_detail', args=(obj.credential.pk,))
        if obj.cloud_credential and obj.cloud_credential.active:
            res['cloud_credential'] = reverse('api:credential_detail',
                                              args=(obj.cloud_credential.pk,))
        return res

    def to_native(self, obj):
        ret = super(JobOptionsSerializer, self).to_native(obj)
        if obj is None:
            return ret
        if 'inventory' in ret and (not obj.inventory or not obj.inventory.active):
            ret['inventory'] = None
        if 'project' in ret and (not obj.project or not obj.project.active):
            ret['project'] = None
            if 'playbook' in ret:
                ret['playbook'] = ''
        if 'credential' in ret and (not obj.credential or not obj.credential.active):
            ret['credential'] = None
        if 'cloud_credential' in ret and (not obj.cloud_credential or not obj.cloud_credential.active):
            ret['cloud_credential'] = None
        return ret

    def validate_playbook(self, attrs, source):
        project = attrs.get('project', None)
        playbook = attrs.get('playbook', '')
        if project and playbook and playbook not in project.playbooks:
            raise serializers.ValidationError('Playbook not found for project')
        return attrs


class JobTemplateSerializer(UnifiedJobTemplateSerializer, JobOptionsSerializer):

    class Meta:
        model = JobTemplate
        fields = ('*', 'host_config_key')

    def get_related(self, obj):
        res = super(JobTemplateSerializer, self).get_related(obj)
        res.update(dict(
            jobs = reverse('api:job_template_jobs_list', args=(obj.pk,)),
            schedules = reverse('api:job_template_schedules_list', args=(obj.pk,)),
            activity_stream = reverse('api:job_template_activity_stream_list', args=(obj.pk,)),
        ))
        if obj.host_config_key:
            res['callback'] = reverse('api:job_template_callback', args=(obj.pk,))
        return res


class JobSerializer(UnifiedJobSerializer, JobOptionsSerializer):

    passwords_needed_to_start = serializers.Field(source='passwords_needed_to_start')

    class Meta:
        model = Job
        fields = ('*', 'job_template', 'passwords_needed_to_start')

    def get_related(self, obj):
        res = super(JobSerializer, self).get_related(obj)
        res.update(dict(
            job_events  = reverse('api:job_job_events_list', args=(obj.pk,)),
            job_host_summaries = reverse('api:job_job_host_summaries_list', args=(obj.pk,)),
            activity_stream = reverse('api:job_activity_stream_list', args=(obj.pk,)),
        ))
        if obj.job_template and obj.job_template.active:
            res['job_template'] = reverse('api:job_template_detail',
                                          args=(obj.job_template.pk,))
        if obj.can_start or True:
            res['start'] = reverse('api:job_start', args=(obj.pk,))
        if obj.can_cancel or True:
            res['cancel'] = reverse('api:job_cancel', args=(obj.pk,))
        return res

    def from_native(self, data, files):
        # When creating a new job and a job template is specified, populate any
        # fields not provided in data from the job template.
        if not self.object and isinstance(data, dict) and 'job_template' in data:
            try:
                job_template = JobTemplate.objects.get(pk=data['job_template'])
            except JobTemplate.DoesNotExist:
                self._errors = {'job_template': 'Invalid job template'}
                return
            # Don't auto-populate name or description.
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
            data.setdefault('forks', job_template.forks)
            data.setdefault('limit', job_template.limit)
            data.setdefault('verbosity', job_template.verbosity)
            data.setdefault('extra_vars', job_template.extra_vars)
            data.setdefault('job_tags', job_template.job_tags)
        return super(JobSerializer, self).from_native(data, files)

    def to_native(self, obj):
        ret = super(JobSerializer, self).to_native(obj)
        if obj is None:
            return ret
        if 'job_template' in ret and (not obj.job_template or not obj.job_template.active):
            ret['job_template'] = None
        return ret

class JobListSerializer(JobSerializer, UnifiedJobListSerializer):

    pass


class JobHostSummarySerializer(BaseSerializer):

    class Meta:
        model = JobHostSummary
        fields = ('*', '-name', '-description', 'job', 'host', 'changed',
                  'dark', 'failures', 'ok', 'processed', 'skipped', 'failed')

    def get_related(self, obj):
        res = super(JobHostSummarySerializer, self).get_related(obj)
        res.update(dict(
            job=reverse('api:job_detail', args=(obj.job.pk,)),
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

    event_display = serializers.Field(source='get_event_display2')
    event_level = serializers.Field(source='event_level')

    class Meta:
        model = JobEvent
        fields = ('*', '-name', '-description', 'job', 'event',
                  'event_display', 'event_data', 'event_level', 'failed',
                  'changed', 'host', 'parent', 'play', 'task')

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


class ScheduleSerializer(BaseSerializer):

    class Meta:
        model = Schedule
        fields = ('*', 'unified_job_template', 'enabled', 'dtstart', 'dtend', 'rrule', 'next_run')

    def get_related(self, obj):
        res = super(ScheduleSerializer, self).get_related(obj)
        res.update(dict(
            unified_jobs = reverse('api:schedule_unified_jobs_list', args=(obj.pk,)),
        ))
        if obj.unified_job_template and obj.unified_job_template.active:
            #TODO: Figure out why we have to do this
            ujt = UnifiedJobTemplate.objects.get(id=obj.unified_job_template.id)
            res['unified_job_template'] = ujt.get_absolute_url() #obj.unified_job_template.get_absolute_url()
        return res

    # We reject rrules if:
    # - DTSTART is not include
    # - INTERVAL is not included
    # - TZID is used
    # - multiple BYDAY (except WEEKLY and YEARLY (see below)), BYMONTHDAY, BYMONTH
    # - multiple BYDAY yearly unless it lists all weekdays OR weekend days
    # - BYDAY prefixed with a number (MO is good but not 20MO)
    # - BYYEARDAY
    # - BYWEEKNO
    def validate_rrule(self, attrs, source):
        rrule_value = attrs[source]
        multi_by_day = ".*?BYDAY[\:\=][a-zA-Z]{2},[a-zA-Z]{2}"
        multi_by_month_day = ".*?BYMONTHDAY[\:\=][0-9]+,-*[0-9]+"
        multi_by_month = ".*?BYMONTH[\:\=][0-9]+,[0-9]+"
        by_day_with_numeric_prefix = ".*?BYDAY[\:\=][0-9]+[a-zA-Z]{2}"
        if not re.match("DTSTART[\:\=][0-9]+T[0-9]+Z", rrule_value):
            raise serializers.ValidationError('DTSTART required in rrule, value should match: DTSTART:YYYYMMDDTHHMMSSZ')
        if not 'interval' in rrule_value.lower():
            raise serializers.ValidationError('INTERVAL required in rrule')
        if 'tzid' in rrule_value.lower():
            raise serializers.ValidationError('TZID is not supported')
        if 'secondly' in rrule_value.lower():
            raise serializers.ValidationError('SECONDLY is not supported')
        if re.match(multi_by_month_day, rrule_value):
            raise serializers.ValidationError('Multiple BYMONTHDAYs not supported')
        if re.match(multi_by_month, rrule_value):
            raise serializers.ValidationError('Multiple BYMONTHs not supported')
        if re.match(by_day_with_numeric_prefix, rrule_value):
            raise serializers.ValidationError("BYDAY with numeric prefix not supported")
        if 'byyearday' in rrule_value.lower():
            raise serializers.ValidationError("BYYEARDAY not supported")
        if 'byweekno' in rrule_value.lower():
            raise serializers.ValidationError("BYWEEKNO not supported")
        if re.match(multi_by_day, rrule_value) and not re.match(".*?FREQ[\:\=](WEEKLY|YEARLY)", rrule_value):
            raise serializers.ValidationError("Multiple BYDAY elements only supported with WEEKLY and YEARLY frequency")
        try:
            sched_rule = rrule.rrulestr(rrule_value)
        except Exception, e:
            raise serializers.ValidationError("rrule parsing failed validation")
        return attrs

class ActivityStreamSerializer(BaseSerializer):

    changes = serializers.SerializerMethodField('get_changes')

    class Meta:
        model = ActivityStream
        fields = ('*', '-name', '-description', '-created', '-modified',
                  'timestamp', 'operation', 'changes', 'object1', 'object2')

    def get_fields(self):
        ret = super(ActivityStreamSerializer, self).get_fields()
        for key, field in ret.items():
            if key == 'changes':
                field.help_text = 'A summary of the new and changed values when an object is created, updated, or deleted'
            if key == 'object1':
                field.help_text = 'For create, update, and delete events this is the object type that was affected.  For associate and disassociate events this is the object type associated or disassociated with object2'
            if key == 'object2':
                field.help_text = 'Unpopulated for create, update, and delete events.  For associate and disassociate events this is the object type that object1 is being associated with'
            if key == 'operation':
                field.help_text = 'The action taken with respect to the given object(s).'
        return ret

    def get_changes(self, obj):
        if obj is None:
            return {}
        try:
            d_changes = json.loads(obj.changes)
            if 'variables' in d_changes:
                d_changes['variables'] = json.loads(d_changes['variables'])
            return d_changes
        except Exception, e:
            logger.warn("Error deserializing activity stream json changes")
        return {}

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
        return rel

    def get_summary_fields(self, obj):
        summary_fields = SortedDict()
        for fk, related_fields in SUMMARIZABLE_FK_FIELDS.items():
            try:
                if not hasattr(obj, fk):
                    continue
                allm2m = getattr(obj, fk).all()
                if allm2m.count() > 0:
                    summary_fields[fk] = []
                    summary_fields['job_template'] = []
                    for thisItem in allm2m:
                        if fk == 'job':
                            job_template_item = {}
                            job_template_fields = SUMMARIZABLE_FK_FIELDS['job_template']
                            job_template = getattr(thisItem, 'job_template', None)
                            if job_template is not None:
                                for field in job_template_fields:
                                    fval = getattr(job_template, field, None)
                                    if fval is not None:
                                        job_template_item[field] = fval
                                summary_fields['job_template'].append(job_template_item)
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


class AuthTokenSerializer(serializers.Serializer):

    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Unable to login with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password"')
