from django.core.management.base import BaseCommand
from django.conf import settings

from awx.main.tasks.system import execution_node_health_check, cluster_node_health_check
from awx.main.models.ha import Instance


class Command(BaseCommand):

    help = (
        'Run health checks throughout the cluster. '
        'This is used in a system job so the user can adjust parameters. '
        'This is the only means to regularily check execution nodes.'
    )

    def handle(self, *args, **options):
        for instance in Instance.objects.all():
            inst_deets = f'{instance.hostname}-{instance.pk}'
            print('')
            if instance.node_type == 'execution':
                print(f'Starting health check for {inst_deets}')
                data = execution_node_health_check(instance.hostname)
                print(f'  health check data has been saved, data:\n{data}')
            elif instance.node_type == 'hop':
                print(f'Not running health check for {inst_deets} because health checks do not apply to hop nodes')
            elif instance.hostname == settings.CLUSTER_HOST_ID:
                print(f'Running health check on local node {inst_deets}')
                data = cluster_node_health_check(instance.hostname)
                print(f'  health check data saved, data:\n{data}')
            elif instance.node_type in ('control', 'hybrid'):
                print(f'Submitting request for health check on {inst_deets}')
                cluster_node_health_check.apply_async([instance.hostname])
