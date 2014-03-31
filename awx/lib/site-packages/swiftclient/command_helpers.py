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

from swiftclient.utils import prt_bytes


def stat_account(conn, options, thread_manager):
    headers = conn.head_account()
    if options.verbose > 1:
        thread_manager.print_items((
            ('StorageURL', conn.url),
            ('Auth Token', conn.token),
        ))
    container_count = int(headers.get('x-account-container-count', 0))
    object_count = prt_bytes(headers.get('x-account-object-count', 0),
                             options.human).lstrip()
    bytes_used = prt_bytes(headers.get('x-account-bytes-used', 0),
                           options.human).lstrip()
    thread_manager.print_items((
        ('Account', conn.url.rsplit('/', 1)[-1]),
        ('Containers', container_count),
        ('Objects', object_count),
        ('Bytes', bytes_used),
    ))
    thread_manager.print_headers(headers,
                                 meta_prefix='x-account-meta-',
                                 exclude_headers=(
                                     'content-length', 'date',
                                     'x-account-container-count',
                                     'x-account-object-count',
                                     'x-account-bytes-used'))


def stat_container(conn, options, args, thread_manager):
    headers = conn.head_container(args[0])
    if options.verbose > 1:
        path = '%s/%s' % (conn.url, args[0])
        thread_manager.print_items((
            ('URL', path),
            ('Auth Token', conn.token),
        ))
    object_count = prt_bytes(
        headers.get('x-container-object-count', 0),
        options.human).lstrip()
    bytes_used = prt_bytes(headers.get('x-container-bytes-used', 0),
                           options.human).lstrip()
    thread_manager.print_items((
        ('Account', conn.url.rsplit('/', 1)[-1]),
        ('Container', args[0]),
        ('Objects', object_count),
        ('Bytes', bytes_used),
        ('Read ACL', headers.get('x-container-read', '')),
        ('Write ACL', headers.get('x-container-write', '')),
        ('Sync To', headers.get('x-container-sync-to', '')),
        ('Sync Key', headers.get('x-container-sync-key', '')),
    ))
    thread_manager.print_headers(headers,
                                 meta_prefix='x-container-meta-',
                                 exclude_headers=(
                                     'content-length', 'date',
                                     'x-container-object-count',
                                     'x-container-bytes-used',
                                     'x-container-read',
                                     'x-container-write',
                                     'x-container-sync-to',
                                     'x-container-sync-key'))


def stat_object(conn, options, args, thread_manager):
    headers = conn.head_object(args[0], args[1])
    if options.verbose > 1:
        path = '%s/%s/%s' % (conn.url, args[0], args[1])
        thread_manager.print_items((
            ('URL', path),
            ('Auth Token', conn.token),
        ))
    content_length = prt_bytes(headers.get('content-length', 0),
                               options.human).lstrip()
    thread_manager.print_items((
        ('Account', conn.url.rsplit('/', 1)[-1]),
        ('Container', args[0]),
        ('Object', args[1]),
        ('Content Type', headers.get('content-type')),
        ('Content Length', content_length),
        ('Last Modified', headers.get('last-modified')),
        ('ETag', headers.get('etag')),
        ('Manifest', headers.get('x-object-manifest')),
    ), skip_missing=True)
    thread_manager.print_headers(headers,
                                 meta_prefix='x-object-meta-',
                                 exclude_headers=(
                                     'content-type', 'content-length',
                                     'last-modified', 'etag', 'date',
                                     'x-object-manifest'))
