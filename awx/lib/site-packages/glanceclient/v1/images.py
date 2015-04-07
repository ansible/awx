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

import copy

from oslo_utils import encodeutils
from oslo_utils import strutils
import six
import six.moves.urllib.parse as urlparse

from glanceclient.common import utils
from glanceclient.openstack.common.apiclient import base

UPDATE_PARAMS = ('name', 'disk_format', 'container_format', 'min_disk',
                 'min_ram', 'owner', 'size', 'is_public', 'protected',
                 'location', 'checksum', 'copy_from', 'properties',
                 #NOTE(bcwaldon: an attempt to update 'deleted' will be
                 # ignored, but we need to support it for backwards-
                 # compatibility with the legacy client library
                 'deleted')

CREATE_PARAMS = UPDATE_PARAMS + ('id', 'store')

DEFAULT_PAGE_SIZE = 20

SORT_DIR_VALUES = ('asc', 'desc')
SORT_KEY_VALUES = ('name', 'status', 'container_format', 'disk_format',
                   'size', 'id', 'created_at', 'updated_at')

OS_REQ_ID_HDR = 'x-openstack-request-id'


class Image(base.Resource):
    def __repr__(self):
        return "<Image %s>" % self._info

    def update(self, **fields):
        self.manager.update(self, **fields)

    def delete(self, **kwargs):
        return self.manager.delete(self)

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class ImageManager(base.ManagerWithFind):
    resource_class = Image

    def _list(self, url, response_key, obj_class=None, body=None):
        resp, body = self.client.get(url)

        if obj_class is None:
            obj_class = self.resource_class

        data = body[response_key]
        return ([obj_class(self, res, loaded=True) for res in data if res],
                resp)

    def _image_meta_from_headers(self, headers):
        meta = {'properties': {}}
        safe_decode = encodeutils.safe_decode
        for key, value in six.iteritems(headers):
            value = safe_decode(value, incoming='utf-8')
            if key.startswith('x-image-meta-property-'):
                _key = safe_decode(key[22:], incoming='utf-8')
                meta['properties'][_key] = value
            elif key.startswith('x-image-meta-'):
                _key = safe_decode(key[13:], incoming='utf-8')
                meta[_key] = value

        for key in ['is_public', 'protected', 'deleted']:
            if key in meta:
                meta[key] = strutils.bool_from_string(meta[key])

        return self._format_image_meta_for_user(meta)

    def _image_meta_to_headers(self, fields):
        headers = {}
        fields_copy = copy.deepcopy(fields)

        # NOTE(flaper87): Convert to str, headers
        # that are not instance of basestring. All
        # headers will be encoded later, before the
        # request is sent.
        def to_str(value):
            if not isinstance(value, six.string_types):
                return str(value)
            return value

        for key, value in six.iteritems(fields_copy.pop('properties', {})):
            headers['x-image-meta-property-%s' % key] = to_str(value)
        for key, value in six.iteritems(fields_copy):
            headers['x-image-meta-%s' % key] = to_str(value)
        return headers

    @staticmethod
    def _format_image_meta_for_user(meta):
        for key in ['size', 'min_ram', 'min_disk']:
            if key in meta:
                try:
                    meta[key] = int(meta[key]) if meta[key] else 0
                except ValueError:
                    pass
        return meta

    def get(self, image, **kwargs):
        """Get the metadata for a specific image.

        :param image: image object or id to look up
        :rtype: :class:`Image`
        """
        image_id = base.getid(image)
        resp, body = self.client.head('/v1/images/%s'
                                      % urlparse.quote(str(image_id)))
        meta = self._image_meta_from_headers(resp.headers)
        return_request_id = kwargs.get('return_req_id', None)
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))
        return Image(self, meta)

    def data(self, image, do_checksum=True, **kwargs):
        """Get the raw data for a specific image.

        :param image: image object or id to look up
        :param do_checksum: Enable/disable checksum validation
        :rtype: iterable containing image data
        """
        image_id = base.getid(image)
        resp, body = self.client.get('/v1/images/%s'
                                     % urlparse.quote(str(image_id)))
        content_length = int(resp.headers.get('content-length', 0))
        checksum = resp.headers.get('x-image-meta-checksum', None)
        if do_checksum and checksum is not None:
            body = utils.integrity_iter(body, checksum)
        return_request_id = kwargs.get('return_req_id', None)
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))

        return utils.IterableWithLength(body, content_length)

    def _build_params(self, parameters):
        params = {'limit': parameters.get('page_size', DEFAULT_PAGE_SIZE)}

        if 'marker' in parameters:
            params['marker'] = parameters['marker']

        sort_key = parameters.get('sort_key')
        if sort_key is not None:
            if sort_key in SORT_KEY_VALUES:
                params['sort_key'] = sort_key
            else:
                raise ValueError('sort_key must be one of the following: %s.'
                                 % ', '.join(SORT_KEY_VALUES))

        sort_dir = parameters.get('sort_dir')
        if sort_dir is not None:
            if sort_dir in SORT_DIR_VALUES:
                params['sort_dir'] = sort_dir
            else:
                raise ValueError('sort_dir must be one of the following: %s.'
                                 % ', '.join(SORT_DIR_VALUES))

        filters = parameters.get('filters', {})
        properties = filters.pop('properties', {})
        for key, value in properties.items():
            params['property-%s' % key] = value
        params.update(filters)
        if parameters.get('owner') is not None:
            params['is_public'] = None
        if 'is_public' in parameters:
            params['is_public'] = parameters['is_public']

        return params

    def list(self, **kwargs):
        """Get a list of images.

        :param page_size: number of items to request in each paginated request
        :param limit: maximum number of images to return
        :param marker: begin returning images that appear later in the image
                       list than that represented by this image id
        :param filters: dict of direct comparison filters that mimics the
                        structure of an image object
        :param owner: If provided, only images with this owner (tenant id)
                      will be listed. An empty string ('') matches ownerless
                      images.
        :param return_request_id: If an empty list is provided, populate this
                              list with the request ID value from the header
                              x-openstack-request-id
        :rtype: list of :class:`Image`
        """
        absolute_limit = kwargs.get('limit')
        page_size = kwargs.get('page_size', DEFAULT_PAGE_SIZE)
        owner = kwargs.get('owner', None)

        def filter_owner(owner, image):
            # If client side owner 'filter' is specified
            # only return images that match 'owner'.
            if owner is None:
                # Do not filter based on owner
                return False
            if (not hasattr(image, 'owner')) or image.owner is None:
                # ownerless image
                return not (owner == '')
            else:
                return not (image.owner == owner)

        def paginate(qp, return_request_id=None):
            for param, value in six.iteritems(qp):
                if isinstance(value, six.string_types):
                    # Note(flaper87) Url encoding should
                    # be moved inside http utils, at least
                    # shouldn't be here.
                    #
                    # Making sure all params are str before
                    # trying to encode them
                    qp[param] = encodeutils.safe_decode(value)

            url = '/v1/images/detail?%s' % urlparse.urlencode(qp)
            images, resp = self._list(url, "images")

            if return_request_id is not None:
                return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))

            for image in images:
                yield image

        return_request_id = kwargs.get('return_req_id', None)

        params = self._build_params(kwargs)

        seen = 0
        while True:
            seen_last_page = 0
            filtered = 0
            for image in paginate(params, return_request_id):
                last_image = image.id

                if filter_owner(owner, image):
                    # Note(kragniz): ignore this image
                    filtered += 1
                    continue

                if (absolute_limit is not None and
                        seen + seen_last_page >= absolute_limit):
                    # Note(kragniz): we've seen enough images
                    return
                else:
                    seen_last_page += 1
                    yield image

            seen += seen_last_page

            if seen_last_page + filtered == 0:
                # Note(kragniz): we didn't get any images in the last page
                return

            if absolute_limit is not None and seen >= absolute_limit:
                # Note(kragniz): reached the limit of images to return
                return

            if page_size and seen_last_page + filtered < page_size:
                # Note(kragniz): we've reached the last page of the images
                return

            # Note(kragniz): there are more images to come
            params['marker'] = last_image
            seen_last_page = 0

    def delete(self, image, **kwargs):
        """Delete an image."""
        url = "/v1/images/%s" % base.getid(image)
        resp, body = self.client.delete(url)
        return_request_id = kwargs.get('return_req_id', None)
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))

    def create(self, **kwargs):
        """Create an image

        TODO(bcwaldon): document accepted params
        """
        image_data = kwargs.pop('data', None)
        if image_data is not None:
            image_size = utils.get_file_size(image_data)
            if image_size is not None:
                kwargs.setdefault('size', image_size)

        fields = {}
        for field in kwargs:
            if field in CREATE_PARAMS:
                fields[field] = kwargs[field]
            elif field == 'return_req_id':
                continue
            else:
                msg = 'create() got an unexpected keyword argument \'%s\''
                raise TypeError(msg % field)

        copy_from = fields.pop('copy_from', None)
        hdrs = self._image_meta_to_headers(fields)
        if copy_from is not None:
            hdrs['x-glance-api-copy-from'] = copy_from

        resp, body = self.client.post('/v1/images',
                                      headers=hdrs,
                                      data=image_data)
        return_request_id = kwargs.get('return_req_id', None)
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))

        return Image(self, self._format_image_meta_for_user(body['image']))

    def update(self, image, **kwargs):
        """Update an image

        TODO(bcwaldon): document accepted params
        """
        image_data = kwargs.pop('data', None)
        if image_data is not None:
            image_size = utils.get_file_size(image_data)
            if image_size is not None:
                kwargs.setdefault('size', image_size)

        hdrs = {}
        purge_props = 'false'
        purge_props_bool = kwargs.pop('purge_props', None)
        if purge_props_bool:
            purge_props = 'true'

        hdrs['x-glance-registry-purge-props'] = purge_props
        fields = {}
        for field in kwargs:
            if field in UPDATE_PARAMS:
                fields[field] = kwargs[field]
            elif field == 'return_req_id':
                continue
            else:
                msg = 'update() got an unexpected keyword argument \'%s\''
                raise TypeError(msg % field)

        copy_from = fields.pop('copy_from', None)
        hdrs.update(self._image_meta_to_headers(fields))
        if copy_from is not None:
            hdrs['x-glance-api-copy-from'] = copy_from

        url = '/v1/images/%s' % base.getid(image)
        resp, body = self.client.put(url, headers=hdrs, data=image_data)
        return_request_id = kwargs.get('return_req_id', None)
        if return_request_id is not None:
            return_request_id.append(resp.headers.get(OS_REQ_ID_HDR, None))

        return Image(self, self._format_image_meta_for_user(body['image']))
