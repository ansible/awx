import os
import itertools
import urlparse

from mongoengine import *
from django.conf import settings
from django.core.files.storage import Storage
from django.core.exceptions import ImproperlyConfigured


class FileDocument(Document):
    """A document used to store a single file in GridFS.
    """
    file = FileField()


class GridFSStorage(Storage):
    """A custom storage backend to store files in GridFS
    """

    def __init__(self, base_url=None):

        if base_url is None:
            base_url = settings.MEDIA_URL
        self.base_url = base_url
        self.document = FileDocument
        self.field = 'file'

    def delete(self, name):
        """Deletes the specified file from the storage system.
        """
        if self.exists(name):
            doc = self.document.objects.first()
            field = getattr(doc, self.field)
            self._get_doc_with_name(name).delete()  # Delete the FileField
            field.delete()                          # Delete the FileDocument

    def exists(self, name):
        """Returns True if a file referened by the given name already exists in the
        storage system, or False if the name is available for a new file.
        """
        doc = self._get_doc_with_name(name)
        if doc:
            field = getattr(doc, self.field)
            return bool(field.name)
        else:
            return False

    def listdir(self, path=None):
        """Lists the contents of the specified path, returning a 2-tuple of lists;
        the first item being directories, the second item being files.
        """
        def name(doc):
            return getattr(doc, self.field).name
        docs = self.document.objects
        return [], [name(d) for d in docs if name(d)]

    def size(self, name):
        """Returns the total size, in bytes, of the file specified by name.
        """
        doc = self._get_doc_with_name(name)
        if doc:
            return getattr(doc, self.field).length
        else:
            raise ValueError("No such file or directory: '%s'" % name)

    def url(self, name):
        """Returns an absolute URL where the file's contents can be accessed
        directly by a web browser.
        """
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")
        return urlparse.urljoin(self.base_url, name).replace('\\', '/')

    def _get_doc_with_name(self, name):
        """Find the documents in the store with the given name
        """
        docs = self.document.objects
        doc = [d for d in docs if hasattr(getattr(d, self.field), 'name') and getattr(d, self.field).name == name]
        if doc:
            return doc[0]
        else:
            return None

    def _open(self, name, mode='rb'):
        doc = self._get_doc_with_name(name)
        if doc:
            return getattr(doc, self.field)
        else:
            raise ValueError("No file found with the name '%s'." % name)

    def get_available_name(self, name):
        """Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        file_root, file_ext = os.path.splitext(name)
        # If the filename already exists, add an underscore and a number (before
        # the file extension, if one exists) to the filename until the generated
        # filename doesn't exist.
        count = itertools.count(1)
        while self.exists(name):
            # file_ext includes the dot.
            name = os.path.join("%s_%s%s" % (file_root, count.next(), file_ext))

        return name

    def _save(self, name, content):
        doc = self.document()
        getattr(doc, self.field).put(content, filename=name)
        doc.save()

        return name
