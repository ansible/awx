#!/usr/bin/python -u
# Copyright (c) 2010-2012 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import signal
import socket
import logging

from errno import EEXIST, ENOENT
from hashlib import md5
from optparse import OptionParser, SUPPRESS_HELP
from os import environ, listdir, makedirs, utime, _exit as os_exit
from os.path import dirname, getmtime, getsize, isdir, join, \
    sep as os_path_sep
from random import shuffle
from sys import argv as sys_argv, exit, stderr, stdout
from time import sleep, time, gmtime, strftime
from six.moves.urllib.parse import quote, unquote

try:
    import simplejson as json
except ImportError:
    import json

from swiftclient import Connection, RequestException
from swiftclient import command_helpers
from swiftclient.utils import config_true_value, prt_bytes, generate_temp_url
from swiftclient.multithreading import MultiThreadingManager
from swiftclient.exceptions import ClientException
from swiftclient import __version__ as client_version


BASENAME = 'swift'
POLICY = 'X-Storage-Policy'
commands = ('delete', 'download', 'list', 'post',
            'stat', 'upload', 'capabilities', 'info', 'tempurl')


def get_conn(options):
    """
    Return a connection building it from the options.
    """
    return Connection(options.auth,
                      options.user,
                      options.key,
                      options.retries,
                      auth_version=options.auth_version,
                      os_options=options.os_options,
                      snet=options.snet,
                      cacert=options.os_cacert,
                      insecure=options.insecure,
                      ssl_compression=options.ssl_compression)


def mkdirs(path):
    try:
        makedirs(path)
    except OSError as err:
        if err.errno != EEXIST:
            raise


def immediate_exit(signum, frame):
    stderr.write(" Aborted\n")
    os_exit(2)

st_delete_options = '''[-all] [--leave-segments]
                    [--object-threads <threads>]
                    [--container-threads <threads>]
                    <container> [object]
'''

st_delete_help = '''
Delete a container or objects within a container.

Positional arguments:
  <container>           Name of container to delete from.
  [object]              Name of object to delete. Specify multiple times
                        for multiple objects.

Optional arguments:
  --all                 Delete all containers and objects.
  --leave-segments      Do not delete segments of manifest objects.
  --object-threads <threads>
                        Number of threads to use for deleting objects.
                        Default is 10.
  --container-threads <threads>
                        Number of threads to use for deleting containers.
                        Default is 10.
'''.strip("\n")


def st_delete(parser, args, thread_manager):
    parser.add_option(
        '-a', '--all', action='store_true', dest='yes_all',
        default=False, help='Delete all containers and objects.')
    parser.add_option(
        '', '--leave-segments', action='store_true',
        dest='leave_segments', default=False,
        help='Do not delete segments of manifest objects.')
    parser.add_option(
        '', '--object-threads', type=int,
        default=10, help='Number of threads to use for deleting objects. '
        'Default is 10')
    parser.add_option('', '--container-threads', type=int,
                      default=10, help='Number of threads to use for '
                      'deleting containers. '
                      'Default is 10.')
    (options, args) = parse_args(parser, args)
    args = args[1:]
    if (not args and not options.yes_all) or (args and options.yes_all):
        thread_manager.error('Usage: %s delete %s\n%s',
                             BASENAME, st_delete_options,
                             st_delete_help)
        return

    def _delete_segment(item, conn):
        (container, obj) = item
        conn.delete_object(container, obj)
        if options.verbose:
            if conn.attempts > 2:
                thread_manager.print_msg(
                    '%s/%s [after %d attempts]', container,
                    obj, conn.attempts)
            else:
                thread_manager.print_msg('%s/%s', container, obj)

    def _delete_object(item, conn):
        (container, obj) = item
        try:
            old_manifest = None
            query_string = None
            if not options.leave_segments:
                try:
                    headers = conn.head_object(container, obj)
                    old_manifest = headers.get('x-object-manifest')
                    if config_true_value(
                            headers.get('x-static-large-object')):
                        query_string = 'multipart-manifest=delete'
                except ClientException as err:
                    if err.http_status != 404:
                        raise
            conn.delete_object(container, obj, query_string=query_string)
            if old_manifest:
                segment_manager = thread_manager.queue_manager(
                    _delete_segment, options.object_threads,
                    connection_maker=create_connection)
                segment_queue = segment_manager.queue
                scontainer, sprefix = old_manifest.split('/', 1)
                scontainer = unquote(scontainer)
                sprefix = unquote(sprefix).rstrip('/') + '/'
                for delobj in conn.get_container(scontainer,
                                                 prefix=sprefix)[1]:
                    segment_queue.put((scontainer, delobj['name']))
                if not segment_queue.empty():
                    with segment_manager:
                        pass
            if options.verbose:
                path = options.yes_all and join(container, obj) or obj
                if path[:1] in ('/', '\\'):
                    path = path[1:]
                if conn.attempts > 1:
                    thread_manager.print_msg('%s [after %d attempts]', path,
                                             conn.attempts)
                else:
                    thread_manager.print_msg(path)
        except ClientException as err:
            if err.http_status != 404:
                raise
            thread_manager.error("Object '%s/%s' not found", container, obj)

    def _delete_container(container, conn, object_queue):
        try:
            marker = ''
            while True:
                objects = [o['name'] for o in
                           conn.get_container(container, marker=marker)[1]]
                if not objects:
                    break
                for obj in objects:
                    object_queue.put((container, obj))
                marker = objects[-1]
            while not object_queue.empty():
                sleep(0.05)
            attempts = 1
            while True:
                try:
                    conn.delete_container(container)
                    break
                except ClientException as err:
                    if err.http_status != 409:
                        raise
                    if attempts > 10:
                        raise
                    attempts += 1
                    sleep(1)
        except ClientException as err:
            if err.http_status != 404:
                raise
            thread_manager.error('Container %r not found', container)

    create_connection = lambda: get_conn(options)
    obj_manager = thread_manager.queue_manager(
        _delete_object, options.object_threads,
        connection_maker=create_connection)
    with obj_manager as object_queue:
        cont_manager = thread_manager.queue_manager(
            _delete_container, options.container_threads, object_queue,
            connection_maker=create_connection)
        with cont_manager as container_queue:
            if not args:
                conn = create_connection()
                try:
                    marker = ''
                    while True:
                        containers = [
                            c['name']
                            for c in conn.get_account(marker=marker)[1]]
                        if not containers:
                            break
                        for container in containers:
                            container_queue.put(container)
                        marker = containers[-1]
                except ClientException as err:
                    if err.http_status != 404:
                        raise
                    thread_manager.error('Account not found')
            elif len(args) == 1:
                if '/' in args[0]:
                    print(
                        'WARNING: / in container name; you might have meant '
                        '%r instead of %r.' % (
                            args[0].replace('/', ' ', 1), args[0]),
                        file=stderr)
                container_queue.put(args[0])
            else:
                for obj in args[1:]:
                    object_queue.put((args[0], obj))

