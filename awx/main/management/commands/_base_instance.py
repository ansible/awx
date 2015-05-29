# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from awx.main.models import Project


class OptionEnforceError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class BaseCommandInstance(BaseCommand):
    #option_list = BaseCommand.option_list

    def __init__(self):
        super(BaseCommandInstance, self).__init__()
        self.enforce_roles = False
        self.enforce_hostname_set = False
        self.enforce_unique_find = False

        self.option_primary = False
        self.option_secondary = False
        self.option_hostname = None
        self.option_uuid = None

        self.UUID = settings.SYSTEM_UUID
        self.unique_fields = {}

    @staticmethod
    def generate_option_hostname():
        return make_option('--hostname',
                           dest='hostname',
                           default='',
                           help='Find instance by specified hostname.')

    @staticmethod
    def generate_option_hostname_set():
        return make_option('--hostname',
                           dest='hostname',
                           default='',
                           help='Hostname to assign to the new instance.')

    @staticmethod
    def generate_option_primary():
        return make_option('--primary',
                           action='store_true',
                           default=False,
                           dest='primary',
                           help='Register instance as primary.')

    @staticmethod
    def generate_option_secondary():
        return make_option('--secondary',
                           action='store_true',
                           default=False,
                           dest='secondary',
                           help='Register instance as secondary.')

    @staticmethod
    def generate_option_uuid():
        return make_option('--uuid', 
                           dest='uuid',
                           default='',
                           help='Find instance by specified uuid.')

    def include_options_roles(self):
        BaseCommand.option_list += ( BaseCommandInstance.generate_option_primary(), BaseCommandInstance.generate_option_secondary(), )
        self.enforce_roles = True

    def include_option_hostname_set(self):
        BaseCommand.option_list += ( BaseCommandInstance.generate_option_hostname_set(), )
        self.enforce_hostname_set = True

    def include_option_hostname_uuid_find(self):
        BaseCommand.option_list += ( BaseCommandInstance.generate_option_hostname(), BaseCommandInstance.generate_option_uuid(), )
        self.enforce_unique_find = True

    def get_option_hostname(self):
        return self.option_hostname

    def get_option_uuid(self):
        return self.option_uuid

    def is_option_primary(self):
        return self.option_primary

    def is_option_secondary(self):
        return self.option_secondary

    def get_UUID(self):
        return self.UUID

    # for the enforce_unique_find policy
    def get_unique_fields(self):
        return self.unique_fields

    @property
    def usage_error(self):
        if self.enforce_roles and self.enforce_hostname_set:
            return CommandError('--hostname and one of --primary or --secondary is required.')
        elif self.enforce_hostname_set:
            return CommandError('--hostname is required.')
        elif self.enforce_roles:
            return CommandError('One of --primary or --secondary is required.')

    def handle(self, *args, **options):
        if self.enforce_hostname_set and self.enforce_unique_find:
            raise OptionEnforceError('Can not enforce --hostname as a setter and --hostname as a getter')            

        if self.enforce_roles:
            self.option_primary = options['primary']
            self.option_secondary = options['secondary']

            if self.is_option_primary() and self.is_option_secondary() or not (self.is_option_primary() or self.is_option_secondary()):
                raise self.usage_error

        if self.enforce_hostname_set:
            if options['hostname']:
                self.option_hostname = options['hostname']
            else:
                raise self.usage_error

        if self.enforce_unique_find:
            if options['hostname']:
                self.unique_fields['hostname'] = self.option_hostname = options['hostname']

            if options['uuid']:
                self.unique_fields['uuid'] = self.option_uuid = options['uuid']

            if len(self.unique_fields) == 0:
                self.unique_fields['uuid'] = self.get_UUID()

    @staticmethod
    def __instance_str(instance, fields):
        string = '('
        for field in fields:
            string += '%s="%s",' % (field, getattr(instance, field))
        if len(fields) > 0:
            string = string[:-1]
        string += ')'
        return string

    @staticmethod
    def instance_str(instance):
        return BaseCommandInstance.__instance_str(instance, ('uuid', 'hostname', 'role'))

    def update_projects(self, instance):
        """Update all projects, ensuring the job runs against this instance,
        which is the primary instance.
        """
        for project in Project.objects.all():
            project.update()
