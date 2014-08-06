#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import datetime
import email.utils
import fnmatch
import hashlib
import numbers
import os
import random
import re
import shutil
import string
from subprocess import Popen, PIPE
import sys
import tempfile
import threading
import time
import types

try:
    import pudb
except ImportError:
    import pdb as pudb
trace = pudb.set_trace

import six

import pyrax
import pyrax.exceptions as exc


def runproc(cmd):
    """
    Convenience method for executing operating system commands.

    Accepts a single string that would be the command as executed on the
    command line.

    Returns a 2-tuple consisting of the output of (STDOUT, STDERR). In your
    code you should check for an empty STDERR output to determine if your
    command completed successfully.
    """
    proc = Popen([cmd], shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE,
            close_fds=True)
    stdoutdata, stderrdata = proc.communicate()
    return (stdoutdata, stderrdata)


class SelfDeletingTempfile(object):
    """
    Convenience class for dealing with temporary files.

    The temp file is created in a secure fashion, and is
    automatically deleted when the context manager exits.

    Usage:

    \code
    with SelfDeletingTempfile() as tmp:
        tmp.write( ... )
        some_func(tmp)
    # More code
    # At this point, the tempfile has been erased.
    \endcode
    """
    name = None

    def __enter__(self):
        fd, self.name = tempfile.mkstemp()
        os.close(fd)
        return self.name

    def __exit__(self, type, value, traceback):
        os.unlink(self.name)


class SelfDeletingTempDirectory(object):
    """
    Convenience class for dealing with temporary folders and the
    files within them.

    The temp folder is created in a secure fashion, and is
    automatically deleted when the context manager exits, along
    with any files that may be contained within. When you
    instantiate this class, you receive the full path to the
    temporary directory.

    Usage:

    \code
    with SelfDeletingTempDirectory() as tmpdir:
        f1 = open(os.path.join(tmpdir, "my_file.txt", "w")
        f1.write("blah...")
        f1.close()
        some_func(tmpdir)
    # More code
    # At this point, the directory 'tmpdir' has been deleted,
    # as well as the file 'f1' within it.
    \endcode
    """
    name = None

    def __enter__(self):
        self.name = tempfile.mkdtemp()
        return self.name

    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.name)



class DotDict(dict):
    """
    Dictionary subclass that allows accessing keys via dot notation.

    If the key is not present, an AttributeError is raised.
    """
    _att_mapper = {}
    _fail = object()

    def __init__(self, *args, **kwargs):
        super(DotDict, self).__init__(*args, **kwargs)

    def __getattr__(self, att):
        att = self._att_mapper.get(att, att)
        ret = self.get(att, self._fail)
        if ret is self._fail:
            raise AttributeError("'%s' object has no attribute '%s'" %
                    (self.__class__.__name__, att))
        return ret

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__



class ResultsIterator(object):
    """
    This object will iterate over all the results for a given type of listing,
    no matter how many items exist.

    This is an abstract class; subclasses must define the _init_methods()
    method to specify what manager method should be called to get the next
    batch of results. Both the equivalent of 'list()' and '_list()' may be
    specified You may also specify any extra args to be sent when this method
    is called.

    By default the marker will be unspecified, and the limit will be 1000. You
    can override either by specifying them during instantiation.

    The 'kwargs' will be converted to attributes. E.g., in this call:
        rit = ResultsIterator(mgr, foo="bar")
    will result in the object having a 'foo' attribute with the value of 'bar'.
    """
    def __init__(self, manager, marker=None, limit=1000, **kwargs):
        self.manager = manager
        self.marker = marker
        self.limit = limit
        for att, val in list(kwargs.items()):
            setattr(self, att, val)
        self.results = []
        self.list_method = None
        self._list_method = None
        self.marker_att = "id"
        self.extra_args = tuple()
        self._init_methods()
        self.next_uri = ""


    def _init_methods(self):
        """
        Must be implemented in subclasses. For results that return a URI for
        the next batch of results, the lower-level '_list_method' will be
        called, using that URI. Otherwise, the 'list_method' will be called,
        with the paging info from the prior call.

        If your class uses an attribute other than 'id' as the marker, set this
        object's 'marker_att' to that attribute.
        """
        raise NotImplementedError()


    def __iter__(self):
        return self


    def next(self):
        """
        Return the next available item. If there are no more items in the
        local 'results' list, check if there is a 'next_uri' value. If so,
        use that to get the next page of results from the API, and return
        the first item from that query.
        """
        try:
            return self.results.pop(0)
        except IndexError:
            if self.next_uri is None:
                raise StopIteration()
            else:
                if not self.next_uri:
                    self.results = self.list_method(marker=self.marker,
                            limit=self.limit, prefix=self.prefix)
                else:
                    args = self.extra_args
                    self.results = self._list_method(self.next_uri, *args)
                if self.results:
                    last_res = self.results[-1]
                    self.marker = getattr(last_res, self.marker_att)
        # We should have more results.
        try:
            return self.results.pop(0)
        except IndexError:
            raise StopIteration()


