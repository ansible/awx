import pytest

from awxkit.utils import filter_by_class
from awxkit.utils.toposort import CircularDependencyError
from awxkit.api.mixins import has_create


class MockHasCreate(has_create.HasCreate):

    connection = None

    def __str__(self):
        return "instance of {0.__class__.__name__} ({1})".format(self, hex(id(self)))

    def __init__(self, *a, **kw):
        self.cleaned = False
        super(MockHasCreate, self).__init__()

    def silent_cleanup(self):
        self.cleaned = True


class A(MockHasCreate):

    def create(self, **kw):
        return self


class B(MockHasCreate):

    optional_dependencies = [A]

    def create(self, a=None, **kw):
        self.create_and_update_dependencies(*filter_by_class((a, A)))
        return self


class C(MockHasCreate):

    dependencies = [A, B]

    def create(self, a=A, b=B, **kw):
        self.create_and_update_dependencies(b, a)
        return self


class D(MockHasCreate):

    dependencies = [A]
    optional_dependencies = [B]

    def create(self, a=A, b=None, **kw):
        self.create_and_update_dependencies(*filter_by_class((a, A), (b, B)))
        return self


class E(MockHasCreate):

    dependencies = [D, C]

    def create(self, c=C, d=D, **kw):
        self.create_and_update_dependencies(d, c)
        return self


class F(MockHasCreate):

    dependencies = [B]
    optional_dependencies = [E]

    def create(self, b=B, e=None, **kw):
        self.create_and_update_dependencies(*filter_by_class((b, B), (e, E)))
        return self


class G(MockHasCreate):

    dependencies = [D]
    optional_dependencies = [F, E]

    def create(self, d=D, f=None, e=None, **kw):
        self.create_and_update_dependencies(*filter_by_class((d, D), (f, F), (e, E)))
        return self


class H(MockHasCreate):

    optional_dependencies = [E, A]

    def create(self,  a=None, e=None, **kw):
        self.create_and_update_dependencies(*filter_by_class((a, A), (e, E)))
        return self


class MultipleWordClassName(MockHasCreate):

    def create(self, **kw):
        return self


class AnotherMultipleWordClassName(MockHasCreate):

    optional_dependencies = [MultipleWordClassName]

    def create(self,  multiple_word_class_name=None, **kw):
        self.create_and_update_dependencies(*filter_by_class((multiple_word_class_name, MultipleWordClassName)))
        return self


def test_dependency_graph_single_page():
    """confirms that `dependency_graph(Base)` will return a dependency graph
    consisting of only dependencies and dependencies of dependencies (if any)
    """
    desired = {}
    desired[G] = set([D])
    desired[D] = set([A])
    desired[A] = set()
    assert has_create.dependency_graph(G) == desired


def test_dependency_graph_page_with_optional():
    """confirms that `dependency_graph(Base, OptionalBase)` will return a dependency
    graph consisting of only dependencies and dependencies of dependencies (if any)
    with the exception that the OptionalBase and its dependencies are included as well.
    """
    desired = {}
    desired[G] = set([D])
    desired[E] = set([D, C])
    desired[C] = set([A, B])
    desired[D] = set([A])
    desired[B] = set()
    desired[A] = set()
    assert has_create.dependency_graph(G, E) == desired


def test_dependency_graph_page_with_additionals():
    """confirms that `dependency_graph(Base, AdditionalBaseOne, AdditionalBaseTwo)`
    will return a dependency graph consisting of only dependencies and dependencies
    of dependencies (if any) with the exception that the AdditionalBases
    are treated as a dependencies of Base (when they aren't) and their dependencies
    are included as well.
    """
    desired = {}
    desired[E] = set([D, C])
    desired[D] = set([A])
    desired[C] = set([A, B])
    desired[F] = set([B])
    desired[G] = set([D])
    desired[A] = set()
    desired[B] = set()
    assert has_create.dependency_graph(E, F, G) == desired


