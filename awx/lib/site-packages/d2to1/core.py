import os
import sys
import warnings

from distutils.core import Distribution as _Distribution
from distutils.errors import DistutilsFileError, DistutilsSetupError
from setuptools.dist import _get_unpatched

from .extern import six
from .util import DefaultGetDict, IgnoreDict, cfg_to_args


_Distribution = _get_unpatched(_Distribution)


def d2to1(dist, attr, value):
    """Implements the actual d2to1 setup() keyword.  When used, this should be
    the only keyword in your setup() aside from `setup_requires`.

    If given as a string, the value of d2to1 is assumed to be the relative path
    to the setup.cfg file to use.  Otherwise, if it evaluates to true, it
    simply assumes that d2to1 should be used, and the default 'setup.cfg' is
    used.

    This works by reading the setup.cfg file, parsing out the supported
    metadata and command options, and using them to rebuild the
    `DistributionMetadata` object and set the newly added command options.

    The reason for doing things this way is that a custom `Distribution` class
    will not play nicely with setup_requires; however, this implementation may
    not work well with distributions that do use a `Distribution` subclass.
    """

    if not value:
        return
    if isinstance(value, six.string_types):
        path = os.path.abspath(value)
    else:
        path = os.path.abspath('setup.cfg')
    if not os.path.exists(path):
        raise DistutilsFileError(
            'The setup.cfg file %s does not exist.' % path)

    # Converts the setup.cfg file to setup() arguments
    try:
        attrs = cfg_to_args(path)
    except:
        e = sys.exc_info()[1]
        raise DistutilsSetupError(
            'Error parsing %s: %s: %s' % (path, e.__class__.__name__,
                                          e.args[0]))

    # Repeat some of the Distribution initialization code with the newly
    # provided attrs
    if attrs:
        # Skips 'options' and 'licence' support which are rarely used; may add
        # back in later if demanded
        for key, val in six.iteritems(attrs):
            if hasattr(dist.metadata, 'set_' + key):
                getattr(dist.metadata, 'set_' + key)(val)
            elif hasattr(dist.metadata, key):
                setattr(dist.metadata, key, val)
            elif hasattr(dist, key):
                setattr(dist, key, val)
            else:
                msg = 'Unknown distribution option: %s' % repr(key)
                warnings.warn(msg)

    # Re-finalize the underlying Distribution
    _Distribution.finalize_options(dist)

    # This bit comes out of distribute/setuptools
    if isinstance(dist.metadata.version, six.integer_types + (float,)):
        # Some people apparently take "version number" too literally :)
        dist.metadata.version = str(dist.metadata.version)

    # This bit of hackery is necessary so that the Distribution will ignore
    # normally unsupport command options (namely pre-hooks and post-hooks).
    # dist.command_options is normally a dict mapping command names to dicts of
    # their options.  Now it will be a defaultdict that returns IgnoreDicts for
    # the each command's options so we can pass through the unsupported options
    ignore = ['pre_hook.*', 'post_hook.*']
    dist.command_options = DefaultGetDict(lambda: IgnoreDict(ignore))
