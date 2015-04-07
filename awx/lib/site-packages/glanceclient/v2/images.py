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

import json

from oslo_utils import encodeutils
import six
from six.moves.urllib import parse
import warlock

from glanceclient.common import utils
from glanceclient import exc
from glanceclient.v2 import schemas

DEFAULT_PAGE_SIZE = 20

SORT_DIR_VALUES = ('asc', 'desc')
SORT_KEY_VALUES = ('name', 'status', 'container_format', 'disk_format',
                   'size', 'id', 'created_at', 'updated_at')


class Controller(object):
    def __init__(self, http_client, schema_client):
        self.http_client = http_client
        self.schema_client = schema_client

    @utils.memoized_property
    def model(self):
        schema = self.schema_client.get('image')
        return warlock.model_factory(schema.raw(), schemas.SchemaBasedModel)

    @staticmethod
    def _wrap(value):
        if isinstance(value, six.string_types):
            return [value]
        return value

    @staticmethod
    def _validate_sort_param(sort):
        """Validates sorting argument for invalid keys and directions values.

        :param sort: comma-separated list of sort keys with optional <:dir>
        after each key
        """
        for sort_param in sort.strip().split(','):
            key, _sep, dir = sort_param.partition(':')
            if dir and dir not in SORT_DIR_VALUES:
                msg = ('Invalid sort direction: %(sort_dir)s.'
                       ' It must be one of the following: %(available)s.'
                       ) % {'sort_dir': dir,
                            'available': ', '.join(SORT_DIR_VALUES)}
                raise exc.HTTPBadRequest(msg)
            if key not in SORT_KEY_VALUES:
                msg = ('Invalid sort key: %(sort_key)s.'
                       ' It must be one of the following: %(available)s.'
                       ) % {'sort_key': key,
                            'available': ', '.join(SORT_KEY_VALUES)}
                raise exc.HTTPBadRequest(msg)
        return sort

    def list(self, **kwargs):
        """Retrieve a listing of Image objects

        :param page_size: Number of images to request in each paginated request
        :returns generator over list of Images
        """

        ori_validate_fun = self.model.validate
        empty_fun = lambda *args, **kwargs: None

        limit = kwargs.get('limit')
        # NOTE(flaper87): Don't use `get('page_size', DEFAULT_SIZE)` otherwise,
        # it could be possible to send invalid data to the server by passing
        # page_size=None.
        page_size = kwargs.get('page_size') or DEFAULT_PAGE_SIZE

        def paginate(url, page_size, limit=None):
            next_url = url

            while True:
                if limit and page_size > limit:
                    # NOTE(flaper87): Avoid requesting 2000 images when limit
                    # is 1
                    next_url = next_url.replace("limit=%s" % page_size,
                                                "limit=%s" % limit)

                resp, body = self.http_client.get(next_url)
                for image in body['images']:
                    # NOTE(bcwaldon): remove 'self' for now until we have
                    # an elegant way to pass it into the model constructor
                    # without conflict.
                    image.pop('self', None)
                    yield self.model(**image)
                    # NOTE(zhiyan): In order to resolve the performance issue
                    # of JSON schema validation for image listing case, we
                    # don't validate each image entry but do it only on first
                    # image entry for each page.
                    self.model.validate = empty_fun

                    if limit:
                        limit -= 1
                        if limit <= 0:
                            raise StopIteration

                # NOTE(zhiyan); Reset validation function.
                self.model.validate = ori_validate_fun

                try:
                    next_url = body['next']
                except KeyError:
                    return

        filters = kwargs.get('filters', {})
        # NOTE(flaper87): We paginate in the client, hence we use
        # the page_size as Glance's limit.
        filters['limit'] = page_size

        tags = filters.pop('tag', [])
        tags_url_params = []

        for tag in tags:
            if isinstance(tag, six.string_types):
                tags_url_params.append({'tag': encodeutils.safe_encode(tag)})

        for param, value in six.iteritems(filters):
            if isinstance(value, six.string_types):
                filters[param] = encodeutils.safe_encode(value)

        url = '/v2/images?%s' % parse.urlencode(filters)

        for param in tags_url_params:
            url = '%s&%s' % (url, parse.urlencode(param))

        if 'sort' in kwargs:
            if 'sort_key' in kwargs or 'sort_dir' in kwargs:
                raise exc.HTTPBadRequest("The 'sort' argument is not supported"
                                         " with 'sort_key' or 'sort_dir'.")
            url = '%s&sort=%s' % (url,
                                  self._validate_sort_param(
                                      kwargs['sort']))
        else:
            sort_dir = self._wrap(kwargs.get('sort_dir', []))
            sort_key = self._wrap(kwargs.get('sort_key', []))

            if len(sort_key) != len(sort_dir) and len(sort_dir) > 1:
                raise exc.HTTPBadRequest(
                    "Unexpected number of sort directions: "
                    "either provide a single sort direction or an equal "
                    "number of sort keys and sort directions.")
            for key in sort_key:
                url = '%s&sort_key=%s' % (url, key)

            for dir in sort_dir:
                url = '%s&sort_dir=%s' % (url, dir)

        for image in paginate(url, page_size, limit):
            yield image

    def get(self, image_id):
        url = '/v2/images/%s' % image_id
        resp, body = self.http_client.get(url)
        #NOTE(bcwaldon): remove 'self' for now until we have an elegant
        # way to pass it into the model constructor without conflict
        body.pop('self', None)
        return self.model(**body)

    def data(self, image_id, do_checksum=True):
        """
        Retrieve data of an image.

        :param image_id:    ID of the image to download.
        :param do_checksum: Enable/disable checksum validation.
        """
        url = '/v2/images/%s/file' % image_id
        resp, body = self.http_client.get(url)
        checksum = resp.headers.get('content-md5', None)
        content_length = int(resp.headers.get('content-length', 0))

        if do_checksum and checksum is not None:
            body = utils.integrity_iter(body, checksum)

        return utils.IterableWithLength(body, content_length)

    def upload(self, image_id, image_data, image_size=None):
        """
        Upload the data for an image.

        :param image_id: ID of the image to upload data for.
        :param image_data: File-like object supplying the data to upload.
        :param image_size: Total size in bytes of image to be uploaded.
        """
        url = '/v2/images/%s/file' % image_id
        hdrs = {'Content-Type': 'application/octet-stream'}
        if image_size:
            body = {'image_data': image_data,
                    'image_size': image_size}
        else:
            body = image_data
        self.http_client.put(url, headers=hdrs, data=body)

    def delete(self, image_id):
        """Delete an image."""
        url = '/v2/images/%s' % image_id
        self.http_client.delete(url)

    def create(self, **kwargs):
        """Create an image."""
        url = '/v2/images'

        image = self.model()
        for (key, value) in kwargs.items():
            try:
                setattr(image, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(utils.exception_to_str(e))

        resp, body = self.http_client.post(url, data=image)
        #NOTE(esheffield): remove 'self' for now until we have an elegant
        # way to pass it into the model constructor without conflict
        body.pop('self', None)
        return self.model(**body)

    def update(self, image_id, remove_props=None, **kwargs):
        """
        Update attributes of an image.

        :param image_id: ID of the image to modify.
        :param remove_props: List of property names to remove
        :param **kwargs: Image attribute names and their new values.
        """
        image = self.get(image_id)
        for (key, value) in kwargs.items():
            try:
                setattr(image, key, value)
            except warlock.InvalidOperation as e:
                raise TypeError(utils.exception_to_str(e))

        if remove_props is not None:
            cur_props = image.keys()
            new_props = kwargs.keys()
            #NOTE(esheffield): Only remove props that currently exist on the
            # image and are NOT in the properties being updated / added
            props_to_remove = set(cur_props).intersection(
                set(remove_props).difference(new_props))

            for key in props_to_remove:
                delattr(image, key)

        url = '/v2/images/%s' % image_id
        hdrs = {'Content-Type': 'application/openstack-images-v2.1-json-patch'}
        self.http_client.patch(url, headers=hdrs, data=image.patch)

        #NOTE(bcwaldon): calling image.patch doesn't clear the changes, so
        # we need to fetch the image again to get a clean history. This is
        # an obvious optimization for warlock
        return self.get(image_id)

    def _get_image_with_locations_or_fail(self, image_id):
        image = self.get(image_id)
        if getattr(image, 'locations', None) is None:
            raise exc.HTTPBadRequest('The administrator has disabled '
                                     'API access to image locations')
        return image

    def _send_image_update_request(self, image_id, patch_body):
        url = '/v2/images/%s' % image_id
        hdrs = {'Content-Type': 'application/openstack-images-v2.1-json-patch'}
        self.http_client.patch(url, headers=hdrs, data=json.dumps(patch_body))

    def add_location(self, image_id, url, metadata):
        """Add a new location entry to an image's list of locations.

        It is an error to add a URL that is already present in the list of
        locations.

        :param image_id: ID of image to which the location is to be added.
        :param url: URL of the location to add.
        :param metadata: Metadata associated with the location.
        :returns: The updated image
        """
        image = self._get_image_with_locations_or_fail(image_id)
        url_list = [l['url'] for l in image.locations]
        if url in url_list:
            err_str = 'A location entry at %s already exists' % url
            raise exc.HTTPConflict(err_str)

        add_patch = [{'op': 'add', 'path': '/locations/-',
                      'value': {'url': url, 'metadata': metadata}}]
        self._send_image_update_request(image_id, add_patch)
        return self.get(image_id)

    def delete_locations(self, image_id, url_set):
        """Remove one or more location entries of an image.

        :param image_id: ID of image from which locations are to be removed.
        :param url_set: set of URLs of location entries to remove.
        :returns: None
        """
        image = self._get_image_with_locations_or_fail(image_id)
        current_urls = [l['url'] for l in image.locations]

        missing_locs = url_set.difference(set(current_urls))
        if missing_locs:
            raise exc.HTTPNotFound('Unknown URL(s): %s' % list(missing_locs))

        # NOTE: warlock doesn't generate the most efficient patch for remove
        # operations (it shifts everything up and deletes the tail elements) so
        # we do it ourselves.
        url_indices = [current_urls.index(url) for url in url_set]
        url_indices.sort(reverse=True)
        patches = [{'op': 'remove', 'path': '/locations/%s' % url_idx}
                   for url_idx in url_indices]
        self._send_image_update_request(image_id, patches)

    def update_location(self, image_id, url, metadata):
        """Update an existing location entry in an image's list of locations.

        The URL specified must be already present in the image's list of
        locations.

        :param image_id: ID of image whose location is to be updated.
        :param url: URL of the location to update.
        :param metadata: Metadata associated with the location.
        :returns: The updated image
        """
        image = self._get_image_with_locations_or_fail(image_id)
        url_map = dict([(l['url'], l) for l in image.locations])
        if url not in url_map:
            raise exc.HTTPNotFound('Unknown URL: %s' % url)

        if url_map[url]['metadata'] == metadata:
            return image

        # NOTE: The server (as of now) doesn't support modifying individual
        # location entries. So we must:
        #   1. Empty existing list of locations.
        #   2. Send another request to set 'locations' to the new list
        #      of locations.
        url_map[url]['metadata'] = metadata
        patches = [{'op': 'replace',
                    'path': '/locations',
                    'value': p} for p in ([], list(url_map.values()))]
        self._send_image_update_request(image_id, patches)

        return self.get(image_id)
