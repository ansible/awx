# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand
from django.conf import settings
from crum import impersonate
from awx.main.models import (
    User, Organization, Project, Inventory, CredentialType,
    Credential, Host, JobTemplate, ExecutionEnvironment
)
from awx.main.signals import disable_computed_fields


class Command(BaseCommand):
    """Create preloaded data, intended for new installs
    """
    help = 'Creates a preload tower data if there is none.'

    def handle(self, *args, **kwargs):
        changed = False

        # Create a default organization as the first superuser found.
        try:
            superuser = User.objects.filter(is_superuser=True).order_by('pk')[0]
        except IndexError:
            superuser = None
        with impersonate(superuser):
            with disable_computed_fields():
                if not Organization.objects.exists():
                    o = Organization.objects.create(name='Default')

                    p = Project(name='Demo Project',
                                scm_type='git',
                                scm_url='https://github.com/ansible/ansible-tower-samples',
                                scm_update_on_launch=True,
                                scm_update_cache_timeout=0,
                                organization=o)
                    p.save(skip_update=True)

                    ssh_type = CredentialType.objects.filter(namespace='ssh').first()
                    c = Credential.objects.create(credential_type=ssh_type,
                                                  name='Demo Credential',
                                                  inputs={
                                                      'username': superuser.username
                                                  },
                                                  created_by=superuser)

                    c.admin_role.members.add(superuser)

                    public_galaxy_credential = Credential(name='Ansible Galaxy',
                                                          managed_by_tower=True,
                                                          credential_type=CredentialType.objects.get(kind='galaxy'),
                                                          inputs={'url': 'https://galaxy.ansible.com/'})
                    public_galaxy_credential.save()
                    o.galaxy_credentials.add(public_galaxy_credential)

                    i = Inventory.objects.create(name='Demo Inventory',
                                                 organization=o,
                                                 created_by=superuser)

                    Host.objects.create(name='localhost',
                                        inventory=i,
                                        variables="ansible_connection: local\nansible_python_interpreter: '{{ ansible_playbook_python }}'",
                                        created_by=superuser)

                    jt = JobTemplate.objects.create(name='Demo Job Template',
                                                    playbook='hello_world.yml',
                                                    project=p,
                                                    inventory=i)
                    jt.credentials.add(c)

                    print('Default organization added.')
                    print('Demo Credential, Inventory, and Job Template added.')
                    changed = True

                default_ee = settings.AWX_EXECUTION_ENVIRONMENT_DEFAULT_IMAGE
                ee, created = ExecutionEnvironment.objects.get_or_create(name='Default EE', defaults={'image': default_ee,
                                                                                                      'managed_by_tower': True})

                if created:
                    changed = True
                    print('Default Execution Environment registered.')

        if changed:
            print('(changed: True)')
        else:
            print('(changed: False)')
