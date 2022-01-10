from django.core.management.base import BaseCommand, CommandError

from awx.main.models import Instance, InstanceLink


class Command(BaseCommand):
    """
    Internal tower command.
    Register the peers of a receptor node.
    """

    help = "Register or remove links between Receptor nodes."

    def add_arguments(self, parser):
        parser.add_argument('source', type=str, help="Receptor node opening the connections.")
        parser.add_argument('--peers', type=str, nargs='+', required=False, help="Nodes that the source node connects out to.")
        parser.add_argument('--disconnect', type=str, nargs='+', required=False, help="Nodes that should no longer be connected to by the source node.")

    def handle(self, **options):
        nodes = Instance.objects.in_bulk(field_name='hostname')
        if options['source'] not in nodes:
            raise CommandError(f"Host {options['source']} is not a registered instance.")
        if not options['peers'] and not options['disconnect']:
            raise CommandError("One of the options --peers or --disconnect is required.")

        if options['peers']:
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

        if options['disconnect']:
            results = 0
            for target in options['disconnect']:
                if target not in nodes:  # Be permissive, the node might have already been de-registered.
                    continue
                n, _ = InstanceLink.objects.filter(source=nodes[options['source']], target=nodes[target]).delete()
                results += n

            print(f"{results} peer links removed from the database.")
