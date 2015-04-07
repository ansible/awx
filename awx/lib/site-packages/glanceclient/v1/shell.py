# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import print_function

import copy
import functools
import os
import six
import sys

from oslo_utils import encodeutils
from oslo_utils import strutils

from glanceclient.common import progressbar
from glanceclient.common import utils
from glanceclient import exc
import glanceclient.v1.images

CONTAINER_FORMATS = 'Acceptable formats: ami, ari, aki, bare, and ovf.'
DISK_FORMATS = ('Acceptable formats: ami, ari, aki, vhd, vmdk, raw, '
                'qcow2, vdi, and iso.')

_bool_strict = functools.partial(strutils.bool_from_string, strict=True)


@utils.arg('--name', metavar='<NAME>',
           help='Filter images to those that have this name.')
@utils.arg('--status', metavar='<STATUS>',
           help='Filter images to those that have this status.')
@utils.arg('--container-format', metavar='<CONTAINER_FORMAT>',
           help='Filter images to those that have this container format. '
                + CONTAINER_FORMATS)
@utils.arg('--disk-format', metavar='<DISK_FORMAT>',
           help='Filter images to those that have this disk format. '
                + DISK_FORMATS)
@utils.arg('--size-min', metavar='<SIZE>', type=int,
           help='Filter images to those with a size greater than this.')
@utils.arg('--size-max', metavar='<SIZE>', type=int,
           help='Filter images to those with a size less than this.')
@utils.arg('--property-filter', metavar='<KEY=VALUE>',
           help="Filter images by a user-defined image property.",
           action='append', dest='properties', default=[])
@utils.arg('--page-size', metavar='<SIZE>', default=None, type=int,
           help='Number of images to request in each paginated request.')
@utils.arg('--human-readable', action='store_true', default=False,
           help='Print image size in a human-friendly format.')
@utils.arg('--sort-key', default='name',
           choices=glanceclient.v1.images.SORT_KEY_VALUES,
           help='Sort image list by specified field.')
@utils.arg('--sort-dir', default='asc',
           choices=glanceclient.v1.images.SORT_DIR_VALUES,
           help='Sort image list in specified direction.')
@utils.arg('--is-public',
           type=_bool_strict, metavar='{True,False}',
           help=('Allows the user to select a listing of public or non '
                 'public images.'))
@utils.arg('--owner', default=None, metavar='<TENANT_ID>',
           help='Display only images owned by this tenant id. Filtering '
                'occurs on the client side so may be inefficient. This option '
                'is mainly intended for admin use. Use an empty string (\'\') '
                'to list images with no owner. Note: This option overrides '
                'the --is-public argument if present. Note: the v2 API '
                'supports more efficient server-side owner based filtering.')
@utils.arg('--all-tenants', action='store_true', default=False,
           help=('Allows the admin user to list all images '
                 'irrespective of the image\'s owner or is_public value.'))
def do_image_list(gc, args):
    """List images you can access."""
    filter_keys = ['name', 'status', 'container_format', 'disk_format',
                   'size_min', 'size_max', 'is_public']
    filter_items = [(key, getattr(args, key)) for key in filter_keys]
    filters = dict([item for item in filter_items if item[1] is not None])

    if args.properties:
        property_filter_items = [p.split('=', 1) for p in args.properties]
        if any(len(pair) != 2 for pair in property_filter_items):
            utils.exit('Argument --property-filter requires properties in the'
                       ' format KEY=VALUE')

        filters['properties'] = dict(property_filter_items)

    kwargs = {'filters': filters}
    if args.page_size is not None:
        kwargs['page_size'] = args.page_size

    kwargs['sort_key'] = args.sort_key
    kwargs['sort_dir'] = args.sort_dir
    kwargs['owner'] = args.owner
    if args.all_tenants is True:
        kwargs['is_public'] = None

    images = gc.images.list(**kwargs)

    if args.human_readable:
        def convert_size(image):
            image.size = utils.make_size_human_readable(image.size)
            return image

        images = (convert_size(image) for image in images)

    columns = ['ID', 'Name', 'Disk Format', 'Container Format',
               'Size', 'Status']
    utils.print_list(images, columns)