def test_optional_dependency_graph_single_page():
    """confirms that has_create._optional_dependency_graph(Base) returns a complete dependency tree
    including all optional_dependencies
    """
    desired = {}
    desired[H] = set([E, A])
    desired[E] = set([D, C])
    desired[D] = set([A, B])
    desired[C] = set([A, B])
    desired[B] = set([A])
    desired[A] = set()
    assert has_create.optional_dependency_graph(H) == desired


def test_optional_dependency_graph_with_additional():
    """confirms that has_create._optional_dependency_graph(Base) returns a complete dependency tree
    including all optional_dependencies with the AdditionalBases treated as a dependencies
    of Base (when they aren't) and their dependencies and optional_dependencies included as well.
    """
    desired = {}
    desired[F] = set([B, E])
    desired[H] = set([E, A])
    desired[E] = set([D, C])
    desired[D] = set([A, B])
    desired[C] = set([A, B])
    desired[B] = set([A])
    desired[A] = set()
    assert has_create.optional_dependency_graph(F, H, A) == desired


def test_creation_order():
    """confirms that `has_create.creation_order()` returns a valid creation order in the desired list of sets format"""
    dependency_graph = dict(eight=set(['seven', 'six']),
                            seven=set(['five']),
                            six=set(),
                            five=set(['two', 'one']),
                            four=set(['one']),
                            three=set(['two']),
                            two=set(['one']),
                            one=set())
    desired = [set(['one', 'six']),
               set(['two', 'four']),
               set(['three', 'five']),
               set(['seven']),
               set(['eight'])]
    assert has_create.creation_order(dependency_graph) == desired


def test_creation_order_with_loop():
    """confirms that `has_create.creation_order()` raises toposort.CircularDependencyError when evaluating
    a cyclic dependency graph
    """
    dependency_graph = dict(eight=set(['seven', 'six']),
                            seven=set(['five']),
                            six=set(),
                            five=set(['two', 'one']),
                            four=set(['one']),
                            three=set(['two']),
                            two=set(['one']),
                            one=set(['eight']))
    with pytest.raises(CircularDependencyError):
        assert has_create.creation_order(dependency_graph)


class One(MockHasCreate):
    pass


class Two(MockHasCreate):
    dependencies = [One]


class Three(MockHasCreate):
    dependencies = [Two, One]


class Four(MockHasCreate):
    optional_dependencies = [Two]


class Five(MockHasCreate):
    dependencies = [Two]
    optional_dependencies = [One]


class IsntAHasCreate(object):
    pass

class Six(MockHasCreate, IsntAHasCreate):
    dependencies = [Two]

class Seven(MockHasCreate):
    dependencies = [IsntAHasCreate]


def test_separate_async_optionals_none_exist():
    """confirms that when creation group classes have no async optional dependencies the order is unchanged"""
    order = has_create.creation_order(has_create.optional_dependency_graph(Three, Two, One))
    assert has_create.separate_async_optionals(order) == order


def test_separate_async_optionals_two_exist():
    """confirms that when two creation group classes have async dependencies
    the class that has shared item as a dependency occurs first in a separate creation group
    """
    order = has_create.creation_order(has_create.optional_dependency_graph(Four, Three, Two))
    assert has_create.separate_async_optionals(order) == [set([One]), set([Two]), set([Three]), set([Four])]


def test_separate_async_optionals_three_exist():
    """confirms that when three creation group classes have async dependencies
    the class that has shared item as a dependency occurs first in a separate creation group
    """
    order = has_create.creation_order(has_create.optional_dependency_graph(Five, Four, Three))
    assert has_create.separate_async_optionals(order) == [set([One]), set([Two]), set([Three]),
                                                          set([Five]), set([Four])]


