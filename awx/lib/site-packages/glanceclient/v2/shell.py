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

from glanceclient.common import progressbar
from glanceclient.common import utils
from glanceclient import exc
from glanceclient.v2.image_members import MEMBER_STATUS_VALUES
from glanceclient.v2 import images
from glanceclient.v2 import tasks
import json
import os
from os.path import expanduser

IMAGE_SCHEMA = None


def get_image_schema():
    global IMAGE_SCHEMA
    if IMAGE_SCHEMA is None:
        schema_path = expanduser("~/.glanceclient/image_schema.json")
        if os.path.isfile(schema_path):
            with open(schema_path, "r") as f:
                schema_raw = f.read()
                IMAGE_SCHEMA = json.loads(schema_raw)
    return IMAGE_SCHEMA


@utils.schema_args(get_image_schema, omit=['created_at', 'updated_at', 'file',
                                           'checksum', 'virtual_size', 'size',
                                           'status', 'schema', 'direct_url'])
@utils.arg('--property', metavar="<key=value>", action='append',
           default=[], help=('Arbitrary property to associate with image.'
                             ' May be used multiple times.'))
@utils.arg('--file', metavar='<FILE>',
           help='Local file that contains disk image to be uploaded '
                'during creation. Alternatively, images can be passed '
                'to the client via stdin.')
@utils.arg('--progress', action='store_true', default=False,
           help='Show upload progress bar.')
def do_image_create(gc, args):
    """Create a new image."""
    schema = gc.schemas.get("image")
    _args = [(x[0].replace('-', '_'), x[1]) for x in vars(args).items()]
    fields = dict(filter(lambda x: x[1] is not None and
                         (x[0] == 'property' or
                          schema.is_core_property(x[0])),
                         _args))

    raw_properties = fields.pop('property', [])
    for datum in raw_properties:
        key, value = datum.split('=', 1)
        fields[key] = value

    file_name = fields.pop('file', None)
    if file_name is not None and os.access(file_name, os.R_OK) is False:
        utils.exit("File %s does not exist or user does not have read "
                   "privileges to it" % file_name)
    image = gc.images.create(**fields)
    try:
        if utils.get_data_file(args) is not None:
            args.id = image['id']
            args.size = None
            do_image_upload(gc, args)
            image = gc.images.get(args.id)
    finally:
        utils.print_image(image)


@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to update.')
@utils.schema_args(get_image_schema, omit=['id', 'locations', 'created_at',
                                           'updated_at', 'file', 'checksum',
                                           'virtual_size', 'size', 'status',
                                           'schema', 'direct_url', 'tags'])
@utils.arg('--property', metavar="<key=value>", action='append',
           default=[], help=('Arbitrary property to associate with image.'
                             ' May be used multiple times.'))
@utils.arg('--remove-property', metavar="key", action='append', default=[],
           help="Name of arbitrary property to remove from the image.")
def do_image_update(gc, args):
    """Update an existing image."""
    schema = gc.schemas.get("image")
    _args = [(x[0].replace('-', '_'), x[1]) for x in vars(args).items()]
    fields = dict(filter(lambda x: x[1] is not None and
                         (x[0] in ['property', 'remove_property'] or
                          schema.is_core_property(x[0])),
                         _args))

    raw_properties = fields.pop('property', [])
    for datum in raw_properties:
        key, value = datum.split('=', 1)
        fields[key] = value

    remove_properties = fields.pop('remove_property', None)

    image_id = fields.pop('id')
    image = gc.images.update(image_id, remove_properties, **fields)
    utils.print_image(image)


@utils.arg('--limit', metavar='<LIMIT>', default=None, type=int,
           help='Maximum number of images to get.')
@utils.arg('--page-size', metavar='<SIZE>', default=None, type=int,
           help='Number of images to request in each paginated request.')
@utils.arg('--visibility', metavar='<VISIBILITY>',
           help='The visibility of the images to display.')
@utils.arg('--member-status', metavar='<MEMBER_STATUS>',
           help='The status of images to display.')
@utils.arg('--owner', metavar='<OWNER>',
           help='Display images owned by <OWNER>.')
@utils.arg('--property-filter', metavar='<KEY=VALUE>',
           help="Filter images by a user-defined image property.",
           action='append', dest='properties', default=[])
@utils.arg('--checksum', metavar='<CHECKSUM>',
           help='Displays images that match the checksum.')
