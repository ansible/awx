"""Helper functions and types to aid with Python 2.5 - 3 support."""

import sys

PY3 = sys.version_info[0] == 3

if PY3:
    import codecs
    from io import BytesIO as StringIO
    # return s converted to binary.  b('test') should be equivalent to b'test'
    def b(s):
        return codecs.latin_1_encode(s)[0]

    bin_type = bytes
    txt_type   = str
else:
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

    # Conversion to binary only necessary in Python 3
    def b(s):
        return s

    bin_type = str
    txt_type = unicode

str_types = (bin_type, txt_type)
