import json
import sys
import traceback
import yaml
import urllib3

from requests.exceptions import ConnectionError, SSLError

from .client import CLI
from awxkit.utils import to_str
from awxkit.exceptions import Unauthorized, Common
from awxkit.cli.utils import cprint


# you'll only see these warnings if you've explicitly *disabled* SSL
# verification, so they're a little annoying, redundant
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def run(stdout=sys.stdout, stderr=sys.stderr, argv=[]):
    cli = CLI(stdout=stdout, stderr=stderr)
    try:
        cli.parse_args(argv or sys.argv)
        cli.connect()
        cli.parse_resource()
    except KeyboardInterrupt:
        sys.exit(1)
    except ConnectionError as e:
        cli.parser.print_help()
        msg = (
            '\nThere was a network error of some kind trying to reach '
            '{}.\nYou might need to specify (or double-check) '
            '--conf.host'.format(cli.get_config('host'))
        )
        if isinstance(e, SSLError):
            msg = (
                '\nCould not establish a secure connection.  '
                '\nPlease add your server to your certificate authority.'
                '\nYou can also run this command by specifying '
                '-k or --conf.insecure'
            )
        cprint(msg + '\n', 'red', file=stderr)
        cprint(e, 'red', file=stderr)
        sys.exit(1)
    except Unauthorized as e:
        cli.parser.print_help()
        msg = '\nValid credentials were not provided.\n$ awx login --help'
        cprint(msg + '\n', 'red', file=stderr)
        if cli.verbose:
            cprint(e.__class__, 'red', file=stderr)
        sys.exit(1)
    except Common as e:
        if cli.verbose:
            print(traceback.format_exc(), sys.stderr)
        if cli.get_config('format') == 'json':
            json.dump(e.msg, sys.stdout)
            print('')
        elif cli.get_config('format') == 'yaml':
            sys.stdout.write(to_str(yaml.safe_dump(e.msg, default_flow_style=False, encoding='utf-8', allow_unicode=True)))
        elif cli.get_config('format') == 'human':
            sys.stdout.write(e.__class__.__name__)
            print('')
        sys.exit(1)
    except Exception as e:
        if cli.verbose:
            e = traceback.format_exc()
        cprint(e, 'red', file=stderr)
        sys.exit(1)
