# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import json
import re
import socket
import urlparse
import logging

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
from awx.main.utils import update_scm_url, camelcase_to_underscore

logger = logging.getLogger('awx.api.serializers')

BASE_FIELDS = ('id', 'url', 'related', 'summary_fields', 'created', 'modified',
               'name', 'description')

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
    'permission': DEFAULT_SUMMARY_FIELDS,
    'job': DEFAULT_SUMMARY_FIELDS + ('status', 'failed',),
    'job_template': DEFAULT_SUMMARY_FIELDS,
    'last_job': DEFAULT_SUMMARY_FIELDS + ('status', 'failed',),
    'last_job_host_summary': DEFAULT_SUMMARY_FIELDS + ('failed',),
    'last_update': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
    'current_update': DEFAULT_SUMMARY_FIELDS + ('status', 'failed', 'license_error'),
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

class BaseSerializer(serializers.ModelSerializer):

    # add the URL and related resources
    url            = serializers.SerializerMethodField('get_url')
    related        = serializers.SerializerMethodField('get_related')
    summary_fields = serializers.SerializerMethodField('get_summary_fields')

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

    def get_url(self, obj):
        if obj is None:
            return ''
        elif isinstance(obj, User):
            return reverse('api:user_detail', args=(obj.pk,))
        else:
            return obj.get_absolute_url()

    def get_related(self, obj):
        res = SortedDict()
        if getattr(obj, 'created_by', None):
            res['created_by'] = reverse('api:user_detail', args=(obj.created_by.pk,))
        return res

    def get_summary_fields(self, obj):
        # Return values for certain fields on related objects, to simplify
        # displaying lists of items without additional API requests.
        summary_fields = SortedDict()
        for fk, related_fields in SUMMARIZABLE_FK_FIELDS.items():
            try:
                fkval = getattr(obj, fk, None)
                if fkval is not None:
                    summary_fields[fk] = SortedDict()
                    for field in related_fields:
                        fval = getattr(fkval, field, None)
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

    def validate_description(self, attrs, source):
        # Description should always be empty string, never null.
        attrs[source] = attrs.get(source, None) or ''
        return attrs

