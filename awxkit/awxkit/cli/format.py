import json
from distutils.util import strtobool

import yaml

from awxkit.cli.utils import colored


def add_authentication_arguments(parser, env):
    auth = parser.add_argument_group('authentication')
    auth.add_argument(
        '--conf.host',
        default=env.get('TOWER_HOST', 'https://127.0.0.1:443'),
        metavar='https://example.awx.org',
    )
    auth.add_argument(
        '--conf.token',
        default=env.get('TOWER_TOKEN', ''),
        help='an OAuth2.0 token (get one by using `awx login`)',
        metavar='TEXT',
    )
    auth.add_argument(
        '--conf.username',
        default=env.get('TOWER_USERNAME', 'admin'),
        metavar='TEXT',
    )
    auth.add_argument(
        '--conf.password',
        default=env.get('TOWER_PASSWORD', 'password'),
        metavar='TEXT',
    )
    auth.add_argument(
        '-k',
        '--conf.insecure',
        help='Allow insecure server connections when using SSL',
        default=not strtobool(env.get('TOWER_VERIFY_SSL', 'True')),
        action='store_true',
    )


def add_output_formatting_arguments(parser, env):
    formatting = parser.add_argument_group('output formatting')

    formatting.add_argument(
        '-f',
        '--conf.format',
        dest='conf.format',
        choices=FORMATTERS.keys(),
        default=env.get('TOWER_FORMAT', 'json'),
        help=(
            'specify an output format'
        ),
    )
    formatting.add_argument(
        '--filter',
        dest='conf.filter',
        default='.',
        metavar='TEXT',
        help=(
            'specify an output filter (only valid with jq or human format)'
        ),
    )
    formatting.add_argument(
        '--conf.color',
        metavar='BOOLEAN',
        help='Display colorized output.  Defaults to True',
        default=env.get('TOWER_COLOR', 't'), type=strtobool,
    )
    formatting.add_argument(
        '-v',
        '--verbose',
        dest='conf.verbose',
        help='print debug-level logs, including requests made',
        default=strtobool(env.get('TOWER_VERBOSE', 'f')),
        action="store_true"
    )


def format_response(response, fmt='json', filter='.', changed=False):
    if response is None:
        return  # HTTP 204
    if isinstance(response, str):
        return response

    if 'results' in response.__dict__:
        results = getattr(response, 'results')
    else:
        results = [response]
    for result in results:
        if 'related' in result.json:
            result.json.pop('related')

    formatted = FORMATTERS[fmt](response.json, filter)

    if changed:
        formatted = colored(formatted, 'green')
    return formatted


def format_jq(output, fmt):
    try:
        import jq
    except ImportError:
        if fmt == '.':
            return output
        raise ImportError(
            'To use `-f jq`, you must install the optional jq dependency.\n'
            '`pip install jq`\n',
            'Note that some platforms may require additional programs to '
            'build jq from source (like `libtool`).\n'
            'See https://pypi.org/project/jq/ for instructions.'
        )
    results = []
    for x in jq.jq(fmt).transform(output, multiple_output=True):
        if x not in (None, ''):
            if isinstance(x, str):
                results.append(x)
            else:
                results.append(json.dumps(x))
    return '\n'.join(results)


def format_json(output, fmt):
    return json.dumps(output, indent=5)


def format_yaml(output, fmt):
    output = json.loads(json.dumps(output))
    return yaml.dump(
        output,
        default_flow_style=False
    )


def format_human(output, fmt):
    if fmt == '.':
        fmt = 'id,name'
    column_names = fmt.split(',')
    try:
        from tabulate import tabulate
    except ImportError:
        raise ImportError(
            'To use `-f human`, you must install the optional tabulate '
            'dependency.\n`pip install tabulate`',
        )
    if 'count' in output:
        output = output['results']
    else:
        output = [output]

    return tabulate([
            dict(
                (col, record.get(col, ''))
                for col in column_names
            )
            for record in output
        ], headers='keys', tablefmt='rst'
    )


FORMATTERS = {
    'json': format_json,
    'yaml': format_yaml,
    'jq': format_jq,
    'human': format_human
}
