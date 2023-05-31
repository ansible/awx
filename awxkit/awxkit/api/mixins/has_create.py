from collections import defaultdict
import inspect

from awxkit.utils import get_class_if_instance, class_name_to_kw_arg, is_proper_subclass, super_dir_set
from awxkit.utils.toposort import toposort


# HasCreate dependency resolution and creation utilities
def dependency_graph(page, *provided_dependencies):
    """Creates a dependency graph of the form
    {page: set(page.dependencies[0:i]),
     page.dependencies[0]: set(page.dependencies[0][0:j]
     ...
     page.dependencies[i][j][...][n]: set(page.dependencies[i][j][...][n][0:z]),
     ...}
    Any optional provided_dependencies will be included as if they were dependencies,
    without affecting the value of each keyed page.
    """
    graph = {}
    dependencies = set(getattr(page, 'dependencies', []))  # Some HasCreate's can claim generic Base's w/o dependencies
    graph[page] = dependencies
    for dependency in dependencies | set(provided_dependencies):
        graph.update(dependency_graph(dependency))
    return graph


def optional_dependency_graph(page, *provided_dependencies):
    """Creates a dependency graph for a page including all dependencies and optional_dependencies
    Any optional provided_dependencies will be included as if they were dependencies,
    without affecting the value of each keyed page.
    """
    graph = {}
    dependencies = set(getattr(page, 'dependencies', []) + getattr(page, 'optional_dependencies', []))
    graph[page] = dependencies
    for dependency in dependencies | set(provided_dependencies):
        graph.update(optional_dependency_graph(dependency))
    return graph


def creation_order(graph):
    """returns a list of sets of HasCreate subclasses representing the order of page creation that will
    resolve the dependencies of subsequent pages for any non-cyclic dependency_graph
    ex:
    [set(Organization), set(Inventory), set(Group)]

    **The result is based entirely on the passed dependency graph and should be blind
    to node attributes.**
    """
    return list(toposort(graph))


def separate_async_optionals(creation_order):
    """In cases where creation group items share dependencies but as asymetric optionals,
    those that create them as actual dependencies to be later sourced as optionals
    need to be listed first
    """
    actual_order = []
    for group in creation_order:
        if len(group) <= 1:
            actual_order.append(group)
            continue
        by_count = defaultdict(set)
        has_creates = [cand for cand in group if hasattr(cand, 'dependencies')]
        counts = {has_create: 0 for has_create in has_creates}
        for has_create in has_creates:
            for dependency in has_create.dependencies:
                for compared in [cand for cand in has_creates if cand != has_create]:
                    if dependency in compared.optional_dependencies:
                        counts[has_create] += 1
        for has_create in group:
            by_count[counts.get(has_create, 0)].add(has_create)
        for count in sorted(by_count, reverse=True):
            actual_order.append(by_count[count])
    return actual_order


def page_creation_order(page=None, *provided_dependencies):
    """returns a creation_order() where HasCreate subclasses do not share creation group sets with members
    of their optional_dependencies.  All provided_dependencies and their dependencies will also be
    included in the creation
    """
    if not page:
        return []
    # dependency_graphs only care about class type
    provided_dependencies = [x[0] if isinstance(x, tuple) else x for x in provided_dependencies]
    provided_dependencies = [get_class_if_instance(x) for x in provided_dependencies]
    # make a set of all pages we may need to create
    to_create = set(dependency_graph(page, *provided_dependencies))
    # creation order w/ the most accurate dependency graph
    full_graph_order = creation_order(optional_dependency_graph(page, *provided_dependencies))
    order = []
    for group in full_graph_order:
        to_append = group & to_create  # we only care about pages we may need to create
        if to_append:
            order.append(to_append)
    actual_order = separate_async_optionals(order)

    return actual_order


def all_instantiated_dependencies(*potential_parents):
    """returns a list of all instantiated dependencies including parents themselves.
    Will be in page_creation_order
    """
    scope_provided_dependencies = []

    instantiated = set([x for x in potential_parents if not isinstance(x, type) and not isinstance(x, tuple)])

    for potential_parent in [x for x in instantiated if hasattr(x, '_dependency_store')]:
        for dependency in potential_parent._dependency_store.values():
            if dependency and dependency not in scope_provided_dependencies:
                scope_provided_dependencies.extend(all_instantiated_dependencies(dependency))

    scope_provided_dependencies.extend(instantiated)
    scope_provided_dependencies = list(set(scope_provided_dependencies))
    class_to_provided = {}
    for provided in scope_provided_dependencies:
        if provided.__class__ in class_to_provided:
            class_to_provided[provided.__class__].append(provided)
        else:
            class_to_provided[provided.__class__] = [provided]

    all_instantiated = []
    for group in page_creation_order(*scope_provided_dependencies):
        for item in group:
            if item in class_to_provided:
                all_instantiated.extend(class_to_provided[item])
                del class_to_provided[item]
            elif item.__class__ in class_to_provided:
                all_instantiated.extend(class_to_provided[item.__class__])
                del class_to_provided[item.__class__]

    return all_instantiated


