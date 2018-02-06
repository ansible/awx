#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2018  Benjamin Thomasson

"""
Usage:
    copy-layout [options] <from> <to>

Options:
    -h, --help        Show this page
    --debug            Show debug logging
    --verbose        Show verbose logging
"""
from docopt import docopt
import logging
import sys
import yaml

logger = logging.getLogger('copy-layout')


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

    with open(parsed_args['<from>']) as f:
        from_fsm = yaml.load(f.read())
    with open(parsed_args['<to>']) as f:
        to_fsm = yaml.load(f.read())

    to_states = {x['label']: x for x in to_fsm.get('states', [])}

    to_fsm['name'] = from_fsm.get('name', '')
    to_fsm['finite_state_machine_id'] = from_fsm.get('finite_state_machine_id', '')
    to_fsm['diagram_id'] = from_fsm.get('diagram_id', '')

    for state in from_fsm.get('states', []):
        to_states.get(state['label'], {})['x'] = state.get('x', 0)
        to_states.get(state['label'], {})['y'] = state.get('y', 0)

    with open(parsed_args['<to>'], 'w') as f:
        f.write(yaml.safe_dump(to_fsm, default_flow_style=False))

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
