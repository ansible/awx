from __future__ import print_function

import argparse

from stevedore import extension


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
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

    mgr = extension.ExtensionManager(
        namespace='stevedore.example.formatter',
        invoke_on_load=True,
        invoke_args=(parsed_args.width,),
    )

    def format_data(ext, data):
        return (ext.name, ext.obj.format(data))

    results = mgr.map(format_data, data)

    for name, result in results:
        print('Formatter: {0}'.format(name))
        for chunk in result:
            print(chunk, end='')
        print('')
