# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

CLOUD_PROVIDERS = ('azure', 'azure_rm', 'ec2', 'gce', 'rax', 'vmware', 'openstack', 'foreman', 'cloudforms')
SCHEDULEABLE_PROVIDERS = CLOUD_PROVIDERS + ('custom',)
