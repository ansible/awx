# -*- coding: utf-8 -*-
# (c) Matthias Dellweg (ATIX AG) 2017

from __future__ import absolute_import, division, print_function
__metaclass__ = type


import json
import re
import time
import traceback

from collections import defaultdict
from functools import wraps

from ansible.module_utils.basic import AnsibleModule

try:
    import apypie
    import requests.exceptions
    HAS_APYPIE = True
except ImportError:
    HAS_APYPIE = False
    APYPIE_IMP_ERR = traceback.format_exc()

try:
    import yaml
    HAS_PYYAML = True
except ImportError:
    HAS_PYYAML = False
    PYYAML_IMP_ERR = traceback.format_exc()

parameter_entity_spec = dict(
    name=dict(required=True),
    value=dict(type='raw', required=True),
    parameter_type=dict(default='string', choices=['string', 'boolean', 'integer', 'real', 'array', 'hash', 'yaml', 'json']),
)


def _exception2fail_json(msg='Generic failure: %s'):
    def decor(f):
        @wraps(f)
        def inner(self, *args, **kwargs):
            try:
                return f(self, *args, **kwargs)
            except Exception as e:
                self.fail_from_exception(e, msg % str(e))
        return inner
    return decor


class KatelloMixin(object):
    def __init__(self, argument_spec=None, **kwargs):
        args = dict(
            organization=dict(required=True),
        )
        if argument_spec:
            args.update(argument_spec)
        super(KatelloMixin, self).__init__(argument_spec=args, **kwargs)

    @_exception2fail_json(msg="Failed to connect to Foreman server: %s ")
    def connect(self):
        super(KatelloMixin, self).connect()
        self._patch_content_uploads_update_api()
        self._patch_organization_update_api()
        self._patch_subscription_index_api()
        self._patch_sync_plan_api()

    def _patch_content_uploads_update_api(self):
        """This is a workaround for the broken content_uploads update apidoc in katello.
            see https://projects.theforeman.org/issues/27590
        """

        _content_upload_methods = self.foremanapi.apidoc['docs']['resources']['content_uploads']['methods']

        _content_upload_update = next(x for x in _content_upload_methods if x['name'] == 'update')
        _content_upload_update_params_id = next(x for x in _content_upload_update['params'] if x['name'] == 'id')
        _content_upload_update_params_id['expected_type'] = 'string'

        _content_upload_destroy = next(x for x in _content_upload_methods if x['name'] == 'destroy')
        _content_upload_destroy_params_id = next(x for x in _content_upload_destroy['params'] if x['name'] == 'id')
        _content_upload_destroy_params_id['expected_type'] = 'string'

    def _patch_organization_update_api(self):
        """This is a workaround for the broken organization update apidoc in katello.
            see https://projects.theforeman.org/issues/27538
        """

        _organization_methods = self.foremanapi.apidoc['docs']['resources']['organizations']['methods']

        _organization_update = next(x for x in _organization_methods if x['name'] == 'update')
        _organization_update_params_organization = next(x for x in _organization_update['params'] if x['name'] == 'organization')
        _organization_update_params_organization['required'] = False

    def _patch_subscription_index_api(self):
        """This is a workaround for the broken subscriptions apidoc in katello.
        https://projects.theforeman.org/issues/27575
        """

        _subscription_methods = self.foremanapi.apidoc['docs']['resources']['subscriptions']['methods']

        _subscription_index = next(x for x in _subscription_methods if x['name'] == 'index')
        _subscription_index_params_organization_id = next(x for x in _subscription_index['params'] if x['name'] == 'organization_id')
        _subscription_index_params_organization_id['required'] = False

    def _patch_sync_plan_api(self):
        """This is a workaround for the broken sync_plan apidoc in katello.
            see https://projects.theforeman.org/issues/27532
        """

        _organization_parameter = {
            u'validations': [],
            u'name': u'organization_id',
            u'show': True,
            u'description': u'\n<p>Filter sync plans by organization name or label</p>\n',
            u'required': False,
            u'allow_nil': False,
            u'allow_blank': False,
            u'full_name': u'organization_id',
            u'expected_type': u'numeric',
            u'metadata': None,
            u'validator': u'Must be a number.',
        }

        _sync_plan_methods = self.foremanapi.apidoc['docs']['resources']['sync_plans']['methods']

        _sync_plan_add_products = next(x for x in _sync_plan_methods if x['name'] == 'add_products')
        if next((x for x in _sync_plan_add_products['params'] if x['name'] == 'organization_id'), None) is None:
            _sync_plan_add_products['params'].append(_organization_parameter)

        _sync_plan_remove_products = next(x for x in _sync_plan_methods if x['name'] == 'remove_products')
        if next((x for x in _sync_plan_remove_products['params'] if x['name'] == 'organization_id'), None) is None:
            _sync_plan_remove_products['params'].append(_organization_parameter)


