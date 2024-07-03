# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.


from awx.settings.application_name import set_application_name
from django.conf import settings


def set_connection_name(function):
    set_application_name(settings.DATABASES, settings.CLUSTER_HOST_ID, function=function)
