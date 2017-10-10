from __future__ import print_function
# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand
from crum import impersonate
from awx.main.models import User, Organization, Project, Inventory, CredentialType, Credential, Host, JobTemplate


class Command(BaseCommand):
    """Create preloaded data, intended for new installs
    """
    help = 'Creates a preload tower data iff there is none.'

    def handle(self, *args, **kwargs):
        # Sanity check: Is there already an organization in the system?
        if Organization.objects.count():
            return

        # Create a default organization as the first superuser found.
        try:
            superuser = User.objects.filter(is_superuser=True).order_by('pk')[0]
        except IndexError:
            superuser = None
        with impersonate(superuser):
            o = Organization.objects.create(name='Default')
            p = Project(name='Demo Project',
                        scm_type='git',
                        scm_url='https://github.com/ansible/ansible-tower-samples',
                        scm_update_on_launch=True,
                        scm_update_cache_timeout=0,
                        organization=o)
            p.save(skip_update=True)
            ssh_type = CredentialType.from_v1_kind('ssh')
            c = Credential.objects.create(credential_type=ssh_type,
                                          name='Demo Credential',
                                          inputs={
                                              'username': superuser.username
                                          },
                                          created_by=superuser)
            c.admin_role.members.add(superuser)
            i = Inventory.objects.create(name='Demo Inventory',
                                         organization=o,
                                         created_by=superuser)
            Host.objects.create(name='localhost',
                                inventory=i,
                                variables="ansible_connection: local",
                                created_by=superuser)
            JobTemplate.objects.create(name='Demo Job Template',
                                       playbook='hello_world.yml',
                                       project=p,
                                       inventory=i,
                                       credential=c)
        print('Default organization added.')
        print('Demo Credential, Inventory, and Job Template added.')
