#!/usr/bin/env python
#
# This script is based on https://github.com/django/django/blob/master/django/core/management/commands/compilemessages.py
# It has been modified to run without Django, because the virtual environment
# is not available when `make languages` is invoked.
#

import codecs
import datetime
import locale
import os
import sys
from decimal import Decimal
from subprocess import PIPE, Popen


def is_writable(path):
    # Known side effect: updating file access/modified time to current time if
    # it is writable.
    try:
        with open(path, 'a'):
            os.utime(path, None)
    except (IOError, OSError):
        return False
    return True


def has_bom(fn):
    with open(fn, 'rb') as f:
        sample = f.read(4)
    return sample.startswith((codecs.BOM_UTF8, codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE))


def popen_wrapper(args, os_err_exc_type=Exception, stdout_encoding='utf-8'):
    """
    Friendly wrapper around Popen.
    Returns stdout output, stderr output and OS status code.
    """
    try:
        p = Popen(args, shell=False, stdout=PIPE, stderr=PIPE, close_fds=os.name != 'nt')
    except OSError as e:
        strerror = force_text(e.strerror, DEFAULT_LOCALE_ENCODING, strings_only=True)
        raise Exception(os_err_exc_type, os_err_exc_type('Error executing %s: %s' %
                                                         (args[0], strerror)), sys.exc_info()[2])
    output, errors = p.communicate()
    return (
        force_text(output, stdout_encoding, strings_only=True, errors='strict'),
        force_text(errors, DEFAULT_LOCALE_ENCODING, strings_only=True, errors='replace'),
        p.returncode
    )


def get_system_encoding():
    """
    The encoding of the default system locale but falls back to the given
    fallback encoding if the encoding is unsupported by python or could
    not be determined.  See tickets #10335 and #5846
    """
    try:
        encoding = locale.getdefaultlocale()[1] or 'ascii'
        codecs.lookup(encoding)
    except Exception:
        encoding = 'ascii'
    return encoding


_PROTECTED_TYPES = (
    type(None), int, float, Decimal, datetime.datetime, datetime.date, datetime.time,
)


def is_protected_type(obj):
    """Determine if the object instance is of a protected type.
    Objects of protected types are preserved as-is when passed to
    force_text(strings_only=True).
    """
    return isinstance(obj, _PROTECTED_TYPES)


DEFAULT_LOCALE_ENCODING = get_system_encoding()


def force_text(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_text, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.
    If strings_only is True, don't convert (some) non-string-like objects.
    """
    # Handle the common case first for performance reasons.
    if issubclass(type(s), str):
        return s
    if strings_only and is_protected_type(s):
        return s
    try:
        if not issubclass(type(s), str):
            if isinstance(s, bytes):
                s = str(s, encoding, errors)
            else:
                s = str(s)
        else:
            # Note: We use .decode() here, instead of str(s, encoding,
            # errors), so that if s is a SafeBytes, it ends up being a
            # SafeText at the end.
            s = s.decode(encoding, errors)
    except UnicodeDecodeError as e:
        if not isinstance(s, Exception):
            raise Exception(s, *e.args)
        else:
            # If we get to here, the caller has passed in an Exception
            # subclass populated with non-ASCII bytestring data without a
            # working unicode method. Try to handle this without raising a
            # further exception by individually forcing the exception args
            # to unicode.
            s = ' '.join(force_text(arg, encoding, strings_only, errors)
                         for arg in s)
    return s


if __name__ == "__main__":
    basedirs = [os.path.join('conf', 'locale'), 'locale']

    # Walk entire tree, looking for locale directories
    for dirpath, dirnames, filenames in os.walk('.', topdown=True):
        for dirname in dirnames:
            if dirname == 'locale':
                basedirs.append(os.path.join(dirpath, dirname))

    basedirs = set(map(os.path.abspath, filter(os.path.isdir, basedirs)))

    for basedir in basedirs:
        dirs = [basedir]
        locations = []
        for ldir in dirs:
            for dirpath, dirnames, filenames in os.walk(ldir):
                locations.extend((dirpath, f) for f in filenames if f.endswith('.po'))
        if locations:
            program = 'msgfmt'
            program_options = ['--check-format']
            for i, (dirpath, f) in enumerate(locations):
                print('processing file %s in %s\n' % (f, dirpath))
                po_path = os.path.join(dirpath, f)
                if has_bom(po_path):
                    raise Exception("The %s file has a BOM (Byte Order Mark). "
                                    "Django only supports .po files encoded in "
                                    "UTF-8 and without any BOM." % po_path)
                base_path = os.path.splitext(po_path)[0]
                # Check writability on first location
                if i == 0 and not is_writable((base_path + '.mo')):
                    raise Exception("The po files under %s are in a seemingly not writable location. "
                                    "mo files will not be updated/created." % dirpath)
                args = [program] + program_options + [
                    '-o', (base_path + '.mo'), (base_path + '.po')
                ]
                output, errors, status = popen_wrapper(args)
                if status:
                    if errors:
                        msg = "Execution of %s failed: %s" % (program, errors)
                    else:
                        msg = "Execution of %s failed" % program
                    raise Exception(msg)