class ForemanAnsibleModule(AnsibleModule):

    def __init__(self, argument_spec, **kwargs):
        args = dict(
            server_url=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            validate_certs=dict(type='bool', default=True, aliases=['verify_ssl']),
        )
        args.update(argument_spec)
        supports_check_mode = kwargs.pop('supports_check_mode', True)
        self._aliases = {alias for arg in args.values() for alias in arg.get('aliases', [])}
        super(ForemanAnsibleModule, self).__init__(argument_spec=args, supports_check_mode=supports_check_mode, **kwargs)

        self._params = self.params.copy()

        self.check_requirements()

        self._foremanapi_server_url = self._params.pop('server_url')
        self._foremanapi_username = self._params.pop('username')
        self._foremanapi_password = self._params.pop('password')
        self._foremanapi_validate_certs = self._params.pop('validate_certs')
        if 'verify_ssl' in self._params:
            self.warn("Please use 'validate_certs' instead of deprecated 'verify_ssl'.")

        self.task_timeout = 60
        self.task_poll = 4

        self._thin_default = False
        self.state = 'undefined'
        self.entity_spec = {}

        self._before = defaultdict(list)
        self._after = defaultdict(list)
        self._after_full = defaultdict(list)

    def clean_params(self):
        return {k: v for (k, v) in self._params.items() if v is not None and k not in self._aliases}

    def _patch_location_api(self):
        """This is a workaround for the broken taxonomies apidoc in foreman.
            see https://projects.theforeman.org/issues/10359
        """

        _location_organizations_parameter = {
            u'validations': [],
            u'name': u'organization_ids',
            u'show': True,
            u'description': u'\n<p>Organization IDs</p>\n',
            u'required': False,
            u'allow_nil': True,
            u'allow_blank': False,
            u'full_name': u'location[organization_ids]',
            u'expected_type': u'array',
            u'metadata': None,
            u'validator': u'',
        }
        _location_methods = self.foremanapi.apidoc['docs']['resources']['locations']['methods']

        _location_create = next(x for x in _location_methods if x['name'] == 'create')
        _location_create_params_location = next(x for x in _location_create['params'] if x['name'] == 'location')
        _location_create_params_location['params'].append(_location_organizations_parameter)

        _location_update = next(x for x in _location_methods if x['name'] == 'update')
        _location_update_params_location = next(x for x in _location_update['params'] if x['name'] == 'location')
        _location_update_params_location['params'].append(_location_organizations_parameter)

    def _patch_subnet_rex_api(self):
        """This is a workaround for the broken subnet apidoc in foreman remote execution.
            see https://projects.theforeman.org/issues/19086
        """

        if 'remote_execution_features' not in self.foremanapi.apidoc['docs']['resources']:
            # the system has no foreman_remote_execution installed, no need to patch
            return

        _subnet_rex_proxies_parameter = {
            u'validations': [],
            u'name': u'remote_execution_proxy_ids',
            u'show': True,
            u'description': u'\n<p>Remote Execution Proxy IDs</p>\n',
            u'required': False,
            u'allow_nil': True,
            u'allow_blank': False,
            u'full_name': u'subnet[remote_execution_proxy_ids]',
            u'expected_type': u'array',
            u'metadata': None,
            u'validator': u'',
        }
        _subnet_methods = self.foremanapi.apidoc['docs']['resources']['subnets']['methods']

        _subnet_create = next(x for x in _subnet_methods if x['name'] == 'create')
        _subnet_create_params_subnet = next(x for x in _subnet_create['params'] if x['name'] == 'subnet')
        _subnet_create_params_subnet['params'].append(_subnet_rex_proxies_parameter)

        _subnet_update = next(x for x in _subnet_methods if x['name'] == 'update')
        _subnet_update_params_subnet = next(x for x in _subnet_update['params'] if x['name'] == 'subnet')
        _subnet_update_params_subnet['params'].append(_subnet_rex_proxies_parameter)

    def check_requirements(self):
        if not HAS_APYPIE:
            self.fail_json(msg='The apypie Python module is required', exception=APYPIE_IMP_ERR)

    @_exception2fail_json(msg="Failed to connect to Foreman server: %s ")
    def connect(self):
        self.foremanapi = apypie.Api(
            uri=self._foremanapi_server_url,
            username=self._foremanapi_username,
            password=self._foremanapi_password,
            api_version=2,
            verify_ssl=self._foremanapi_validate_certs,
        )

        self.ping()

        self._patch_location_api()
        self._patch_subnet_rex_api()

    @_exception2fail_json(msg="Failed to connect to Foreman server: %s ")
    def ping(self):
        return self.foremanapi.resource('home').call('status')

    @_exception2fail_json(msg='Failed to show resource: %s')
    def show_resource(self, resource, resource_id, params=None):
        if params is None:
            params = {}
        else:
            params = params.copy()

        params['id'] = resource_id

        params = self.foremanapi.resource(resource).action('show').prepare_params(params)

        return self.foremanapi.resource(resource).call('show', params)

    @_exception2fail_json(msg='Failed to list resource: %s')
    def list_resource(self, resource, search=None, params=None):
        if params is None:
            params = {}
        else:
            params = params.copy()

        if search is not None:
            params['search'] = search
        params['per_page'] = 2 << 31

        params = self.foremanapi.resource(resource).action('index').prepare_params(params)

        return self.foremanapi.resource(resource).call('index', params)['results']

    def find_resource(self, resource, search, name=None, params=None, failsafe=False, thin=None):
        list_params = {}
        if params is not None:
            list_params.update(params)
        if thin is None:
            thin = self._thin_default
        list_params['thin'] = thin
        results = self.list_resource(resource, search, list_params)
        if resource == 'snapshots':
            # Snapshots API does not do search
            snapshot = []
            for result in results:
                if result['name'] == name:
                    snapshot.append(result)
                    break
            results = snapshot
        if len(results) == 1:
            result = results[0]
        elif failsafe:
            result = None
        else:
            self.fail_json(msg="No data found for %s" % search)
        if result:
            if thin:
                result = {'id': result['id']}
            else:
                result = self.show_resource(resource, result['id'], params=params)
        return result

    def find_resource_by_name(self, resource, name, **kwargs):
        search = 'name="{0}"'.format(name)
        kwargs['name'] = name
        return self.find_resource(resource, search, **kwargs)

    def find_resource_by_title(self, resource, title, **kwargs):
        search = 'title="{0}"'.format(title)
        return self.find_resource(resource, search, **kwargs)

    def find_resource_by_id(self, resource, obj_id, **kwargs):
        search = 'id="{0}"'.format(obj_id)
        return self.find_resource(resource, search, **kwargs)

    def find_resources(self, resource, search_list, **kwargs):
        return [self.find_resource(resource, search_item, **kwargs) for search_item in search_list]

    def find_resources_by_name(self, resource, names, **kwargs):
        return [self.find_resource_by_name(resource, name, **kwargs) for name in names]

    def find_resources_by_title(self, resource, titles, **kwargs):
        return [self.find_resource_by_title(resource, title, **kwargs) for title in titles]

    def find_resources_by_id(self, resource, obj_ids, **kwargs):
        return [self.find_resource_by_id(resource, obj_id, **kwargs) for obj_id in obj_ids]

    def find_operatingsystem(self, name, params=None, failsafe=False, thin=None):
        result = self.find_resource_by_title('operatingsystems', name, params=params, failsafe=True, thin=thin)
        if not result:
            search = 'title~"{0}"'.format(name)
            result = self.find_resource('operatingsystems', search, params=params, failsafe=failsafe, thin=thin)
        return result

    def find_operatingsystems(self, names, **kwargs):
        return [self.find_operatingsystem(name, **kwargs) for name in names]

    def record_before(self, resource, entity):
        self._before[resource].append(entity)

    def record_after(self, resource, entity):
        self._after[resource].append(entity)

    def record_after_full(self, resource, entity):
        self._after_full[resource].append(entity)

    def ensure_entity_state(self, *args, **kwargs):
        changed, _entity = self.ensure_entity(*args, **kwargs)
        return changed

    @_exception2fail_json(msg='Failed to ensure entity state: %s')
    def ensure_entity(self, resource, desired_entity, current_entity, params=None, state=None, entity_spec=None, synchronous=True):
        """Ensure that a given entity has a certain state

            Parameters:
                resource (string): Plural name of the api resource to manipulate
                desired_entity (dict): Desired properties of the entity
                current_entity (dict, None): Current properties of the entity or None if nonexistent
                params (dict): Lookup parameters (i.e. parent_id for nested entities) (optional)
                state (dict): Desired state of the entity (optionally taken from the module)
                entity_spec (dict): Description of the entity structure (optionally taken from module)
            Return value:
                Pair of boolean indicating whether something changed and the new current state if the entity
        """
        if state is None:
            state = self.state
        if entity_spec is None:
            entity_spec = self.entity_spec
        else:
            entity_spec, _dummy = _entity_spec_helper(entity_spec)

        changed = False
        updated_entity = None

        self.record_before(resource, _flatten_entity(current_entity, entity_spec))

        if state == 'present_with_defaults':
            if current_entity is None:
                changed, updated_entity = self._create_entity(resource, desired_entity, params, entity_spec, synchronous)
        elif state == 'present':
            if current_entity is None:
                changed, updated_entity = self._create_entity(resource, desired_entity, params, entity_spec, synchronous)
            else:
                changed, updated_entity = self._update_entity(resource, desired_entity, current_entity, params, entity_spec, synchronous)
        elif state == 'copied':
            if current_entity is not None:
                changed, updated_entity = self._copy_entity(resource, desired_entity, current_entity, params, synchronous)
        elif state == 'reverted':
            if current_entity is not None:
                changed, updated_entity = self._revert_entity(resource, current_entity, params, synchronous)
        elif state == 'absent':
            if current_entity is not None:
                changed, updated_entity = self._delete_entity(resource, current_entity, params, synchronous)
        else:
            self.fail_json(msg='Not a valid state: {0}'.format(state))

        self.record_after(resource, _flatten_entity(updated_entity, entity_spec))
        self.record_after_full(resource, updated_entity)

        return changed, updated_entity

    def _create_entity(self, resource, desired_entity, params, entity_spec, synchronous):
        """Create entity with given properties

            Parameters:
                resource (string): Plural name of the api resource to manipulate
                desired_entity (dict): Desired properties of the entity
                params (dict): Lookup parameters (i.e. parent_id for nested entities) (optional)
                entity_spec (dict): Description of the entity structure
            Return value:
                Pair of boolean indicating whether something changed and the new current state if the entity
        """
        payload = _flatten_entity(desired_entity, entity_spec)
        if not self.check_mode:
            if params:
                payload.update(params)
            return self.resource_action(resource, 'create', payload, synchronous=synchronous)
        else:
            fake_entity = desired_entity.copy()
            fake_entity['id'] = -1
            return True, fake_entity

    def _update_entity(self, resource, desired_entity, current_entity, params, entity_spec, synchronous):
        """Update a given entity with given properties if any diverge

            Parameters:
                resource (string): Plural name of the api resource to manipulate
                desired_entity (dict): Desired properties of the entity
                current_entity (dict): Current properties of the entity
                params (dict): Lookup parameters (i.e. parent_id for nested entities) (optional)
                entity_spec (dict): Description of the entity structure
            Return value:
                Pair of boolean indicating whether something changed and the new current state if the entity
        """
        payload = {}
        desired_entity = _flatten_entity(desired_entity, entity_spec)
        current_entity = _flatten_entity(current_entity, entity_spec)
        for key, value in desired_entity.items():
            if current_entity.get(key) != value:
                payload[key] = value
        if payload:
            payload['id'] = current_entity['id']
            if not self.check_mode:
                if params:
                    payload.update(params)
                return self.resource_action(resource, 'update', payload, synchronous=synchronous)
            else:
                # In check_mode we emulate the server updating the entity
                fake_entity = current_entity.copy()
                fake_entity.update(payload)
                return True, fake_entity
        else:
            # Nothing needs changing
            return False, current_entity

    def _copy_entity(self, resource, desired_entity, current_entity, params, synchronous):
        """Copy a given entity

            Parameters:
                resource (string): Plural name of the api resource to manipulate
                current_entity (dict): Current properties of the entity
                params (dict): Lookup parameters (i.e. parent_id for nested entities) (optional)
            Return value:
                Pair of boolean indicating whether something changed and the new current state of the entity
        """
        payload = {
            'id': current_entity['id'],
            'new_name': desired_entity['new_name'],
        }
        if params:
            payload.update(params)
        return self.resource_action(resource, 'copy', payload, synchronous=synchronous)

    def _revert_entity(self, resource, current_entity, params, synchronous):
        """Revert a given entity

            Parameters:
                resource (string): Plural name of the api resource to manipulate
                current_entity (dict): Current properties of the entity
                params (dict): Lookup parameters (i.e. parent_id for nested entities) (optional)
            Return value:
                Pair of boolean indicating whether something changed and the new current state of the entity
        """
        payload = {'id': current_entity['id']}
        if params:
            payload.update(params)
        return self.resource_action(resource, 'revert', payload, synchronous=synchronous)

    def _delete_entity(self, resource, current_entity, params, synchronous):
        """Delete a given entity

            Parameters:
                resource (string): Plural name of the api resource to manipulate
                current_entity (dict): Current properties of the entity
                params (dict): Lookup parameters (i.e. parent_id for nested entities) (optional)
            Return value:
                Pair of boolean indicating whether something changed and the new current state of the entity
        """
        payload = {'id': current_entity['id']}
        if params:
            payload.update(params)
        changed, entity = self.resource_action(resource, 'destroy', payload, synchronous=synchronous)

        # this is a workaround for https://projects.theforeman.org/issues/26937
        if entity and 'error' in entity and 'message' in entity['error']:
            self.fail_json(msg=entity['error']['message'])

        return changed, None

    def resource_action(self, resource, action, params, options=None, data=None, files=None, synchronous=True, ignore_check_mode=False):
        resource_payload = self.foremanapi.resource(resource).action(action).prepare_params(params)
        if options is None:
            options = {}
        try:
            result = None
            if ignore_check_mode or not self.check_mode:
                result = self.foremanapi.resource(resource).call(action, resource_payload, options=options, data=data, files=files)
                is_foreman_task = isinstance(result, dict) and 'action' in result and 'state' in result and 'pending' in result
                if synchronous and is_foreman_task:
                    result = self.wait_for_task(result)
        except Exception as e:
            msg = 'Error while performing {0} on {1}: {2}'.format(
                action, resource, str(e))
            self.fail_from_exception(e, msg)
        return True, result

    def wait_for_task(self, task):
        duration = self.task_timeout
        while task['state'] not in ['paused', 'stopped']:
            duration -= self.task_poll
            if duration <= 0:
                self.fail_json(msg="Timout waiting for Task {0}".format(task['id']))
            time.sleep(self.task_poll)

            _task_changed, task = self.resource_action('foreman_tasks', 'show', {'id': task['id']}, synchronous=False)

        return task

    def fail_from_exception(self, exc, msg):
        fail = {'msg': msg}
        if isinstance(exc, requests.exceptions.HTTPError):
            try:
                response = exc.response.json()
                if 'error' in response:
                    fail['error'] = response['error']
                else:
                    fail['error'] = response
            except Exception:
                fail['error'] = exc.response.text
        self.fail_json(**fail)


