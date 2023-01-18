import warnings

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

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
        parser.add_argument(
            '--exact',
            type=str,
            nargs='*',
            required=False,
            help="The exact set of nodes the source node should connect out to. Any existing links registered in the database that do not match will be removed. May be empty.",
        )

    def handle(self, **options):
        # provides a mapping of hostname to Instance objects
        nodes = Instance.objects.in_bulk(field_name='hostname')

        if options['source'] not in nodes:
            raise CommandError(f"Host {options['source']} is not a registered instance.")
        if not (options['peers'] or options['disconnect'] or options['exact'] is not None):
            raise CommandError("One of the options --peers, --disconnect, or --exact is required.")
        if options['exact'] is not None and options['peers']:
            raise CommandError("The option --peers may not be used with --exact.")
        if options['exact'] is not None and options['disconnect']:
            raise CommandError("The option --disconnect may not be used with --exact.")

        # No 1-cycles
        for collection in ('peers', 'disconnect', 'exact'):
            if options[collection] is not None and options['source'] in options[collection]:
                raise CommandError(f"Source node {options['source']} may not also be in --{collection}.")

        # No 2-cycles
        if options['peers'] or options['exact'] is not None:
            peers = set(options['peers'] or options['exact'])
            incoming = set(InstanceLink.objects.filter(target=nodes[options['source']]).values_list('source__hostname', flat=True))
            if peers & incoming:
                warnings.warn(f"Source node {options['source']} should not link to nodes already peering to it: {peers & incoming}.")

        if options['peers']:
            missing_peers = set(options['peers']) - set(nodes)
            if missing_peers:
                missing = ' '.join(missing_peers)
                raise CommandError(f"Peers not currently registered as instances: {missing}")

            results = 0
            for target in options['peers']:
                _, created = InstanceLink.objects.update_or_create(
                    source=nodes[options['source']], target=nodes[target], defaults={'link_state': InstanceLink.States.ESTABLISHED}
                )
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

        if options['exact'] is not None:
            additions = 0
            with transaction.atomic():
                peers = set(options['exact'])
                links = set(InstanceLink.objects.filter(source=nodes[options['source']]).values_list('target__hostname', flat=True))
                removals, _ = InstanceLink.objects.filter(source=nodes[options['source']], target__hostname__in=links - peers).delete()
                for target in peers - links:
                    _, created = InstanceLink.objects.update_or_create(
                        source=nodes[options['source']], target=nodes[target], defaults={'link_state': InstanceLink.States.ESTABLISHED}
                    )
                    if created:
                        additions += 1

            print(f"{additions} peer links added and {removals} deleted from the database.")