@utils.arg('--tag', metavar='<TAG>', action='append',
           help="Filter images by a user-defined tag.")
@utils.arg('--sort-key', default=[], action='append',
           choices=images.SORT_KEY_VALUES,
           help='Sort image list by specified fields.')
@utils.arg('--sort-dir', default=[], action='append',
           choices=images.SORT_DIR_VALUES,
           help='Sort image list in specified directions.')
@utils.arg('--sort', metavar='<key>[:<direction>]', default=None,
           help=(("Comma-separated list of sort keys and directions in the "
                  "form of <key>[:<asc|desc>]. Valid keys: %s. OPTIONAL: "
                  "Default='name:asc'.") % ', '.join(images.SORT_KEY_VALUES)))
def do_image_list(gc, args):
    """List images you can access."""
    filter_keys = ['visibility', 'member_status', 'owner', 'checksum', 'tag']
    filter_items = [(key, getattr(args, key)) for key in filter_keys]
    if args.properties:
        filter_properties = [prop.split('=', 1) for prop in args.properties]
        if False in (len(pair) == 2 for pair in filter_properties):
            utils.exit('Argument --property-filter expected properties in the'
                       ' format KEY=VALUE')
        filter_items += filter_properties
    filters = dict([item for item in filter_items if item[1] is not None])

    kwargs = {'filters': filters}
    if args.limit is not None:
        kwargs['limit'] = args.limit
    if args.page_size is not None:
        kwargs['page_size'] = args.page_size

    if args.sort_key:
        kwargs['sort_key'] = args.sort_key
    if args.sort_dir:
        kwargs['sort_dir'] = args.sort_dir
    if args.sort is not None:
        kwargs['sort'] = args.sort
    elif not args.sort_dir and not args.sort_key:
        kwargs['sort'] = 'name:asc'

    images = gc.images.list(**kwargs)
    columns = ['ID', 'Name']
    utils.print_list(images, columns)


@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to describe.')
@utils.arg('--max-column-width', metavar='<integer>', default=80,
           help='The max column width of the printed table.')
def do_image_show(gc, args):
    """Describe a specific image."""
    image = gc.images.get(args.id)
    utils.print_image(image, int(args.max_column_width))


@utils.arg('--image-id', metavar='<IMAGE_ID>', required=True,
           help='Image to display members of.')
def do_member_list(gc, args):
    """Describe sharing permissions by image."""

    members = gc.image_members.list(args.image_id)
    columns = ['Image ID', 'Member ID', 'Status']
    utils.print_list(members, columns)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help='Image from which to remove member.')
@utils.arg('member_id', metavar='<MEMBER_ID>',
           help='Tenant to remove as member.')
def do_member_delete(gc, args):
    """Delete image member."""
    if not (args.image_id and args.member_id):
        utils.exit('Unable to delete member. Specify image_id and member_id')
    else:
        gc.image_members.delete(args.image_id, args.member_id)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help='Image from which to update member.')
@utils.arg('member_id', metavar='<MEMBER_ID>',
           help='Tenant to update.')
@utils.arg('member_status', metavar='<MEMBER_STATUS>',
           choices=MEMBER_STATUS_VALUES,
           help='Updated status of member.'
                ' Valid Values: %s' %
                ', '.join(str(val) for val in MEMBER_STATUS_VALUES))
def do_member_update(gc, args):
    """Update the status of a member for a given image."""
    if not (args.image_id and args.member_id and args.member_status):
        utils.exit('Unable to update member. Specify image_id, member_id and'
                   ' member_status')
    else:
        member = gc.image_members.update(args.image_id, args.member_id,
                                         args.member_status)
        member = [member]
        columns = ['Image ID', 'Member ID', 'Status']
        utils.print_list(member, columns)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help='Image with which to create member.')
@utils.arg('member_id', metavar='<MEMBER_ID>',
           help='Tenant to add as member.')
def do_member_create(gc, args):
    """Create member for a given image."""
    if not (args.image_id and args.member_id):
        utils.exit('Unable to create member. Specify image_id and member_id')
    else:
        member = gc.image_members.create(args.image_id, args.member_id)
        member = [member]
        columns = ['Image ID', 'Member ID', 'Status']
        utils.print_list(member, columns)