def get_checksum(content, encoding="utf8", block_size=8192):
    """
    Returns the MD5 checksum in hex for the given content. If 'content'
    is a file-like object, the content will be obtained from its read()
    method. If 'content' is a file path, that file is read and its
    contents used. Otherwise, 'content' is assumed to be the string whose
    checksum is desired. If the content is unicode, it will be encoded
    using the specified encoding.

    To conserve memory, files and file-like objects will be read in blocks,
    with the default block size of 8192 bytes, which is 64 * the digest block
    size of md5 (128). This is optimal for most cases, but you can change this
    by passing in a different value for `block_size`.
    """
    md = hashlib.md5()

    def safe_update(txt):
        try:
            md.update(txt)
        except UnicodeEncodeError:
            md.update(txt.encode(encoding))

    try:
        isfile = os.path.isfile(content)
    except TypeError:
        # Will happen with binary content.
        isfile = False
    if isfile:
        with open(content, "rb") as ff:
            txt = ff.read(block_size)
            while txt:
                safe_update(txt)
                txt = ff.read(block_size)
    elif hasattr(content, "read"):
        pos = content.tell()
        content.seek(0)
        txt = content.read(block_size)
        while txt:
            safe_update(txt)
            txt = content.read(block_size)
        content.seek(pos)
    else:
        safe_update(content)
    return md.hexdigest()


def _join_chars(chars, length):
    """
    Used by the random character functions.
    """
    mult = int(length / len(chars)) + 1
    mult_chars = chars * mult
    return "".join(random.sample(mult_chars, length))


def random_unicode(length=20):
    """
    Generates a random name; useful for testing.

    Returns an encoded string of the specified length containing unicode values
    up to code point 1000.
    """
    def get_char():
        return six.unichr(random.randint(32, 1000))
    chars = u"".join([get_char() for ii in six.moves.range(length)])
    return _join_chars(chars, length)


def random_ascii(length=20, ascii_only=False):
    """
    Generates a random name; useful for testing.

    Returns a string of the specified length containing only ASCII characters.
    """
    return _join_chars(string.ascii_letters, length)


def coerce_string_to_list(val):
    """
    For parameters that can take either a single string or a list of strings,
    this function will ensure that the result is a list containing the passed
    values.
    """
    if val:
        if not isinstance(val, (list, tuple)):
            val = [val]
    else:
        val = []
    return val


def folder_size(pth, ignore=None):
    """
    Returns the total bytes for the specified path, optionally ignoring
    any files which match the 'ignore' parameter. 'ignore' can either be
    a single string pattern, or a list of such patterns.
    """
    if not os.path.isdir(pth):
        raise exc.FolderNotFound

    ignore = coerce_string_to_list(ignore)

    def get_size(total, root, names):
        paths = [os.path.realpath(os.path.join(root, nm)) for nm in names]
        for pth in paths[::-1]:
            if not os.path.exists(pth):
                paths.remove(pth)
            elif os.path.isdir(pth):
                # Don't count folder stat sizes
                paths.remove(pth)
            elif match_pattern(pth, ignore):
                paths.remove(pth)
        total[0] += sum(os.stat(pth).st_size for pth in paths)

    # Need a mutable to pass
    total = [0]
    os.path.walk(pth, get_size, total)
    return total[0]


