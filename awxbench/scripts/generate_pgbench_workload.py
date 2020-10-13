#!/usr/bin/env python

import sys
import os


def write_copy_from_csv_file(path, values, count):
    row = ','.join(values)
    with open(path, 'w') as f:
        for i in range(count):
            f.write(row)
            if i != count-1:
                f.write('\n')


def write_copy_from_sql_file(path, query):
    with open(path, 'w') as f:
        print(query, file=f)


def write_batch_insert_sql_file(path, fields, values, count):
    values_str = ''
    for i in range(count):
        values_str += '('
        for v in values:
            try:
                values_str += f"{int(v)}"
            except Exception:
                values_str += f"'{v}'"
            values_str += ','

        values_str = values_str[:-1] # strip last ,
        values_str += '),'

    values_str = values_str[:-1] # strip last ,
    query = f"INSERT INTO main_jobevent ({','.join(fields)}) VALUES {values_str}"
    with open(path, 'w') as f:
        f.write(query)


def generate_event(size):
    return 'a' * size


def run(output_dir):
    fields = ['parent_uuid','job_id','host_name','event','failed','changed','uuid','playbook','play','role','task','counter','stdout','verbosity','start_line','end_line','modified','event_data']
    values = ['1','1','blah','runner_on_ok','f','f','8cdaade0-74e3-4764-8cd2-0a3b99db8665','test.yml','play','role','task','0','stdout','0','0','0','2020-10-12 01:38:04.585325', generate_event(2048)]
    table = 'main_jobevent'

    csv_file_path = os.path.join(output_dir, 'job_events_copy_from_1000.csv')
    copy_from_sql_path = os.path.join(output_dir, 'job_events_copy_from_1000.sql')
    insert_batch_sql_path = os.path.join(output_dir, 'job_events_insert_batch_1000.sql')

    copy_from_query = f"COPY {table} ({','.join(fields)}) FROM '{{{{ db_benchmark_files_base_path }}}}/job_events_copy_from_1000.csv' DELIMITER ',' CSV"

    write_copy_from_csv_file(csv_file_path, values, 1000)
    write_copy_from_sql_file(copy_from_sql_path, copy_from_query)
    write_batch_insert_sql_file(insert_batch_sql_path, fields, values, 1000)

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <output_dir>", file=sys.stderr)
    sys.exit(-1)

output_dir = sys.argv[1]
run(output_dir)
