# Python
from copy import copy, deepcopy
import json
import logging
import os

import requests

# Django
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User # noqa
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.query import QuerySet
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.main.models.base import prevent_search
from awx.main.models.rbac import (
    Role, RoleAncestorEntry, get_roles_on_resource
)
from awx.main.utils import parse_yaml_or_json, get_custom_venv_choices, get_licenser
from awx.main.utils.encryption import decrypt_value, get_encryption_key, is_encrypted
from awx.main.utils.polymorphic import build_polymorphic_ctypes_map
from awx.main.fields import JSONField, AskForField
from awx.main.constants import ACTIVE_STATES


logger = logging.getLogger('awx.main.models.mixins')


__all__ = ['ResourceMixin', 'SurveyJobTemplateMixin', 'SurveyJobMixin',
           'TaskManagerUnifiedJobMixin', 'TaskManagerJobMixin', 'TaskManagerProjectUpdateMixin',
           'TaskManagerInventoryUpdateMixin', 'CustomVirtualEnvMixin']


class ResourceMixin(models.Model):

    class Meta:
        abstract = True

    @classmethod
    def accessible_objects(cls, accessor, role_field):
        '''
        Use instead of `MyModel.objects` when you want to only consider
        resources that a user has specific permissions for. For example:
        MyModel.accessible_objects(user, 'read_role').filter(name__istartswith='bar');
        NOTE: This should only be used for list type things. If you have a
        specific resource you want to check permissions on, it is more
        performant to resolve the resource in question then call
        `myresource.get_permissions(user)`.
        '''
        return ResourceMixin._accessible_objects(cls, accessor, role_field)

    @classmethod
    def accessible_pk_qs(cls, accessor, role_field):
        return ResourceMixin._accessible_pk_qs(cls, accessor, role_field)

    @staticmethod
    def _accessible_pk_qs(cls, accessor, role_field, content_types=None):
        if type(accessor) == User:
            ancestor_roles = accessor.roles.all()
        elif type(accessor) == Role:
            ancestor_roles = [accessor]
        else:
            accessor_type = ContentType.objects.get_for_model(accessor)
            ancestor_roles = Role.objects.filter(content_type__pk=accessor_type.id,
                                                 object_id=accessor.id)

        if content_types is None:
            ct_kwarg = dict(content_type_id = ContentType.objects.get_for_model(cls).id)
        else:
            ct_kwarg = dict(content_type_id__in = content_types)

        return RoleAncestorEntry.objects.filter(
            ancestor__in = ancestor_roles,
            role_field = role_field,
            **ct_kwarg
        ).values_list('object_id').distinct()


    @staticmethod
    def _accessible_objects(cls, accessor, role_field):
        return cls.objects.filter(pk__in = ResourceMixin._accessible_pk_qs(cls, accessor, role_field))


    def get_permissions(self, accessor):
        '''
        Returns a string list of the roles a accessor has for a given resource.
        An accessor can be either a User, Role, or an arbitrary resource that
        contains one or more Roles associated with it.
        '''

        return get_roles_on_resource(self, accessor)


