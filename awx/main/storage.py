# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import base64
from cStringIO import StringIO

from django.core import files
from django.core.files.storage import Storage


class DatabaseStorage(Storage):
    """A class for storing uploaded files into the database, rather than
    on the filesystem.
    """
    def __init__(self, model):
        self.model = model
    
    def _open(self, name, mode='rb'):
        try:
            f = self.model.objects.get(filename=name)
        except self.model.DoesNotExist:
            return None
        fh = StringIO(base64.b64decode(f.contents))
        fh.name = name
        fh.mode = mode
        fh.size = f.size
        return files.File(fh)
    
    def _save(self, name, content):
        try:
            file_ = self.model.objects.get(filename=name)
        except self.model.DoesNotExist:
            file_ = self.model(filename=name)
        file_.contents = base64.b64encode(content.read())
        file_.save()
        return name
    
    def exists(self, name):
        """Return True if the given file already exists in the database,
        or False otherwise.
        """
        return bool(self.model.objects.filter(filename=name).count())
    
    def delete(self, name):
        """Delete the file in the database, failing silently if the file
        does not exist.
        """
        self.model.objects.filter(filename=name).delete()

    def listdir(self, path=None):
        """Return a full list of files stored in the database, ignoring
        whatever may be sent to the `path` argument.
        """
        filenames = [i.filename for i in self.model.order_by('filename')]
        return ([], filenames)
    
    def url(self, name):
        raise NotImplementedError
    
    def size(self, name):
        """Return the size of the given file, if it exists; raise DoesNotExist
        if the file is not present.
        """
        file_ = self.model.objects.get(filename=name)
        return len(file_.contents)