st_download_options = '''[--all] [--marker] [--prefix <prefix>]
                      [--output <out_file>] [--object-threads <threads>]
                      [--container-threads <threads>] [--no-download]
                      <container> [object]
'''

st_download_help = '''
Download objects from containers.

Positional arguments:
  <container>           Name of container to download from. To download a
                        whole account, omit this and specify --all.
  [object]              Name of object to download. Specify multiple times
                        for multiple objects. Omit this to download all
                        objects from the container.

Optional arguments:
  --all                 Indicates that you really want to download everything
                        in the account.
  --marker              Marker to use when starting a container or account
                        download.
  --prefix <prefix>     Only download items beginning with <prefix>.
  --output <out_file>   For a single file download, stream the output to
                        <out_file>. Specifying "-" as <out_file> will
                        redirect to stdout.
  --object-threads <threads>
                        Number of threads to use for downloading objects.
                        Default is 10
  --container-threads <threads>
                        Number of threads to use for downloading containers.
                        Default is 10
  --no-download         Perform download(s), but don't actually write anything
                        to disk.
  --header <header_name:header_value>
                        Adds a customized request header to the query, like
                        "Range" or "If-Match". This argument is repeatable.
                        Example --header "content-type:text/plain"
  --skip-identical      Skip downloading files that are identical on both
                        sides.
'''.strip("\n")


def st_download(parser, args, thread_manager):
    parser.add_option(
        '-a', '--all', action='store_true', dest='yes_all',
        default=False, help='Indicates that you really want to download '
        'everything in the account.')
    parser.add_option(
        '-m', '--marker', dest='marker',
        default='', help='Marker to use when starting a container or '
        'account download.')
    parser.add_option(
        '-p', '--prefix', dest='prefix',
        help='Only download items beginning with the <prefix>.')
    parser.add_option(
        '-o', '--output', dest='out_file', help='For a single '
        'download, stream the output to <out_file>. '
        'Specifying "-" as <out_file> will redirect to stdout.')
    parser.add_option(
        '', '--object-threads', type=int,
        default=10, help='Number of threads to use for downloading objects. '
        'Default is 10.')
    parser.add_option(
        '', '--container-threads', type=int, default=10,
        help='Number of threads to use for downloading containers. '
        'Default is 10.')
    parser.add_option(
        '', '--no-download', action='store_true',
        default=False,
        help="Perform download(s), but don't actually write anything to disk.")
    parser.add_option(
        '-H', '--header', action='append', dest='header',
        default=[],
        help='Adds a customized request header to the query, like "Range" or '
        '"If-Match". This argument is repeatable. '
        'Example: --header "content-type:text/plain"')
    parser.add_option(
        '--skip-identical', action='store_true', dest='skip_identical',
        default=False, help='Skip downloading files that are identical on '
        'both sides.')
    (options, args) = parse_args(parser, args)
    args = args[1:]
    if options.out_file == '-':
        options.verbose = 0
    if options.out_file and len(args) != 2:
        exit('-o option only allowed for single file downloads')
    if (not args and not options.yes_all) or (args and options.yes_all):
        thread_manager.error('Usage: %s download %s\n%s', BASENAME,
                             st_download_options, st_download_help)
        return
    req_headers = split_headers(options.header, '', thread_manager)

    def _download_object(queue_arg, conn):
        if len(queue_arg) == 2:
            container, obj = queue_arg
            out_file = None
        elif len(queue_arg) == 3:
            container, obj, out_file = queue_arg
        else:
            raise Exception("Invalid queue_arg length of %s" % len(queue_arg))
        path = options.yes_all and join(container, obj) or obj
        path = path.lstrip(os_path_sep)
        if options.skip_identical and out_file != '-':
            filename = out_file if out_file else path
            try:
                fp = open(filename, 'rb')
            except IOError:
                pass
            else:
                with fp:
                    md5sum = md5()
                    while True:
                        data = fp.read(65536)
                        if not data:
                            break
                        md5sum.update(data)
                    req_headers['If-None-Match'] = md5sum.hexdigest()
        try:
            start_time = time()
            headers, body = \
                conn.get_object(container, obj, resp_chunk_size=65536,
                                headers=req_headers)
            headers_receipt = time()
            content_type = headers.get('content-type')
            if 'content-length' in headers:
                content_length = int(headers.get('content-length'))
            else:
                content_length = None
            etag = headers.get('etag')
            md5sum = None
            make_dir = not options.no_download and out_file != "-"
            if content_type.split(';', 1)[0] == 'text/directory':
                if make_dir and not isdir(path):
                    mkdirs(path)
                read_length = 0
                if 'x-object-manifest' not in headers and \
                        'x-static-large-object' not in headers:
                    md5sum = md5()
                for chunk in body:
                    read_length += len(chunk)
                    if md5sum:
                        md5sum.update(chunk)
            else:
                dirpath = dirname(path)
                if make_dir and dirpath and not isdir(dirpath):
                    mkdirs(dirpath)
                if not options.no_download:
                    if out_file == "-":
                        fp = stdout
                    elif out_file:
                        fp = open(out_file, 'wb')
                    else:
                        fp = open(path, 'wb')
                read_length = 0
                if 'x-object-manifest' not in headers and \
                        'x-static-large-object' not in headers:
                    md5sum = md5()
                for chunk in body:
                    if not options.no_download:
                        fp.write(chunk)
                    read_length += len(chunk)
                    if md5sum:
                        md5sum.update(chunk)
                if not options.no_download:
                    fp.close()
            if md5sum and md5sum.hexdigest() != etag:
                thread_manager.error('%s: md5sum != etag, %s != %s',
                                     path, md5sum.hexdigest(), etag)
            if content_length is not None and read_length != content_length:
                thread_manager.error(
                    '%s: read_length != content_length, %d != %d',
                    path, read_length, content_length)
            if 'x-object-meta-mtime' in headers and not options.out_file \
                    and not options.no_download:

                mtime = float(headers['x-object-meta-mtime'])
                utime(path, (mtime, mtime))
            if options.verbose:
                finish_time = time()
                auth_time = conn.auth_end_time - start_time
                headers_receipt = headers_receipt - start_time
                total_time = finish_time - start_time
                download_time = total_time - auth_time
                time_str = ('auth %.3fs, headers %.3fs, total %.3fs, '
                            '%.3f MB/s' % (
                                auth_time, headers_receipt, total_time,
                                float(read_length) / download_time / 1000000))
                if conn.attempts > 1:
                    thread_manager.print_msg('%s [%s after %d attempts]', path,
                                             time_str, conn.attempts)
                else:
                    thread_manager.print_msg('%s [%s]', path, time_str)
        except ClientException as err:
            if err.http_status == 304 and options.skip_identical:
                thread_manager.print_msg("Skipped identical file '%s'", path)
                return
            if err.http_status != 404:
                raise
            thread_manager.error("Object '%s/%s' not found", container, obj)

    def _download_container(queue_arg, conn):
        if len(queue_arg) == 2:
            container, object_queue = queue_arg
            prefix = None
        elif len(queue_arg) == 3:
            container, object_queue, prefix = queue_arg
        else:
            raise Exception("Invalid queue_arg length of %s" % len(queue_arg))
        try:
            marker = options.marker
            while True:
                objects = [
                    o['name'] for o in
                    conn.get_container(container, marker=marker,
                                       prefix=prefix)[1]]
                if not objects:
                    break
                marker = objects[-1]
                shuffle(objects)
                for obj in objects:
                    object_queue.put((container, obj))
        except ClientException as err:
            if err.http_status != 404:
                raise
            thread_manager.error('Container %r not found', container)

    create_connection = lambda: get_conn(options)
    obj_manager = thread_manager.queue_manager(
        _download_object, options.object_threads,
        connection_maker=create_connection)
    with obj_manager as object_queue:
        cont_manager = thread_manager.queue_manager(
            _download_container, options.container_threads,
            connection_maker=create_connection)
        with cont_manager as container_queue:
            if not args:
                # --all case
                conn = create_connection()
                try:
                    marker = options.marker
                    while True:
                        containers = [
                            c['name'] for c in conn.get_account(
                                marker=marker, prefix=options.prefix)[1]]
                        if not containers:
                            break
                        marker = containers[-1]
                        shuffle(containers)
                        for container in containers:
                            container_queue.put((container, object_queue))
                except ClientException as err:
                    if err.http_status != 404:
                        raise
                    thread_manager.error('Account not found')
            elif len(args) == 1:
                if '/' in args[0]:
                    print(
                        'WARNING: / in container name; you might have meant '
                        '%r instead of %r.' % (
                            args[0].replace('/', ' ', 1), args[0]),
                        file=stderr)
                container_queue.put((args[0], object_queue, options.prefix))
            else:
                if len(args) == 2:
                    obj = args[1]
                    object_queue.put((args[0], obj, options.out_file))
                else:
                    for obj in args[1:]:
                        object_queue.put((args[0], obj))

