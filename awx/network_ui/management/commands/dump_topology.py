# Copyright (c) 2017 Red Hat, Inc
from django.core.management.base import BaseCommand

from awx.network_ui.serializers import yaml_serialize_topology



class Command(BaseCommand):
    help = 'Dumps data of a topology to a yaml file'

    def add_arguments(self, parser):
        parser.add_argument('topology_id', type=int)

    def handle(self, *args, **options):
        topology_id = options['topology_id']

        print yaml_serialize_topology(topology_id)
