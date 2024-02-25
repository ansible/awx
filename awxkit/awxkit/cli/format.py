import locale
import json
from distutils.util import strtobool

import yaml

from awxkit.cli.utils import colored
from awxkit import config


def get_config_credentials():
    """Load username and password from config.credentials.default.

    In order to respect configurations from AWXKIT_CREDENTIAL_FILE.
    """
    default_username = 'admin'
    default_password = 'password'

    if not hasattr(config, 'credentials'):
        return default_username, default_password

    default = config.credentials.get('default', {})
    return (default.get('username', default_username), default.get('password', default_password))


def add_authentication_arguments(parser, env):
    auth = parser.add_argument_group('authentication')
    auth.add_argument(
        '--conf.host',
        default=env.get('CONTROLLER_HOST', env.get('TOWER_HOST', 'https://127.0.0.1:443')),
        metavar='https://example.awx.org',
    )
    auth.add_argument(
        '--conf.token',
        default=env.get('CONTROLLER_OAUTH_TOKEN', env.get('CONTROLLER_TOKEN', env.get('TOWER_OAUTH_TOKEN', env.get('TOWER_TOKEN', '')))),
        help='an OAuth2.0 token (get one by using `awx login`)',
        metavar='TEXT',
    )

    config_username, config_password = get_config_credentials()
    # options configured via cli args take higher precedence than those from the config
    auth.add_argument(
        '--conf.username',
        default=env.get('CONTROLLER_USERNAME', env.get('TOWER_USERNAME', config_username)),
        metavar='TEXT',
    )
    auth.add_argument(
        '--conf.password',
        default=env.get('CONTROLLER_PASSWORD', env.get('TOWER_PASSWORD', config_password)),
        metavar='TEXT',
    )

    auth.add_argument(
        '-k',
        '--conf.insecure',
        help='Allow insecure server connections when using SSL',
        default=not strtobool(env.get('CONTROLLER_VERIFY_SSL', env.get('TOWER_VERIFY_SSL', 'True'))),
        action='store_true',
    )


def add_verbose(formatting, env):
    formatting.add_argument(
        '-v',
        '--verbose',
        dest='conf.verbose',
        help='print debug-level logs, including requests made',
        default=strtobool(env.get('CONTROLLER_VERBOSE', env.get('TOWER_VERBOSE', 'f'))),
        action="store_true",
    )


def add_formatting_import_export(parser, env):
    formatting = parser.add_argument_group('input/output formatting')
    formatting.add_argument(
        '-f',
        '--conf.format',
        dest='conf.format',
        choices=['json', 'yaml'],
        default=env.get('CONTROLLER_FORMAT', env.get('TOWER_FORMAT', 'json')),
        help=('specify a format for the input and output'),
    )
    add_verbose(formatting, env)


def add_output_formatting_arguments(parser, env):
    formatting = parser.add_argument_group('input/output formatting')

    formatting.add_argument(
        '-f',
        '--conf.format',
        dest='conf.format',
        choices=FORMATTERS.keys(),
        default=env.get('CONTROLLER_FORMAT', env.get('TOWER_FORMAT', 'json')),
        help=('specify a format for the input and output'),
    )
    formatting.add_argument(
        '--filter',
        dest='conf.filter',
        default='.',
        metavar='TEXT',
        help=('specify an output filter (only valid with jq or human format)'),
    )
    formatting.add_argument(
        '--conf.color',
        metavar='BOOLEAN',
        help='Display colorized output.  Defaults to True',
        default=env.get('CONTROLLER_COLOR', env.get('TOWER_COLOR', 't')),
        type=strtobool,
    )
    add_verbose(formatting, env)


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
            'To use `-f jq`, you must install the optional jq dependency.\n`pip install jq`\n',
            'Note that some platforms may require additional programs to '
            'build jq from source (like `libtool`).\n'
            'See https://pypi.org/project/jq/ for instructions.',
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
    return yaml.safe_dump(output, default_flow_style=False, allow_unicode=True)


def format_human(output, fmt):
    lines = []
    if fmt == '.':
        fmt = 'id,name'
    column_names = [col.strip() for col in fmt.split(',')]
    if 'count' in output:
        output = output['results']
    else:
        output = [output]

    if fmt == '*' and len(output):
        column_names = list(output[0].keys())
        for k in ('summary_fields', 'related'):
            if k in column_names:
                column_names.remove(k)

    table = [column_names]
    table.extend([[record.get(col, '') for col in column_names] for record in output])
    col_paddings = []

    def format_num(v):
        try:
            return locale.format("%.*f", (0, int(v)), True)
        except (ValueError, TypeError):
            if isinstance(v, (list, dict)):
                return json.dumps(v)
            if v is None:
                return ''
            return v

    # calculate the max width of each column
    for i, _ in enumerate(column_names):
        max_width = max([len(format_num(row[i])) for row in table])
        col_paddings.append(max_width)

    # insert a row of === header lines
    table.insert(1, ['=' * i for i in col_paddings])

    # print each row of the table data, justified based on col_paddings
    for row in table:
        line = ''
        for i, value in enumerate(row):
            line += format_num(value).ljust(col_paddings[i] + 1)
        lines.append(line)
    return '\n'.join(lines)


FORMATTERS = {'json': format_json, 'yaml': format_yaml, 'jq': format_jq, 'human': format_human}