st_list_options = '''[--long] [--lh] [--totals] [--prefix <prefix>]
                  [--delimiter <delimiter>]
'''
st_list_help = '''
Lists the containers for the account or the objects for a container.

Positional arguments:
  [container]           Name of container to list object in.

Optional arguments:
  --long                Long listing format, similar to ls -l.
  --lh                  Report sizes in human readable format similar to
                        ls -lh.
  --totals              Used with -l or --lh, only report totals.
  --prefix              Only list items beginning with the prefix.
  --delimiter           Roll up items with the given delimiter. For containers
                        only. See OpenStack Swift API documentation for what
                        this means.
'''.strip('\n')


def st_list(parser, args, thread_manager):
    parser.add_option(
        '-l', '--long', dest='long', action='store_true', default=False,
        help='Long listing format, similar to ls -l.')
    parser.add_option(
        '--lh', dest='human', action='store_true',
        default=False, help='Report sizes in human readable format, '
        "similar to ls -lh.")
    parser.add_option(
        '-t', '--totals', dest='totals', action='store_true', default=False,
        help='Used with -l or --lh, only report totals.')
    parser.add_option(
        '-p', '--prefix', dest='prefix',
        help='Only list items beginning with the prefix.')
    parser.add_option(
        '-d', '--delimiter', dest='delimiter',
        help='Roll up items with the given delimiter. '
        'For containers only. See OpenStack Swift API documentation for '
        'what this means.')
    (options, args) = parse_args(parser, args)
    args = args[1:]
    if options.delimiter and not args:
        exit('-d option only allowed for container listings')
    if len(args) > 1 or len(args) == 1 and args[0].find('/') >= 0:
        thread_manager.error('Usage: %s list %s\n%s', BASENAME,
                             st_list_options, st_list_help)
        return

    conn = get_conn(options)
    try:
        marker = ''
        total_count = total_bytes = 0
        while True:
            if not args:
                items = \
                    conn.get_account(marker=marker, prefix=options.prefix)[1]
            else:
                items = conn.get_container(
                    args[0], marker=marker,
                    prefix=options.prefix, delimiter=options.delimiter)[1]
            if not items:
                break
            for item in items:
                item_name = item.get('name')

                if not options.long and not options.human:
                    thread_manager.print_msg(
                        item.get('name', item.get('subdir')))
                else:
                    item_bytes = item.get('bytes')
                    total_bytes += item_bytes
                    if len(args) == 0:    # listing containers
                        byte_str = prt_bytes(item_bytes, options.human)
                        count = item.get('count')
                        total_count += count
                        try:
                            meta = conn.head_container(item_name)
                            utc = gmtime(float(meta.get('x-timestamp')))
                            datestamp = strftime('%Y-%m-%d %H:%M:%S', utc)
                        except ClientException:
                            datestamp = '????-??-?? ??:??:??'
                        if not options.totals:
                            thread_manager.print_msg("%5s %s %s %s", count,
                                                     byte_str, datestamp,
                                                     item_name)
                    else:    # list container contents
                        subdir = item.get('subdir')
                        if subdir is None:
                            byte_str = prt_bytes(item_bytes, options.human)
                            date, xtime = item.get('last_modified').split('T')
                            xtime = xtime.split('.')[0]
                        else:
                            byte_str = prt_bytes(0, options.human)
                            date = xtime = ''
                            item_name = subdir
                        if not options.totals:
                            thread_manager.print_msg("%s %10s %8s %s",
                                                     byte_str, date, xtime,
                                                     item_name)

                marker = items[-1].get('name', items[-1].get('subdir'))

        # report totals
        if options.long or options.human:
            if len(args) == 0:
                thread_manager.print_msg(
                    "%5s %s", prt_bytes(total_count, True),
                    prt_bytes(total_bytes, options.human))
            else:
                thread_manager.print_msg(prt_bytes(total_bytes, options.human))

    except ClientException as err:
        if err.http_status != 404:
            raise
        if not args:
            thread_manager.error('Account not found')
        else:
            thread_manager.error('Container %r not found', args[0])

st_stat_options = '''[--lh]
                  [container] [object]
'''

st_stat_help = '''
Displays information for the account, container, or object.

Positional arguments:
  [container]           Name of container to stat from.
  [object]              Name of object to stat. Specify multiple times
                        for multiple objects.

Optional arguments:
  --lh                  Report sizes in human readable format similar to
                        ls -lh.
'''.strip('\n')