class ForemanEntityAnsibleModule(ForemanAnsibleModule):

    def __init__(self, argument_spec=None, **kwargs):
        entity_spec, gen_args = _entity_spec_helper(kwargs.pop('entity_spec', {}))
        args = dict(
            state=dict(choices=['present', 'absent'], default='present'),
        )
        args.update(gen_args)
        if argument_spec is not None:
            args.update(argument_spec)
        super(ForemanEntityAnsibleModule, self).__init__(argument_spec=args, **kwargs)

        self.entity_spec = entity_spec
        self.state = self._params.pop('state')
        self.desired_absent = self.state == 'absent'
        self._thin_default = self.desired_absent

    def ensure_scoped_parameters(self, scope, entity, parameters):
        changed = False
        if parameters is not None:
            if self.state == 'present' or (self.state == 'present_with_defaults' and entity is None):
                if entity:
                    current_parameters = {parameter['name']: parameter for parameter in self.list_resource('parameters', params=scope)}
                else:
                    current_parameters = {}
                desired_parameters = {parameter['name']: parameter for parameter in parameters}

                for name in desired_parameters:
                    desired_parameter = desired_parameters[name]
                    desired_parameter['value'] = parameter_value_to_str(desired_parameter['value'], desired_parameter['parameter_type'])
                    current_parameter = current_parameters.pop(name, None)
                    if current_parameter:
                        if 'parameter_type' not in current_parameter:
                            current_parameter['parameter_type'] = 'string'
                        current_parameter['value'] = parameter_value_to_str(current_parameter['value'], current_parameter['parameter_type'])
                    changed |= self.ensure_entity_state(
                        'parameters', desired_parameter, current_parameter, state="present", entity_spec=parameter_entity_spec, params=scope)
                for current_parameter in current_parameters.values():
                    changed |= self.ensure_entity_state(
                        'parameters', None, current_parameter, state="absent", entity_spec=parameter_entity_spec, params=scope)
        return changed

    def exit_json(self, **kwargs):
        if 'diff' not in kwargs:
            kwargs['diff'] = {'before': self._before,
                              'after': self._after}
        if 'entity' not in kwargs:
            kwargs['entity'] = self._after_full
        super(ForemanEntityAnsibleModule, self).exit_json(**kwargs)