class SurveyJobTemplateMixin(models.Model):
    class Meta:
        abstract = True

    survey_enabled = models.BooleanField(
        default=False,
    )
    survey_spec = prevent_search(JSONField(
        blank=True,
        default=dict,
    ))
    ask_variables_on_launch = AskForField(
        blank=True,
        default=False,
        allows_field='extra_vars'
    )

    def survey_password_variables(self):
        vars = []
        if self.survey_enabled and 'spec' in self.survey_spec:
            # Get variables that are type password
            for survey_element in self.survey_spec['spec']:
                if survey_element['type'] == 'password':
                    vars.append(survey_element['variable'])
        return vars

    @property
    def variables_needed_to_start(self):
        vars = []
        if self.survey_enabled and 'spec' in self.survey_spec:
            for survey_element in self.survey_spec['spec']:
                if survey_element['required']:
                    vars.append(survey_element['variable'])
        return vars

    def _update_unified_job_kwargs(self, create_kwargs, kwargs):
        '''
        Combine extra_vars with variable precedence order:
          JT extra_vars -> JT survey defaults -> runtime extra_vars

        :param create_kwargs: key-worded arguments to be updated and later used for creating unified job.
        :type create_kwargs: dict
        :param kwargs: request parameters used to override unified job template fields with runtime values.
        :type kwargs: dict
        :return: modified create_kwargs.
        :rtype: dict
        '''
        # Job Template extra_vars
        extra_vars = self.extra_vars_dict

        survey_defaults = {}

        # transform to dict
        if 'extra_vars' in kwargs:
            runtime_extra_vars = kwargs['extra_vars']
            runtime_extra_vars = parse_yaml_or_json(runtime_extra_vars)
        else:
            runtime_extra_vars = {}

        # Overwrite job template extra vars with survey default vars
        if self.survey_enabled and 'spec' in self.survey_spec:
            for survey_element in self.survey_spec.get("spec", []):
                default = survey_element.get('default')
                variable_key = survey_element.get('variable')

                if survey_element.get('type') == 'password':
                    if variable_key in runtime_extra_vars:
                        kw_value = runtime_extra_vars[variable_key]
                        if kw_value == '$encrypted$':
                            runtime_extra_vars.pop(variable_key)

                if default is not None:
                    decrypted_default = default
                    if (
                        survey_element['type'] == "password" and
                        isinstance(decrypted_default, str) and
                        decrypted_default.startswith('$encrypted$')
                    ):
                        decrypted_default = decrypt_value(get_encryption_key('value', pk=None), decrypted_default)
                    errors = self._survey_element_validation(survey_element, {variable_key: decrypted_default})
                    if not errors:
                        survey_defaults[variable_key] = default
        extra_vars.update(survey_defaults)

        # Overwrite job template extra vars with explicit job extra vars
        # and add on job extra vars
        extra_vars.update(runtime_extra_vars)
        create_kwargs['extra_vars'] = json.dumps(extra_vars)
        return create_kwargs

    def _survey_element_validation(self, survey_element, data, validate_required=True):
        # Don't apply validation to the `$encrypted$` placeholder; the decrypted
        # default (if any) will be validated against instead
        errors = []

        if (survey_element['type'] == "password"):
            password_value = data.get(survey_element['variable'])
            if (
                isinstance(password_value, str) and
                password_value == '$encrypted$'
            ):
                if survey_element.get('default') is None and survey_element['required']:
                    if validate_required:
                        errors.append("'%s' value missing" % survey_element['variable'])
                return errors

        if survey_element['variable'] not in data and survey_element['required']:
            if validate_required:
                errors.append("'%s' value missing" % survey_element['variable'])
        elif survey_element['type'] in ["textarea", "text", "password"]:
            if survey_element['variable'] in data:
                if not isinstance(data[survey_element['variable']], str):
                    errors.append("Value %s for '%s' expected to be a string." % (data[survey_element['variable']],
                                                                                  survey_element['variable']))
                    return errors

                if 'min' in survey_element and survey_element['min'] not in ["", None] and len(data[survey_element['variable']]) < int(survey_element['min']):
                    errors.append("'%s' value %s is too small (length is %s must be at least %s)." %
                                  (survey_element['variable'], data[survey_element['variable']], len(data[survey_element['variable']]), survey_element['min']))
                if 'max' in survey_element and survey_element['max'] not in ["", None] and len(data[survey_element['variable']]) > int(survey_element['max']):
                    errors.append("'%s' value %s is too large (must be no more than %s)." %
                                  (survey_element['variable'], data[survey_element['variable']], survey_element['max']))

        elif survey_element['type'] == 'integer':
            if survey_element['variable'] in data:
                if type(data[survey_element['variable']]) != int:
                    errors.append("Value %s for '%s' expected to be an integer." % (data[survey_element['variable']],
                                                                                    survey_element['variable']))
                    return errors
                if 'min' in survey_element and survey_element['min'] not in ["", None] and survey_element['variable'] in data and \
                   data[survey_element['variable']] < int(survey_element['min']):
                    errors.append("'%s' value %s is too small (must be at least %s)." %
                                  (survey_element['variable'], data[survey_element['variable']], survey_element['min']))
                if 'max' in survey_element and survey_element['max'] not in ["", None] and survey_element['variable'] in data and \
                   data[survey_element['variable']] > int(survey_element['max']):
                    errors.append("'%s' value %s is too large (must be no more than %s)." %
                                  (survey_element['variable'], data[survey_element['variable']], survey_element['max']))
        elif survey_element['type'] == 'float':
            if survey_element['variable'] in data:
                if type(data[survey_element['variable']]) not in (float, int):
                    errors.append("Value %s for '%s' expected to be a numeric type." % (data[survey_element['variable']],
                                                                                        survey_element['variable']))
                    return errors
                if 'min' in survey_element and survey_element['min'] not in ["", None] and data[survey_element['variable']] < float(survey_element['min']):
                    errors.append("'%s' value %s is too small (must be at least %s)." %
                                  (survey_element['variable'], data[survey_element['variable']], survey_element['min']))
                if 'max' in survey_element and survey_element['max'] not in ["", None] and data[survey_element['variable']] > float(survey_element['max']):
                    errors.append("'%s' value %s is too large (must be no more than %s)." %
                                  (survey_element['variable'], data[survey_element['variable']], survey_element['max']))
        elif survey_element['type'] == 'multiselect':
            if survey_element['variable'] in data:
                if type(data[survey_element['variable']]) != list:
                    errors.append("'%s' value is expected to be a list." % survey_element['variable'])
                else:
                    choice_list = copy(survey_element['choices'])
                    if isinstance(choice_list, str):
                        choice_list = [choice for choice in choice_list.splitlines() if choice.strip() != '']
                    for val in data[survey_element['variable']]:
                        if val not in choice_list:
                            errors.append("Value %s for '%s' expected to be one of %s." % (val, survey_element['variable'],
                                                                                           choice_list))
        elif survey_element['type'] == 'multiplechoice':
            choice_list = copy(survey_element['choices'])
            if isinstance(choice_list, str):
                choice_list = [choice for choice in choice_list.splitlines() if choice.strip() != '']
            if survey_element['variable'] in data:
                if data[survey_element['variable']] not in choice_list:
                    errors.append("Value %s for '%s' expected to be one of %s." % (data[survey_element['variable']],
                                                                                   survey_element['variable'],
                                                                                   choice_list))
        return errors

    def _accept_or_ignore_variables(self, data, errors=None, _exclude_errors=(), extra_passwords=None):
        survey_is_enabled = (self.survey_enabled and self.survey_spec)
        extra_vars = data.copy()
        if errors is None:
            errors = {}
        rejected = {}
        accepted = {}

        if survey_is_enabled:
            # Check for data violation of survey rules
            survey_errors = []
            for survey_element in self.survey_spec.get("spec", []):
                key = survey_element.get('variable', None)
                value = data.get(key, None)
                validate_required = 'required' not in _exclude_errors
                if extra_passwords and key in extra_passwords and is_encrypted(value):
                    element_errors = self._survey_element_validation(survey_element, {
                        key: decrypt_value(get_encryption_key('value', pk=None), value)
                    }, validate_required=validate_required)
                else:
                    element_errors = self._survey_element_validation(
                        survey_element, data, validate_required=validate_required)

                if element_errors:
                    survey_errors += element_errors
                    if key is not None and key in extra_vars:
                        rejected[key] = extra_vars.pop(key)
                elif key in extra_vars:
                    accepted[key] = extra_vars.pop(key)
            if survey_errors:
                errors['variables_needed_to_start'] = survey_errors

        if self.ask_variables_on_launch:
            # We can accept all variables
            accepted.update(extra_vars)
            extra_vars = {}

        if extra_vars:
            # Prune the prompted variables for those identical to template
            tmp_extra_vars = self.extra_vars_dict
            for key in (set(tmp_extra_vars.keys()) & set(extra_vars.keys())):
                if tmp_extra_vars[key] == extra_vars[key]:
                    extra_vars.pop(key)

        if extra_vars:
            # Leftover extra_vars, keys provided that are not allowed
            rejected.update(extra_vars)
            # ignored variables does not block manual launch
            if 'prompts' not in _exclude_errors:
                errors['extra_vars'] = [_('Variables {list_of_keys} are not allowed on launch. Check the Prompt on Launch setting '+
                                        'on the {model_name} to include Extra Variables.').format(
                    list_of_keys=', '.join([str(key) for key in extra_vars.keys()]),
                    model_name=self._meta.verbose_name.title())]

        return (accepted, rejected, errors)

    @staticmethod
    def pivot_spec(spec):
        '''
        Utility method that will return a dictionary keyed off variable names
        '''
        pivoted = {}
        for element_data in spec.get('spec', []):
            if 'variable' in element_data:
                pivoted[element_data['variable']] = element_data
        return pivoted

    def survey_variable_validation(self, data):
        errors = []
        if not self.survey_enabled:
            return errors
        if 'name' not in self.survey_spec:
            errors.append("'name' missing from survey spec.")
        if 'description' not in self.survey_spec:
            errors.append("'description' missing from survey spec.")
        for survey_element in self.survey_spec.get("spec", []):
            errors += self._survey_element_validation(survey_element, data)
        return errors

    def display_survey_spec(self):
        '''
        Hide encrypted default passwords in survey specs
        '''
        survey_spec = deepcopy(self.survey_spec) if self.survey_spec else {}
        for field in survey_spec.get('spec', []):
            if field.get('type') == 'password':
                if 'default' in field and field['default']:
                    field['default'] = '$encrypted$'
        return survey_spec