def st_stat(parser, args, thread_manager):
    parser.add_option(
        '--lh', dest='human', action='store_true', default=False,
        help='Report sizes in human readable format similar to ls -lh.')
    (options, args) = parse_args(parser, args)
    args = args[1:]
    conn = get_conn(options)
    if not args:
        try:
            command_helpers.stat_account(conn, options, thread_manager)
        except ClientException as err:
            if err.http_status != 404:
                raise
            thread_manager.error('Account not found')
    elif len(args) == 1:
        if '/' in args[0]:
            print(
                'WARNING: / in container name; you might have meant %r instead'
                ' of %r.' % (
                    args[0].replace('/', ' ', 1), args[0]),
                file=stderr)
        try:
            command_helpers.stat_container(conn, options, args,
                                           thread_manager)
        except ClientException as err:
            if err.http_status != 404:
                raise
            thread_manager.error('Container %r not found', args[0])
    elif len(args) == 2:
        try:
            command_helpers.stat_object(conn, options, args, thread_manager)
        except ClientException as err:
            if err.http_status != 404:
                raise
            thread_manager.error("Object %s/%s not found", args[0], args[1])
    else:
        thread_manager.error('Usage: %s stat %s\n%s', BASENAME,
                             st_stat_options, st_stat_help)


st_post_options = '''[--read-acl <acl>] [--write-acl <acl>] [--sync-to]
                  [--sync-key <sync-key>] [--meta <name:value>]
                  [--header <header>]
                  [container] [object]
'''

st_post_help = '''
Updates meta information for the account, container, or object.
If the container is not found, it will be created automatically.

Positional arguments:
  [container]           Name of container to post to.
  [object]              Name of object to post. Specify multiple times
                        for multiple objects.

Optional arguments:
  --read-acl <acl>      Read ACL for containers. Quick summary of ACL syntax:
                        .r:*, .r:-.example.com, .r:www.example.com, account1,
                        account2:user2
  --write-acl <acl>     Write ACL for containers. Quick summary of ACL syntax:
                        account1 account2:user2
  --sync-to <sync-to>   Sync To for containers, for multi-cluster replication.
  --sync-key <sync-key> Sync Key for containers, for multi-cluster replication.
  --meta <name:value>   Sets a meta data item. This option may be repeated.
                        Example: -m Color:Blue -m Size:Large
  --header <header>     Set request headers. This option may be repeated.
                        Example -H "content-type:text/plain"
'''.strip('\n')


def st_post(parser, args, thread_manager):
    parser.add_option(
        '-r', '--read-acl', dest='read_acl', help='Read ACL for containers. '
        'Quick summary of ACL syntax: .r:*, .r:-.example.com, '
        '.r:www.example.com, account1, account2:user2')
    parser.add_option(
        '-w', '--write-acl', dest='write_acl', help='Write ACL for '
        'containers. Quick summary of ACL syntax: account1, '
        'account2:user2')
    parser.add_option(
        '-t', '--sync-to', dest='sync_to', help='Sets the '
        'Sync To for containers, for multi-cluster replication.')
    parser.add_option(
        '-k', '--sync-key', dest='sync_key', help='Sets the '
        'Sync Key for containers, for multi-cluster replication.')
    parser.add_option(
        '-m', '--meta', action='append', dest='meta', default=[],
        help='Sets a meta data item. This option may be repeated. '
        'Example: -m Color:Blue -m Size:Large')
    parser.add_option(
        '-H', '--header', action='append', dest='header',
        default=[], help='Set request headers. This option may be repeated. '
        'Example: -H "content-type:text/plain" '
        '-H "Content-Length: 4000"')
    (options, args) = parse_args(parser, args)
    args = args[1:]
    if (options.read_acl or options.write_acl or options.sync_to or
            options.sync_key) and not args:
        exit('-r, -w, -t, and -k options only allowed for containers')
    conn = get_conn(options)
    if not args:
        headers = split_headers(
            options.meta, 'X-Account-Meta-', thread_manager)
        headers.update(split_headers(options.header, '', thread_manager))
        try:
            conn.post_account(headers=headers)
        except ClientException as err:
            if err.http_status != 404:
                raise
            thread_manager.error('Account not found')
    elif len(args) == 1:
        if '/' in args[0]:
            print(
                'WARNING: / in container name; you might have meant %r instead'
                ' of %r.' % (
                    args[0].replace('/', ' ', 1), args[0]),
                file=stderr)
        headers = split_headers(options.meta, 'X-Container-Meta-',
                                thread_manager)
        headers.update(split_headers(options.header, '', thread_manager))
        if options.read_acl is not None:
            headers['X-Container-Read'] = options.read_acl
        if options.write_acl is not None:
            headers['X-Container-Write'] = options.write_acl
        if options.sync_to is not None:
            headers['X-Container-Sync-To'] = options.sync_to
        if options.sync_key is not None:
            headers['X-Container-Sync-Key'] = options.sync_key
        try:
            conn.post_container(args[0], headers=headers)
        except ClientException as err:
            if err.http_status != 404:
                raise
            conn.put_container(args[0], headers=headers)
    elif len(args) == 2:
        headers = split_headers(options.meta, 'X-Object-Meta-', thread_manager)
        # add header options to the headers object for the request.
        headers.update(split_headers(options.header, '', thread_manager))
        try:
            conn.post_object(args[0], args[1], headers=headers)
        except ClientException as err:
            if err.http_status != 404:
                raise
            thread_manager.error("Object '%s/%s' not found", args[0], args[1])
    else:
        thread_manager.error('Usage: %s post %s\n%s', BASENAME,
                             st_post_options, st_post_help)

st_upload_options = '''[--changed] [--skip-identical] [--segment-size <size>]
                    [--segment-container <container>] [--leave-segments]
                    [--object-threads <thread>] [--segment-threads <threads>]
                    [--header <header>] [--use-slo]
                    [--object-name <object-name>]
                    <container> <file_or_directory>
'''

st_upload_help = '''
Uploads specified files and directories to the given container.

Positional arguments:
  <container>           Name of container to upload to.
  <file_or_directory>   Name of file or directory to upload. Specify multiple
                        times for multiple uploads.

Optional arguments:
  --changed             Only upload files that have changed since the last
                        upload.
  --skip-identical      Skip uploading files that are identical on both sides.
  --segment-size <size> Upload files in segments no larger than <size> (in
                        Bytes) and then create a "manifest" file that will
                        download all the segments as if it were the original
                        file.
  --segment-container <container>
                        Upload the segments into the specified container. If
                        not specified, the segments will be uploaded to a
                        <container>_segments container to not pollute the
                        main <container> listings.
  --leave-segments      Indicates that you want the older segments of manifest
                        objects left alone (in the case of overwrites).
  --object-threads <threads>
                        Number of threads to use for uploading full objects.
                        Default is 10.
  --segment-threads <threads>
                        Number of threads to use for uploading object segments.
                        Default is 10.
  --header <header>     Set request headers with the syntax header:value.
                        This option may be repeated.
                        Example -H "content-type:text/plain".
  --use-slo             When used in conjunction with --segment-size it will
                        create a Static Large Object instead of the default
                        Dynamic Large Object.
  --object-name <object-name>
                        Upload file and name object to <object-name> or upload
                        dir and use <object-name> as object prefix instead of
                        folder name.
'''.strip('\n')