@utils.arg('model', metavar='<MODEL>', help='Name of model to describe.')
def do_explain(gc, args):
    """Describe a specific model."""
    try:
        schema = gc.schemas.get(args.model)
    except exc.HTTPNotFound:
        utils.exit('Unable to find requested model \'%s\'' % args.model)
    else:
        formatters = {'Attribute': lambda m: m.name}
        columns = ['Attribute', 'Description']
        utils.print_list(schema.properties, columns, formatters)


@utils.arg('--file', metavar='<FILE>',
           help='Local file to save downloaded image data to. '
                'If this is not specified the image data will be '
                'written to stdout.')
@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to download.')
@utils.arg('--progress', action='store_true', default=False,
           help='Show download progress bar.')
def do_image_download(gc, args):
    """Download a specific image."""
    body = gc.images.data(args.id)
    if args.progress:
        body = progressbar.VerboseIteratorWrapper(body, len(body))
    utils.save_image(body, args.file)


@utils.arg('--file', metavar='<FILE>',
           help=('Local file that contains disk image to be uploaded.'
                 ' Alternatively, images can be passed'
                 ' to the client via stdin.'))
@utils.arg('--size', metavar='<IMAGE_SIZE>', type=int,
           help='Size in bytes of image to be uploaded. Default is to get '
                'size from provided data object but this is supported in case '
                'where size cannot be inferred.',
           default=None)
@utils.arg('--progress', action='store_true', default=False,
           help='Show upload progress bar.')
@utils.arg('id', metavar='<IMAGE_ID>',
           help='ID of image to upload data to.')
def do_image_upload(gc, args):
    """Upload data for a specific image."""
    image_data = utils.get_data_file(args)
    if args.progress:
        filesize = utils.get_file_size(image_data)
        if filesize is not None:
            # NOTE(kragniz): do not show a progress bar if the size of the
            # input is unknown (most likely a piped input)
            image_data = progressbar.VerboseFileWrapper(image_data, filesize)
    gc.images.upload(args.id, image_data, args.size)


@utils.arg('id', metavar='<IMAGE_ID>', help='ID of image to delete.')
def do_image_delete(gc, args):
    """Delete specified image."""
    image = gc.images.get(args.id)
    if image and image.status == "deleted":
        msg = "No image with an ID of '%s' exists." % image.id
        utils.exit(msg)
    gc.images.delete(args.id)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help='Image to be updated with the given tag.')
@utils.arg('tag_value', metavar='<TAG_VALUE>',
           help='Value of the tag.')
def do_image_tag_update(gc, args):
        """Update an image with the given tag."""
        if not (args.image_id and args.tag_value):
            utils.exit('Unable to update tag. Specify image_id and tag_value')
        else:
            gc.image_tags.update(args.image_id, args.tag_value)
            image = gc.images.get(args.image_id)
            image = [image]
            columns = ['ID', 'Tags']
            utils.print_list(image, columns)


@utils.arg('image_id', metavar='<IMAGE_ID>',
           help='ID of the image from which to delete tag.')
@utils.arg('tag_value', metavar='<TAG_VALUE>',
           help='Value of the tag.')
def do_image_tag_delete(gc, args):
    """Delete the tag associated with the given image."""
    if not (args.image_id and args.tag_value):
        utils.exit('Unable to delete tag. Specify image_id and tag_value')
    else:
        gc.image_tags.delete(args.image_id, args.tag_value)


@utils.arg('--url', metavar='<URL>', required=True,
           help='URL of location to add.')
@utils.arg('--metadata', metavar='<STRING>', default='{}',
           help=('Metadata associated with the location. '
                 'Must be a valid JSON object (default: %(default)s)'))
@utils.arg('id', metavar='<ID>',
           help='ID of image to which the location is to be added.')
def do_location_add(gc, args):
    """Add a location (and related metadata) to an image."""
    try:
        metadata = json.loads(args.metadata)
    except ValueError:
        utils.exit('Metadata is not a valid JSON object.')
    else:
        image = gc.images.add_location(args.id, args.url, metadata)
        utils.print_dict(image)


@utils.arg('--url', metavar='<URL>', action='append', required=True,
           help='URL of location to remove. May be used multiple times.')
@utils.arg('id', metavar='<ID>',
           help='ID of image whose locations are to be removed.')
def do_location_delete(gc, args):
    """Remove locations (and related metadata) from an image."""
    gc.images.delete_locations(args.id, set(args.url))


@utils.arg('--url', metavar='<URL>', required=True,
           help='URL of location to update.')