def _image_show(image, human_readable=False, max_column_width=80):
    # Flatten image properties dict for display
    info = copy.deepcopy(image._info)
    if human_readable:
        info['size'] = utils.make_size_human_readable(info['size'])
    for (k, v) in six.iteritems(info.pop('properties')):
        info['Property \'%s\'' % k] = v

    utils.print_dict(info, max_column_width=max_column_width)


def _set_data_field(fields, args):
    if 'location' not in fields and 'copy_from' not in fields:
        fields['data'] = utils.get_data_file(args)


@utils.arg('image', metavar='<IMAGE>', help='Name or ID of image to describe.')
@utils.arg('--human-readable', action='store_true', default=False,
           help='Print image size in a human-friendly format.')
@utils.arg('--max-column-width', metavar='<integer>', default=80,
           help='The max column width of the printed table.')
def do_image_show(gc, args):
    """Describe a specific image."""
    image_id = utils.find_resource(gc.images, args.image).id
    image = gc.images.get(image_id)
    _image_show(image, args.human_readable,
                max_column_width=int(args.max_column_width))


@utils.arg('--file', metavar='<FILE>',
           help='Local file to save downloaded image data to. '
                'If this is not specified the image data will be '
                'written to stdout.')
@utils.arg('image', metavar='<IMAGE>', help='Name or ID of image to download.')
@utils.arg('--progress', action='store_true', default=False,
           help='Show download progress bar.')
def do_image_download(gc, args):
    """Download a specific image."""
    image = utils.find_resource(gc.images, args.image)
    body = image.data()
    if args.progress:
        body = progressbar.VerboseIteratorWrapper(body, len(body))
    utils.save_image(body, args.file)


@utils.arg('--id', metavar='<IMAGE_ID>',
           help='ID of image to reserve.')
@utils.arg('--name', metavar='<NAME>',
           help='Name of image.')
@utils.arg('--store', metavar='<STORE>',
           help='Store to upload image to.')
@utils.arg('--disk-format', metavar='<DISK_FORMAT>',
           help='Disk format of image. ' + DISK_FORMATS)
@utils.arg('--container-format', metavar='<CONTAINER_FORMAT>',
           help='Container format of image. ' + CONTAINER_FORMATS)
@utils.arg('--owner', metavar='<TENANT_ID>',
           help='Tenant who should own image.')
@utils.arg('--size', metavar='<SIZE>', type=int,
           help=('Size of image data (in bytes). Only used with'
                 ' \'--location\' and \'--copy_from\'.'))
@utils.arg('--min-disk', metavar='<DISK_GB>', type=int,
           help='Minimum size of disk needed to boot image (in gigabytes).')
@utils.arg('--min-ram', metavar='<DISK_RAM>', type=int,
           help='Minimum amount of ram needed to boot image (in megabytes).')
@utils.arg('--location', metavar='<IMAGE_URL>',
           help=('URL where the data for this image already resides. For '
                 'example, if the image data is stored in swift, you could '
                 'specify \'swift+http://tenant%%3Aaccount:key@auth_url/'
                 'v2.0/container/obj\'. '
                 '(Note: \'%%3A\' is \':\' URL encoded.)'))
@utils.arg('--file', metavar='<FILE>',
           help=('Local file that contains disk image to be uploaded during'
                 ' creation. Alternatively, images can be passed to the client'
                 ' via stdin.'))
@utils.arg('--checksum', metavar='<CHECKSUM>',
           help=('Hash of image data used Glance can use for verification.'
                 ' Provide a md5 checksum here.'))
@utils.arg('--copy-from', metavar='<IMAGE_URL>',
           help=('Similar to \'--location\' in usage, but this indicates that'
                 ' the Glance server should immediately copy the data and'
                 ' store it in its configured image store.'))
@utils.arg('--is-public',
           type=_bool_strict, metavar='{True,False}',
           help='Make image accessible to the public.')
@utils.arg('--is-protected',
           type=_bool_strict, metavar='{True,False}',
           help='Prevent image from being deleted.')