def st_upload(parser, args, thread_manager):
    parser.add_option(
        '-c', '--changed', action='store_true', dest='changed',
        default=False, help='Only upload files that have changed since '
        'the last upload.')
    parser.add_option(
        '--skip-identical', action='store_true', dest='skip_identical',
        default=False, help='Skip uploading files that are identical on '
        'both sides.')
    parser.add_option(
        '-S', '--segment-size', dest='segment_size', help='Upload files '
        'in segments no larger than <size> (in Bytes) and then create a '
        '"manifest" file that will download all the segments as if it were '
        'the original file.')
    parser.add_option(
        '-C', '--segment-container', dest='segment_container',
        help='Upload the segments into the specified container. '
        'If not specified, the segments will be uploaded to a '
        '<container>_segments container to not pollute the main '
        '<container> listings.')
    parser.add_option(
        '', '--leave-segments', action='store_true',
        dest='leave_segments', default=False, help='Indicates that you want '
        'the older segments of manifest objects left alone (in the case of '
        'overwrites).')
    parser.add_option(
        '', '--object-threads', type=int, default=10,
        help='Number of threads to use for uploading full objects. '
        'Default is 10.')
    parser.add_option(
        '', '--segment-threads', type=int, default=10,
        help='Number of threads to use for uploading object segments. '
        'Default is 10.')
    parser.add_option(
        '-H', '--header', action='append', dest='header',
        default=[], help='Set request headers with the syntax header:value. '
        ' This option may be repeated. Example -H "content-type:text/plain" '
        '-H "Content-Length: 4000"')
    parser.add_option(
        '', '--use-slo', action='store_true', default=False,
        help='When used in conjunction with --segment-size, it will '
        'create a Static Large Object instead of the default '
        'Dynamic Large Object.')
    parser.add_option(
        '', '--object-name', dest='object_name',
        help='Upload file and name object to <object-name> or upload dir and '
        'use <object-name> as object prefix instead of folder name.')
    (options, args) = parse_args(parser, args)
    args = args[1:]
    if len(args) < 2:
        thread_manager.error(
            'Usage: %s upload %s\n%s', BASENAME, st_upload_options,
            st_upload_help)
        return

    def _segment_job(job, conn):
        if job.get('delete', False):
            conn.delete_object(job['container'], job['obj'])
        else:
            fp = open(job['path'], 'rb')
            fp.seek(job['segment_start'])
            seg_container = args[0] + '_segments'
            if options.segment_container:
                seg_container = options.segment_container
            etag = conn.put_object(job.get('container', seg_container),
                                   job['obj'], fp,
                                   content_length=job['segment_size'])
            job['segment_location'] = '/%s/%s' % (seg_container, job['obj'])
            job['segment_etag'] = etag
        if options.verbose and 'log_line' in job:
            if conn.attempts > 1:
                thread_manager.print_msg('%s [after %d attempts]',
                                         job['log_line'], conn.attempts)
            else:
                thread_manager.print_msg(job['log_line'])
        return job

    def _object_job(job, conn):
        path = job['path']
        container = job.get('container', args[0])
        dir_marker = job.get('dir_marker', False)
        object_name = job['object_name']
        try:
            if object_name is not None:
                object_name.replace("\\", "/")
                obj = object_name
            else:
                obj = path
                if obj.startswith('./') or obj.startswith('.\\'):
                    obj = obj[2:]
                if obj.startswith('/'):
                    obj = obj[1:]
            put_headers = {'x-object-meta-mtime': "%f" % getmtime(path)}
            if dir_marker:
                if options.changed:
                    try:
                        headers = conn.head_object(container, obj)
                        ct = headers.get('content-type')
                        cl = int(headers.get('content-length'))
                        et = headers.get('etag')
                        mt = headers.get('x-object-meta-mtime')
                        if ct.split(';', 1)[0] == 'text/directory' and \
                                cl == 0 and \
                                et == 'd41d8cd98f00b204e9800998ecf8427e' and \
                                mt == put_headers['x-object-meta-mtime']:
                            return
                    except ClientException as err:
                        if err.http_status != 404:
                            raise
                conn.put_object(container, obj, '', content_length=0,
                                content_type='text/directory',
                                headers=put_headers)
            else:
                # We need to HEAD all objects now in case we're overwriting a
                # manifest object and need to delete the old segments
                # ourselves.
                old_manifest = None
                old_slo_manifest_paths = []
                new_slo_manifest_paths = set()
                if options.changed or options.skip_identical \
                        or not options.leave_segments:
                    if options.skip_identical:
                        checksum = None
                        try:
                            fp = open(path, 'rb')
                        except IOError:
                            pass
                        else:
                            with fp:
                                md5sum = md5()
                                while True:
                                    data = fp.read(65536)
                                    if not data:
                                        break
                                    md5sum.update(data)
                            checksum = md5sum.hexdigest()
                    try:
                        headers = conn.head_object(container, obj)
                        cl = int(headers.get('content-length'))
                        mt = headers.get('x-object-meta-mtime')
                        if (options.skip_identical and
                                checksum == headers.get('etag')):
                            thread_manager.print_msg(
                                "Skipped identical file '%s'", path)
                            return
                        if options.changed and cl == getsize(path) and \
                                mt == put_headers['x-object-meta-mtime']:
                            return
                        if not options.leave_segments:
                            old_manifest = headers.get('x-object-manifest')
                            if config_true_value(
                                    headers.get('x-static-large-object')):
                                headers, manifest_data = conn.get_object(
                                    container, obj,
                                    query_string='multipart-manifest=get')
                                for old_seg in json.loads(manifest_data):
                                    seg_path = old_seg['name'].lstrip('/')
                                    if isinstance(seg_path, unicode):
                                        seg_path = seg_path.encode('utf-8')
                                    old_slo_manifest_paths.append(seg_path)
                    except ClientException as err:
                        if err.http_status != 404:
                            raise
                # Merge the command line header options to the put_headers
                put_headers.update(split_headers(options.header, '',
                                                 thread_manager))
                # Don't do segment job if object is not big enough
                if options.segment_size and \
                        getsize(path) > int(options.segment_size):
                    seg_container = container + '_segments'
                    if options.segment_container:
                        seg_container = options.segment_container
                    full_size = getsize(path)

                    slo_segments = []
                    error_counter = [0]
                    segment_manager = thread_manager.queue_manager(
                        _segment_job, options.segment_threads,
                        store_results=slo_segments,
                        error_counter=error_counter,
                        connection_maker=create_connection)
                    with segment_manager as segment_queue:
                        segment = 0
                        segment_start = 0
                        while segment_start < full_size:
                            segment_size = int(options.segment_size)
                            if segment_start + segment_size > full_size:
                                segment_size = full_size - segment_start
                            if options.use_slo:
                                segment_name = '%s/slo/%s/%s/%s/%08d' % (
                                    obj, put_headers['x-object-meta-mtime'],
                                    full_size, options.segment_size, segment)
                            else:
                                segment_name = '%s/%s/%s/%s/%08d' % (
                                    obj, put_headers['x-object-meta-mtime'],
                                    full_size, options.segment_size, segment)
                            segment_queue.put(
                                {'path': path, 'obj': segment_name,
                                 'segment_start': segment_start,
                                 'segment_size': segment_size,
                                 'segment_index': segment,
                                 'log_line': '%s segment %s' % (obj, segment)})
                            segment += 1
                            segment_start += segment_size
                    if error_counter[0]:
                        raise ClientException(
                            'Aborting manifest creation '
                            'because not all segments could be uploaded. %s/%s'
                            % (container, obj))
                    if options.use_slo:
                        slo_segments.sort(key=lambda d: d['segment_index'])
                        for seg in slo_segments:
                            seg_loc = seg['segment_location'].lstrip('/')
                            if isinstance(seg_loc, unicode):
                                seg_loc = seg_loc.encode('utf-8')
                            new_slo_manifest_paths.add(seg_loc)

                        manifest_data = json.dumps([
                            {'path': d['segment_location'],
                             'etag': d['segment_etag'],
                             'size_bytes': d['segment_size']}
                            for d in slo_segments])

                        put_headers['x-static-large-object'] = 'true'
                        conn.put_object(container, obj, manifest_data,
                                        headers=put_headers,
                                        query_string='multipart-manifest=put')
                    else:
                        new_object_manifest = '%s/%s/%s/%s/%s/' % (
                            quote(seg_container), quote(obj),
                            put_headers['x-object-meta-mtime'], full_size,
                            options.segment_size)
                        if old_manifest and old_manifest.rstrip('/') == \
                                new_object_manifest.rstrip('/'):
                            old_manifest = None
                        put_headers['x-object-manifest'] = new_object_manifest
                        conn.put_object(container, obj, '', content_length=0,
                                        headers=put_headers)
                else:
                    conn.put_object(
                        container, obj, open(path, 'rb'),
                        content_length=getsize(path), headers=put_headers)
                if old_manifest or old_slo_manifest_paths:
                    segment_manager = thread_manager.queue_manager(
                        _segment_job, options.segment_threads,
                        connection_maker=create_connection)
                    segment_queue = segment_manager.queue
                    if old_manifest:
                        scontainer, sprefix = old_manifest.split('/', 1)
                        scontainer = unquote(scontainer)
                        sprefix = unquote(sprefix).rstrip('/') + '/'
                        for delobj in conn.get_container(scontainer,
                                                         prefix=sprefix)[1]:
                            segment_queue.put(
                                {'delete': True,
                                 'container': scontainer,
                                 'obj': delobj['name']})
                    if old_slo_manifest_paths:
                        for seg_to_delete in old_slo_manifest_paths:
                            if seg_to_delete in new_slo_manifest_paths:
                                continue
                            scont, sobj = \
                                seg_to_delete.split('/', 1)
                            segment_queue.put(
                                {'delete': True,
                                 'container': scont, 'obj': sobj})
                    if not segment_queue.empty():
                        with segment_manager:
                            pass
            if options.verbose:
                if conn.attempts > 1:
                    thread_manager.print_msg('%s [after %d attempts]', obj,
                                             conn.attempts)
                else:
                    thread_manager.print_msg(obj)
        except OSError as err:
            if err.errno != ENOENT:
                raise
            thread_manager.error('Local file %r not found', path)

    def _upload_dir(path, object_queue, object_name):
        names = listdir(path)
        if not names:
            object_queue.put({'path': path, 'object_name': object_name,
                             'dir_marker': True})
        else:
            for name in listdir(path):
                subpath = join(path, name)
                subobjname = None
                if object_name is not None:
                    subobjname = join(object_name, name)
                if isdir(subpath):
                    _upload_dir(subpath, object_queue, subobjname)
                else:
                    object_queue.put({'path': subpath,
                                     'object_name': subobjname})

    create_connection = lambda: get_conn(options)
    conn = create_connection()

    # Try to create the container, just in case it doesn't exist. If this
    # fails, it might just be because the user doesn't have container PUT
    # permissions, so we'll ignore any error. If there's really a problem,
    # it'll surface on the first object PUT.
    container_name = args[0]
    try:
        policy_header = {}
        _header = split_headers(options.header)
        if POLICY in _header:
            policy_header[POLICY] = \
                _header[POLICY]
        try:
            conn.put_container(args[0], policy_header)
        except ClientException as err:
            if err.http_status != 409:
                raise
            if POLICY in _header:
                thread_manager.error('Error trying to create %s with '
                                     'Storage Policy %s', args[0],
                                     _header[POLICY].strip())
        if options.segment_size is not None:
            container_name = seg_container = args[0] + '_segments'
            if options.segment_container:
                container_name = seg_container = options.segment_container
            seg_headers = {}
            if POLICY in _header:
                seg_headers[POLICY] = \
                    _header[POLICY]
            else:
                # Since no storage policy was specified on the command line,
                # rather than just letting swift pick the default storage
                # policy, we'll try to create the segments container with the
                # same as the upload container
                _meta = conn.head_container(args[0])
                if 'x-storage-policy' in _meta:
                    seg_headers[POLICY] = \
                        _meta.get('x-storage-policy')
            try:
                conn.put_container(seg_container, seg_headers)
            except ClientException as err:
                if err.http_status != 409:
                    raise
                if POLICY in seg_headers:
                    thread_manager.error('Error trying to create %s with '
                                         'Storage Policy %s', seg_container,
                                         seg_headers[POLICY].strip())
    except ClientException as err:
        msg = ' '.join(str(x) for x in (err.http_status, err.http_reason))
        if err.http_response_content:
            if msg:
                msg += ': '
            msg += err.http_response_content[:60]
        thread_manager.error(
            'Error trying to create container %r: %s', container_name,
            msg)
    except Exception as err:
        thread_manager.error(
            'Error trying to create container %r: %s', container_name,
            err)

    if options.object_name is not None:
        if len(args[1:]) > 1:
            thread_manager.error('object-name only be used with 1 file or dir')
            return
    object_name = options.object_name

    object_manager = thread_manager.queue_manager(
        _object_job, options.object_threads,
        connection_maker=create_connection)
    with object_manager as object_queue:
        try:
            for arg in args[1:]:
                if isdir(arg):
                    _upload_dir(arg, object_queue, object_name)
                else:
                    object_queue.put({'path': arg, 'object_name': object_name})
        except ClientException as err:
            if err.http_status != 404:
                raise
            thread_manager.error('Account not found')