class SurveyJobMixin(models.Model):
    class Meta:
        abstract = True

    survey_passwords = prevent_search(JSONField(
        blank=True,
        default=dict,
        editable=False,
    ))

    def display_extra_vars(self):
        '''
        Hides fields marked as passwords in survey.
        '''
        if self.survey_passwords:
            extra_vars = json.loads(self.extra_vars)
            for key, value in self.survey_passwords.items():
                if key in extra_vars:
                    extra_vars[key] = value
            return json.dumps(extra_vars)
        else:
            return self.extra_vars

    def decrypted_extra_vars(self):
        '''
        Decrypts fields marked as passwords in survey.
        '''
        if self.survey_passwords:
            extra_vars = json.loads(self.extra_vars)
            for key in self.survey_passwords:
                value = extra_vars.get(key)
                if value and isinstance(value, str) and value.startswith('$encrypted$'):
                    extra_vars[key] = decrypt_value(get_encryption_key('value', pk=None), value)
            return json.dumps(extra_vars)
        else:
            return self.extra_vars


class TaskManagerUnifiedJobMixin(models.Model):
    class Meta:
        abstract = True

    def get_jobs_fail_chain(self):
        return []

    def dependent_jobs_finished(self):
        return True


class TaskManagerJobMixin(TaskManagerUnifiedJobMixin):
    class Meta:
        abstract = True

    def get_jobs_fail_chain(self):
        return [self.project_update] if self.project_update else []

    def dependent_jobs_finished(self):
        for j in self.dependent_jobs.all():
            if j.status in ['pending', 'waiting', 'running']:
                return False
        return True


