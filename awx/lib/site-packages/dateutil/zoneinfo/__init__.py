# -*- coding: utf-8 -*-
import logging
import os
import warnings
import tempfile
import shutil
from subprocess import check_call
from tarfile import TarFile
from pkgutil import get_data
from io import BytesIO
from contextlib import closing

from dateutil.tz import tzfile

__all__ = ["setcachesize", "gettz", "rebuild"]

_ZONEFILENAME = "dateutil-zoneinfo.tar.gz"

# python2.6 compatability. Note that TarFile.__exit__ != TarFile.close, but
# it's close enough for python2.6
_tar_open = TarFile.open
if not hasattr(TarFile, '__exit__'):
    def _tar_open(*args, **kwargs):
        return closing(TarFile.open(*args, **kwargs))


class tzfile(tzfile):
    def __reduce__(self):
        return (gettz, (self._filename,))


def getzoneinfofile_stream():
    try:
        return BytesIO(get_data(__name__, _ZONEFILENAME))
    except IOError as e:  # TODO  switch to FileNotFoundError?
        warnings.warn("I/O error({0}): {1}".format(e.errno, e.strerror))
        return None


class ZoneInfoFile(object):
    def __init__(self, zonefile_stream=None):
        if zonefile_stream is not None:
            with _tar_open(fileobj=zonefile_stream, mode='r') as tf:
                # dict comprehension does not work on python2.6
                # TODO: get back to the nicer syntax when we ditch python2.6
                # self.zones = {zf.name: tzfile(tf.extractfile(zf),
                #               filename = zf.name)
                #              for zf in tf.getmembers() if zf.isfile()}
                self.zones = dict((zf.name, tzfile(tf.extractfile(zf),
                                                   filename=zf.name))
                                  for zf in tf.getmembers() if zf.isfile())
                # deal with links: They'll point to their parent object. Less
                # waste of memory
                # links = {zl.name: self.zones[zl.linkname]
                #        for zl in tf.getmembers() if zl.islnk() or zl.issym()}
                links = dict((zl.name, self.zones[zl.linkname])
                             for zl in tf.getmembers() if
                             zl.islnk() or zl.issym())
                self.zones.update(links)
        else:
            self.zones = dict()


# The current API has gettz as a module function, although in fact it taps into
# a stateful class. So as a workaround for now, without changing the API, we
# will create a new "global" class instance the first time a user requests a
# timezone. Ugly, but adheres to the api.
#
# TODO: deprecate this.
_CLASS_ZONE_INSTANCE = list()


def gettz(name):
    if len(_CLASS_ZONE_INSTANCE) == 0:
        _CLASS_ZONE_INSTANCE.append(ZoneInfoFile(getzoneinfofile_stream()))
    return _CLASS_ZONE_INSTANCE[0].zones.get(name)


def rebuild(filename, tag=None, format="gz", zonegroups=[]):
    """Rebuild the internal timezone info in dateutil/zoneinfo/zoneinfo*tar*

    filename is the timezone tarball from ftp.iana.org/tz.

    """
    tmpdir = tempfile.mkdtemp()
    zonedir = os.path.join(tmpdir, "zoneinfo")
    moduledir = os.path.dirname(__file__)
    try:
        with _tar_open(filename) as tf:
            for name in zonegroups:
                tf.extract(name, tmpdir)
            filepaths = [os.path.join(tmpdir, n) for n in zonegroups]
            try:
                check_call(["zic", "-d", zonedir] + filepaths)
            except OSError as e:
                if e.errno == 2:
                    logging.error(
                        "Could not find zic. Perhaps you need to install "
                        "libc-bin or some other package that provides it, "
                        "or it's not in your PATH?")
                    raise
        target = os.path.join(moduledir, _ZONEFILENAME)
        with _tar_open(target, "w:%s" % format) as tf:
            for entry in os.listdir(zonedir):
                entrypath = os.path.join(zonedir, entry)
                tf.add(entrypath, entry)
    finally:
        shutil.rmtree(tmpdir)