st_capabilities_options = "[<proxy_url>]"
st_info_options = st_capabilities_options
st_capabilities_help = '''
Retrieve capability of the proxy.

Optional positional arguments:
  <proxy_url>           Proxy URL of the cluster to retrieve capabilities.
'''.strip('\n')
st_info_help = st_capabilities_help


def st_capabilities(parser, args, thread_manager):
    def _print_compo_cap(name, capabilities):
        for feature, options in sorted(capabilities.items(),
                                       key=lambda x: x[0]):
            thread_manager.print_msg("%s: %s" % (name, feature))
            if options:
                thread_manager.print_msg(" Options:")
                for key, value in sorted(options.items(),
                                         key=lambda x: x[0]):
                    thread_manager.print_msg("  %s: %s" % (key, value))
    (options, args) = parse_args(parser, args)
    if (args and len(args) > 2):
        thread_manager.error('Usage: %s capabilities %s\n%s',
                             BASENAME,
                             st_capabilities_options, st_capabilities_help)
        return
    conn = get_conn(options)
    url = None
    if len(args) == 2:
        url = args[1]
    capabilities = conn.get_capabilities(url)
    _print_compo_cap('Core', {'swift': capabilities['swift']})
    del capabilities['swift']
    _print_compo_cap('Additional middleware', capabilities)