class KatelloAnsibleModule(KatelloMixin, ForemanAnsibleModule):
    pass


class KatelloEntityAnsibleModule(KatelloMixin, ForemanEntityAnsibleModule):
    pass


def _entity_spec_helper(spec):
    """Extend an entity spec by adding entries for all flat_names.
    Extract ansible compatible argument_spec on the way.
    """
    entity_spec = {'id': {}}
    argument_spec = {}
    for key, value in spec.items():
        entity_value = {}
        argument_value = value.copy()
        if 'flat_name' in argument_value:
            flat_name = argument_value.pop('flat_name')
            entity_value['flat_name'] = flat_name
            entity_spec[flat_name] = {}

        if argument_value.get('type') == 'entity':
            entity_value['type'] = argument_value.pop('type')
        elif argument_value.get('type') == 'entity_list':
            argument_value['type'] = 'list'
            entity_value['type'] = 'entity_list'
        elif argument_value.get('type') == 'nested_list':
            argument_value['type'] = 'list'
            argument_value['elements'] = 'dict'
            _dummy, argument_value['options'] = _entity_spec_helper(argument_value.pop('entity_spec'))
            entity_value = None
        if entity_value is not None:
            entity_spec[key] = entity_value
        if argument_value.get('type') != 'invisible':
            argument_spec[key] = argument_value

    return entity_spec, argument_spec