class DSAdapter(object):
    """Access HasCreate._dependency_store dependencies by attribute instead of class.

    ex:
    ```
    base_sc = HasCreate().create(inventory=awxkit.api.Inventory)
    base_sc._dependency_store[Inventory] == base.ds.inventory
    ```
    """

    def __init__(self, owner, dependency_store):
        self.owner = owner
        self.dependency_store = dependency_store
        self._lookup = {class_name_to_kw_arg(cls.__name__): cls for cls in dependency_store}

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(list(self._lookup.keys()))

    def __getattr__(self, attr):
        if attr in self._lookup:
            dep = self.dependency_store[self._lookup[attr]]
            if dep:
                return dep
        raise AttributeError('{0.owner} has no dependency "{1}"'.format(self, attr))

    def __getitem__(self, item):
        return getattr(self, item)

    def __iter__(self):
        return iter(self._lookup)

    def __dir__(self):
        attrs = super_dir_set(self.__class__)
        if '_lookup' in self.__dict__ and hasattr(self._lookup, 'keys'):
            attrs.update(self._lookup.keys())
        return sorted(attrs)


# Hijack json.dumps and simplejson.dumps (used by requests)
# to allow HasCreate.create_payload() serialization without impacting payload.ds access
def filter_ds_from_payload(dumps):
    def _filter_ds_from_payload(obj, *a, **kw):
        if hasattr(obj, 'get') and isinstance(obj.get('ds'), DSAdapter):
            filtered = obj.copy()
            del filtered['ds']
        else:
            filtered = obj
        return dumps(filtered, *a, **kw)

    return _filter_ds_from_payload


import json  # noqa

json.dumps = filter_ds_from_payload(json.dumps)

try:
    import simplejson  # noqa

    simplejson.dumps = filter_ds_from_payload(simplejson.dumps)
except ImportError:
    pass