def add_method(obj, func, name=None):
    """Adds an instance method to an object."""
    if name is None:
        name = func.func_name
    method = types.MethodType(func, obj, obj.__class__)
    setattr(obj, name, method)


class _WaitThread(threading.Thread):
    """
    Threading class to wait for object status in the background. Note that
    verbose will always be False for a background thread.
    """
    def __init__(self, obj, att, desired, callback, interval, attempts,
            verbose, verbose_atts):
        self.obj = obj
        self.att = att
        self.desired = desired
        self.callback = callback
        self.interval = interval
        self.attempts = attempts
        self.verbose = verbose
        threading.Thread.__init__(self)

    def run(self):
        """Starts the thread."""
        resp = _wait_until(obj=self.obj, att=self.att,
                desired=self.desired, callback=None,
                interval=self.interval, attempts=self.attempts,
                verbose=False, verbose_atts=None)
        self.callback(resp)


def wait_until(obj, att, desired, callback=None, interval=5, attempts=0,
        verbose=False, verbose_atts=None):
    """
    When changing the state of an object, it will commonly be in a transitional
    state until the change is complete. This will reload the object every
    `interval` seconds, and check its `att` attribute until the `desired` value
    is reached, or until the maximum number of attempts is reached. The updated
    object is returned. It is up to the calling program to check the returned
    object to make sure that it successfully reached the desired state.

    Once the desired value of the attribute is reached, the method returns. If
    not, it will re-try until the attribute's value matches one of the
    `desired` values. By default (attempts=0) it will loop infinitely until the
    attribute reaches the desired value. You can optionally limit the number of
    times that the object is reloaded by passing a positive value to
    `attempts`. If the attribute has not reached the desired value by then, the
    method will exit.

    If `verbose` is True, each attempt will print out the current value of the
    watched attribute and the time that has elapsed since the original request.
    Also, if `verbose_atts` is specified, the values of those attributes will
    also be output. If `verbose` is False, then `verbose_atts` has no effect.

    Note that `desired` can be a list of values; if the attribute becomes equal
    to any of those values, this will succeed. For example, when creating a new
    cloud server, it will initially have a status of 'BUILD', and you can't
    work with it until its status is 'ACTIVE'. However, there might be a
    problem with the build process, and the server will change to a status of
    'ERROR'. So for this case you need to set the `desired` parameter to
    `['ACTIVE', 'ERROR']`. If you simply pass 'ACTIVE' as the desired state,
    this will loop indefinitely if a build fails, as the server will never
    reach a status of 'ACTIVE'.

    Since this process of waiting can take a potentially long time, and will
    block your program's execution until the desired state of the object is
    reached, you may specify a callback function. The callback can be any
    callable that accepts a single parameter; the parameter it receives will be
    either the updated object (success), or None (failure). If a callback is
    specified, the program will return immediately after spawning the wait
    process in a separate thread.
    """
    if callback:
        waiter = _WaitThread(obj=obj, att=att, desired=desired, callback=callback,
                interval=interval, attempts=attempts, verbose=verbose,
                verbose_atts=verbose_atts)
        waiter.start()
        return waiter
    else:
        return _wait_until(obj=obj, att=att, desired=desired, callback=None,
                interval=interval, attempts=attempts, verbose=verbose,
                verbose_atts=verbose_atts)


def _wait_until(obj, att, desired, callback, interval, attempts, verbose,
        verbose_atts):
    """
    Loops until either the desired value of the attribute is reached, or the
    number of attempts is exceeded.
    """
    if not isinstance(desired, (list, tuple)):
        desired = [desired]
    if verbose_atts is None:
        verbose_atts = []
    if not isinstance(verbose_atts, (list, tuple)):
        verbose_atts = [verbose_atts]
    infinite = (attempts == 0)
    attempt = 0
    start = time.time()
    while infinite or (attempt < attempts):
        try:
            # For servers:
            obj.get()
        except AttributeError:
            try:
                # For other objects that don't support .get()
                obj = obj.manager.get(obj.id)
            except AttributeError:
                # punt
                raise exc.NoReloadError("The 'wait_until' method is not "
                        "supported for '%s' objects." % obj.__class__)
        attval = getattr(obj, att)
        if verbose:
            elapsed = time.time() - start
            msgs = ["Current value of %s: %s (elapsed: %4.1f seconds)" % (
                    att, attval, elapsed)]
            for vatt in verbose_atts:
                vattval = getattr(obj, vatt, None)
                msgs.append("%s=%s" % (vatt, vattval))
            print(" ".join(msgs))
        if attval in desired:
            return obj
        time.sleep(interval)
        attempt += 1
    return obj