def test_separate_async_optionals_not_has_create():
    """confirms that when a dependency isn't a HasCreate has_create.separate_aysnc_optionals doesn't
    unnecessarily move it from the initial creation group
    """
    order = has_create.creation_order(has_create.optional_dependency_graph(Seven, Six))
    assert has_create.separate_async_optionals(order) == [set([One, IsntAHasCreate]), set([Two, Seven]), set([Six])]


def test_page_creation_order_single_page():
    """confirms that `has_create.page_creation_order()` returns a valid creation order"""
    desired = [set([A]), set([D]), set([G])]
    assert has_create.page_creation_order(G) == desired


def test_page_creation_order_optionals_provided():
    """confirms that `has_create.page_creation_order()` returns a valid creation order
    when optional_dependencies are included
    """
    desired = [set([A]), set([B]), set([C]), set([D]), set([E]), set([H])]
    assert has_create.page_creation_order(H, A, E) == desired


def test_page_creation_order_additionals_provided():
    """confirms that `has_create.page_creation_order()` returns a valid creation order
    when additional pages are included
    """
    desired = [set([A]), set([B]), set([D]), set([F, H]), set([G])]
    assert has_create.page_creation_order(F, H, G) == desired


def test_all_instantiated_dependencies_single_page():
    f = F().create()
    b = f._dependency_store[B]
    desired = set([b, f])
    assert set(has_create.all_instantiated_dependencies(f, A, B, C, D, E, F, G, H)) == desired


def test_all_instantiated_dependencies_single_page_are_ordered():
    f = F().create()
    b = f._dependency_store[B]
    desired = [b, f]
    assert has_create.all_instantiated_dependencies(f, A, B, C, D, E, F, G, H) == desired


def test_all_instantiated_dependencies_optionals():
    a = A().create()
    b = B().create(a=a)
    c = C().create(a=a, b=b)
    d = D().create(a=a, b=b)
    e = E().create(c=c, d=d)
    h = H().create(a=a, e=e)
    desired = set([a, b, c, d, e, h])
    assert set(has_create.all_instantiated_dependencies(h, A, B, C, D, E, F, G, H)) == desired


def test_all_instantiated_dependencies_optionals_are_ordered():
    a = A().create()
    b = B().create(a=a)
    c = C().create(a=a, b=b)
    d = D().create(a=a, b=b)
    e = E().create(c=c, d=d)
    h = H().create(a=a, e=e)
    desired = [a, b, c, d, e, h]
    assert has_create.all_instantiated_dependencies(h, A, B, C, D, E, F, G, H) == desired


def test_dependency_resolution_complete():
    h = H().create(a=True, e=True)
    a = h._dependency_store[A]
    e = h._dependency_store[E]
    c = e._dependency_store[C]
    d = e._dependency_store[D]
    b = c._dependency_store[B]

    for item in (h, a, e, d, c, b):
        if item._dependency_store:
            assert all(item._dependency_store.values()
                   ), "{0} missing dependency: {0._dependency_store}".format(item)

    assert a == b._dependency_store[A], "Duplicate dependency detected"
    assert a == c._dependency_store[A], "Duplicate dependency detected"
    assert a == d._dependency_store[A], "Duplicate dependency detected"
    assert b == c._dependency_store[B], "Duplicate dependency detected"
    assert b == d._dependency_store[B], "Duplicate dependency detected"


def test_ds_mapping():
    h = H().create(a=True, e=True)
    a = h._dependency_store[A]
    e = h._dependency_store[E]
    c = e._dependency_store[C]
    d = e._dependency_store[D]
    b = c._dependency_store[B]

    assert a == h.ds.a
    assert e == h.ds.e
    assert c == e.ds.c
    assert d == e.ds.d
    assert b == c.ds.b


def test_ds_multiple_word_class_and_attribute_name():
    amwcn = AnotherMultipleWordClassName().create(multiple_word_class_name=True)
    mwcn = amwcn._dependency_store[MultipleWordClassName]
    assert amwcn.ds.multiple_word_class_name == mwcn


def test_ds_missing_dependency():
    a = A().create()

    with pytest.raises(AttributeError):
        a.ds.b


