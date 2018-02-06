#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2017 Red Hat, Inc

"""
Usage:
    transform_fsm [options] <input> <output>

Options:
    -h, --help        Show this page
    --debug            Show debug logging
    --verbose        Show verbose logging
"""
from docopt import docopt
import logging
import sys
import yaml

logger = logging.getLogger('transform_fsm')


def transform_fsm(data):

    state_map = dict()

    for state in data['states']:
        state_map[state['label']] = state
        state['functions'] = dict()

    for transition in data['transitions']:
        state = state_map.get(transition['from_state'], dict(label=transition['from_state'], functions=dict()))
        state_map[transition['from_state']] = state
        if state not in data['states']:
            data['states'].append(state)
        function_transitions = state['functions'].get(transition['label'], list())
        function_transitions.append(dict(to_state=transition['to_state']))
        state['functions'][transition['label']] = function_transitions

    for state in data['states']:
        state['functions'] = sorted(state['functions'].items())

    return data

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

    with open(parsed_args['<input>']) as f:
        data = yaml.load(f.read())

    data = transform_fsm(data)

    with open(parsed_args['<output>'], 'w') as f:
        f.write(yaml.safe_dump(data, default_flow_style=False))

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

