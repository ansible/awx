from django.core.management.base import BaseCommand, CommandError
from awx.main.models.ha import Instance


class Command(BaseCommand):
    help = 'Check if the task manager instance is ready throw error if not ready, can be use as readiness probe for k8s.'

    def handle(self, *args, **options):
        if Instance.objects.me().node_state != Instance.States.READY:
            raise CommandError('Instance is not ready')  # so that return code is not 0

        return