@utils.arg('--metadata', metavar='<STRING>', default='{}',
           help=('Metadata associated with the location. '
                 'Must be a valid JSON object (default: %(default)s)'))
@utils.arg('id', metavar='<ID>',
           help='ID of image whose location is to be updated.')
def do_location_update(gc, args):
    """Update metadata of an image's location."""
    try:
        metadata = json.loads(args.metadata)
    except ValueError:
        utils.exit('Metadata is not a valid JSON object.')
    else:
        image = gc.images.update_location(args.id, args.url, metadata)
        utils.print_dict(image)


# Metadata - catalog
NAMESPACE_SCHEMA = None


def get_namespace_schema():
    global NAMESPACE_SCHEMA
    if NAMESPACE_SCHEMA is None:
        schema_path = expanduser("~/.glanceclient/namespace_schema.json")
        if os.path.isfile(schema_path):
            with open(schema_path, "r") as f:
                schema_raw = f.read()
                NAMESPACE_SCHEMA = json.loads(schema_raw)
    return NAMESPACE_SCHEMA


def _namespace_show(namespace, max_column_width=None):
    namespace = dict(namespace)  # Warlock objects are compatible with dicts
    # Flatten dicts for display
    if 'properties' in namespace:
        props = [k for k in namespace['properties']]
        namespace['properties'] = props
    if 'resource_type_associations' in namespace:
        assocs = [assoc['name']
                  for assoc in namespace['resource_type_associations']]
        namespace['resource_type_associations'] = assocs
    if 'objects' in namespace:
        objects = [obj['name'] for obj in namespace['objects']]
        namespace['objects'] = objects

    if max_column_width:
        utils.print_dict(namespace, max_column_width)
    else:
        utils.print_dict(namespace)


@utils.arg('namespace', metavar='<NAMESPACE>', help='Name of the namespace.')
@utils.schema_args(get_namespace_schema, omit=['namespace', 'property_count',
                                               'properties', 'tag_count',
                                               'tags', 'object_count',
                                               'objects', 'resource_types'])
def do_md_namespace_create(gc, args):
    """Create a new metadata definitions namespace."""
    schema = gc.schemas.get('metadefs/namespace')
    _args = [(x[0].replace('-', '_'), x[1]) for x in vars(args).items()]
    fields = dict(filter(lambda x: x[1] is not None and
                         (schema.is_core_property(x[0])),
                         _args))
    namespace = gc.metadefs_namespace.create(**fields)

    _namespace_show(namespace)


@utils.arg('--file', metavar='<FILEPATH>',
           help='Path to file with namespace schema to import. Alternatively, '
                'namespaces schema can be passed to the client via stdin.')
def do_md_namespace_import(gc, args):
    """Import a metadata definitions namespace from file or standard input."""
    namespace_data = utils.get_data_file(args)
    if not namespace_data:
        utils.exit('No metadata definition namespace passed via stdin or '
                   '--file argument.')

    try:
        namespace_json = json.load(namespace_data)
    except ValueError:
        utils.exit('Schema is not a valid JSON object.')
    else:
        namespace = gc.metadefs_namespace.create(**namespace_json)
        _namespace_show(namespace)


@utils.arg('id', metavar='<NAMESPACE>', help='Name of namespace to update.')
@utils.schema_args(get_namespace_schema, omit=['property_count', 'properties',
                                               'tag_count', 'tags',
                                               'object_count', 'objects',
                                               'resource_type_associations',
                                               'schema'])
def do_md_namespace_update(gc, args):
    """Update an existing metadata definitions namespace."""
    schema = gc.schemas.get('metadefs/namespace')

    _args = [(x[0].replace('-', '_'), x[1]) for x in vars(args).items()]
    fields = dict(filter(lambda x: x[1] is not None and
                         (schema.is_core_property(x[0])),
                         _args))
    namespace = gc.metadefs_namespace.update(args.id, **fields)

    _namespace_show(namespace)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help='Name of namespace to describe.')
@utils.arg('--resource-type', metavar='<RESOURCE_TYPE>',
           help='Applies prefix of given resource type associated to a '
                'namespace to all properties of a namespace.', default=None)
@utils.arg('--max-column-width', metavar='<integer>', default=80,
           help='The max column width of the printed table.')