@utils.arg('--property', metavar="<key=value>", action='append', default=[],
           help=("Arbitrary property to associate with image. "
                 "May be used multiple times."))
@utils.arg('--human-readable', action='store_true', default=False,
           help='Print image size in a human-friendly format.')
@utils.arg('--progress', action='store_true', default=False,
           help='Show upload progress bar.')
def do_image_create(gc, args):
    """Create a new image."""
    # Filter out None values
    fields = dict(filter(lambda x: x[1] is not None, vars(args).items()))

    fields['is_public'] = fields.get('is_public')

    if 'is_protected' in fields:
        fields['protected'] = fields.pop('is_protected')

    raw_properties = fields.pop('property')
    fields['properties'] = {}
    for datum in raw_properties:
        key, value = datum.split('=', 1)
        fields['properties'][key] = value

    # Filter out values we can't use
    CREATE_PARAMS = glanceclient.v1.images.CREATE_PARAMS
    fields = dict(filter(lambda x: x[0] in CREATE_PARAMS, fields.items()))

    _set_data_field(fields, args)

    # Only show progress bar for local image files
    if fields.get('data') and args.progress:
        filesize = utils.get_file_size(fields['data'])
        if filesize is not None:
            # NOTE(kragniz): do not show a progress bar if the size of the
            # input is unknown (most likely a piped input)
            fields['data'] = progressbar.VerboseFileWrapper(
                fields['data'], filesize
            )

    image = gc.images.create(**fields)
    _image_show(image, args.human_readable)


def _is_image_data_provided(args):
    """Return True if some image data has probably been provided by the user"""
    # NOTE(kragniz): Check stdin works, then check is there is any data
    # on stdin or a filename has been provided with --file
    try:
        os.fstat(0)
    except OSError:
        return False
    return not sys.stdin.isatty() or args.file or args.copy_from


@utils.arg('image', metavar='<IMAGE>', help='Name or ID of image to modify.')
@utils.arg('--name', metavar='<NAME>',
           help='Name of image.')
@utils.arg('--disk-format', metavar='<DISK_FORMAT>',
           help='Disk format of image. ' + DISK_FORMATS)
@utils.arg('--container-format', metavar='<CONTAINER_FORMAT>',
           help='Container format of image. ' + CONTAINER_FORMATS)
@utils.arg('--owner', metavar='<TENANT_ID>',
           help='Tenant who should own image.')
@utils.arg('--size', metavar='<SIZE>', type=int,
           help='Size of image data (in bytes).')
@utils.arg('--min-disk', metavar='<DISK_GB>', type=int,
           help='Minimum size of disk needed to boot image (in gigabytes).')
@utils.arg('--min-ram', metavar='<DISK_RAM>', type=int,
           help='Minimum amount of ram needed to boot image (in megabytes).')
@utils.arg('--location', metavar='<IMAGE_URL>',
           help=('URL where the data for this image already resides. For '
                 'example, if the image data is stored in swift, you could '
                 'specify \'swift+http://tenant%%3Aaccount:key@auth_url/'
                 'v2.0/container/obj\'. '
                 '(Note: \'%%3A\' is \':\' URL encoded.)'))
@utils.arg('--file', metavar='<FILE>',
           help=('Local file that contains disk image to be uploaded during'
                 ' update. Alternatively, images can be passed to the client'
                 ' via stdin.'))
@utils.arg('--checksum', metavar='<CHECKSUM>',
           help='Hash of image data used Glance can use for verification.')
@utils.arg('--copy-from', metavar='<IMAGE_URL>',
           help=('Similar to \'--location\' in usage, but this indicates that'
                 ' the Glance server should immediately copy the data and'
                 ' store it in its configured image store.'))
@utils.arg('--is-public',
           type=_bool_strict, metavar='{True,False}',
           help='Make image accessible to the public.')
@utils.arg('--is-protected',
           type=_bool_strict, metavar='{True,False}',
           help='Prevent image from being deleted.')
@utils.arg('--property', metavar="<key=value>", action='append', default=[],
           help=("Arbitrary property to associate with image. "
                 "May be used multiple times."))
