"""TestExtensionManager

Extension manager used only for testing.
"""

import logging
import warnings

from stevedore import extension


LOG = logging.getLogger(__name__)


class TestExtensionManager(extension.ExtensionManager):
    """ExtensionManager that is explicitly initialized for tests.

    .. deprecated:: 0.13

       Use the :func:`make_test_instance` class method of the class
       being replaced by the test instance instead of using this class
       directly.

    :param extensions: Pre-configured Extension instances to use
                       instead of loading them from entry points.
    :type extensions: list of :class:`~stevedore.extension.Extension`
    :param namespace: The namespace for the entry points.
    :type namespace: str
    :param invoke_on_load: Boolean controlling whether to invoke the
        object returned by the entry point after the driver is loaded.
    :type invoke_on_load: bool
    :param invoke_args: Positional arguments to pass when invoking
        the object returned by the entry point. Only used if invoke_on_load
        is True.
    :type invoke_args: tuple
    :param invoke_kwds: Named arguments to pass when invoking
        the object returned by the entry point. Only used if invoke_on_load
        is True.
    :type invoke_kwds: dict

    """

    def __init__(self, extensions,
                 namespace='test',
                 invoke_on_load=False,
                 invoke_args=(),
                 invoke_kwds={}):
        super(TestExtensionManager, self).__init__(namespace,
                                                   invoke_on_load,
                                                   invoke_args,
                                                   invoke_kwds,
                                                   )
        self.extensions = extensions
        warnings.warn(
            'TestExtesionManager has been replaced by make_test_instance()',
            DeprecationWarning)

    def _load_plugins(self, *args, **kwds):
        return []
