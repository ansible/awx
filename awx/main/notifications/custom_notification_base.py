# Copyright (c) 2019 Ansible, Inc.
# All Rights Reserved.


class CustomNotificationBase(object):
    DEFAULT_MSG = "{{ job_friendly_name }} #{{ job.id }} '{{ job.name }}' {{ job.status }}: {{ url }}"
    DEFAULT_BODY = "{{ job_friendly_name }} #{{ job.id }} had status {{ job.status }}, view details at {{ url }}\n\n{{ job_metadata }}"

    DEFAULT_APPROVAL_RUNNING_MSG = 'The approval node "{{ approval_node_name }}" needs review. This node can be viewed at: {{ workflow_url }}'
    DEFAULT_APPROVAL_RUNNING_BODY = ('The approval node "{{ approval_node_name }}" needs review. '
                                     'This approval node can be viewed at: {{ workflow_url }}\n\n{{ job_metadata }}')

    DEFAULT_APPROVAL_APPROVED_MSG = 'The approval node "{{ approval_node_name }}" was approved. {{ workflow_url }}'
    DEFAULT_APPROVAL_APPROVED_BODY = 'The approval node "{{ approval_node_name }}" was approved. {{ workflow_url }}\n\n{{ job_metadata }}'

    DEFAULT_APPROVAL_TIMEOUT_MSG = 'The approval node "{{ approval_node_name }}" has timed out. {{ workflow_url }}'
    DEFAULT_APPROVAL_TIMEOUT_BODY = 'The approval node "{{ approval_node_name }}" has timed out. {{ workflow_url }}\n\n{{ job_metadata }}'

    DEFAULT_APPROVAL_DENIED_MSG = 'The approval node "{{ approval_node_name }}" was denied. {{ workflow_url }}'
    DEFAULT_APPROVAL_DENIED_BODY = 'The approval node "{{ approval_node_name }}" was denied. {{ workflow_url }}\n\n{{ job_metadata }}'


    default_messages = {"started": {"message": DEFAULT_MSG, "body": None},
                        "success": {"message": DEFAULT_MSG, "body": None},
                        "error": {"message": DEFAULT_MSG, "body": None},
                        "workflow_approval": {"running": {"message": DEFAULT_APPROVAL_RUNNING_MSG, "body": None},
                                              "approved": {"message": DEFAULT_APPROVAL_APPROVED_MSG, "body": None},
                                              "timed_out": {"message": DEFAULT_APPROVAL_TIMEOUT_MSG, "body": None},
                                              "denied": {"message": DEFAULT_APPROVAL_DENIED_MSG, "body": None}}}
