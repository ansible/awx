#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Red Hat, Inc

"""
Usage:
    fsm_generate_diffs [options] <design> <implementation>

Options:
    -h, --help        Show this page
    --debug            Show debug logging
    --verbose        Show verbose logging
    --append         Append the newly generated code to the implementation.
"""
from docopt import docopt
import logging
import sys
import fsm_diff.cli
import transform_fsm
import yaml

from jinja2 import FileSystemLoader, Environment

from subprocess import Popen, PIPE

logger = logging.getLogger('fsm_generate_diffs')


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

    implementation = parsed_args['<implementation>']

    p = Popen(['./extract.js', implementation], stdout=PIPE)
    output = p.communicate()[0]
    if p.returncode == 0:
        b = yaml.load(output)
    else:
        return 1

    with open(parsed_args['<design>']) as f:
        a = yaml.load(f.read())

    data = fsm_diff.cli.fsm_diff(a, b)
    data = transform_fsm.transform_fsm(data)

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template('fsm.jst')

    if parsed_args['--append']:
        with open(implementation, "a") as f:
            f.write(template.render(**data))
    else:
        print (template.render(**data))



    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))
