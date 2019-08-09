import optparse
import json

from awxkit.utils import random_title


def upload_inventory(ansible_runner, nhosts=10, ini=False):
    """Helper to upload inventory script to target host"""
    # Create an inventory script
    if ini:
        copy_mode = '0644'
        copy_dest = '/tmp/inventory{}.ini'.format(random_title(non_ascii=False))
        copy_content = ini_inventory(nhosts)
    else:
        copy_mode = '0755'
        copy_dest = '/tmp/inventory{}.sh'.format(random_title(non_ascii=False))
        copy_content = '''#!/bin/bash
cat <<EOF
%s
EOF''' % json_inventory(nhosts)

    # Copy script to test system
    contacted = ansible_runner.copy(dest=copy_dest, force=True, mode=copy_mode, content=copy_content)
    for result in contacted.values():
        assert not result.get('failed', False), \
            "Failed to create inventory file: %s" % result
    return copy_dest


def generate_inventory(nhosts=100):
    """Generate a somewhat complex inventory with a configurable number of hosts"""
    inv_list = {
        '_meta': {
            'hostvars': {},
        },
    }

    for n in range(nhosts):
        hostname = 'host-%08d.example.com' % n
        group_evens_odds = 'evens.example.com' if n % 2 == 0 else 'odds.example.com'
        group_threes = 'threes.example.com' if n % 3 == 0 else ''
        group_fours = 'fours.example.com' if n % 4 == 0 else ''
        group_fives = 'fives.example.com' if n % 5 == 0 else ''
        group_sixes = 'sixes.example.com' if n % 6 == 0 else ''
        group_sevens = 'sevens.example.com' if n % 7 == 0 else ''
        group_eights = 'eights.example.com' if n % 8 == 0 else ''
        group_nines = 'nines.example.com' if n % 9 == 0 else ''
        group_tens = 'tens.example.com' if n % 10 == 0 else ''
        group_by_10s = 'group-%07dX.example.com' % (n / 10)
        group_by_100s = 'group-%06dXX.example.com' % (n / 100)
        group_by_1000s = 'group-%05dXXX.example.com' % (n / 1000)
        for group in [group_evens_odds, group_threes, group_fours, group_fives, group_sixes, group_sevens,
                      group_eights, group_nines, group_tens, group_by_10s]:
            if not group:
                continue
            if group in inv_list:
                inv_list[group]['hosts'].append(hostname)
            else:
                inv_list[group] = {'hosts': [hostname], 'children': [], 'vars': {'group_prefix': group.split('.')[0]}}
        if group_by_1000s not in inv_list:
            inv_list[group_by_1000s] = {'hosts': [], 'children': [],
                                        'vars': {'group_prefix': group_by_1000s.split('.')[0]}}
        if group_by_100s not in inv_list:
            inv_list[group_by_100s] = {'hosts': [], 'children': [],
                                       'vars': {'group_prefix': group_by_100s.split('.')[0]}}
        if group_by_100s not in inv_list[group_by_1000s]['children']:
            inv_list[group_by_1000s]['children'].append(group_by_100s)
        if group_by_10s not in inv_list[group_by_100s]['children']:
            inv_list[group_by_100s]['children'].append(group_by_10s)
        inv_list['_meta']['hostvars'][hostname] = {
            'ansible_user': 'example',
            'ansible_connection': 'local',
            'host_prefix': hostname.split('.')[0],
            'host_id': n,
        }

    return inv_list


def json_inventory(nhosts=10):
    """Return a JSON representation of inventory"""
    return json.dumps(generate_inventory(nhosts), indent=4)


def ini_inventory(nhosts=10):
    """Return a .INI representation of inventory"""
    output = list()
    inv_list = generate_inventory(nhosts)

    for group in inv_list.keys():
        if group == '_meta':
            continue

        # output host groups
        output.append('[%s]' % group)
        for host in inv_list[group].get('hosts', []):
            output.append(host)
        output.append('')  # newline

        # output child groups
        output.append('[%s:children]' % group)
        for child in inv_list[group].get('children', []):
            output.append(child)
        output.append('')  # newline

        # output group vars
        output.append('[%s:vars]' % group)
        for k, v in inv_list[group].get('vars', {}).items():
            output.append('%s=%s' % (k, v))
        output.append('')  # newline

    return '\n'.join(output)


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--json', action='store_true', dest='json')
    parser.add_option('--ini', action='store_true', dest='ini')
    parser.add_option('--host', dest='hostname', default='')
    parser.add_option('--nhosts', dest='nhosts', action='store', type='int', default=10)
    options, args = parser.parse_args()
    if options.json:
        print(json_inventory(nhosts=options.nhosts))
    elif options.ini:
        print(ini_inventory(nhosts=options.nhosts))
    elif options.hostname:
        print(json_inventory(nhosts=options.nhosts)['_meta']['hostvars'][options.hostname])
    else:
        print(json.dumps({}, indent=4))
