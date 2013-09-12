# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Python
import json
import re
import socket
import urlparse

# PyYAML
import yaml

# Django
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework.compat import get_concrete_model
from rest_framework import serializers

# AWX
from awx.main.models import *
from awx.main.utils import update_scm_url

BASE_FIELDS = ('id', 'url', 'related', 'summary_fields', 'created', 'modified',
               'name', 'description')

# objects that if found we should add summary info for them
SUMMARIZABLE_FKS = ( 
   'organization', 'host', 'group', 'inventory', 'project', 'team', 'job',
   'job_template', 'credential', 'permission', 'user', 'last_job',
)
# fields that should be summarized regardless of object type
SUMMARIZABLE_FIELDS = (
   'name', 'username', 'first_name', 'last_name', 'description',
)

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
        if isinstance(obj, User):
            return reverse('main:user_detail', args=(obj.pk,))
        else:
            return obj.get_absolute_url()

    def get_related(self, obj):
        res = SortedDict()
        if getattr(obj, 'created_by', None):
            res['created_by'] = reverse('main:user_detail', args=(obj.created_by.pk,))
        return res

    def get_summary_fields(self, obj):
        # return the names (at least) for various fields, so we don't have to write this
        # method for each object.
        summary_fields = SortedDict()
        for fk in SUMMARIZABLE_FKS:
            try:
                fkval = getattr(obj, fk, None)
                if fkval is not None:
                    summary_fields[fk] = SortedDict()
                    for field in SUMMARIZABLE_FIELDS:
                        fval = getattr(fkval, field, None)
                        if fval is not None:
                            summary_fields[fk][field] = fval
            # Can be raised by the reverse accessor for a OneToOneField.
            except ObjectDoesNotExist:
                pass
        return summary_fields 

    def get_created(self, obj):
        if isinstance(obj, User):
            return obj.date_joined
        else:
            return obj.created

    def get_modified(self, obj):
        if isinstance(obj, User):
            return obj.last_login # Not actually exposed for User.
        else:
            return obj.modified

    def get_active(self, obj):
        if isinstance(obj, User):
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
        res = super(UserSerializer, self).get_related(obj)
        res.update(dict(
            teams                  = reverse('main:user_teams_list',               args=(obj.pk,)),
            organizations          = reverse('main:user_organizations_list',       args=(obj.pk,)),
            admin_of_organizations = reverse('main:user_admin_of_organizations_list', args=(obj.pk,)),
            projects               = reverse('main:user_projects_list',            args=(obj.pk,)),
            credentials            = reverse('main:user_credentials_list',         args=(obj.pk,)),
            permissions            = reverse('main:user_permissions_list',         args=(obj.pk,)),
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
        res = super(OrganizationSerializer, self).get_related(obj)
        res.update(dict(
            #audit_trail = reverse('main:organization_audit_trail_list',    args=(obj.pk,)),
            projects    = reverse('main:organization_projects_list',       args=(obj.pk,)),
            inventories = reverse('main:organization_inventories_list',    args=(obj.pk,)),
            users       = reverse('main:organization_users_list',          args=(obj.pk,)),
            admins      = reverse('main:organization_admins_list',         args=(obj.pk,)),
            #tags        = reverse('main:organization_tags_list',           args=(obj.pk,)),
            teams       = reverse('main:organization_teams_list',          args=(obj.pk,)),
        ))
        return res

class ProjectSerializer(BaseSerializer):

    scm_password = serializers.WritableField(required=False, default='')
    scm_key_data = serializers.WritableField(required=False, default='')
    scm_key_unlock = serializers.WritableField(required=False, default='')

    playbooks = serializers.Field(source='playbooks', help_text='Array of playbooks available within this project.')
    scm_delete_on_next_update = serializers.Field(source='scm_delete_on_next_update')

    class Meta:
        model = Project
        fields = BASE_FIELDS + ('local_path', 'scm_type', 'scm_url',
                                'scm_branch', 'scm_clean',
                                'scm_delete_on_update', 'scm_delete_on_next_update',
                                'scm_update_on_launch',
                                'scm_username', 'scm_password', 'scm_key_data',
                                'scm_key_unlock', 'last_update_failed', 'status', 'last_updated')

    def to_native(self, obj):
        ret = super(ProjectSerializer, self).to_native(obj)
        # Replace the actual encrypted value with the string $encrypted$.
        for field in Project.PASSWORD_FIELDS:
            if field in ret and unicode(ret[field]).startswith('$encrypted$'):
                ret[field] = '$encrypted$'
        return ret

    def restore_object(self, attrs, instance=None):
        # If the value sent to the API startswith $encrypted$, ignore it.
        for field in Project.PASSWORD_FIELDS:
            if unicode(attrs.get(field, '')).startswith('$encrypted$'):
                attrs.pop(field, None)
        instance = super(ProjectSerializer, self).restore_object(attrs, instance)
        return instance

    def get_related(self, obj):
        res = super(ProjectSerializer, self).get_related(obj)
        res.update(dict(
            organizations = reverse('main:project_organizations_list', args=(obj.pk,)),
            teams = reverse('main:project_teams_list', args=(obj.pk,)),
            playbooks = reverse('main:project_playbooks', args=(obj.pk,)),
            update = reverse('main:project_update_view', args=(obj.pk,)),
            project_updates = reverse('main:project_updates_list', args=(obj.pk,)),
        ))
        if obj.current_update:
            res['current_update'] = reverse('main:project_update_detail',
                                            args=(obj.current_update.pk,))
        if obj.last_update:
            res['last_update'] = reverse('main:project_update_detail',
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
        #print scm_url_parts
        if scm_type and not any(scm_url_parts):
            raise serializers.ValidationError('SCM URL is required')
        return attrs

    def validate_scm_username(self, attrs, source):
        if self.object:
            scm_type = attrs.get('scm_type', self.object.scm_type) or ''
            scm_url = unicode(attrs.get('scm_url', self.object.scm_url) or '')
            scm_username = attrs.get('scm_username', self.object.scm_username) or ''
        else:
            scm_type = attrs.get('scm_type', '') or ''
            scm_url = unicode(attrs.get('scm_url', '') or '')
            scm_username = attrs.get('scm_username', '') or ''
        if not scm_type:
            return attrs
        try:
            if scm_url and scm_username:
                update_scm_url(scm_type, scm_url, scm_username)
        except ValueError, e:
            raise serializers.ValidationError((e.args or ('Invalid SCM username',))[0])
        return attrs

    def validate_scm_password(self, attrs, source):
        if self.object:
            scm_type = attrs.get('scm_type', self.object.scm_type) or ''
            scm_url = unicode(attrs.get('scm_url', self.object.scm_url) or '')
            scm_username = attrs.get('scm_username', self.object.scm_username) or ''
            scm_password = attrs.get('scm_password', self.object.scm_password) or ''
        else:
            scm_type = attrs.get('scm_type', '') or ''
            scm_url = unicode(attrs.get('scm_url', '') or '')
            scm_username = attrs.get('scm_username', '') or ''
            scm_password = attrs.get('scm_password', '') or ''
        if not scm_type:
            return attrs
        try:
            try:
                if scm_url and scm_username:
                    update_scm_url(scm_type, scm_url, scm_username)
            except ValueError:
                pass
            else:
                if scm_url and scm_username and scm_password:
                    update_scm_url(scm_type, scm_url, scm_username, '**')
        except ValueError, e:
            raise serializers.ValidationError((e.args or ('Invalid SCM password',))[0])
        return attrs

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
        res = super(ProjectUpdateSerializer, self).get_related(obj)
        res.update(dict(
            project = reverse('main:project_detail', args=(obj.project.pk,)),
            cancel = reverse('main:project_update_cancel', args=(obj.pk,)),
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
                                'has_active_failures')

    def get_related(self, obj):
        res = super(InventorySerializer, self).get_related(obj)
        res.update(dict(
            hosts         = reverse('main:inventory_hosts_list',        args=(obj.pk,)),
            groups        = reverse('main:inventory_groups_list',       args=(obj.pk,)),
            root_groups   = reverse('main:inventory_root_groups_list',  args=(obj.pk,)),
            variable_data = reverse('main:inventory_variable_data',     args=(obj.pk,)),
            script        = reverse('main:inventory_script_view',       args=(obj.pk,)),
            tree          = reverse('main:inventory_tree_view',         args=(obj.pk,)),
            organization  = reverse('main:organization_detail',         args=(obj.organization.pk,)),
        ))
        return res

class HostSerializer(BaseSerializerWithVariables):

    class Meta:
        model = Host
        fields = BASE_FIELDS + ('inventory', 'variables', 'has_active_failures',
                                'last_job', 'last_job_host_summary')

    def get_related(self, obj):
        res = super(HostSerializer, self).get_related(obj)
        res.update(dict(
            variable_data = reverse('main:host_variable_data',   args=(obj.pk,)),
            inventory     = reverse('main:inventory_detail',     args=(obj.inventory.pk,)),
            groups        = reverse('main:host_groups_list',     args=(obj.pk,)),
            all_groups    = reverse('main:host_all_groups_list', args=(obj.pk,)),
            job_events    = reverse('main:host_job_events_list',  args=(obj.pk,)),
            job_host_summaries = reverse('main:host_job_host_summaries_list', args=(obj.pk,)),
        ))
        if obj.last_job:
            res['last_job'] = reverse('main:job_detail', args=(obj.last_job.pk,))
        if obj.last_job_host_summary:
            res['last_job_host_summary'] = reverse('main:job_host_summary_detail', args=(obj.last_job_host_summary.pk,))
        return res

    def get_summary_fields(self, obj):
        d = super(HostSerializer, self).get_summary_fields(obj)
        d['all_groups'] = [{'id': g.id, 'name': g.name} for g in obj.all_groups.all()]
        d['groups'] = [{'id': g.id, 'name': g.name} for g in obj.groups.all()]
        return d

    def validate_name(self, attrs, source):
        name = unicode(attrs.get(source, ''))
        # Allow hostname (except IPv6 for now) to specify the port # inline.
        if name.count(':') == 1:
            name, port = name.split(':')
            try:
                port = int(port)
                if port < 1 or port > 65535:
                    raise ValueError
            except ValueError:
                raise serializers.ValidationError('Invalid port specification')
        for family in (socket.AF_INET, socket.AF_INET6):
            try:
                socket.inet_pton(family, name)
                return attrs
            except socket.error:
                pass
        # Hostname should match the following regular expression and have at
        # last one letter in the name (to catch invalid IPv4 addresses from
        # above).
        valid_host_re = r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$'
        if re.match(valid_host_re, name) and re.match(r'^.*?[a-zA-Z].*?$', name):
            return attrs
        raise serializers.ValidationError('Invalid host name or IP')

class GroupSerializer(BaseSerializerWithVariables):

    class Meta:
        model = Group
        fields = BASE_FIELDS + ('inventory', 'variables', 'has_active_failures')

    def get_related(self, obj):
        res = super(GroupSerializer, self).get_related(obj)
        res.update(dict(
            variable_data = reverse('main:group_variable_data',   args=(obj.pk,)),
            hosts         = reverse('main:group_hosts_list',      args=(obj.pk,)),
            children      = reverse('main:group_children_list',   args=(obj.pk,)),
            all_hosts     = reverse('main:group_all_hosts_list',  args=(obj.pk,)),
            inventory     = reverse('main:inventory_detail',       args=(obj.inventory.pk,)),
            job_events    = reverse('main:group_job_events_list',   args=(obj.pk,)),
            job_host_summaries = reverse('main:group_job_host_summaries_list', args=(obj.pk,)),
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
                                'children')

    def get_children(self, obj):
        children_qs = obj.children.filter(active=True)
        return GroupTreeSerializer(children_qs, many=True).data

class BaseVariableDataSerializer(BaseSerializer):

    def to_native(self, obj):
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

class TeamSerializer(BaseSerializer):

    class Meta:
        model = Team
        fields = BASE_FIELDS + ('organization',)

    def get_related(self, obj):
        res = super(TeamSerializer, self).get_related(obj)
        res.update(dict(
            projects     = reverse('main:team_projects_list',    args=(obj.pk,)),
            users        = reverse('main:team_users_list',       args=(obj.pk,)),
            credentials  = reverse('main:team_credentials_list', args=(obj.pk,)),
            organization = reverse('main:organization_detail',   args=(obj.organization.pk,)),
            permissions  = reverse('main:team_permissions_list', args=(obj.pk,)),
        ))
        return res

class PermissionSerializer(BaseSerializer):

    class Meta:
        model = Permission
        fields = BASE_FIELDS + ('user', 'team', 'project', 'inventory',
                                'permission_type',)
         
    def get_related(self, obj):
        res = super(PermissionSerializer, self).get_related(obj)
        if obj.user:
            res['user']        = reverse('main:user_detail', args=(obj.user.pk,))
        if obj.team:
            res['team']        = reverse('main:team_detail', args=(obj.team.pk,))
        if obj.project:
            res['project']     = reverse('main:project_detail', args=(obj.project.pk,)) 
        if obj.inventory:
            res['inventory']   = reverse('main:inventory_detail', args=(obj.inventory.pk,))
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

    ssh_password = serializers.WritableField(required=False, default='')
    ssh_key_data = serializers.WritableField(required=False, default='')
    ssh_key_unlock = serializers.WritableField(required=False, default='')
    sudo_password = serializers.WritableField(required=False, default='')

    class Meta:
        model = Credential
        fields = BASE_FIELDS + ('ssh_username', 'ssh_password', 'ssh_key_data',
                                'ssh_key_unlock', 'sudo_username',
                                'sudo_password', 'user', 'team',)

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
        res = super(CredentialSerializer, self).get_related(obj)
        if obj.user:
            res['user'] = reverse('main:user_detail', args=(obj.user.pk,))
        if obj.team:
            res['team'] = reverse('main:team_detail', args=(obj.team.pk,))
        return res

    def validate(self, attrs):
        ''' some fields cannot be changed once written '''
        if self.object is not None:
            # this is an update
            if 'user' in attrs and self.object.user != attrs['user']:
                raise serializers.ValidationError("user cannot be changed")
            if 'team' in attrs and self.object.team != attrs['team']:
                raise serializers.ValidationError("team cannot be changed")
        return attrs

class JobTemplateSerializer(BaseSerializer):

    class Meta:
        model = JobTemplate
        fields = BASE_FIELDS + ('job_type', 'inventory', 'project', 'playbook',
                                'credential', 'forks', 'limit', 'verbosity',
                                'extra_vars', 'job_tags', 'host_config_key')

    def get_related(self, obj):
        res = super(JobTemplateSerializer, self).get_related(obj)
        res.update(dict(
            inventory   = reverse('main:inventory_detail',   args=(obj.inventory.pk,)),
            project     = reverse('main:project_detail',    args=(obj.project.pk,)),
            jobs        = reverse('main:job_template_jobs_list', args=(obj.pk,)),
        ))
        if obj.credential:
            res['credential'] = reverse('main:credential_detail', args=(obj.credential.pk,))
        if obj.host_config_key:
            res['callback'] = reverse('main:job_template_callback', args=(obj.pk,))
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
        fields = BASE_FIELDS + ('job_template', 'job_type', 'inventory',
                                'project', 'playbook', 'credential',
                                'forks', 'limit', 'verbosity', 'extra_vars',
                                'job_tags', 'launch_type', 'status', 'failed',
                                'result_stdout', 'result_traceback',
                                'passwords_needed_to_start', 'job_args',
                                'job_cwd', 'job_env')

    def get_related(self, obj):
        res = super(JobSerializer, self).get_related(obj)
        res.update(dict(
            inventory   = reverse('main:inventory_detail',   args=(obj.inventory.pk,)),
            project     = reverse('main:project_detail',    args=(obj.project.pk,)),
            credential  = reverse('main:credential_detail', args=(obj.credential.pk,)),
            job_events  = reverse('main:job_job_events_list', args=(obj.pk,)),
            job_host_summaries = reverse('main:job_job_host_summaries_list', args=(obj.pk,)),
        ))
        if obj.job_template:
            res['job_template'] = reverse('main:job_template_detail', args=(obj.job_template.pk,))
        if obj.can_start or True:
            res['start'] = reverse('main:job_start', args=(obj.pk,))
        if obj.can_cancel or True:
            res['cancel'] = reverse('main:job_cancel', args=(obj.pk,))
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
        res = super(JobHostSummarySerializer, self).get_related(obj)
        res.update(dict(
            job=reverse('main:job_detail', args=(obj.job.pk,)),
            host=reverse('main:host_detail', args=(obj.host.pk,))
        ))
        return res

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
        res = super(JobEventSerializer, self).get_related(obj)
        res.update(dict(
            job = reverse('main:job_detail', args=(obj.job.pk,)),
            #children = reverse('main:job_event_children_list', args=(obj.pk,)),
        ))
        if obj.parent:
            res['parent'] = reverse('main:job_event_detail', args=(obj.parent.pk,))
        if obj.children.count():
            res['children'] = reverse('main:job_event_children_list', args=(obj.pk,))
        if obj.host:
            res['host'] = reverse('main:host_detail', args=(obj.host.pk,))
        if obj.hosts.count():
            res['hosts'] = reverse('main:job_event_hosts_list', args=(obj.pk,))
        return res

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