def wait_for_build(obj, att=None, desired=None, callback=None, interval=None,
        attempts=None, verbose=None, verbose_atts=None):
    """
    Designed to handle the most common use case for wait_until: an object whose
    'status' attribute will end up in either 'ACTIVE' or 'ERROR' state. Since
    builds don't happen very quickly, the interval will default to 20 seconds
    to avoid excess polling.
    """
    att = att or "status"
    desired = desired or ["ACTIVE", "ERROR", "available", "COMPLETED"]
    interval = interval or 20
    attempts = attempts or 0
    verbose_atts = verbose_atts or "progress"
    return wait_until(obj, att, desired, callback=callback, interval=interval,
            attempts=attempts, verbose=verbose, verbose_atts=verbose_atts)


def _parse_datetime_string(val):
    """
    Attempts to parse a string representation of a date or datetime value, and
    returns a datetime if successful. If not, a InvalidDateTimeString exception
    will be raised.
    """
    dt = None
    lenval = len(val)
    fmt = {19: "%Y-%m-%d %H:%M:%S", 10: "%Y-%m-%d"}.get(lenval)
    if fmt is None:
        # Invalid date
        raise exc.InvalidDateTimeString("The supplied value '%s' does not "
              "match either of the formats 'YYYY-MM-DD HH:MM:SS' or "
              "'YYYY-MM-DD'." % val)
    return datetime.datetime.strptime(val, fmt)


def iso_time_string(val, show_tzinfo=False):
    """
    Takes either a date, datetime or a string, and returns the standard ISO
    formatted string for that date/time, with any fractional second portion
    removed.
    """
    if not val:
        return ""
    if isinstance(val, six.string_types):
        dt = _parse_datetime_string(val)
    else:
        dt = val
    if not isinstance(dt, datetime.datetime):
        dt = datetime.datetime.fromordinal(dt.toordinal())
    has_tz = (dt.tzinfo is not None)
    if show_tzinfo and has_tz:
        # Need to remove the colon in the TZ portion
        ret = "".join(dt.isoformat().rsplit(":", 1))
    elif show_tzinfo and not has_tz:
        ret = "%s+0000" % dt.isoformat().split(".")[0]
    elif not show_tzinfo and has_tz:
        ret = dt.isoformat()[:-6]
    elif not show_tzinfo and not has_tz:
        ret = dt.isoformat().split(".")[0]
    return ret


def rfc2822_format(val):
    """
    Takes either a date, a datetime, or a string, and returns a string that
    represents the value in RFC 2822 format. If a string is passed it is
    returned unchanged.
    """
    if isinstance(val, six.string_types):
        return val
    elif isinstance(val, (datetime.datetime, datetime.date)):
        # Convert to a timestamp
        val = time.mktime(val.timetuple())
    if isinstance(val, numbers.Number):
        return email.utils.formatdate(val)
    else:
        # Bail
        return val


def to_timestamp(val):
    """
    Takes a value that is either a Python date, datetime, or a string
    representation of a date/datetime value. Returns a standard Unix timestamp
    corresponding to that value.
    """
    # If we're given a number, give it right back - it's already a timestamp.
    if isinstance(val, numbers.Number):
        return val
    elif isinstance(val, six.string_types):
        dt = _parse_datetime_string(val)
    else:
        dt = val
    return time.mktime(dt.timetuple())


def get_id(id_or_obj):
    """
    Returns the 'id' attribute of 'id_or_obj' if present; if not,
    returns 'id_or_obj'.
    """
    if isinstance(id_or_obj, six.string_types + (int,)):
        # It's an ID
        return id_or_obj
    try:
        return id_or_obj.id
    except AttributeError:
        return id_or_obj