def test_teardown_calls_silent_cleanup():
    g = G().create(f=True, e=True)
    f = g._dependency_store[F]
    e = g._dependency_store[E]
    b = f._dependency_store[B]
    d = e._dependency_store[D]
    c = e._dependency_store[C]
    a = c._dependency_store[A]
    instances = [g, f, e, b, d, c, a]

    for instance in instances:
        assert not instance.cleaned

    g.teardown()
    for instance in instances:
        assert instance.cleaned


def test_teardown_dependency_store_cleared():
    g = G().create(f=True, e=True)
    f = g._dependency_store[F]
    e = g._dependency_store[E]
    b = f._dependency_store[B]
    d = e._dependency_store[D]
    c = e._dependency_store[C]
    a = c._dependency_store[A]

    g.teardown()

    assert not g._dependency_store[F]
    assert not g._dependency_store[E]
    assert not f._dependency_store[B]
    assert not e._dependency_store[D]
    assert not e._dependency_store[C]
    assert not c._dependency_store[A]


def test_idempotent_teardown_dependency_store_cleared():
    g = G().create(f=True, e=True)
    f = g._dependency_store[F]
    e = g._dependency_store[E]
    b = f._dependency_store[B]
    d = e._dependency_store[D]
    c = e._dependency_store[C]
    a = c._dependency_store[A]

    for item in (g, f, e, b, d, c, a):
        item.teardown()
        item.teardown()

    assert not g._dependency_store[F]
    assert not g._dependency_store[E]
    assert not f._dependency_store[B]
    assert not e._dependency_store[D]
    assert not e._dependency_store[C]
    assert not c._dependency_store[A]


def test_teardown_ds_cleared():
    g = G().create(f=True, e=True)
    f = g._dependency_store[F]
    e = g._dependency_store[E]
    b = f._dependency_store[B]
    d = e._dependency_store[D]
    c = e._dependency_store[C]
    a = c._dependency_store[A]

    g.teardown()

    for former_dep in ('f', 'e'):
        with pytest.raises(AttributeError):
            getattr(g.ds, former_dep)

    with pytest.raises(AttributeError):
        getattr(f.ds, 'b')

    for former_dep in ('d', 'c'):
        with pytest.raises(AttributeError):
            getattr(e.ds, former_dep)

    with pytest.raises(AttributeError):
        getattr(c.ds, 'a')


class OneWithArgs(MockHasCreate):

    def create(self, **kw):
        self.kw = kw
        return self


class TwoWithArgs(MockHasCreate):

    dependencies = [OneWithArgs]

    def create(self, one_with_args=OneWithArgs, **kw):
        if not one_with_args and kw.pop('make_one_with_args', False):
            one_with_args = (OneWithArgs, dict(a='a', b='b', c='c'))
        self.create_and_update_dependencies(one_with_args)
        self.kw = kw
        return self


class ThreeWithArgs(MockHasCreate):

    dependencies = [OneWithArgs]
    optional_dependencies = [TwoWithArgs]

    def create(self, one_with_args=OneWithArgs, two_with_args=None, **kw):
        self.create_and_update_dependencies(*filter_by_class((one_with_args, OneWithArgs),
                                                             (two_with_args, TwoWithArgs)))
        self.kw = kw
        return self

class FourWithArgs(MockHasCreate):

    dependencies = [TwoWithArgs, ThreeWithArgs]

    def create(self, two_with_args=TwoWithArgs, three_with_args=ThreeWithArgs, **kw):
        self.create_and_update_dependencies(*filter_by_class((two_with_args, TwoWithArgs),
                                                             (three_with_args, ThreeWithArgs)))
        self.kw = kw
        return self


def test_single_kwargs_class_in_create_and_update_dependencies():
    two_wa = TwoWithArgs().create(one_with_args=False, make_one_with_args=True, two_with_args_kw_arg=123)
    assert isinstance(two_wa.ds.one_with_args, OneWithArgs)
    assert two_wa.ds.one_with_args.kw == dict(a='a', b='b', c='c')
    assert two_wa.kw == dict(two_with_args_kw_arg=123)


