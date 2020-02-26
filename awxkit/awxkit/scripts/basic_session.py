from argparse import ArgumentParser
import logging
import pdb  # noqa
import sys
import os

from awxkit import api, config, utils, exceptions, WSClient  # noqa
from awxkit.awx.utils import check_related, delete_all, get_all, uses_sessions  # noqa
from awxkit.awx.utils import as_user as _as_user

if str(os.getenv('AWXKIT_DEBUG', 'false')).lower() in ['true', '1']:
    logging.basicConfig(level='DEBUG')


def parse_args():
    parser = ArgumentParser()
    parser.add_argument(
        '--base-url',
        dest='base_url',
        default=os.getenv(
            'AWXKIT_BASE_URL',
            'http://127.0.0.1:8013'),
        help='URL for AWX.  Defaults to env var AWXKIT_BASE_URL or http://127.0.0.1:8013')
    parser.add_argument(
        '-c',
        '--credential-file',
        dest='credential_file',
        default=os.getenv(
            'AWXKIT_CREDENTIAL_FILE',
            utils.not_provided),
        help='Path for yml credential file.  If not provided or set by AWXKIT_CREDENTIAL_FILE, set '
        'AWXKIT_USER and AWXKIT_USER_PASSWORD env vars for awx user credentials.')
    parser.add_argument(
        '-p',
        '--project-file',
        dest='project_file',
        default=os.getenv(
            'AWXKIT_PROJECT_FILE'),
        help='Path for yml project config file.'
             'If not provided or set by AWXKIT_PROJECT_FILE, projects will not have default SCM_URL')
    parser.add_argument('-f', '--file', dest='akit_script', default=False,
                        help='akit script file to run in interactive session.')
    parser.add_argument(
        '-x',
        '--non-interactive',
        action='store_true',
        dest='non_interactive',
        help='Do not run in interactive mode.')
    return parser.parse_known_args()[0]


def main():
    exc = None
    try:
        global akit_args
        akit_args = parse_args()
        config.base_url = akit_args.base_url

        if akit_args.credential_file != utils.not_provided:
            config.credentials = utils.load_credentials(
                akit_args.credential_file)
        else:
            config.credentials = utils.PseudoNamespace({
                'default': {
                    'username': os.getenv('AWXKIT_USER', 'admin'),
                    'password': os.getenv('AWXKIT_USER_PASSWORD', 'password')
                }
            })

        if akit_args.project_file != utils.not_provided:
            config.project_urls = utils.load_projects(
                akit_args.project_file)

        global root
        root = api.Api()
        if uses_sessions(root.connection):
            config.use_sessions = True
            root.load_session().get()
        else:
            root.load_authtoken().get()

        if 'v2' in root.available_versions:
            global v2
            v2 = root.available_versions.v2.get()

        rc = 0
        if akit_args.akit_script:
            try:
                exec(open(akit_args.akit_script).read(), globals())
            except Exception as e:
                exc = e
                raise
    except Exception as e:
        exc = e  # noqa
        rc = 1  # noqa
        raise


def as_user(username, password=None):
    return _as_user(root, username, password)


def load_interactive():
    if '--help' in sys.argv or '-h' in sys.argv:
        return parse_args()

    try:
        from IPython import start_ipython
        basic_session_path = os.path.abspath(__file__)
        if basic_session_path[-1] == 'c':  # start_ipython doesn't work w/ .pyc
            basic_session_path = basic_session_path[:-1]
        sargs = ['-i', basic_session_path]
        if sys.argv[1:]:
            sargs.extend(['--'] + sys.argv[1:])
        return start_ipython(argv=sargs)
    except ImportError:
        from code import interact
        main()
        interact('', local=dict(globals(), **locals()))


if __name__ == '__main__':
    main()
