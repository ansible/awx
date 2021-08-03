#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2018, Samuel Carpentier <samuelcarpentier0@gmail.ca>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ['preview'], 'supported_by': 'community'}


DOCUMENTATION = '''
---
module: notification_template
author: "Samuel Carpentier (@samcarpentier)"
short_description: create, update, or destroy Automation Platform Controller notification.
description:
    - Create, update, or destroy Automation Platform Controller notifications. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name of the notification.
      type: str
      required: True
    new_name:
      description:
        - Setting this option will change the existing name (looked up via the name field.
      type: str
    copy_from:
      description:
        - Name or id to copy the notification from.
        - This will copy an existing notification and change any parameters supplied.
        - The new notification name will be the one provided in the name parameter.
        - The organization parameter is not used in this, to facilitate copy from one organization to another.
        - Provide the id or use the lookup plugin to provide the id if multiple notifications share the same name.
      type: str
    description:
      description:
        - The description of the notification.
      type: str
    organization:
      description:
        - The organization the notification belongs to.
      type: str
    notification_type:
      description:
        - The type of notification to be sent.
      choices:
        - 'email'
        - 'grafana'
        - 'irc'
        - 'mattermost'
        - 'pagerduty'
        - 'rocketchat'
        - 'slack'
        - 'twilio'
        - 'webhook'
      type: str
    notification_configuration:
      description:
        - The notification configuration file. Note providing this field would disable all notification-configuration-related fields.
        - username (the mail server username)
        - sender (the sender email address)
        - recipients (the recipients email addresses)
        - use_tls (the TLS trigger)
        - host (the mail server host)
        - use_ssl (the SSL trigger)
        - password (the mail server password)
        - port (the mail server port)
        - channels (the destination Slack channels)
        - token (the access token)
        - account_token (the Twillio account token)
        - from_number (the source phone number)
        - to_numbers (the destination phone numbers)
        - account_sid (the Twillio account SID)
        - subdomain (the PagerDuty subdomain)
        - service_key (the PagerDuty service/integration API key)
        - client_name (the PagerDuty client identifier)
        - message_from (the label to be shown with the notification)
        - color (the notification color)
        - notify (the notify channel trigger)
        - url (the target URL)
        - headers (the HTTP headers as JSON string)
        - server (the IRC server address)
        - nickname (the IRC nickname)
        - targets (the destination channels or users)
      type: dict
    messages:
      description:
        - Optional custom messages for notification template.
      type: dict
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
      type: str
extends_documentation_fragment: awx.awx.auth
'''


EXAMPLES = '''
- name: Add Slack notification with custom messages
  notification_template:
    name: slack notification
    organization: Default
    notification_type: slack
    notification_configuration:
      channels:
        - general
      token: cefda9e2be1f21d11cdd9452f5b7f97fda977f42
    messages:
       started:
         message: "{{ '{{ job_friendly_name }}{{ job.id }} started' }}"
       success:
         message: "{{ '{{ job_friendly_name }} completed in {{ job.elapsed }} seconds' }}"
       error:
         message: "{{ '{{ job_friendly_name }} FAILED! Please look at {{ job.url }}' }}"
    state: present
    controller_config_file: "~/tower_cli.cfg"

- name: Add webhook notification
  notification_template:
    name: webhook notification
    notification_type: webhook
    notification_configuration:
      url: http://www.example.com/hook
      headers:
        X-Custom-Header: value123
    state: present
    controller_config_file: "~/tower_cli.cfg"

- name: Add email notification
  notification_template:
    name: email notification
    notification_type: email
    notification_configuration:
      username: user
      password: s3cr3t
      sender: controller@example.com
      recipients:
        - user1@example.com
      host: smtp.example.com
      port: 25
      use_tls: no
      use_ssl: no
    state: present
    controller_config_file: "~/tower_cli.cfg"

- name: Add twilio notification
  notification_template:
    name: twilio notification
    notification_type: twilio
    notification_configuration:
      account_token: a_token
      account_sid: a_sid
      from_number: '+15551112222'
      to_numbers:
        - '+15553334444'
    state: present
    controller_config_file: "~/tower_cli.cfg"

- name: Add PagerDuty notification
  notification_template:
    name: pagerduty notification
    notification_type: pagerduty
    notification_configuration:
      token: a_token
      subdomain: sub
      client_name: client
      service_key: a_key
    state: present
    controller_config_file: "~/tower_cli.cfg"

- name: Add IRC notification
  notification_template:
    name: irc notification
    notification_type: irc
    notification_configuration:
      nickname: controller
      password: s3cr3t
      targets:
        - user1
      port: 8080
      server: irc.example.com
      use_ssl: no
    state: present
    controller_config_file: "~/tower_cli.cfg"

- name: Delete notification
  notification_template:
    name: old notification
    state: absent
    controller_config_file: "~/tower_cli.cfg"

- name: Copy webhook notification
  notification_template:
    name: foo notification
    copy_from: email notification
    organization: Foo
'''


RETURN = ''' # '''


from ..module_utils.controller_api import ControllerAPIModule


def main():
    # Any additional arguments that are not fields of the item can be added here
    argument_spec = dict(
        name=dict(required=True),
        new_name=dict(),
        copy_from=dict(),
        description=dict(),
        organization=dict(),
        notification_type=dict(choices=['email', 'grafana', 'irc', 'mattermost', 'pagerduty', 'rocketchat', 'slack', 'twilio', 'webhook']),
        notification_configuration=dict(type='dict'),
        messages=dict(type='dict'),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    # Create a module for ourselves
    module = ControllerAPIModule(argument_spec=argument_spec)

    # Extract our parameters
    name = module.params.get('name')
    new_name = module.params.get('new_name')
    copy_from = module.params.get('copy_from')
    description = module.params.get('description')
    organization = module.params.get('organization')
    notification_type = module.params.get('notification_type')
    notification_configuration = module.params.get('notification_configuration')
    messages = module.params.get('messages')
    state = module.params.get('state')

    # Attempt to look up the related items the user specified (these will fail the module if not found)
    organization_id = None
    if organization:
        organization_id = module.resolve_name_to_id('organizations', organization)

    # Attempt to look up an existing item based on the provided data
    existing_item = module.get_one(
        'notification_templates',
        name_or_id=name,
        **{
            'data': {
                'organization': organization_id,
            }
        }
    )

    # Attempt to look up credential to copy based on the provided name
    if copy_from:
        # a new existing item is formed when copying and is returned.
        existing_item = module.copy_item(
            existing_item,
            copy_from,
            name,
            endpoint='notification_templates',
            item_type='notification_template',
            copy_lookup_data={},
        )

    if state == 'absent':
        # If the state was absent we can let the module delete it if needed, the module will handle exiting from this
        module.delete_if_needed(existing_item)

    final_notification_configuration = {}
    if notification_configuration is not None:
        final_notification_configuration.update(notification_configuration)

    # Create the data that gets sent for create and update
    new_fields = {}
    if final_notification_configuration:
        new_fields['notification_configuration'] = final_notification_configuration
    new_fields['name'] = new_name if new_name else (module.get_item_name(existing_item) if existing_item else name)
    if description is not None:
        new_fields['description'] = description
    if organization is not None:
        new_fields['organization'] = organization_id
    if notification_type is not None:
        new_fields['notification_type'] = notification_type
    if messages is not None:
        new_fields['messages'] = messages

    # If the state was present and we can let the module build or update the existing item, this will return on its own
    module.create_or_update_if_needed(existing_item, new_fields, endpoint='notification_templates', item_type='notification_template', associations={})


if __name__ == '__main__':
    main()