st_info = st_capabilities


st_tempurl_options = '<method> <seconds> <path> <key>'

st_tempurl_help = '''
Generates a temporary URL for a Swift object.

Positions arguments:
  [method]              An HTTP method to allow for this temporary URL.
                        Usually 'GET' or 'PUT'.
  [seconds]             The amount of time in seconds the temporary URL will
                        be valid for.
  [path]                The full path to the Swift object. Example:
                        /v1/AUTH_account/c/o.
  [key]                 The secret temporary URL key set on the Swift cluster.
                        To set a key, run \'swift post -m
                        "Temp-URL-Key:b3968d0207b54ece87cccc06515a89d4"\'
'''.strip('\n')


def st_tempurl(parser, args, thread_manager):
    (options, args) = parse_args(parser, args)
    args = args[1:]
    if len(args) < 4:
        thread_manager.error('Usage: %s tempurl %s\n%s', BASENAME,
                             st_tempurl_options, st_tempurl_help)
        return
    method, seconds, path, key = args[:4]
    try:
        seconds = int(seconds)
    except ValueError:
        thread_manager.error('Seconds must be an integer')
        return
    if method.upper() not in ['GET', 'PUT', 'HEAD', 'POST', 'DELETE']:
        thread_manager.print_msg('WARNING: Non default HTTP method %s for '
                                 'tempurl specified, possibly an error' %
                                 method.upper())
    url = generate_temp_url(path, seconds, key, method)
    thread_manager.print_msg(url)


def split_headers(options, prefix='', thread_manager=None):
    """
    Splits 'Key: Value' strings and returns them as a dictionary.

    :param options: An array of 'Key: Value' strings
    :param prefix: String to prepend to all of the keys in the dictionary.
    :param thread_manager: MultiThreadingManager for thread safe error
        reporting.
    """
    headers = {}
    for item in options:
        split_item = item.split(':', 1)
        if len(split_item) == 2:
            headers[(prefix + split_item[0]).title()] = split_item[1]
        else:
            error_string = "Metadata parameter %s must contain a ':'.\n%s" \
                           % (item, st_post_help)
            if thread_manager:
                thread_manager.error(error_string)
            else:
                exit(error_string)
    return headers


def parse_args(parser, args, enforce_requires=True):
    if not args:
        args = ['-h']
    (options, args) = parser.parse_args(args)

    if len(args) > 1 and args[1] == '--help':
        _help = globals().get('st_%s_help' % args[0],
                              "no help for %s" % args[0])
        print(_help)
        exit()

    # Short circuit for tempurl, which doesn't need auth
    if len(args) > 0 and args[0] == 'tempurl':
        return options, args

    if (not (options.auth and options.user and options.key)):
        # Use 2.0 auth if none of the old args are present
        options.auth_version = '2.0'

    # Use new-style args if old ones not present
    if not options.auth and options.os_auth_url:
        options.auth = options.os_auth_url
    if not options.user and options.os_username:
        options.user = options.os_username
    if not options.key and options.os_password:
        options.key = options.os_password

    # Specific OpenStack options
    options.os_options = {
        'tenant_id': options.os_tenant_id,
        'tenant_name': options.os_tenant_name,
        'service_type': options.os_service_type,
        'endpoint_type': options.os_endpoint_type,
        'auth_token': options.os_auth_token,
        'object_storage_url': options.os_storage_url,
        'region_name': options.os_region_name,
    }

    if len(args) > 1 and args[0] == "capabilities":
        return options, args

    if (options.os_options.get('object_storage_url') and
            options.os_options.get('auth_token') and
            options.auth_version == '2.0'):
        return options, args

    if enforce_requires and \
            not (options.auth and options.user and options.key):
        exit('''
Auth version 1.0 requires ST_AUTH, ST_USER, and ST_KEY environment variables
to be set or overridden with -A, -U, or -K.

Auth version 2.0 requires OS_AUTH_URL, OS_USERNAME, OS_PASSWORD, and
OS_TENANT_NAME OS_TENANT_ID to be set or overridden with --os-auth-url,
--os-username, --os-password, --os-tenant-name or os-tenant-id. Note:
adding "-V 2" is necessary for this.'''.strip('\n'))
    return options, args


