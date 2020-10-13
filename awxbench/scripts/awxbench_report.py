#!/usr/bin/env python

import os
import sys
import re
import csv

'''
transaction type: /var/lib/awx/benchmark_job_events/job_events_insert_batch_1000.sql
scaling factor: 1
query mode: simple
number of clients: 1
number of threads: 1
number of transactions per client: 10
number of transactions actually processed: 10/10
latency average = 120.145 ms
tps = 8.323300 (including connections establishing)
tps = 8.350792 (excluding connections establishing)
'''

def run():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <results_dir> <report_file>", file=sys.stderr)
        return -1

    results_dir = sys.argv[1]
    report_fname = sys.argv[2]

    stats = {
        'insert_batch': [],
        'copy_from': [],
    }

    client_re = re.compile("number of clients: ([0-9]+)", re.M)
    tps_re = re.compile("tps = (\d*\.?\d+) \(including connections establishing\)", re.M)

    fnames = os.listdir(results_dir)
    for fname in fnames:
        with open(os.path.join(results_dir, fname)) as f:
            contents = f.read()

        client_match = client_re.search(contents)
        tps_match = tps_re.search(contents)
        if not client_match or not tps_match:
            print(f"number of clients or tps not found in file {fname}", file=sys.stderr)
            return -1

        if 'job_events_insert_batch_1000' in contents:
            stats['insert_batch'].append([int(client_match.group(1)), float(tps_match.group(1)) * 1000])
        elif 'job_events_copy_from_1000' in contents:
            stats['copy_from'].append([int(client_match.group(1)), float(tps_match.group(1)) * 1000])
        else:
            print(f"expected script name not found in output file {fname}", file=sys.stderr)
            return -1

    with open(report_fname, 'w') as r:
        print("Batch insert of 1,000", file=r)
        print("concurrency,inserts_per_second", file=r)
        for (concurrency, inserts_per_second) in sorted(stats['insert_batch'], key=lambda e: e[0]):
            print(f"{concurrency}, {inserts_per_second}", file=r)
        print("", file=r)


        print("Batch COPY FROM of 1,000", file=r)
        print("concurrency,inserts_per_second", file=r)
        for (concurrency, inserts_per_second) in sorted(stats['copy_from'], key=lambda e: e[0]):
            print(f"{concurrency}, {inserts_per_second}", file=r)
    return 0

res = run()
sys.exit(res)
