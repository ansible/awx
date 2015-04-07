from __future__ import print_function

import argparse

from stevedore import driver


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'format',
        nargs='?',
        default='simple',
        help='the output format',
    )
    parser.add_argument(
        '--width',
        default=60,
        type=int,
        help='maximum output width for text',
    )
    parsed_args = parser.parse_args()

    data = {
        'a': 'A',
        'b': 'B',
        'long': 'word ' * 80,
    }

    mgr = driver.DriverManager(
        namespace='stevedore.example.formatter',
        name=parsed_args.format,
        invoke_on_load=True,
        invoke_args=(parsed_args.width,),
    )
    for chunk in mgr.driver.format(data):
        print(chunk, end='')