def main(arguments=None):
    if arguments:
        argv = arguments
    else:
        argv = sys_argv

    version = client_version
    parser = OptionParser(version='%%prog %s' % version,
                          usage='''
usage: %%prog [--version] [--help] [--snet] [--verbose]
             [--debug] [--info] [--quiet] [--auth <auth_url>]
             [--auth-version <auth_version>] [--user <username>]
             [--key <api_key>] [--retries <num_retries>]
             [--os-username <auth-user-name>] [--os-password <auth-password>]
             [--os-tenant-id <auth-tenant-id>]
             [--os-tenant-name <auth-tenant-name>]
             [--os-auth-url <auth-url>] [--os-auth-token <auth-token>]
             [--os-storage-url <storage-url>] [--os-region-name <region-name>]
             [--os-service-type <service-type>]
             [--os-endpoint-type <endpoint-type>]
             [--os-cacert <ca-certificate>] [--insecure]
             [--no-ssl-compression]
             <subcommand> [--help]

Command-line interface to the OpenStack Swift API.

Positional arguments:
  <subcommand>
    delete               Delete a container or objects within a container.
    download             Download objects from containers.
    list                 Lists the containers for the account or the objects
                         for a container.
    post                 Updates meta information for the account, container,
                         or object; creates containers if not present.
    stat                 Displays information for the account, container,
                         or object.
    upload               Uploads files or directories to the given container.
    capabilities         List cluster capabilities.
    tempurl              Create a temporary URL


Examples:
  %%prog download --help

  %%prog -A https://auth.api.rackspacecloud.com/v1.0 -U user -K api_key stat -v

  %%prog --os-auth-url https://api.example.com/v2.0 --os-tenant-name tenant \\
      --os-username user --os-password password list

  %%prog --os-auth-token 6ee5eb33efad4e45ab46806eac010566 \\
      --os-storage-url https://10.1.5.2:8080/v1/AUTH_ced809b6a4baea7aeab61a \\
      list

  %%prog list --lh
'''.strip('\n') % globals())
    parser.add_option('-s', '--snet', action='store_true', dest='snet',
                      default=False, help='Use SERVICENET internal network.')
    parser.add_option('-v', '--verbose', action='count', dest='verbose',
                      default=1, help='Print more info.')
    parser.add_option('--debug', action='store_true', dest='debug',
                      default=False, help='Show the curl commands and results '
                      'of all http queries regardless of result status.')
    parser.add_option('--info', action='store_true', dest='info',
                      default=False, help='Show the curl commands and results '
                      ' of all http queries which return an error.')
    parser.add_option('-q', '--quiet', action='store_const', dest='verbose',
                      const=0, default=1, help='Suppress status output.')
    parser.add_option('-A', '--auth', dest='auth',
                      default=environ.get('ST_AUTH'),
                      help='URL for obtaining an auth token.')
    parser.add_option('-V', '--auth-version',
                      dest='auth_version',
                      default=environ.get('ST_AUTH_VERSION', '1.0'),
                      type=str,
                      help='Specify a version for authentication. '
                           'Defaults to 1.0.')
    parser.add_option('-U', '--user', dest='user',
                      default=environ.get('ST_USER'),
                      help='User name for obtaining an auth token.')
    parser.add_option('-K', '--key', dest='key',
                      default=environ.get('ST_KEY'),
                      help='Key for obtaining an auth token.')
    parser.add_option('-R', '--retries', type=int, default=5, dest='retries',
                      help='The number of times to retry a failed connection.')
    parser.add_option('--os-username',
                      metavar='<auth-user-name>',
                      default=environ.get('OS_USERNAME'),
                      help='OpenStack username. Defaults to env[OS_USERNAME].')
    parser.add_option('--os_username',
                      help=SUPPRESS_HELP)
    parser.add_option('--os-password',
                      metavar='<auth-password>',
                      default=environ.get('OS_PASSWORD'),
                      help='OpenStack password. Defaults to env[OS_PASSWORD].')
    parser.add_option('--os_password',
                      help=SUPPRESS_HELP)
    parser.add_option('--os-tenant-id',
                      metavar='<auth-tenant-id>',
                      default=environ.get('OS_TENANT_ID'),
                      help='OpenStack tenant ID. '
                      'Defaults to env[OS_TENANT_ID].')
    parser.add_option('--os_tenant_id',
                      help=SUPPRESS_HELP)
    parser.add_option('--os-tenant-name',
                      metavar='<auth-tenant-name>',
                      default=environ.get('OS_TENANT_NAME'),
                      help='OpenStack tenant name. '
                           'Defaults to env[OS_TENANT_NAME].')
    parser.add_option('--os_tenant_name',
                      help=SUPPRESS_HELP)
    parser.add_option('--os-auth-url',
                      metavar='<auth-url>',
                      default=environ.get('OS_AUTH_URL'),
                      help='OpenStack auth URL. Defaults to env[OS_AUTH_URL].')
    parser.add_option('--os_auth_url',
                      help=SUPPRESS_HELP)
    parser.add_option('--os-auth-token',
                      metavar='<auth-token>',
                      default=environ.get('OS_AUTH_TOKEN'),
                      help='OpenStack token. Defaults to env[OS_AUTH_TOKEN]. '
                           'Used with --os-storage-url to bypass the '
                           'usual username/password authentication.')
    parser.add_option('--os_auth_token',
                      help=SUPPRESS_HELP)
    parser.add_option('--os-storage-url',
                      metavar='<storage-url>',
                      default=environ.get('OS_STORAGE_URL'),
                      help='OpenStack storage URL. '
                           'Defaults to env[OS_STORAGE_URL]. '
                           'Overrides the storage url returned during auth. '
                           'Will bypass authentication when used with '
                           '--os-auth-token.')
    parser.add_option('--os_storage_url',
                      help=SUPPRESS_HELP)
    parser.add_option('--os-region-name',
                      metavar='<region-name>',
                      default=environ.get('OS_REGION_NAME'),
                      help='OpenStack region name. '
                           'Defaults to env[OS_REGION_NAME].')
    parser.add_option('--os_region_name',
                      help=SUPPRESS_HELP)
    parser.add_option('--os-service-type',
                      metavar='<service-type>',
                      default=environ.get('OS_SERVICE_TYPE'),
                      help='OpenStack Service type. '
                           'Defaults to env[OS_SERVICE_TYPE].')
    parser.add_option('--os_service_type',
                      help=SUPPRESS_HELP)
    parser.add_option('--os-endpoint-type',
                      metavar='<endpoint-type>',
                      default=environ.get('OS_ENDPOINT_TYPE'),
                      help='OpenStack Endpoint type. '
                           'Defaults to env[OS_ENDPOINT_TYPE].')
    parser.add_option('--os-cacert',
                      metavar='<ca-certificate>',
                      default=environ.get('OS_CACERT'),
                      help='Specify a CA bundle file to use in verifying a '
                      'TLS (https) server certificate. '
                      'Defaults to env[OS_CACERT].')
    default_val = config_true_value(environ.get('SWIFTCLIENT_INSECURE'))
    parser.add_option('--insecure',
                      action="store_true", dest="insecure",
                      default=default_val,
                      help='Allow swiftclient to access servers without '
                           'having to verify the SSL certificate. '
                           'Defaults to env[SWIFTCLIENT_INSECURE] '
                           '(set to \'true\' to enable).')
    parser.add_option('--no-ssl-compression',
                      action='store_false', dest='ssl_compression',
                      default=True,
                      help='This option is deprecated and not used anymore. '
                           'SSL compression should be disabled by default '
                           'by the system SSL library.')
    parser.disable_interspersed_args()
    (options, args) = parse_args(parser, argv[1:], enforce_requires=False)
    parser.enable_interspersed_args()

    if not args or args[0] not in commands:
        parser.print_usage()
        if args:
            exit('no such command: %s' % args[0])
        exit()

    signal.signal(signal.SIGINT, immediate_exit)

    if options.debug or options.info:
        logging.getLogger("swiftclient")
        if options.debug:
            logging.basicConfig(level=logging.DEBUG)
        elif options.info:
            logging.basicConfig(level=logging.INFO)

    had_error = False

    with MultiThreadingManager() as thread_manager:
        parser.usage = globals()['st_%s_help' % args[0]]
        try:
            globals()['st_%s' % args[0]](parser, argv[1:], thread_manager)
        except (ClientException, RequestException, socket.error) as err:
            thread_manager.error(str(err))

        had_error = thread_manager.error_count

    if had_error:
        exit(1)


if __name__ == '__main__':
    main()