class TaskManagerUpdateOnLaunchMixin(TaskManagerUnifiedJobMixin):
    class Meta:
        abstract = True

    def get_jobs_fail_chain(self):
        return list(self.dependent_jobs.all())


class TaskManagerProjectUpdateMixin(TaskManagerUpdateOnLaunchMixin):
    class Meta:
        abstract = True


class TaskManagerInventoryUpdateMixin(TaskManagerUpdateOnLaunchMixin):
    class Meta:
        abstract = True


class CustomVirtualEnvMixin(models.Model):
    class Meta:
        abstract = True

    custom_virtualenv = models.CharField(
        blank=True,
        null=True,
        default=None,
        max_length=100,
        help_text=_('Local absolute file path containing a custom Python virtualenv to use')
    )

    def clean_custom_virtualenv(self):
        value = self.custom_virtualenv
        if value and os.path.join(value, '') not in get_custom_venv_choices():
            raise ValidationError(
                _('{} is not a valid virtualenv in {}').format(value, settings.BASE_VENV_PATH)
            )
        if value:
            return os.path.join(value, '')
        return None


class RelatedJobsMixin(object):

    '''
    This method is intended to be overwritten.
    Called by get_active_jobs()
    Returns a list of active jobs (i.e. running) associated with the calling
    resource (self). Expected to return a QuerySet
    '''
    def _get_related_jobs(self):
        return self.objects.none()

    def _get_active_jobs(self):
        return self._get_related_jobs().filter(status__in=ACTIVE_STATES)

    '''
    Returns [{'id': 1, 'type': 'job'}, {'id': 2, 'type': 'project_update'}, ...]
    '''
    def get_active_jobs(self):
        UnifiedJob = apps.get_model('main', 'UnifiedJob')
        mapping = build_polymorphic_ctypes_map(UnifiedJob)
        jobs = self._get_active_jobs()
        if not isinstance(jobs, QuerySet):
            raise RuntimeError("Programmer error. Expected _get_active_jobs() to return a QuerySet.")

        return [dict(id=t[0], type=mapping[t[1]]) for t in jobs.values_list('id', 'polymorphic_ctype_id')]