class UserSerializer(BaseSerializer):

    password = serializers.WritableField(required=False, default='',
        help_text='Write-only field used to change the password.')
    ldap_dn = serializers.Field(source='profile.ldap_dn')

    class Meta:
        model = User
        fields = ('id', 'url', 'related', 'created', 'username', 'first_name',
                  'last_name', 'email', 'is_superuser', 'password', 'ldap_dn')

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
        if obj is None:
            return {}
        res = super(UserSerializer, self).get_related(obj)
        res.update(dict(
            teams                  = reverse('api:user_teams_list',               args=(obj.pk,)),
            organizations          = reverse('api:user_organizations_list',       args=(obj.pk,)),
            admin_of_organizations = reverse('api:user_admin_of_organizations_list', args=(obj.pk,)),
            projects               = reverse('api:user_projects_list',            args=(obj.pk,)),
            credentials            = reverse('api:user_credentials_list',         args=(obj.pk,)),
            permissions            = reverse('api:user_permissions_list',         args=(obj.pk,)),
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
        fields = BASE_FIELDS

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(OrganizationSerializer, self).get_related(obj)
        res.update(dict(
            #audit_trail = reverse('api:organization_audit_trail_list',    args=(obj.pk,)),
            projects    = reverse('api:organization_projects_list',       args=(obj.pk,)),
            inventories = reverse('api:organization_inventories_list',    args=(obj.pk,)),
            users       = reverse('api:organization_users_list',          args=(obj.pk,)),
            admins      = reverse('api:organization_admins_list',         args=(obj.pk,)),
            #tags        = reverse('api:organization_tags_list',           args=(obj.pk,)),
            teams       = reverse('api:organization_teams_list',          args=(obj.pk,)),
        ))
        return res

class ProjectSerializer(BaseSerializer):

    playbooks = serializers.Field(source='playbooks', help_text='Array of playbooks available within this project.')
    scm_delete_on_next_update = serializers.Field(source='scm_delete_on_next_update')

    class Meta:
        model = Project
        fields = BASE_FIELDS + ('local_path', 'scm_type', 'scm_url',
                                'scm_branch', 'scm_clean',
                                'scm_delete_on_update', 'scm_delete_on_next_update',
                                'scm_update_on_launch', 'credential',
                                'last_update_failed', 'status', 'last_updated')

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(ProjectSerializer, self).get_related(obj)
        res.update(dict(
            organizations = reverse('api:project_organizations_list', args=(obj.pk,)),
            teams = reverse('api:project_teams_list', args=(obj.pk,)),
            playbooks = reverse('api:project_playbooks', args=(obj.pk,)),
            update = reverse('api:project_update_view', args=(obj.pk,)),
            project_updates = reverse('api:project_updates_list', args=(obj.pk,)),
        ))
        if obj.credential:
            res['credential'] = reverse('api:credential_detail',
                                        args=(obj.credential.pk,))
        if obj.current_update:
            res['current_update'] = reverse('api:project_update_detail',
                                            args=(obj.current_update.pk,))
        if obj.last_update:
            res['last_update'] = reverse('api:project_update_detail',
                                         args=(obj.last_update.pk,))
        return res

    def validate_local_path(self, attrs, source):
        # Don't allow assigning a local_path used by another project.
        # Don't allow assigning a local_path when scm_type is set.
        valid_local_paths = Project.get_local_path_choices()
        if self.object:
            scm_type = attrs.get('scm_type', self.object.scm_type)
            if not scm_type:
                valid_local_paths.append(self.object.local_path)
        else:
            scm_type = attrs.get('scm_type', '')
        if scm_type:
            attrs.pop(source, None)
        if source in attrs and attrs[source] not in valid_local_paths:
            raise serializers.ValidationError('Invalid path choice')
        return attrs

    def validate_scm_url(self, attrs, source):
        if self.object:
            scm_type = attrs.get('scm_type', self.object.scm_type) or ''
        else:
            scm_type = attrs.get('scm_type', '') or ''
        scm_url = unicode(attrs.get(source, None) or '')
        if not scm_type:
            return attrs
        try:
            scm_url = update_scm_url(scm_type, scm_url)
        except ValueError, e:
            raise serializers.ValidationError((e.args or ('Invalid SCM URL',))[0])
        scm_url_parts = urlparse.urlsplit(scm_url)
        if scm_type and not any(scm_url_parts):
            raise serializers.ValidationError('SCM URL is required')
        return attrs

    #def validate_scm_username(self, attrs, source):
    #    if self.object:
    #        scm_type = attrs.get('scm_type', self.object.scm_type) or ''
    #        scm_url = unicode(attrs.get('scm_url', self.object.scm_url) or '')
    #        scm_username = attrs.get('scm_username', self.object.scm_username) or ''
    #    else:
    #        scm_type = attrs.get('scm_type', '') or ''
    #        scm_url = unicode(attrs.get('scm_url', '') or '')
    #        scm_username = attrs.get('scm_username', '') or ''
    #    if not scm_type:
    #        return attrs
    #    try:
    #        if scm_url and scm_username:
    #            update_scm_url(scm_type, scm_url, scm_username)
    #    except ValueError, e:
    #        raise serializers.ValidationError((e.args or ('Invalid SCM username',))[0])
    #    return attrs

    #def validate_scm_password(self, attrs, source):
    #    if self.object:
    #        scm_type = attrs.get('scm_type', self.object.scm_type) or ''
    #        scm_url = unicode(attrs.get('scm_url', self.object.scm_url) or '')
    #        scm_username = attrs.get('scm_username', self.object.scm_username) or ''
    #        scm_password = attrs.get('scm_password', self.object.scm_password) or ''
    #    else:
    #        scm_type = attrs.get('scm_type', '') or ''
    #        scm_url = unicode(attrs.get('scm_url', '') or '')
    #        scm_username = attrs.get('scm_username', '') or ''
    #        scm_password = attrs.get('scm_password', '') or ''
    #    if not scm_type:
    #        return attrs
    #    try:
    #        try:
    #            if scm_url and scm_username:
    #                update_scm_url(scm_type, scm_url, scm_username)
    #        except ValueError:
    #            pass
    #        else:
    #            if scm_url and scm_username and scm_password:
    #                update_scm_url(scm_type, scm_url, scm_username, '**')
    #    except ValueError, e:
    #        raise serializers.ValidationError((e.args or ('Invalid SCM password',))[0])
    #    return attrs
    
    # FIXME: Validate combination of SCM URL and credential!

class ProjectPlaybooksSerializer(ProjectSerializer):

    class Meta:
        model = Project
        fields = ('playbooks',)

    def to_native(self, obj):
        ret = super(ProjectPlaybooksSerializer, self).to_native(obj)
        return ret.get('playbooks', [])

class ProjectUpdateSerializer(BaseSerializer):

    class Meta:
        model = ProjectUpdate
        fields = ('id', 'url', 'related', 'summary_fields', 'created',
                  'modified', 'project', 'status', 'failed', 'result_stdout',
                  'result_traceback', 'job_args', 'job_cwd', 'job_env')

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(ProjectUpdateSerializer, self).get_related(obj)
        res.update(dict(
            project = reverse('api:project_detail', args=(obj.project.pk,)),
            cancel = reverse('api:project_update_cancel', args=(obj.pk,)),
        ))
        return res

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
        fields = BASE_FIELDS + ('organization', 'variables',
                                'has_active_failures', 'total_hosts',
                                'hosts_with_active_failures', 'total_groups',
                                'groups_with_active_failures',
                                'has_inventory_sources',
                                'total_inventory_sources',
                                'inventory_sources_with_failures',)

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(InventorySerializer, self).get_related(obj)
        res.update(dict(
            hosts         = reverse('api:inventory_hosts_list',        args=(obj.pk,)),
            groups        = reverse('api:inventory_groups_list',       args=(obj.pk,)),
            root_groups   = reverse('api:inventory_root_groups_list',  args=(obj.pk,)),
            variable_data = reverse('api:inventory_variable_data',     args=(obj.pk,)),
            script        = reverse('api:inventory_script_view',       args=(obj.pk,)),
            tree          = reverse('api:inventory_tree_view',         args=(obj.pk,)),
            organization  = reverse('api:organization_detail',         args=(obj.organization.pk,)),
            inventory_sources = reverse('api:inventory_inventory_sources_list', args=(obj.pk,)),
        ))
        return res

class HostSerializer(BaseSerializerWithVariables):

    class Meta:
        model = Host
        fields = BASE_FIELDS + ('inventory', 'enabled', 'instance_id', 'variables',
                                'has_active_failures', 'has_inventory_sources',
                                'last_job', 'last_job_host_summary')

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(HostSerializer, self).get_related(obj)
        res.update(dict(
            variable_data = reverse('api:host_variable_data',   args=(obj.pk,)),
            inventory     = reverse('api:inventory_detail',     args=(obj.inventory.pk,)),
            groups        = reverse('api:host_groups_list',     args=(obj.pk,)),
            all_groups    = reverse('api:host_all_groups_list', args=(obj.pk,)),
            job_events    = reverse('api:host_job_events_list',  args=(obj.pk,)),
            job_host_summaries = reverse('api:host_job_host_summaries_list', args=(obj.pk,)),
            #inventory_sources = reverse('api:host_inventory_sources_list', args=(obj.pk,)),
        ))
        if obj.last_job:
            res['last_job'] = reverse('api:job_detail', args=(obj.last_job.pk,))
        if obj.last_job_host_summary:
            res['last_job_host_summary'] = reverse('api:job_host_summary_detail', args=(obj.last_job_host_summary.pk,))
        return res

    def get_summary_fields(self, obj):
        if obj is None:
            return {}
        d = super(HostSerializer, self).get_summary_fields(obj)
        try:
            d['last_job']['job_template_id'] = obj.last_job.job_template.id
            d['last_job']['job_template_name'] = obj.last_job.job_template.name
        except (KeyError, AttributeError):
            pass
        d['all_groups'] = [{'id': g.id, 'name': g.name} for g in obj.all_groups.all()]
        d['groups'] = [{'id': g.id, 'name': g.name} for g in obj.groups.all()]
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


class GroupSerializer(BaseSerializerWithVariables):

    class Meta:
        model = Group
        fields = BASE_FIELDS + ('inventory', 'variables', 'has_active_failures',
                                'total_hosts', 'hosts_with_active_failures',
                                'total_groups', 'groups_with_active_failures',
                                'has_inventory_sources')

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(GroupSerializer, self).get_related(obj)
        res.update(dict(
            variable_data = reverse('api:group_variable_data',   args=(obj.pk,)),
            hosts         = reverse('api:group_hosts_list',      args=(obj.pk,)),
            potential_children = reverse('api:group_potential_children_list',   args=(obj.pk,)),
            children      = reverse('api:group_children_list',   args=(obj.pk,)),
            all_hosts     = reverse('api:group_all_hosts_list',  args=(obj.pk,)),
            inventory     = reverse('api:inventory_detail',       args=(obj.inventory.pk,)),
            job_events    = reverse('api:group_job_events_list',   args=(obj.pk,)),
            job_host_summaries = reverse('api:group_job_host_summaries_list', args=(obj.pk,)),
            inventory_source = reverse('api:inventory_source_detail', args=(obj.inventory_source.pk,)),
            #inventory_sources = reverse('api:group_inventory_sources_list', args=(obj.pk,)),
        ))
        return res

    def validate_name(self, attrs, source):
        name = attrs.get(source, '')
        if name in ('all', '_meta'):
            raise serializers.ValidationError('Invalid group name')
        return attrs

class GroupTreeSerializer(GroupSerializer):
    
    children = serializers.SerializerMethodField('get_children')

    class Meta:
        model = Group
        fields = BASE_FIELDS + ('inventory', 'variables', 'has_active_failures',
                                'total_hosts', 'hosts_with_active_failures',
                                'total_groups', 'groups_with_active_failures',
                                'has_inventory_sources', 'children')

    def get_children(self, obj):
        if obj is None:
            return {}
        children_qs = obj.children.filter(active=True)
        return GroupTreeSerializer(children_qs, many=True).data

class BaseVariableDataSerializer(BaseSerializer):

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
        fields = ('variables',)

class HostVariableDataSerializer(BaseVariableDataSerializer):

    class Meta:
        model = Host
        fields = ('variables',)

class GroupVariableDataSerializer(BaseVariableDataSerializer):

    class Meta:
        model = Group
        fields = ('variables',)

class InventorySourceSerializer(BaseSerializer):
    
    #source_password = serializers.WritableField(required=False, default='')

    class Meta:
        model = InventorySource
        fields = ('id', 'url', 'related', 'summary_fields', 'created',
                  'modified', 'inventory', 'group', 'source', 'source_path',
                  'source_vars', 'credential', 'source_regions', 'overwrite',
                  'overwrite_vars', 'update_on_launch', 'update_interval',
                  'last_update_failed', 'status', 'last_updated')
        read_only_fields = ('inventory', 'group')

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(InventorySourceSerializer, self).get_related(obj)
        res.update(dict(
            update = reverse('api:inventory_source_update_view', args=(obj.pk,)),
            inventory_updates = reverse('api:inventory_source_updates_list', args=(obj.pk,)),
            #hosts = reverse('api:inventory_source_hosts_list', args=(obj.pk,)),
            #groups = reverse('api:inventory_source_groups_list', args=(obj.pk,)),
        ))
        if obj.inventory:
            res['inventory'] = reverse('api:inventory_detail', args=(obj.inventory.pk,))
        if obj.group:
            res['group'] = reverse('api:group_detail', args=(obj.group.pk,))
        if obj.credential:
            res['credential'] = reverse('api:credential_detail',
                                        args=(obj.credential.pk,))
        if obj.current_update:
            res['current_update'] = reverse('api:inventory_update_detail',
                                            args=(obj.current_update.pk,))
        if obj.last_update:
            res['last_update'] = reverse('api:inventory_update_detail',
                                         args=(obj.last_update.pk,))
        return res

    def get_summary_fields(self, obj):
        if obj is None:
            return {}
        d = super(InventorySourceSerializer, self).get_summary_fields(obj)
        return d

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

class InventoryUpdateSerializer(BaseSerializer):

    class Meta:
        model = InventoryUpdate
        fields = ('id', 'url', 'related', 'summary_fields', 'created',
                  'modified', 'inventory_source', 'status', 'failed',
                  'result_stdout', 'result_traceback', 'job_args', 'job_cwd',
                  'job_env', 'license_error')

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(InventoryUpdateSerializer, self).get_related(obj)
        res.update(dict(
            inventory_source = reverse('api:inventory_source_detail', args=(obj.inventory_source.pk,)),
            cancel = reverse('api:inventory_update_cancel', args=(obj.pk,)),
        ))
        return res

class TeamSerializer(BaseSerializer):

    class Meta:
        model = Team
        fields = BASE_FIELDS + ('organization',)

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(TeamSerializer, self).get_related(obj)
        res.update(dict(
            projects     = reverse('api:team_projects_list',    args=(obj.pk,)),
            users        = reverse('api:team_users_list',       args=(obj.pk,)),
            credentials  = reverse('api:team_credentials_list', args=(obj.pk,)),
            organization = reverse('api:organization_detail',   args=(obj.organization.pk,)),
            permissions  = reverse('api:team_permissions_list', args=(obj.pk,)),
        ))
        return res

class PermissionSerializer(BaseSerializer):

    class Meta:
        model = Permission
        fields = BASE_FIELDS + ('user', 'team', 'project', 'inventory',
                                'permission_type',)
         
    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(PermissionSerializer, self).get_related(obj)
        if obj.user:
            res['user']        = reverse('api:user_detail', args=(obj.user.pk,))
        if obj.team:
            res['team']        = reverse('api:team_detail', args=(obj.team.pk,))
        if obj.project:
            res['project']     = reverse('api:project_detail', args=(obj.project.pk,)) 
        if obj.inventory:
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

class CredentialSerializer(BaseSerializer):

    # FIXME: may want to make some of these filtered based on user accessing

    password = serializers.WritableField(required=False, default='')
    ssh_key_data = serializers.WritableField(required=False, default='')
    ssh_key_unlock = serializers.WritableField(required=False, default='')
    sudo_password = serializers.WritableField(required=False, default='')

    class Meta:
        model = Credential
        fields = BASE_FIELDS + ('user', 'team', 'kind', 'cloud', 'username',
                                'password', 'ssh_key_data', 'ssh_key_unlock',
                                'sudo_username', 'sudo_password',)

    def to_native(self, obj):
        ret = super(CredentialSerializer, self).to_native(obj)
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
        if obj is None:
            return {}
        res = super(CredentialSerializer, self).get_related(obj)
        if obj.user:
            res['user'] = reverse('api:user_detail', args=(obj.user.pk,))
        if obj.team:
            res['team'] = reverse('api:team_detail', args=(obj.team.pk,))
        return res

class JobTemplateSerializer(BaseSerializer):

    class Meta:
        model = JobTemplate
        fields = BASE_FIELDS + ('job_type', 'inventory', 'project', 'playbook',
                                'credential', 'forks', 'limit', 'verbosity',
                                'extra_vars', 'job_tags', 'host_config_key')

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(JobTemplateSerializer, self).get_related(obj)
        res.update(dict(
            inventory   = reverse('api:inventory_detail',   args=(obj.inventory.pk,)),
            project     = reverse('api:project_detail',    args=(obj.project.pk,)),
            jobs        = reverse('api:job_template_jobs_list', args=(obj.pk,)),
        ))
        if obj.credential:
            res['credential'] = reverse('api:credential_detail', args=(obj.credential.pk,))
        if obj.host_config_key:
            res['callback'] = reverse('api:job_template_callback', args=(obj.pk,))
        return res

    def validate_playbook(self, attrs, source):
        project = attrs.get('project', None)
        playbook = attrs.get('playbook', '')
        if project and playbook and playbook not in project.playbooks:
            raise serializers.ValidationError('Playbook not found for project')
        return attrs

class JobSerializer(BaseSerializer):

    passwords_needed_to_start = serializers.Field(source='passwords_needed_to_start')

    class Meta:
        model = Job
        fields = ('id', 'url', 'related', 'summary_fields', 'created',
                  'modified', 'job_template', 'job_type', 'inventory',
                  'project', 'playbook', 'credential',
                  'forks', 'limit', 'verbosity', 'extra_vars',
                  'job_tags', 'launch_type', 'status', 'failed',
                  'result_stdout', 'result_traceback',
                  'passwords_needed_to_start', 'job_args',
                  'job_cwd', 'job_env')

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(JobSerializer, self).get_related(obj)
        res.update(dict(
            inventory   = reverse('api:inventory_detail',   args=(obj.inventory.pk,)),
            project     = reverse('api:project_detail',    args=(obj.project.pk,)),
            credential  = reverse('api:credential_detail', args=(obj.credential.pk,)),
            job_events  = reverse('api:job_job_events_list', args=(obj.pk,)),
            job_host_summaries = reverse('api:job_job_host_summaries_list', args=(obj.pk,)),
        ))
        if obj.job_template:
            res['job_template'] = reverse('api:job_template_detail', args=(obj.job_template.pk,))
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
            data.setdefault('inventory', job_template.inventory.pk)
            data.setdefault('project', job_template.project.pk)
            data.setdefault('playbook', job_template.playbook)
            if job_template.credential:
                data.setdefault('credential', job_template.credential.pk)
            data.setdefault('forks', job_template.forks)
            data.setdefault('limit', job_template.limit)
            data.setdefault('verbosity', job_template.verbosity)
            data.setdefault('extra_vars', job_template.extra_vars)
            data.setdefault('job_tags', job_template.job_tags)
        return super(JobSerializer, self).from_native(data, files)

class JobHostSummarySerializer(BaseSerializer):

    class Meta:
        model = JobHostSummary
        fields = ('id', 'url', 'job', 'host', 'created', 'modified',
                  'summary_fields', 'related', 'changed', 'dark', 'failures',
                  'ok', 'processed', 'skipped', 'failed')

    def get_related(self, obj):
        if obj is None:
            return {}
        res = super(JobHostSummarySerializer, self).get_related(obj)
        res.update(dict(
            job=reverse('api:job_detail', args=(obj.job.pk,)),
            host=reverse('api:host_detail', args=(obj.host.pk,))
        ))
        return res

    def get_summary_fields(self, obj):
        if obj is None:
            return {}
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
        fields = ('id', 'url', 'created', 'modified', 'job', 'event',
                  'event_display', 'event_data', 'event_level', 'failed',
                  'changed', 'host', 'related', 'summary_fields', 'parent',
                  'play', 'task')

    def get_related(self, obj):
        if obj is None:
            return {}
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
        if obj is None:
            return {}
        d = super(JobEventSerializer, self).get_summary_fields(obj)
        try:
            d['job']['job_template_id'] = obj.job.job_template.id
            d['job']['job_template_name'] = obj.job.job_template.name
        except (KeyError, AttributeError):
            pass
        return d

class ActivityStreamSerializer(BaseSerializer):

    class Meta:
        model = ActivityStream
        fields = ('id', 'url', 'related', 'summary_fields', 'timestamp', 'operation', 'changes',
                  'object1_id', 'object1_type', 'object2_id', 'object2_type', 'object_relationship_type')

    def get_related(self, obj):
        if obj is None:
            return {}
        rel = {}
        if obj.user is not None:
            rel['user'] = reverse('api:user_detail', args=(obj.user.pk,))
        obj1_resolution = camelcase_to_underscore(obj.object1_type.split(".")[-1])
        rel['object1'] = reverse('api:' + obj1_resolution + '_detail', args=(obj.object1_id,))
        if obj.operation in ('associate', 'disassociate'):
            obj2_resolution = camelcase_to_underscore(obj.object2_type.split(".")[-1])
            rel['object2'] = reverse('api:' + obj2_resolution + '_detail', args=(obj.object2_id,))
        return rel

    def get_summary_fields(self, obj):
        if obj is None:
            return {}
        d = super(ActivityStreamSerializer, self).get_summary_fields(obj)
        try:
            short_obj_type = obj.object1_type.split(".")[-1]
            under_short_obj_type = camelcase_to_underscore(short_obj_type)
            obj1 = eval(obj.object1_type + ".objects.get(id=" + str(obj.object1_id) + ")")
            d['object1'] = {'name': obj1.name, 'description': obj1.description,
                            'base': under_short_obj_type, 'id': obj.object1_id}
            if under_short_obj_type == "host" or under_short_obj_type == "group":
                d['inventory'] = {'name': obj1.inventory.name, 'id': obj1.inventory.id}
        except Exception, e:
            logger.error("Error getting object 1 summary: " + str(e))
        try:
            short_obj_type = obj.object2_type.split(".")[-1]
            under_short_obj_type = camelcase_to_underscore(short_obj_type)
            if obj.operation in ('associate', 'disassociate'):
                obj2 = eval(obj.object2_type + ".objects.get(id=" + str(obj.object2_id) + ")")
                d['object2'] = {'name': obj2.name, 'description': obj2.description,
                                'base': under_short_obj_type, 'id': obj.object2_id}
            if under_short_obj_type == "host" or under_short_obj_type == "group":
                d['inventory'] = {'name': obj2.inventory.name, 'id': obj2.inventory.id}
        except Exception, e:
            pass
        return d


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
