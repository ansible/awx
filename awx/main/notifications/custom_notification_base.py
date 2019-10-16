# Copyright (c) 2019 Ansible, Inc.
# All Rights Reserved.

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _


class CustomNotificationBase(object):
    DEFAULT_MSG = "{{ job_friendly_name }} #{{ job.id }} '{{ job.name }}' {{ job.status }}: {{ url }}"
    DEFAULT_BODY = smart_text(_("{{ job_friendly_name }} #{{ job.id }} had status {{ job.status }}, view details at {{ url }}\n\n{{ job_summary_dict }}"))

    default_messages = {"started": {"message": DEFAULT_MSG, "body": None},
                        "success": {"message": DEFAULT_MSG, "body": None},
                        "error": {"message": DEFAULT_MSG, "body": None},
                        "workflow_approval": {"running": {"message": 'The approval node "{{ approval_node_name }}" needs review. '
                                                                     'This node can be viewed at: {{ workflow_url }}',
                                                                     "body": None},
                                              "approved": {"message": 'The approval node "{{ approval_node_name }}" was approved. {{ workflow_url }}',
                                                           "body": None},
                                              "timed_out": {"message": 'The approval node "{{ approval_node_name }}" has timed out. {{ workflow_url }}',
                                                            "body": None},
                                              "denied": {"message": 'The approval node "{{ approval_node_name }}" was denied. {{ workflow_url }}',
                                                         "body": None}}}