def test_no_tuple_for_class_arg_causes_shared_dependencies_staggered():
    three_wo = ThreeWithArgs().create(two_with_args=True)
    assert isinstance(three_wo.ds.one_with_args, OneWithArgs)
    assert isinstance(three_wo.ds.two_with_args, TwoWithArgs)
    assert isinstance(three_wo.ds.two_with_args.ds.one_with_args, OneWithArgs)
    assert three_wo.ds.one_with_args == three_wo.ds.two_with_args.ds.one_with_args


def test_no_tuple_for_class_arg_causes_shared_dependencies_nested_staggering():
    four_wo = FourWithArgs().create()
    assert isinstance(four_wo.ds.two_with_args, TwoWithArgs)
    assert isinstance(four_wo.ds.three_with_args, ThreeWithArgs)
    assert isinstance(four_wo.ds.two_with_args.ds.one_with_args, OneWithArgs)
    assert isinstance(four_wo.ds.three_with_args.ds.one_with_args, OneWithArgs)
    assert isinstance(four_wo.ds.three_with_args.ds.two_with_args, TwoWithArgs)
    assert four_wo.ds.two_with_args.ds.one_with_args == four_wo.ds.three_with_args.ds.one_with_args
    assert four_wo.ds.two_with_args == four_wo.ds.three_with_args.ds.two_with_args


def test_tuple_for_class_arg_causes_unshared_dependencies_when_downstream():
    """Confirms that provided arg-tuple for dependency type is applied instead of chained dependency"""
    three_wa = ThreeWithArgs().create(two_with_args=(TwoWithArgs, dict(one_with_args=False,
                                                                       make_one_with_args=True,
                                                                       two_with_args_kw_arg=234)),
                                      three_with_args_kw_arg=345)
    assert isinstance(three_wa.ds.one_with_args, OneWithArgs)
    assert isinstance(three_wa.ds.two_with_args, TwoWithArgs)
    assert isinstance(three_wa.ds.two_with_args.ds.one_with_args, OneWithArgs)
    assert three_wa.ds.one_with_args != three_wa.ds.two_with_args.ds.one_with_args
    assert three_wa.ds.one_with_args.kw == dict()
    assert three_wa.ds.two_with_args.kw == dict(two_with_args_kw_arg=234)
    assert three_wa.ds.two_with_args.ds.one_with_args.kw == dict(a='a', b='b', c='c')
    assert three_wa.kw == dict(three_with_args_kw_arg=345)


def test_tuples_for_class_arg_cause_unshared_dependencies_when_downstream():
    """Confirms that provided arg-tuple for dependency type is applied instead of chained dependency"""
    four_wa = FourWithArgs().create(two_with_args=(TwoWithArgs, dict(one_with_args=False,
                                                                     make_one_with_args=True,
                                                                     two_with_args_kw_arg=456)),
                                    # No shared dependencies with four_wa.ds.two_with_args
                                    three_with_args=(ThreeWithArgs, dict(one_with_args=(OneWithArgs, {}),
                                                                         two_with_args=False)),
                                    four_with_args_kw=567)
    assert isinstance(four_wa.ds.two_with_args, TwoWithArgs)
    assert isinstance(four_wa.ds.three_with_args, ThreeWithArgs)
    assert isinstance(four_wa.ds.two_with_args.ds.one_with_args, OneWithArgs)
    assert isinstance(four_wa.ds.three_with_args.ds.one_with_args, OneWithArgs)
    assert four_wa.ds.three_with_args.ds.one_with_args != four_wa.ds.two_with_args.ds.one_with_args
    with pytest.raises(AttributeError):
        four_wa.ds.three_with_args.ds.two_with_args
    assert four_wa.kw == dict(four_with_args_kw=567)