class HasCreate(object):
    # For reference only.  Use self.ds, or self._dependency_store if mutating.
    dependencies = []
    optional_dependencies = []

    # Provides introspection capability in recursive create_and_update_dependencies calls
    _scoped_dependencies_by_frame = dict()

    def __init__(self, *a, **kw):
        dependency_store = kw.get('ds')
        if dependency_store is None:
            deps = self.dependencies + self.optional_dependencies
            self._dependency_store = {base_subclass: None for base_subclass in deps}
            self.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        else:
            self._dependency_store = dependency_store.dependency_store
            self.ds = dependency_store
        super(HasCreate, self).__init__(*a, **kw)

    def _update_dependencies(self, dependency_candidates):
        """updates self._dependency_store to reflect instantiated dependencies, if any."""
        if self._dependency_store:
            potentials = []

            # in case the candidate is an instance of a desired base class
            # (e.g. Project for self._dependency_store = {'UnifiedJobTemplate': None})
            # we try each of its base classes until a match is found
            base_lookup = {}
            for candidate in dependency_candidates:
                for cls_type in inspect.getmro(candidate[0].__class__):
                    if cls_type in self._dependency_store:
                        base_lookup[candidate[0]] = cls_type
                        potentials.append(candidate)
                        break
            second_pass = []
            for candidate, claimed in potentials:
                if claimed:
                    self._dependency_store[base_lookup[candidate]] = candidate
                else:
                    second_pass.append(candidate)
            # Technical Debt: We need to iron out the expected behavior of multiple instances
            # of unclaimed types. Right now the last one in potentials is marked as a dependency.
            second_pass.reverse()  # for the last one in the list to be marked we need to reverse.
            for candidate in second_pass:
                if not self._dependency_store[base_lookup[candidate]]:
                    self._dependency_store[base_lookup[candidate]] = candidate

    def create_and_update_dependencies(self, *provided_and_desired_dependencies):
        """in order creation of dependencies and updating of self._dependency_store
        to include instances, indexed by page class.  If a (HasCreate, dict()) tuple is
        provided as a desired dependency, the dict() will be unpacked as kwargs for the
        `HasCreate.create(**dict())` call.

        ***
        Providing (HasCreate, dict()) tuples for dependency args to this method
        removes the assurance that all shared dependencies types will be the same instance
        and only one instance of each type is created
        (Tech Debt: can create orphans if default dependency isn't claimed).
        The provided args are only in scope of the desired page, override any previously created
        instance of the same class, and replace said instances in the continuing chain.
        ***

        ```
        ex:
        self.dependencies = [awxkit.api.pages.Inventory]
        self.create_and_update_dependencies()
        inventory = self._dependency_store[awxkit.api.pages.Inventory]

        ex:
        self.dependencies = [awxkit.api.pages.Inventory]
        self.create_and_update_dependencies((awxkit.api.pages.Inventory, dict(attr_one=1, attr_two=2)))
        inventory = self._dependency_store[awxkit.api.pages.Inventory]
        # assume kwargs are set as attributes by Inventory.create()
        inventory.attr_one == 1
        > True
        inventory.attr_two == 2
        > True

        ex:
        self.dependencies = []
        self.optional_dependencies = [awxkit.api.pages.Organization]
        self.create_and_update_dependencies(awxkit.api.pages.Organization)
        organization = self._dependency_store[awxkit.api.pages.Organization]

        ex:
        self.dependencies = [awxkit.api.pages.Inventory]
        inventory = v2.inventories.create()
        self.create_and_update_dependencies(inventory)
        inventory == self._dependency_store[awxkit.api.pages.Inventory]
        > True
        ```
        """
        if not any((self.dependencies, self.optional_dependencies)):
            return

        # remove falsy values
        provided_and_desired_dependencies = [x for x in provided_and_desired_dependencies if x]
        # (HasCreate(), True) tells HasCreate._update_dependencies to link
        provided_dependencies = [(x, True) for x in provided_and_desired_dependencies if not isinstance(x, type) and not isinstance(x, tuple)]

        # Since dependencies are often declared at runtime, we need to use some introspection
        # to determine previously created ones for proper dependency store linking.
        # This is done by keeping an updated dependency record by the root caller's frame
        caller_frame = inspect.currentframe()
        self.parent_frame = None
        for frame in inspect.stack()[1:]:
            if frame[3] == 'create_and_update_dependencies':
                self.parent_frame = frame[0]

        if not self.parent_frame:
            # a maintained dict of instantiated resources keyed by lowercase class name to be
            # expanded as keyword args during `create()` calls
            all_instantiated = all_instantiated_dependencies(*[d[0] for d in provided_dependencies])
            scoped_dependencies = {class_name_to_kw_arg(d.__class__.__name__): d for d in all_instantiated}
            self._scoped_dependencies_by_frame[caller_frame] = [self, scoped_dependencies]
        else:
            scoped_dependencies = self._scoped_dependencies_by_frame[self.parent_frame][1]

        desired_dependencies = []
        desired_dependency_classes = []
        for item in provided_and_desired_dependencies:
            if isinstance(item, tuple):
                item_cls = item[0]
            elif inspect.isclass(item):
                item_cls = item
            else:
                item_cls = item.__class__
            if item_cls not in [x[0].__class__ for x in provided_dependencies]:
                desired_dependency_classes.append(item_cls)
                desired_dependencies.append(item)

        if desired_dependencies:
            ordered_desired_dependencies = []
            creation_order = [item for s in page_creation_order(*desired_dependency_classes) for item in s]
            for item in creation_order:
                for desired in desired_dependency_classes:
                    if desired == item or is_proper_subclass(desired, item):
                        ordered_desired_dependencies.append(desired)
                        desired_dependency_classes.remove(desired)
                        break

            # keep track of (HasCreate, kwarg_dict)
            provided_with_kwargs = dict()
            for page_cls, provided_kwargs in [x for x in desired_dependencies if isinstance(x, tuple)]:
                provided_with_kwargs[page_cls] = provided_kwargs

            for to_create in ordered_desired_dependencies:
                scoped_args = dict(scoped_dependencies)

                if to_create in provided_with_kwargs:
                    scoped_args.pop(to_create, None)  # remove any conflicts in favor of explicit kwargs
                    scoped_args.update(provided_with_kwargs.pop(to_create))

                scoped_args.pop(class_name_to_kw_arg(to_create.__name__), None)

                created = to_create(self.connection).create(**scoped_args)
                provided_dependencies.append((created, True))

                for dependency, _ in provided_dependencies:
                    if dependency not in scoped_dependencies:
                        scoped_dependencies[class_name_to_kw_arg(dependency.__class__.__name__)] = dependency

        self._update_dependencies(provided_dependencies)

        if not self.parent_frame:
            del self._scoped_dependencies_by_frame[caller_frame]

    def teardown(self):
        """Calls `silent_cleanup()` on all dependencies and self in reverse page creation order."""
        to_teardown = all_instantiated_dependencies(self)
        to_teardown_types = set(map(get_class_if_instance, to_teardown))
        order = [
            set([potential for potential in (get_class_if_instance(x) for x in group) if potential in to_teardown_types])
            for group in page_creation_order(self, *to_teardown)
        ]
        order.reverse()
        for teardown_group in order:
            for teardown_class in teardown_group:
                instance = [x for x in to_teardown if isinstance(x, teardown_class)].pop()
                instance.silent_cleanup()

        for item in to_teardown:
            for dep_type, dep in item._dependency_store.items():
                if dep and dep_type in to_teardown_types:
                    item._dependency_store[dep_type] = None  # Note that we don't call del