def do_md_namespace_show(gc, args):
    """Describe a specific metadata definitions namespace.

    Lists also the namespace properties, objects and resource type
    associations.
    """
    kwargs = {}
    if args.resource_type:
        kwargs['resource_type'] = args.resource_type

    namespace = gc.metadefs_namespace.get(args.namespace, **kwargs)
    _namespace_show(namespace, int(args.max_column_width))


@utils.arg('--resource-types', metavar='<RESOURCE_TYPES>', action='append',
           help='Resource type to filter namespaces.')
@utils.arg('--visibility', metavar='<VISIBILITY>',
           help='Visibility parameter to filter namespaces.')
@utils.arg('--page-size', metavar='<SIZE>', default=None, type=int,
           help='Number of namespaces to request in each paginated request.')
def do_md_namespace_list(gc, args):
    """List metadata definitions namespaces."""
    filter_keys = ['resource_types', 'visibility']
    filter_items = [(key, getattr(args, key, None)) for key in filter_keys]
    filters = dict([item for item in filter_items if item[1] is not None])

    kwargs = {'filters': filters}
    if args.page_size is not None:
        kwargs['page_size'] = args.page_size

    namespaces = gc.metadefs_namespace.list(**kwargs)
    columns = ['namespace']
    utils.print_list(namespaces, columns)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help='Name of namespace to delete.')
def do_md_namespace_delete(gc, args):
    """Delete specified metadata definitions namespace with its contents."""
    gc.metadefs_namespace.delete(args.namespace)


# Metadata - catalog
RESOURCE_TYPE_SCHEMA = None


def get_resource_type_schema():
    global RESOURCE_TYPE_SCHEMA
    if RESOURCE_TYPE_SCHEMA is None:
        schema_path = expanduser("~/.glanceclient/resource_type_schema.json")
        if os.path.isfile(schema_path):
            with open(schema_path, "r") as f:
                schema_raw = f.read()
                RESOURCE_TYPE_SCHEMA = json.loads(schema_raw)
    return RESOURCE_TYPE_SCHEMA


@utils.arg('namespace', metavar='<NAMESPACE>', help='Name of namespace.')
@utils.schema_args(get_resource_type_schema)
def do_md_resource_type_associate(gc, args):
    """Associate resource type with a metadata definitions namespace."""
    schema = gc.schemas.get('metadefs/resource_type')
    _args = [(x[0].replace('-', '_'), x[1]) for x in vars(args).items()]
    fields = dict(filter(lambda x: x[1] is not None and
                         (schema.is_core_property(x[0])),
                         _args))
    resource_type = gc.metadefs_resource_type.associate(args.namespace,
                                                        **fields)
    utils.print_dict(resource_type)


@utils.arg('namespace', metavar='<NAMESPACE>', help='Name of namespace.')
@utils.arg('resource_type', metavar='<RESOURCE_TYPE>',
           help='Name of resource type.')
def do_md_resource_type_deassociate(gc, args):
    """Deassociate resource type with a metadata definitions namespace."""
    gc.metadefs_resource_type.deassociate(args.namespace, args.resource_type)


def do_md_resource_type_list(gc, args):
    """List available resource type names."""
    resource_types = gc.metadefs_resource_type.list()
    utils.print_list(resource_types, ['name'])


@utils.arg('namespace', metavar='<NAMESPACE>', help='Name of namespace.')
def do_md_namespace_resource_type_list(gc, args):
    """List resource types associated to specific namespace."""
    resource_types = gc.metadefs_resource_type.get(args.namespace)
    utils.print_list(resource_types, ['name', 'prefix', 'properties_target'])


@utils.arg('namespace', metavar='<NAMESPACE>',
           help='Name of namespace the property will belong.')
@utils.arg('--name', metavar='<NAME>', required=True,
           help='Internal name of a property.')
@utils.arg('--title', metavar='<TITLE>', required=True,
           help='Property name displayed to the user.')
@utils.arg('--schema', metavar='<SCHEMA>', required=True,
           help='Valid JSON schema of a property.')
def do_md_property_create(gc, args):
    """Create a new metadata definitions property inside a namespace."""
    try:
        schema = json.loads(args.schema)
    except ValueError:
        utils.exit('Schema is not a valid JSON object.')
    else:
        fields = {'name': args.name, 'title': args.title}
        fields.update(schema)
        new_property = gc.metadefs_property.create(args.namespace, **fields)
        utils.print_dict(new_property)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help='Name of namespace the property belongs.')
