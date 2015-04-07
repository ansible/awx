from .named import NamedExtensionManager


class HookManager(NamedExtensionManager):
    """Coordinate execution of multiple extensions using a common name.

    :param namespace: The namespace for the entry points.
    :type namespace: str
    :param name: The name of the hooks to load.
    :type name: str
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
    :param on_load_failure_callback: Callback function that will be called when
        a entrypoint can not be loaded. The arguments that will be provided
        when this is called (when an entrypoint fails to load) are
        (manager, entrypoint, exception)
    :type on_load_failure_callback: function
    :param verify_requirements: Use setuptools to enforce the
        dependencies of the plugin(s) being loaded. Defaults to False.
    :type verify_requirements: bool
    """

    def __init__(self, namespace, name,
                 invoke_on_load=False, invoke_args=(), invoke_kwds={},
                 on_load_failure_callback=None,
                 verify_requirements=False):
        super(HookManager, self).__init__(
            namespace,
            [name],
            invoke_on_load=invoke_on_load,
            invoke_args=invoke_args,
            invoke_kwds=invoke_kwds,
            on_load_failure_callback=on_load_failure_callback,
            verify_requirements=verify_requirements,
        )

    def _init_attributes(self, namespace, names, name_order=False,
                         propagate_map_exceptions=False,
                         on_load_failure_callback=None):
        super(HookManager, self)._init_attributes(
            namespace, names,
            propagate_map_exceptions=propagate_map_exceptions,
            on_load_failure_callback=on_load_failure_callback)
        self._name = names[0]

    def __getitem__(self, name):
        """Return the named extensions.

        Accessing a HookManager as a dictionary (``em['name']``)
        produces a list of the :class:`Extension` instance(s) with the
        specified name, in the order they would be invoked by map().
        """
        if name != self._name:
            raise KeyError(name)
        return self.extensions
