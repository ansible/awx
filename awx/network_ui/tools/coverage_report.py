#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage:
    coverage_report [options] <server>

Options:
    -h, --help        Show this page
    --debug            Show debug logging
    --verbose        Show verbose logging
"""
from docopt import docopt
import logging
import sys
import os
import requests

logger = logging.getLogger('coverage_report')

TESTS_API = '/network_ui/tests'



def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parsed_args = docopt(__doc__, args)
    if parsed_args['--debug']:
        logging.basicConfig(level=logging.DEBUG)
    elif parsed_args['--verbose']:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)


    print (parsed_args['<server>'])
    server = parsed_args['<server>']

    tests = requests.get(server + TESTS_API, verify=False).json()

    for test in tests['tests']:
        if not os.path.exists(test['name']):
            os.mkdir(test['name'])
        with open(test['name'] + "/coverage.json", 'w') as f:
            f.write(requests.get(server + test['coverage'], verify=False).text)


    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))