@utils.arg('property', metavar='<PROPERTY>', help='Name of a property.')
@utils.arg('--name', metavar='<NAME>', default=None,
           help='New name of a property.')
@utils.arg('--title', metavar='<TITLE>', default=None,
           help='Property name displayed to the user.')
@utils.arg('--schema', metavar='<SCHEMA>', default=None,
           help='Valid JSON schema of a property.')
def do_md_property_update(gc, args):
    """Update metadata definitions property inside a namespace."""
    fields = {}
    if args.name:
        fields['name'] = args.name
    if args.title:
        fields['title'] = args.title
    if args.schema:
        try:
            schema = json.loads(args.schema)
        except ValueError:
            utils.exit('Schema is not a valid JSON object.')
        else:
            fields.update(schema)

    new_property = gc.metadefs_property.update(args.namespace, args.property,
                                               **fields)
    utils.print_dict(new_property)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help='Name of namespace the property belongs.')
@utils.arg('property', metavar='<PROPERTY>', help='Name of a property.')
@utils.arg('--max-column-width', metavar='<integer>', default=80,
           help='The max column width of the printed table.')
def do_md_property_show(gc, args):
    """Describe a specific metadata definitions property inside a namespace."""
    prop = gc.metadefs_property.get(args.namespace, args.property)
    utils.print_dict(prop, int(args.max_column_width))


@utils.arg('namespace', metavar='<NAMESPACE>',
           help='Name of namespace the property belongs.')
@utils.arg('property', metavar='<PROPERTY>', help='Name of a property.')
def do_md_property_delete(gc, args):
    """Delete a specific metadata definitions property inside a namespace."""
    gc.metadefs_property.delete(args.namespace, args.property)


@utils.arg('namespace', metavar='<NAMESPACE>', help='Name of namespace.')
def do_md_namespace_properties_delete(gc, args):
    """Delete all metadata definitions property inside a specific namespace."""
    gc.metadefs_property.delete_all(args.namespace)


@utils.arg('namespace', metavar='<NAMESPACE>', help='Name of namespace.')
def do_md_property_list(gc, args):
    """List metadata definitions properties inside a specific namespace."""
    properties = gc.metadefs_property.list(args.namespace)
    columns = ['name', 'title', 'type']
    utils.print_list(properties, columns)


def _object_show(obj, max_column_width=None):
    obj = dict(obj)  # Warlock objects are compatible with dicts
    # Flatten dicts for display
    if 'properties' in obj:
        objects = [k for k in obj['properties']]
        obj['properties'] = objects

    if max_column_width:
        utils.print_dict(obj, max_column_width)
    else:
        utils.print_dict(obj)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help='Name of namespace the object will belong.')
@utils.arg('--name', metavar='<NAME>', required=True,
           help='Internal name of an object.')
@utils.arg('--schema', metavar='<SCHEMA>', required=True,
           help='Valid JSON schema of an object.')
def do_md_object_create(gc, args):
    """Create a new metadata definitions object inside a namespace."""
    try:
        schema = json.loads(args.schema)
    except ValueError:
        utils.exit('Schema is not a valid JSON object.')
    else:
        fields = {'name': args.name}
        fields.update(schema)
        new_object = gc.metadefs_object.create(args.namespace, **fields)
        _object_show(new_object)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help='Name of namespace the object belongs.')
@utils.arg('object', metavar='<OBJECT>', help='Name of an object.')
@utils.arg('--name', metavar='<NAME>', default=None,
           help='New name of an object.')
@utils.arg('--schema', metavar='<SCHEMA>', default=None,
           help='Valid JSON schema of an object.')
def do_md_object_update(gc, args):
    """Update metadata definitions object inside a namespace."""
    fields = {}
    if args.name:
        fields['name'] = args.name
    if args.schema:
        try:
            schema = json.loads(args.schema)
        except ValueError:
            utils.exit('Schema is not a valid JSON object.')
        else:
            fields.update(schema)

    new_object = gc.metadefs_object.update(args.namespace, args.object,
                                           **fields)
    _object_show(new_object)


@utils.arg('namespace', metavar='<NAMESPACE>',
           help='Name of namespace the object belongs.')
@utils.arg('object', metavar='<OBJECT>', help='Name of an object.')
@utils.arg('--max-column-width', metavar='<integer>', default=80,
           help='The max column width of the printed table.')
