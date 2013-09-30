# Copyright 2010 Jacob Kaplan-Moss
"""
Image interface.
"""
from novaclient import base
from novaclient.openstack.common.py3kcompat import urlutils


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

    def get(self, image):
        """
        Get an image.

        :param image: The ID of the image to get.
        :rtype: :class:`Image`
        """
        return self._get("/images/%s" % base.getid(image), "image")

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
        query = '?%s' % urlutils.urlencode(params) if params else ''
        return self._list('/images%s%s' % (detail, query), 'images')

    def delete(self, image):
        """
        Delete an image.

        It should go without saying that you can't delete an image
        that you didn't create.

        :param image: The :class:`Image` (or its ID) to delete.
        """
        self._delete("/images/%s" % base.getid(image))

    def set_meta(self, image, metadata):
        """
        Set an images metadata

        :param image: The :class:`Image` to add metadata to
        :param metadata: A dict of metadata to add to the image
        """
        body = {'metadata': metadata}
        return self._create("/images/%s/metadata" % base.getid(image), body,
                             "metadata")

    def delete_meta(self, image, keys):
        """
        Delete metadata from an image

        :param image: The :class:`Image` to add metadata to
        :param keys: A list of metadata keys to delete from the image
        """
        for k in keys:
            self._delete("/images/%s/metadata/%s" % (base.getid(image), k))