class NotHasCreate(object):

    pass


class MixinUserA(MockHasCreate, NotHasCreate):

    def create(self, **kw):
        return self


class MixinUserB(MockHasCreate, NotHasCreate):

    def create(self, **kw):
        return self


class MixinUserC(MixinUserB):

    def create(self, **kw):
        return self


class MixinUserD(MixinUserC):

    def create(self, **kw):
        return self


class NotHasCreateDependencyHolder(MockHasCreate):

    dependencies = [NotHasCreate]

    def create(self, not_has_create=MixinUserA):
        self.create_and_update_dependencies(not_has_create)
        return self


def test_not_has_create_default_dependency():
    """Confirms that HasCreates that claim non-HasCreates as dependencies claim them by correct kwarg
    class name in _dependency_store
    """
    dep_holder = NotHasCreateDependencyHolder().create()
    assert isinstance(dep_holder.ds.not_has_create, MixinUserA)


def test_not_has_create_passed_dependency():
    """Confirms that passed non-HasCreate subclasses are sourced as dependency"""
    dep = MixinUserB().create()
    assert isinstance(dep, MixinUserB)
    dep_holder = NotHasCreateDependencyHolder().create(not_has_create=dep)
    assert dep_holder.ds.not_has_create == dep


class HasCreateParentDependencyHolder(MockHasCreate):

    dependencies = [MixinUserB]

    def create(self, mixin_user_b=MixinUserC):
        self.create_and_update_dependencies(mixin_user_b)
        return self


def test_has_create_stored_as_parent_dependency():
    """Confirms that HasCreate subclasses are sourced as their parent"""
    dep = MixinUserC().create()
    assert isinstance(dep, MixinUserC)
    assert isinstance(dep, MixinUserB)
    dep_holder = HasCreateParentDependencyHolder().create(mixin_user_b=dep)
    assert dep_holder.ds.mixin_user_b == dep


class DynamicallyDeclaresNotHasCreateDependency(MockHasCreate):

    dependencies = [NotHasCreate]

    def create(self, not_has_create=MixinUserA):
        dynamic_dependency = dict(mixinusera=MixinUserA,
                                  mixinuserb=MixinUserB,
                                  mixinuserc=MixinUserC)
        self.create_and_update_dependencies(dynamic_dependency[not_has_create])
        return self


@pytest.mark.parametrize('dependency,dependency_class',
                         [('mixinusera', MixinUserA),
                          ('mixinuserb', MixinUserB),
                          ('mixinuserc', MixinUserC)])
def test_subclass_or_parent_dynamic_not_has_create_dependency_declaration(dependency, dependency_class):
    """Confirms that dependencies that dynamically declare dependencies subclassed from not HasCreate
    are properly linked
    """
    dep_holder = DynamicallyDeclaresNotHasCreateDependency().create(dependency)
    assert dep_holder.ds.not_has_create.__class__ == dependency_class


class DynamicallyDeclaresHasCreateDependency(MockHasCreate):

    dependencies = [MixinUserB]

    def create(self, mixin_user_b=MixinUserB):
        dynamic_dependency = dict(mixinuserb=MixinUserB,
                                  mixinuserc=MixinUserC,
                                  mixinuserd=MixinUserD)
        self.create_and_update_dependencies(dynamic_dependency[mixin_user_b])
        return self


@pytest.mark.parametrize('dependency,dependency_class',
                         [('mixinuserb', MixinUserB),
                          ('mixinuserc', MixinUserC),
                          ('mixinuserd', MixinUserD)])
def test_subclass_or_parent_dynamic_has_create_dependency_declaration(dependency, dependency_class):
    """Confirms that dependencies that dynamically declare dependencies subclassed from not HasCreate
    are properly linked
    """
    dep_holder = DynamicallyDeclaresHasCreateDependency().create(dependency)
    assert dep_holder.ds.mixin_user_b.__class__ == dependency_class