def do_md_object_show(gc, args):
    """Describe a specific metadata definitions object inside a namespace."""
    obj = gc.metadefs_object.get(args.namespace, args.object)
    _object_show(obj, int(args.max_column_width))


@utils.arg('namespace', metavar='<NAMESPACE>',
           help='Name of namespace the object belongs.')
@utils.arg('object', metavar='<OBJECT>', help='Name of an object.')
@utils.arg('property', metavar='<PROPERTY>', help='Name of a property.')
@utils.arg('--max-column-width', metavar='<integer>', default=80,
           help='The max column width of the printed table.')
def do_md_object_property_show(gc, args):
    """Describe a specific metadata definitions property inside an object."""
    obj = gc.metadefs_object.get(args.namespace, args.object)
    try:
        prop = obj['properties'][args.property]
        prop['name'] = args.property
    except KeyError:
        utils.exit('Property %s not found in object %s.' % (args.property,
                   args.object))
    utils.print_dict(prop, int(args.max_column_width))


@utils.arg('namespace', metavar='<NAMESPACE>',
           help='Name of namespace the object belongs.')
@utils.arg('object', metavar='<OBJECT>', help='Name of an object.')
def do_md_object_delete(gc, args):
    """Delete a specific metadata definitions object inside a namespace."""
    gc.metadefs_object.delete(args.namespace, args.object)


@utils.arg('namespace', metavar='<NAMESPACE>', help='Name of namespace.')
def do_md_namespace_objects_delete(gc, args):
    """Delete all metadata definitions objects inside a specific namespace."""
    gc.metadefs_object.delete_all(args.namespace)


@utils.arg('namespace', metavar='<NAMESPACE>', help='Name of namespace.')
def do_md_object_list(gc, args):
    """List metadata definitions objects inside a specific namespace."""
    objects = gc.metadefs_object.list(args.namespace)
    columns = ['name', 'description']
    column_settings = {
        "description": {
            "max_width": 50,
            "align": "l"
        }
    }
    utils.print_list(objects, columns, field_settings=column_settings)


@utils.arg('--sort-key', default='status',
           choices=tasks.SORT_KEY_VALUES,
           help='Sort task list by specified field.')
@utils.arg('--sort-dir', default='desc',
           choices=tasks.SORT_DIR_VALUES,
           help='Sort task list in specified direction.')
@utils.arg('--page-size', metavar='<SIZE>', default=None, type=int,
           help='Number of tasks to request in each paginated request.')
@utils.arg('--type', metavar='<TYPE>',
           help='Filter tasks to those that have this type.')
@utils.arg('--status', metavar='<STATUS>',
           help='Filter tasks to those that have this status.')
def do_task_list(gc, args):
    """List tasks you can access."""
    filter_keys = ['type', 'status']
    filter_items = [(key, getattr(args, key)) for key in filter_keys]
    filters = dict([item for item in filter_items if item[1] is not None])

    kwargs = {'filters': filters}
    if args.page_size is not None:
        kwargs['page_size'] = args.page_size

    kwargs['sort_key'] = args.sort_key
    kwargs['sort_dir'] = args.sort_dir

    tasks = gc.tasks.list(**kwargs)

    columns = ['ID', 'Type', 'Status', 'Owner']
    utils.print_list(tasks, columns)


@utils.arg('id', metavar='<TASK_ID>', help='ID of task to describe.')
def do_task_show(gc, args):
    """Describe a specific task."""
    task = gc.tasks.get(args.id)
    ignore = ['self', 'schema']
    task = dict([item for item in task.iteritems() if item[0] not in ignore])
    utils.print_dict(task)


@utils.arg('--type', metavar='<TYPE>',
           help='Type of Task. Please refer to Glance schema or documentation'
           ' to see which tasks are supported.')
@utils.arg('--input', metavar='<STRING>', default='{}',
           help='Parameters of the task to be launched')
def do_task_create(gc, args):
    """Create a new task."""
    if not (args.type and args.input):
        utils.exit('Unable to create task. Specify task type and input.')
    else:
        try:
            input = json.loads(args.input)
        except ValueError:
            utils.exit('Failed to parse the "input" parameter. Must be a '
                       'valid JSON object.')

        task_values = {'type': args.type, 'input': input}
        task = gc.tasks.create(**task_values)
        ignore = ['self', 'schema']
        task = dict([item for item in task.iteritems()
                     if item[0] not in ignore])
        utils.print_dict(task)
