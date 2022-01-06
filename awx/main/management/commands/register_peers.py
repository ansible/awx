from django.core.management.base import BaseCommand, CommandError

from awx.main.models import Instance, InstanceLink


class Command(BaseCommand):
    """
    Internal tower command.
    Register the peers of a receptor node.
    """

    def add_arguments(self, parser):
        parser.add_argument('source', type=str, help="")
        parser.add_argument('--peers', type=str, nargs='+', required=True, help="")

    def handle(self, **options):
        nodes = Instance.objects.in_bulk(field_name='hostname')
        if options['source'] not in nodes:
            raise CommandError(f"Host {options['source']} is not a registered instance.")
        missing_peers = set(options['peers']) - set(nodes)
        if missing_peers:
            missing = ' '.join(missing_peers)
            raise CommandError(f"Peers not currently registered as instances: {missing}")

        results = 0
        for target in options['peers']:
            instance, created = InstanceLink.objects.get_or_create(source=nodes[options['source']], target=nodes[target])
            if created:
                results += 1

        print(f"{results} new peer links added to the database.")
