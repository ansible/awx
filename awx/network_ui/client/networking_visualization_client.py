#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:
    networking_visualization_client.py [options] (create|list|get|update|delete) [device|topology|interface|link] [<filter>...]

Options:
    -h, --help                   Show this page
    --user=<u>                   User
    --password-file=<f>|-p=<f>   Password file
    --debug                      Show debug logging
    --verbose                    Show verbose logging
"""
from docopt import docopt
import logging
import sys
from getpass import getpass

from conf import settings
import json
import os

import v2_api_client


logger = logging.getLogger('networking_visualization_client')


def main(args=None):
    try:
        if args is None:
            args = sys.argv[1:]
        parsed_args = docopt(__doc__, args)
        if parsed_args['--debug']:
            logging.basicConfig(level=logging.DEBUG)
        elif parsed_args['--verbose']:
            logging.basicConfig(level=logging.INFO)
        else:
            logging.basicConfig(level=logging.WARNING)

        settings.user = parsed_args['--user']
        if parsed_args['--password-file'] and os.path.exists(os.path.abspath(parsed_args['--password-file'])):
            with open(os.path.abspath(parsed_args['--password-file'])) as f:
                settings.password = f.read().strip()
        else:
            settings.password = getpass()
        query_filter = {}
        if parsed_args['<filter>']:
            for key_value in parsed_args['<filter>']:
                if "=" in key_value:
                    key, _, value = key_value.partition("=")
                    if value.lower() in ["true", "yes"]:
                        query_filter[key] = True
                    elif value.lower() in ["false", "no"]:
                        query_filter[key] = False
                    else:
                        try:
                            query_filter[key] = int(value)
                        except ValueError:
                            try:
                                query_filter[key] = float(value)
                            except ValueError:
                                query_filter[key] = value
                else:
                    raise Exception("Filters should be in the form of 'key=value'")

        operation = ('get' if parsed_args['get'] else 
                     'list' if parsed_args['list'] else
                     'create' if parsed_args['create'] else
                     'delete' if parsed_args['delete'] else
                     'update' if parsed_args['update'] else None)

        if (parsed_args['topology']):
            result = v2_api_client.__dict__[operation + "_topology"](**query_filter)
        elif (parsed_args['device']):
            result = v2_api_client.__dict__[operation + "_device"](**query_filter)
        elif (parsed_args['interface']):
            result = v2_api_client.__dict__[operation + "_interface"](**query_filter)
        elif (parsed_args['link']):
            result = v2_api_client.__dict__[operation + "_link"](**query_filter)
        if isinstance(result, dict) or isinstance(result, list):
            print json.dumps(result, sort_keys=True, indent=4)

    except BaseException, e:
        print ("Error: {0}".format(e))
        raise
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