def _flatten_entity(entity, entity_spec):
    """Flatten entity according to spec"""
    result = {}
    if entity is None:
        entity = {}
    for key, value in entity.items():
        if key in entity_spec and value is not None:
            spec = entity_spec[key]
            flat_name = spec.get('flat_name', key)
            property_type = spec.get('type', 'str')
            if property_type == 'entity':
                result[flat_name] = value['id']
            elif property_type == 'entity_list':
                result[flat_name] = sorted(val['id'] for val in value)
            else:
                result[flat_name] = value
    return result


# Helper for (global, operatingsystem, ...) parameters
def parameter_value_to_str(value, parameter_type):
    """Helper to convert the value of parameters to string according to their parameter_type."""
    if parameter_type in ['real', 'integer']:
        parameter_string = str(value)
    elif parameter_type in ['array', 'hash', 'yaml', 'json']:
        parameter_string = json.dumps(value, sort_keys=True)
    else:
        parameter_string = value
    return parameter_string


# Helper for templates
def parse_template(template_content, module):
    if not HAS_PYYAML:
        module.fail_json(msg='The PyYAML Python module is required', exception=PYYAML_IMP_ERR)

    try:
        template_dict = {}
        data = re.search(
            r'<%#([^%]*([^%]*%*[^>%])*%*)%>', template_content)
        if data:
            datalist = data.group(1)
            if datalist[-1] == '-':
                datalist = datalist[:-1]
            template_dict = yaml.safe_load(datalist)
        # No metadata, import template anyway
        template_dict['template'] = template_content
    except Exception as e:
        module.fail_json(msg='Error while parsing template: ' + str(e))
    return template_dict


def parse_template_from_file(file_name, module):
    try:
        with open(file_name) as input_file:
            template_content = input_file.read()
            template_dict = parse_template(template_content, module)
    except Exception as e:
        module.fail_json(msg='Error while reading template file: ' + str(e))
    return template_dict


# Helper for titles
def split_fqn(title):
    """ Split fully qualified name (title) in name and parent title """
    fqn = title.split('/')
    if len(fqn) > 1:
        name = fqn.pop()
        return (name, '/'.join(fqn))
    else:
        return (title, None)


def build_fqn(name, parent=None):
    if parent:
        return "%s/%s" % (parent, name)
    else:
        return name


# Helper constants
OS_LIST = ['AIX',
           'Altlinux',
           'Archlinux',
           'Coreos',
           'Debian',
           'Freebsd',
           'Gentoo',
           'Junos',
           'NXOS',
           'Rancheros',
           'Redhat',
           'Solaris',
           'Suse',
           'Windows',
           'Xenserver',
           ]
