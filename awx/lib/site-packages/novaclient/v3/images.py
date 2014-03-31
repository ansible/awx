# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2013 IBM Corp.
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

"""
Image interface.
"""

from six.moves.urllib import parse

from novaclient import base
from novaclient.openstack.common import strutils


class Image(base.Resource):
    """
    An image is a collection of files used to create or rebuild a server.
    """
    HUMAN_ID = True

    def __repr__(self):
        return "<Image: %s>" % self.name

    def delete(self):
        """
        Delete this image.
        """
        self.manager.delete(self)


class ImageManager(base.ManagerWithFind):
    """
    Manage :class:`Image` resources.
    """
    resource_class = Image
    # NOTE(cyeoh): Eventually we'll want novaclient to be smart
    # enough to do version discovery, but for now we just request
    # the v1 image API
    image_api_prefix = '/v1'

    def _image_meta_from_headers(self, headers):
        meta = {'properties': {}}
        safe_decode = strutils.safe_decode
        for key, value in headers.items():
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

    @staticmethod
    def _format_image_meta_for_user(meta):
        for key in ['size', 'min_ram', 'min_disk']:
            if key in meta:
                try:
                    meta[key] = int(meta[key])
                except ValueError:
                    pass
        return meta

    def get(self, image):
        """
        Get an image.

        :param image: The ID of the image to get.
        :rtype: :class:`Image`
        """
        url = "%s/images/%s" % (self.image_api_prefix, base.getid(image))
        resp, _ = self.api.client._cs_request(url, 'HEAD')
        foo = self._image_meta_from_headers(resp.headers)
        return Image(self, foo)

    def list(self, detailed=True, limit=None):
        """
        Get a list of all images.

        :rtype: list of :class:`Image`
        :param limit: maximum number of images to return.
        """
        params = {}
        detail = ''
        if detailed:
            detail = '/detail'
        if limit:
            params['limit'] = int(limit)
        query = '?%s' % parse.urlencode(params) if params else ''
        return self._list('/v1/images%s%s' % (detail, query), 'images')
