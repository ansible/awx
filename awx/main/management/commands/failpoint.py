import json

from django.core.management.base import BaseCommand, CommandError

from awx.main.utils import failpoints
from awx.main.utils.job_invariants import check_job


def _parse_match(pairs):
    match = {}
    for pair in pairs or []:
        if '=' not in pair:
            raise CommandError(f'--match expects key=value, got {pair!r}')
        key, value = pair.split('=', 1)
        match[key] = value
    return match


def _dump(obj):
    return json.dumps(obj, indent=2, default=str)


class Command(BaseCommand):
    help = 'Arm, release and inspect failpoints (test facility; see awx/main/utils/failpoints.py)'

    def add_arguments(self, parser):
        sub = parser.add_subparsers(dest='cmd', required=True)

        sub.add_parser('registry', help='List the failpoint names that exist in the code')

        p = sub.add_parser('arm', help='Arm a failpoint')
        p.add_argument('name')
        p.add_argument('--action', required=True, choices=failpoints.ACTIONS)
        p.add_argument('--match', action='append', metavar='KEY=VALUE', help='Only fire when the call context matches; repeatable')
        p.add_argument('--nth', type=int, help='Fire only on the Nth matching hit')
        p.add_argument('--times', type=int, help='Fire at most this many times')
        p.add_argument('--timeout', type=float, help='pause: give up after this many seconds (default 600)')
        p.add_argument('--seconds', type=float, help='sleep: how long to sleep')
        p.add_argument('--exception', help='raise: dotted exception class to raise instead of FailpointError')

        p = sub.add_parser('release', help='Let paused callers of a failpoint continue')
        p.add_argument('name')

        p = sub.add_parser('disarm', help='Remove a failpoint, or all with --all')
        p.add_argument('name', nargs='?')
        p.add_argument('--all', action='store_true')

        sub.add_parser('list', help='Show armed failpoints')

        p = sub.add_parser('hits', help='Show recorded hits')
        p.add_argument('name', nargs='?')
        p.add_argument('--fired', action='store_true', help='Only hits that fired')

        sub.add_parser('clear-hits', help='Delete the hit log')

        p = sub.add_parser('wait', help='Block until a failpoint has fired (exit 1 on timeout)')
        p.add_argument('name')
        p.add_argument('--timeout', type=float, default=300)
        p.add_argument('--any-hit', action='store_true', help='Return on any hit, not only one that fired')

        p = sub.add_parser('check-job', help='Run job invariants and print the result as JSON')
        p.add_argument('job_id', type=int)

    def handle(self, *args, **options):
        cmd = options['cmd']
        if cmd == 'registry':
            for name, desc in sorted(failpoints.REGISTRY.items()):
                self.stdout.write(f'{name}\n    {desc}')
        elif cmd == 'arm':
            arg = {k: options[k] for k in ('timeout', 'seconds', 'exception') if options.get(k) is not None}
            try:
                failpoints.arm(options['name'], options['action'], match=_parse_match(options['match']), nth=options['nth'], times=options['times'], **arg)
            except (KeyError, ValueError, TypeError, ImportError, AttributeError) as exc:
                raise CommandError(str(exc))
            self.stdout.write(f"armed {options['name']}")
        elif cmd == 'release':
            n = failpoints.release(options['name'])
            self.stdout.write(f"released {options['name']} ({n} row)")
        elif cmd == 'disarm':
            if not options['name'] and not options['all']:
                raise CommandError('give a name or --all')
            n = failpoints.disarm(None if options['all'] else options['name'])
            self.stdout.write(f'disarmed {n}')
        elif cmd == 'list':
            self.stdout.write(_dump(failpoints.armed_list()))
        elif cmd == 'hits':
            self.stdout.write(_dump(failpoints.hits(options['name'], fired_only=options['fired'])))
        elif cmd == 'clear-hits':
            failpoints.clear_hits()
            self.stdout.write('cleared')
        elif cmd == 'wait':
            hit = failpoints.wait_for_hit(options['name'], fired_only=not options['any_hit'], timeout=options['timeout'])
            if hit is None:
                raise CommandError(f"timed out waiting for {options['name']}")
            self.stdout.write(_dump(hit))
        elif cmd == 'check-job':
            self.stdout.write(_dump(check_job(options['job_id'])))