def get_name(name_or_obj):
    """
    Returns the 'name' attribute of 'name_or_obj' if present; if not,
    returns 'name_or_obj'.
    """
    if isinstance(name_or_obj, six.string_types):
        # It's a name
        return name_or_obj
    try:
        return name_or_obj.name
    except AttributeError:
        raise exc.MissingName(name_or_obj)


def params_to_dict(params, dct, local_dict):
    """
    Given a set of optional parameter names, constructs a dictionary with the
    parameter name as the key, and the value for that key in the local_dict as
    the value, for all non-None values.
    """
    for param in params:
        val = local_dict.get(param)
        if val is None:
            continue
        dct[param] = val
    return dct


def dict_to_qs(dct):
    """
    Takes a dictionary and uses it to create a query string.
    """
    itms = ["%s=%s" % (key, val) for key, val in list(dct.items())
            if val is not None]
    return "&".join(itms)


def match_pattern(nm, patterns):
    """
    Compares `nm` with the supplied patterns, and returns True if it matches
    at least one.

    Patterns are standard file-name wildcard strings, as defined in the
    `fnmatch` module. For example, the pattern "*.py" will match the names
    of all Python scripts.
    """
    patterns = coerce_string_to_list(patterns)
    for pat in patterns:
        if fnmatch.fnmatch(nm, pat):
            return True
    return False


def update_exc(exc, msg, before=True, separator="\n"):
    """
    Adds additional text to an exception's error message.

    The new text will be added before the existing text by default; to append
    it after the original text, pass False to the `before` parameter.

    By default the old and new text will be separated by a newline. If you wish
    to use a different separator, pass that as the `separator` parameter.
    """
    emsg = exc.message
    if before:
        parts = (msg, separator, emsg)
    else:
        parts = (emsg, separator, msg)
    new_msg = "%s%s%s" % parts
    new_args = (new_msg, ) + exc.args[1:]
    exc.message = new_msg
    exc.args = new_args
    return exc


def case_insensitive_update(dct1, dct2):
    """
    Given two dicts, updates the first one with the second, but considers keys
    that are identical except for case to be the same.

    No return value; this function modified dct1 similar to the update() method.
    """
    lowkeys = dict([(key.lower(), key) for key in dct1])
    for key, val in dct2.items():
        d1_key = lowkeys.get(key.lower(), key)
        dct1[d1_key] = val


def env(*args, **kwargs):
    """
    Returns the first environment variable set
    if none are non-empty, defaults to "" or keyword arg default
    """
    for arg in args:
        value = os.environ.get(arg, None)
        if value:
            return value
    return kwargs.get("default", "")


def unauthenticated(fnc):
    """
    Adds 'unauthenticated' attribute to decorated function.
    Usage:
        @unauthenticated
        def mymethod(fnc):
            ...
    """
    fnc.unauthenticated = True
    return fnc


def isunauthenticated(fnc):
    """
    Checks to see if the function is marked as not requiring authentication
    with the @unauthenticated decorator. Returns True if decorator is
    set to True, False otherwise.
    """
    return getattr(fnc, "unauthenticated", False)


def safe_issubclass(*args):
    """Like issubclass, but will just return False if not a class."""
    try:
        if issubclass(*args):
            return True
    except TypeError:
        pass
    return False


def import_class(import_str):
    """Returns a class from a string including module and class."""
    mod_str, _sep, class_str = import_str.rpartition(".")
    __import__(mod_str)
    return getattr(sys.modules[mod_str], class_str)


# http://code.activestate.com/recipes/
#   577257-slugify-make-a-string-usable-in-a-url-or-filename/
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    _slugify_strip_re = re.compile(r"[^\w\s-]")
    _slugify_hyphenate_re = re.compile(r"[-\s]+")
    if not isinstance(value, six.text_type):
        value = six.text_type(value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore")
    value = six.text_type(_slugify_strip_re.sub("", value).strip().lower())
    return _slugify_hyphenate_re.sub("-", value)