class WebhookTemplateMixin(models.Model):
    class Meta:
        abstract = True

    SERVICES = [
        ('github', "GitHub"),
        ('gitlab', "GitLab"),
    ]

    webhook_service = models.CharField(
        max_length=16,
        choices=SERVICES,
        blank=True,
        help_text=_('Service that webhook requests will be accepted from')
    )
    webhook_key = prevent_search(models.CharField(
        max_length=64,
        blank=True,
        help_text=_('Shared secret that the webhook service will use to sign requests')
    ))
    webhook_credential = models.ForeignKey(
        'Credential',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='%(class)ss',
        help_text=_('Personal Access Token for posting back the status to the service API')
    )

    def rotate_webhook_key(self):
        self.webhook_key = get_random_string(length=50)

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')

        if not self.pk or self._values_have_edits({'webhook_service': self.webhook_service}):
            if self.webhook_service:
                self.rotate_webhook_key()
            else:
                self.webhook_key = ''

            if update_fields and 'webhook_service' in update_fields:
                update_fields.add('webhook_key')

        super().save(*args, **kwargs)


class WebhookMixin(models.Model):
    class Meta:
        abstract = True

    SERVICES = WebhookTemplateMixin.SERVICES

    webhook_service = models.CharField(
        max_length=16,
        choices=SERVICES,
        blank=True,
        help_text=_('Service that webhook requests will be accepted from')
    )
    webhook_credential = models.ForeignKey(
        'Credential',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='%(class)ss',
        help_text=_('Personal Access Token for posting back the status to the service API')
    )
    webhook_guid = models.CharField(
        blank=True,
        max_length=128,
        help_text=_('Unique identifier of the event that triggered this webhook')
    )

    def update_webhook_status(self, status):
        if not self.webhook_credential:
            return

        status_api = self.extra_vars_dict.get('tower_webhook_status_api')
        if not status_api:
            logger.debug("Webhook event did not have a status API endpoint associated, skipping.")
            return

        service_header = {
            'github': ('Authorization', 'token {}'),
            'gitlab': ('PRIVATE-TOKEN', '{}'),
        }
        service_statuses = {
            'github': {
                'pending': 'pending',
                'successful': 'success',
                'failed': 'failure',
                'canceled': 'failure',  # GitHub doesn't have a 'canceled' status :(
                'error': 'error',
            },
            'gitlab': {
                'pending': 'pending',
                'running': 'running',
                'successful': 'success',
                'failed': 'failed',
                'error': 'failed',  # GitLab doesn't have an 'error' status distinct from 'failed' :(
                'canceled': 'canceled',
            },
        }

        statuses = service_statuses[self.webhook_service]
        if status not in statuses:
            logger.debug("Skipping webhook job status change: '{}'".format(status))
            return
        try:
            license_type = get_licenser().validate().get('license_type')
            data = {
                'state': statuses[status],
                'context': 'ansible/awx' if license_type == 'open' else 'ansible/tower',
                'target_url': self.get_ui_url(),
            }
            k, v = service_header[self.webhook_service]
            headers = {
                k: v.format(self.webhook_credential.get_input('token')),
                'Content-Type': 'application/json'
            }
            response = requests.post(status_api, data=json.dumps(data), headers=headers, timeout=30)
        except Exception:
            logger.exception("Posting webhook status caused an error.")
            return

        if response.status_code < 400:
            logger.debug("Webhook status update sent.")
        else:
            logger.error(
                "Posting webhook status failed, code: {}\n"
                "{}\n"
                "Payload sent: {}".format(response.status_code, response.text, json.dumps(data))
            )