@utils.arg('--purge-props', action='store_true', default=False,
           help=("If this flag is present, delete all image properties "
                 "not explicitly set in the update request. Otherwise, "
                 "those properties not referenced are preserved."))
@utils.arg('--human-readable', action='store_true', default=False,
           help='Print image size in a human-friendly format.')
@utils.arg('--progress', action='store_true', default=False,
           help='Show upload progress bar.')
def do_image_update(gc, args):
    """Update a specific image."""
    # Filter out None values
    fields = dict(filter(lambda x: x[1] is not None, vars(args).items()))

    image_arg = fields.pop('image')
    image = utils.find_resource(gc.images, image_arg)

    if 'is_protected' in fields:
        fields['protected'] = fields.pop('is_protected')

    raw_properties = fields.pop('property')
    fields['properties'] = {}
    for datum in raw_properties:
        key, value = datum.split('=', 1)
        fields['properties'][key] = value

    # Filter out values we can't use
    UPDATE_PARAMS = glanceclient.v1.images.UPDATE_PARAMS
    fields = dict(filter(lambda x: x[0] in UPDATE_PARAMS, fields.items()))

    if image.status == 'queued':
        _set_data_field(fields, args)

        if args.progress:
            filesize = utils.get_file_size(fields['data'])
            fields['data'] = progressbar.VerboseFileWrapper(
                fields['data'], filesize
            )

    elif _is_image_data_provided(args):
        # NOTE(kragniz): Exit with an error if the status is not queued
        # and image data was provided
        utils.exit('Unable to upload image data to an image which '
                   'is %s.' % image.status)

    image = gc.images.update(image, purge_props=args.purge_props, **fields)
    _image_show(image, args.human_readable)


@utils.arg('images', metavar='<IMAGE>', nargs='+',
           help='Name or ID of image(s) to delete.')
def do_image_delete(gc, args):
    """Delete specified image(s)."""
    for args_image in args.images:
        image = utils.find_resource(gc.images, args_image)
        if image and image.status == "deleted":
            msg = "No image with an ID of '%s' exists." % image.id
            raise exc.CommandError(msg)
        try:
            if args.verbose:
                print('Requesting image delete for %s ...' %
                      encodeutils.safe_decode(args_image), end=' ')

            gc.images.delete(image)

            if args.verbose:
                print('[Done]')

        except exc.HTTPException as e:
            if args.verbose:
                print('[Fail]')
            print('%s: Unable to delete image %s' % (e, args_image))


@utils.arg('--image-id', metavar='<IMAGE_ID>',
           help='Filter results by an image ID.')
@utils.arg('--tenant-id', metavar='<TENANT_ID>',
           help='Filter results by a tenant ID.')
def do_member_list(gc, args):
    """Describe sharing permissions by image or tenant."""
    if args.image_id and args.tenant_id:
        utils.exit('Unable to filter members by both --image-id and'
                   ' --tenant-id.')
    elif args.image_id:
        kwargs = {'image': args.image_id}
    elif args.tenant_id:
        kwargs = {'member': args.tenant_id}
    else:
        utils.exit('Unable to list all members. Specify --image-id or'
                   ' --tenant-id')

    members = gc.image_members.list(**kwargs)
    columns = ['Image ID', 'Member ID', 'Can Share']
    utils.print_list(members, columns)


@utils.arg('image', metavar='<IMAGE>',
           help='Image to add member to.')
@utils.arg('tenant_id', metavar='<TENANT_ID>',
           help='Tenant to add as member')
@utils.arg('--can-share', action='store_true', default=False,
           help='Allow the specified tenant to share this image.')
def do_member_create(gc, args):
    """Share a specific image with a tenant."""
    image = utils.find_resource(gc.images, args.image)
    gc.image_members.create(image, args.tenant_id, args.can_share)


@utils.arg('image', metavar='<IMAGE>',
           help='Image from which to remove member.')
@utils.arg('tenant_id', metavar='<TENANT_ID>',
           help='Tenant to remove as member.')
def do_member_delete(gc, args):
    """Remove a shared image from a tenant."""
    image_id = utils.find_resource(gc.images, args.image).id
    gc.image_members.delete(image_id, args.tenant_id)
