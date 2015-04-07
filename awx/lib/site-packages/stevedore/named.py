from .extension import ExtensionManager


class NamedExtensionManager(ExtensionManager):
    """Loads only the named extensions.

    This is useful for explicitly enabling extensions in a
    configuration file, for example.

    :param namespace: The namespace for the entry points.
    :type namespace: str
    :param names: The names of the extensions to load.
    :type names: list(str)
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
    :param name_order: If true, sort the loaded extensions to match the
        order used in ``names``.
    :type name_order: bool
    :param propagate_map_exceptions: Boolean controlling whether exceptions
        are propagated up through the map call or whether they are logged and
        then ignored
    :type propagate_map_exceptions: bool
    :param on_load_failure_callback: Callback function that will be called when
        a entrypoint can not be loaded. The arguments that will be provided
        when this is called (when an entrypoint fails to load) are
        (manager, entrypoint, exception)
    :type on_load_failure_callback: function
    :param verify_requirements: Use setuptools to enforce the
        dependencies of the plugin(s) being loaded. Defaults to False.
    :type verify_requirements: bool

    """

    def __init__(self, namespace, names,
                 invoke_on_load=False, invoke_args=(), invoke_kwds={},
                 name_order=False, propagate_map_exceptions=False,
                 on_load_failure_callback=None,
                 verify_requirements=False):
        self._init_attributes(
            namespace, names, name_order=name_order,
            propagate_map_exceptions=propagate_map_exceptions,
            on_load_failure_callback=on_load_failure_callback)
        extensions = self._load_plugins(invoke_on_load,
                                        invoke_args,
                                        invoke_kwds,
                                        verify_requirements)
        self._init_plugins(extensions)

    @classmethod
    def make_test_instance(cls, extensions, namespace='TESTING',
                           propagate_map_exceptions=False,
                           on_load_failure_callback=None,
                           verify_requirements=False):
        """Construct a test NamedExtensionManager

        Test instances are passed a list of extensions to use rather than
        loading them from entry points.

        :param extensions: Pre-configured Extension instances
        :type extensions: list of :class:`~stevedore.extension.Extension`
        :param namespace: The namespace for the manager; used only for
            identification since the extensions are passed in.
        :type namespace: str
        :param propagate_map_exceptions: Boolean controlling whether exceptions
            are propagated up through the map call or whether they are logged
            and then ignored
        :type propagate_map_exceptions: bool
        :param on_load_failure_callback: Callback function that will
            be called when a entrypoint can not be loaded. The
            arguments that will be provided when this is called (when
            an entrypoint fails to load) are (manager, entrypoint,
            exception)
        :type on_load_failure_callback: function
        :param verify_requirements: Use setuptools to enforce the
            dependencies of the plugin(s) being loaded. Defaults to False.
        :type verify_requirements: bool
        :return: The manager instance, initialized for testing

        """

        o = cls.__new__(cls)
        names = [e.name for e in extensions]
        o._init_attributes(namespace, names,
                           propagate_map_exceptions=propagate_map_exceptions,
                           on_load_failure_callback=on_load_failure_callback)
        o._init_plugins(extensions)
        return o

    def _init_attributes(self, namespace, names, name_order=False,
                         propagate_map_exceptions=False,
                         on_load_failure_callback=None):
        super(NamedExtensionManager, self)._init_attributes(
            namespace, propagate_map_exceptions=propagate_map_exceptions,
            on_load_failure_callback=on_load_failure_callback)

        self._names = names
        self._name_order = name_order

    def _init_plugins(self, extensions):
        super(NamedExtensionManager, self)._init_plugins(extensions)

        if self._name_order:
            self.extensions = [self[n] for n in self._names]

    def _load_one_plugin(self, ep, invoke_on_load, invoke_args, invoke_kwds,
                         verify_requirements):
        # Check the name before going any further to prevent
        # undesirable code from being loaded at all if we are not
        # going to use it.
        if ep.name not in self._names:
            return None
        return super(NamedExtensionManager, self)._load_one_plugin(
            ep, invoke_on_load, invoke_args, invoke_kwds,
            verify_requirements,
        )
