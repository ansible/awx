from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule, env_fallback
from .tower_connector import TowerConnector, AnsibleTowerException


class TowerModule(AnsibleModule):
    ENCRYPTED_STRING = "$encrypted$"
    tower_connector = None

    def __init__(self, argument_spec, **kwargs):
        args = dict(
            tower_host=dict(required=False, fallback=(env_fallback, ['TOWER_HOST'])),
            tower_username=dict(required=False, fallback=(env_fallback, ['TOWER_USERNAME'])),
            tower_password=dict(no_log=True, required=False, fallback=(env_fallback, ['TOWER_PASSWORD'])),
            validate_certs=dict(type='bool', aliases=['tower_verify_ssl'], required=False,
                                fallback=(env_fallback, ['TOWER_VERIFY_SSL'])),
            tower_oauthtoken=dict(type='str', no_log=True, required=False,
                                  fallback=(env_fallback, ['TOWER_OAUTH_TOKEN'])),
            tower_config_file=dict(type='path', required=False, default=None),
        )
        args.update(argument_spec)
        kwargs['supports_check_mode'] = True

        self.json_output = {'changed': False}

        super(TowerModule, self).__init__(argument_spec=args, **kwargs)

        try:
            self.tower_connector = TowerConnector(**{
                'host': self.params.get('tower_host'),
                'username': self.params.get('tower_username'),
                'password': self.params.get('tower_password'),
                'verify_ssl': self.params.get('validate_certs'),
                'oauth_token': self.params.get('tower_oauthtoken'),
                'warning_method': self.warn,
                'tower_config_file': self.params.get('tower_config_file')
            })
        except AnsibleTowerException as ate:
            self.exit_tower_exception(ate)

    @staticmethod
    def param_to_endpoint(name):
        exceptions = {
            'inventory': 'inventories',
            'target_team': 'teams',
            'workflow': 'workflow_job_templates'
        }
        return exceptions.get(name, '{0}s'.format(name))

    def head_endpoint(self, endpoint, *args, **kwargs):
        try:
            return self.tower_connector.make_request('HEAD', endpoint, **kwargs)
        except AnsibleTowerException as ate:
            self.exit_tower_exception(ate)

    def get_endpoint(self, endpoint, *args, **kwargs):
        try:
            return self.tower_connector.make_request('GET', endpoint, **kwargs)
        except AnsibleTowerException as ate:
            self.exit_tower_exception(ate)

    def patch_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output['changed'] = True
            self.exit_json(**self.json_output)

        try:
            return self.tower_connector.make_request('PATCH', endpoint, **kwargs)
        except AnsibleTowerException as ate:
            self.exit_tower_exception(ate)

    def post_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output['changed'] = True
            self.exit_json(**self.json_output)

        try:
            return self.tower_connector.make_request('POST', endpoint, **kwargs)
        except AnsibleTowerException as ate:
            self.exit_tower_exception(ate)

    def delete_endpoint(self, endpoint, *args, **kwargs):
        # Handle check mode
        if self.check_mode:
            self.json_output['changed'] = True
            self.exit_json(**self.json_output)

        try:
            return self.tower_connector.make_request('DELETE', endpoint, **kwargs)
        except AnsibleTowerException as ate:
            self.exit_tower_exception(ate)

    def get_all_endpoint(self, endpoint, *args, **kwargs):
        response = self.get_endpoint(endpoint, *args, **kwargs)
        if 'next' not in response['json']:
            raise RuntimeError('Expected list from API at {0}, got: {1}'.format(endpoint, response))
        next_page = response['json']['next']

        if response['json']['count'] > 10000:
            self.fail_json(msg='The number of items being queried for is higher than 10,000.')

        while next_page is not None:
            next_response = self.get_endpoint(next_page)
            response['json']['results'] = response['json']['results'] + next_response['json']['results']
            next_page = next_response['json']['next']
            response['json']['next'] = next_page
        return response

    def get_one(self, endpoint, *args, **kwargs):
        response = self.get_endpoint(endpoint, *args, **kwargs)
        if response['status_code'] != 200:
            fail_msg = "Got a {0} response when trying to get one from {1}".format(response['status_code'], endpoint)
            if 'detail' in response.get('json', {}):
                fail_msg += ', detail: {0}'.format(response['json']['detail'])
            self.fail_json(msg=fail_msg)

        if 'count' not in response['json'] or 'results' not in response['json']:
            self.fail_json(msg="The endpoint did not provide count and results")

        if response['json']['count'] == 0:
            return None
        elif response['json']['count'] > 1:
            self.fail_json(
                msg="An unexpected number of items was returned from the API ({0})".format(response['json']['count']))

        return response['json']['results'][0]

    def resolve_name_to_id(self, endpoint, name_or_id):
        # Try to resolve the object by name
        name_field = 'name'
        if endpoint == 'users':
            name_field = 'username'

        response = self.get_endpoint(endpoint, **{'data': {name_field: name_or_id}})
        if response['status_code'] == 400:
            self.fail_json(msg="Unable to try and resolve {0} for {1} : {2}".format(endpoint, name_or_id,
                                                                                    response['json']['detail']))

        if response['json']['count'] == 1:
            return response['json']['results'][0]['id']
        elif response['json']['count'] == 0:
            try:
                int(name_or_id)
                # If we got 0 items by name, maybe they gave us an ID, let's try looking it up by ID
                response = self.head_endpoint("{0}/{1}".format(endpoint, name_or_id), **{'return_none_on_404': True})
                if response is not None:
                    return name_or_id
            except ValueError:
                # If we got a value error than we didn't have an integer so we can just pass and fall down to the fail
                pass

            self.fail_json(msg="The {0} {1} was not found on the Tower server".format(endpoint, name_or_id))
        else:
            self.fail_json(
                msg="Found too many names {0} at endpoint {1} try using an ID instead of a name".format(name_or_id,
                                                                                                        endpoint))

    def default_check_mode(self):
        '''Execute check mode logic for Ansible Tower modules'''
        if self.check_mode:
            try:
                result = self.get_endpoint('ping')
                self.exit_json(**{'changed': True, 'tower_version': '{0}'.format(result['json']['version'])})
            except(Exception) as excinfo:
                self.fail_json(changed=False, msg='Failed check mode: {0}'.format(excinfo))

    def delete_if_needed(self, existing_item, on_delete=None):
        # This will exit from the module on its own.
        # If the method successfully deletes an item and on_delete param is defined,
        #   the on_delete parameter will be called as a method pasing in this object and the json from the response
        # This will return one of two things:
        #   1. None if the existing_item is not defined (so no delete needs to happen)
        #   2. The response from Tower from calling the delete on the endpont. It's up to you to process the response and exit from the module
        # Note: common error codes from the Tower API can cause the module to fail
        if existing_item:
            # If we have an item, we can try to delete it
            try:
                item_url = existing_item['url']
                item_type = existing_item['type']
                item_id = existing_item['id']
            except KeyError as ke:
                self.fail_json(msg="Unable to process delete of item due to missing data {0}".format(ke))

            if 'name' in existing_item:
                item_name = existing_item['name']
            elif 'username' in existing_item:
                item_name = existing_item['username']
            else:
                self.fail_json(msg="Unable to process delete of {0} due to missing name".format(item_type))

            response = self.delete_endpoint(item_url)

            if response['status_code'] in [202, 204]:
                if on_delete:
                    on_delete(self, response['json'])
                self.json_output['changed'] = True
                self.json_output['id'] = item_id
                self.exit_json(**self.json_output)
            else:
                if 'json' in response and '__all__' in response['json']:
                    self.fail_json(msg="Unable to delete {0} {1}: {2}".format(item_type, item_name,
                                                                              response['json']['__all__'][0]))
                elif 'json' in response:
                    # This is from a project delete (if there is an active job against it)
                    if 'error' in response['json']:
                        self.fail_json(
                            msg="Unable to delete {0} {1}: {2}".format(item_type, item_name, response['json']['error']))
                    else:
                        self.fail_json(
                            msg="Unable to delete {0} {1}: {2}".format(item_type, item_name, response['json']))
                else:
                    self.fail_json(
                        msg="Unable to delete {0} {1}: {2}".format(item_type, item_name, response['status_code']))
        else:
            self.exit_json(**self.json_output)

    def modify_associations(self, association_endpoint, new_association_list):
        # if we got None instead of [] we are not modifying the association_list
        if new_association_list is None:
            return

        # First get the existing associations
        response = self.get_all_endpoint(association_endpoint)
        existing_associated_ids = [association['id'] for association in response['json']['results']]

        # Disassociate anything that is in existing_associated_ids but not in new_association_list
        ids_to_remove = list(set(existing_associated_ids) - set(new_association_list))
        for an_id in ids_to_remove:
            response = self.post_endpoint(association_endpoint, **{'data': {'id': int(an_id), 'disassociate': True}})
            if response['status_code'] == 204:
                self.json_output['changed'] = True
            else:
                self.fail_json(msg="Failed to disassociate item {0}".format(response['json']['detail']))

        # Associate anything that is in new_association_list but not in `association`
        for an_id in list(set(new_association_list) - set(existing_associated_ids)):
            response = self.post_endpoint(association_endpoint, **{'data': {'id': int(an_id)}})
            if response['status_code'] == 204:
                self.json_output['changed'] = True
            else:
                self.fail_json(msg="Failed to associate item {0}".format(response['json']['detail']))

    def create_if_needed(self, existing_item, new_item, endpoint, on_create=None, item_type='unknown',
                         associations=None):

        # This will exit from the module on its own
        # If the method successfully creates an item and on_create param is defined,
        #    the on_create parameter will be called as a method pasing in this object and the json from the response
        # This will return one of two things:
        #    1. None if the existing_item is already defined (so no create needs to happen)
        #    2. The response from Tower from calling the patch on the endpont. It's up to you to process the response and exit from the module
        # Note: common error codes from the Tower API can cause the module to fail

        if not endpoint:
            self.fail_json(msg="Unable to create new {0} due to missing endpoint".format(item_type))

        item_url = None
        if existing_item:
            try:
                item_url = existing_item['url']
            except KeyError as ke:
                self.fail_json(msg="Unable to process create of item due to missing data {0}".format(ke))
        else:
            # If we don't have an exisitng_item, we can try to create it

            # We have to rely on item_type being passed in since we don't have an existing item that declares its type
            # We will pull the item_name out from the new_item, if it exists
            for key in ('name', 'username', 'identifier', 'hostname'):
                if key in new_item:
                    item_name = new_item[key]
                    break
            else:
                item_name = 'unknown'

            response = self.post_endpoint(endpoint, **{'data': new_item})
            if response['status_code'] == 201:
                self.json_output['name'] = 'unknown'
                for key in ('name', 'username', 'identifier', 'hostname'):
                    if key in response['json']:
                        self.json_output['name'] = response['json'][key]
                self.json_output['id'] = response['json']['id']
                self.json_output['changed'] = True
                item_url = response['json']['url']
            else:
                if 'json' in response and '__all__' in response['json']:
                    self.fail_json(msg="Unable to create {0} {1}: {2}".format(item_type, item_name,
                                                                              response['json']['__all__'][0]))
                elif 'json' in response:
                    self.fail_json(msg="Unable to create {0} {1}: {2}".format(item_type, item_name, response['json']))
                else:
                    self.fail_json(
                        msg="Unable to create {0} {1}: {2}".format(item_type, item_name, response['status_code']))

        # Process any associations with this item
        if associations is not None:
            for association_type in associations:
                sub_endpoint = '{0}{1}/'.format(item_url, association_type)
                self.modify_associations(sub_endpoint, associations[association_type])

        # If we have an on_create method and we actually changed something we can call on_create
        if on_create is not None and self.json_output['changed']:
            on_create(self, response['json'])
        else:
            self.exit_json(**self.json_output)

    def _encrypted_changed_warning(self, field, old, warning=False):
        if not warning:
            return
        self.warn(
            'The field {0} of {1} {2} has encrypted data and may inaccurately report task is changed.'.format(
                field, old.get('type', 'unknown'), old.get('id', 'unknown')
            ))

    @staticmethod
    def has_encrypted_values(obj):
        """Returns True if JSON-like python content in obj has $encrypted$
        anywhere in the data as a value
        """
        if isinstance(obj, dict):
            for val in obj.values():
                if TowerModule.has_encrypted_values(val):
                    return True
        elif isinstance(obj, list):
            for val in obj:
                if TowerModule.has_encrypted_values(val):
                    return True
        elif obj == TowerModule.ENCRYPTED_STRING:
            return True
        return False

    def objects_could_be_different(self, old, new, field_set=None, warning=False):
        if field_set is None:
            field_set = set(fd for fd in new.keys() if fd not in ('modified', 'related', 'summary_fields'))
        for field in field_set:
            new_field = new.get(field, None)
            old_field = old.get(field, None)
            if old_field != new_field:
                return True  # Something doesn't match
            elif self.has_encrypted_values(new_field) or field not in new:
                # case of 'field not in new' - user password write-only field that API will not display
                self._encrypted_changed_warning(field, old, warning=warning)
                return True
        return False

    def update_if_needed(self, existing_item, new_item, on_update=None, associations=None):
        # This will exit from the module on its own
        # If the method successfully updates an item and on_update param is defined,
        #   the on_update parameter will be called as a method pasing in this object and the json from the response
        # This will return one of three things:
        #    1. None if the existing_item does not need to be updated
        #    2. The response from Tower from patching to the endpoint. It's up to you to process the response and exit from the module.
        #    3. An ItemNotDefined exception, if the existing_item does not exist
        # Note: common error codes from the Tower API can cause the module to fail
        response = None
        if existing_item:

            # If we have an item, we can see if it needs an update
            try:
                item_url = existing_item['url']
                item_type = existing_item['type']
                if item_type == 'user':
                    item_name = existing_item['username']
                elif item_type == 'workflow_job_template_node':
                    item_name = existing_item['identifier']
                else:
                    item_name = existing_item['name']
                item_id = existing_item['id']
            except KeyError as ke:
                self.fail_json(msg="Unable to process update of item due to missing data {0}".format(ke))

            # Check to see if anything within the item requires the item to be updated
            needs_patch = self.objects_could_be_different(existing_item, new_item)

            # If we decided the item needs to be updated, update it
            self.json_output['id'] = item_id
            if needs_patch:
                response = self.patch_endpoint(item_url, **{'data': new_item})
                if response['status_code'] == 200:
                    # compare apples-to-apples, old API data to new API data
                    # but do so considering the fields given in parameters
                    self.json_output['changed'] = self.objects_could_be_different(
                        existing_item, response['json'], field_set=new_item.keys(), warning=True)
                elif 'json' in response and '__all__' in response['json']:
                    self.fail_json(msg=response['json']['__all__'])
                else:
                    self.fail_json(**{'msg': "Unable to update {0} {1}, see response".format(item_type, item_name),
                                      'response': response})

        else:
            raise RuntimeError('update_if_needed called incorrectly without existing_item')

        # Process any associations with this item
        if associations is not None:
            for association_type, id_list in associations.items():
                endpoint = '{0}{1}/'.format(item_url, association_type)
                self.modify_associations(endpoint, id_list)

        # If we change something and have an on_change call it
        if on_update is not None and self.json_output['changed']:
            if response is None:
                last_data = existing_item
            else:
                last_data = response['json']
            on_update(self, last_data)
        else:
            self.exit_json(**self.json_output)

    def create_or_update_if_needed(self, existing_item, new_item, endpoint=None, item_type='unknown', on_create=None,
                                   on_update=None, associations=None):
        if existing_item:
            return self.update_if_needed(existing_item, new_item, on_update=on_update, associations=associations)
        else:
            return self.create_if_needed(existing_item, new_item, endpoint, on_create=on_create, item_type=item_type,
                                         associations=associations)

    def exit_tower_exception(self, tower_exception):
        response_data = {}
        if tower_exception.response:
            response_data['response'] = tower_exception.response
        self.fail_json(msg=tower_exception.message, **response_data)

    def fail_json(self, **kwargs):
        # Try to log out if we are authenticated
        if self.tower_connector:
            self.tower_connector.logout()
        super(TowerModule, self).fail_json(**kwargs)

    def exit_json(self, **kwargs):
        # Try to log out if we are authenticated
        if self.tower_connector:
            self.tower_connector.logout()
        super(TowerModule, self).exit_json(**kwargs)

    def is_job_done(self, job_status):
        if job_status in ['new', 'pending', 'waiting', 'running']:
            return False
        else:
            return True
