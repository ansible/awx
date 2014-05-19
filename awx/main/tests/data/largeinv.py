#!/usr/bin/env python

# Python
import json
import optparse
import os

nhosts = int(os.environ.get('NHOSTS', 100))

inv_list = {
    '_meta': {
        'hostvars': {},
    },
}

for n in xrange(nhosts):
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
    for group in [group_evens_odds, group_threes, group_fours, group_fives, group_sixes, group_sevens, group_eights, group_nines, group_tens, group_by_10s]:
        if not group:
            continue
        if group in inv_list:
            inv_list[group]['hosts'].append(hostname)
        else:
            inv_list[group] = {'hosts': [hostname], 'children': [], 'vars': {'group_prefix': group.split('.')[0]}}
    if group_by_1000s not in inv_list:
        inv_list[group_by_1000s] = {'hosts': [], 'children': [], 'vars': {'group_prefix': group_by_1000s.split('.')[0]}}
    if group_by_100s not in inv_list:
        inv_list[group_by_100s] = {'hosts': [], 'children': [], 'vars': {'group_prefix': group_by_100s.split('.')[0]}}
    if group_by_100s not in inv_list[group_by_1000s]['children']:
        inv_list[group_by_1000s]['children'].append(group_by_100s)
    if group_by_10s not in inv_list[group_by_100s]['children']:
        inv_list[group_by_100s]['children'].append(group_by_10s)
    inv_list['_meta']['hostvars'][hostname] = {
        'ansible_ssh_user': 'example',
        'ansible_connection': 'local',
        'host_prefix': hostname.split('.')[0],
        'host_id': n,
    }

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--list', action='store_true', dest='list')
    parser.add_option('--host', dest='hostname', default='')
    options, args = parser.parse_args()
    if options.list:
        print json.dumps(inv_list, indent=4)
    elif options.hostname:
        print json.dumps(inv_list['_meta']['hostvars'][options.hostname], indent=4)
    else:
        print json.dumps({}, indent=4)

