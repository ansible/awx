#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:
    merge_yaml [options] <a> <b>

Options:
    -h, --help        Show this page
    --debug            Show debug logging
    --verbose        Show verbose logging
"""
from docopt import docopt
import logging
import sys
import yaml

logger = logging.getLogger('merge_yaml')


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

    with open(parsed_args['<a>']) as f:
        a = yaml.load(f.read())
    with open(parsed_args['<b>']) as f:
        b = yaml.load(f.read())

    a_models = {x['name']: x for x in a.get('models', [])}
    for model in b.get('models', []):
        for key, value in model.iteritems():
            a_models[model['name']][key] = value


    print (yaml.safe_dump(a, default_flow_style=False))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

