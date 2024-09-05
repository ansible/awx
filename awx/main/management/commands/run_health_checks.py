from django.core.management.base import BaseCommand

from awx.main.tasks.system import execution_node_health_check
from awx.main.models.ha import Instance


class Command(BaseCommand):
    help = (
        'Run health checks on all execution nodes in the cluster. '
        'This is used in a system job so the user can adjust parameters. '
        'This is the only means to regularily check health of execution nodes '
        'which were last known to be healthy.'
    )

    def handle(self, *args, **options):
        for instance in Instance.objects.filter(node_type='execution'):
            inst_deets = f'{instance.hostname}-{instance.pk}'
            print('')
            print(f'Starting health check for {inst_deets}')
            data = execution_node_health_check(instance.hostname)
            print(f'  health check data has been saved, data:\n{data}')
