import copy

import pytest

from awx.main.tasks.host_indirect import get_hashable_form


class TestHashableForm:
    @pytest.mark.parametrize(
        'data',
        [
            {'a': 'b'},
            ['a', 'b'],
            ('a', 'b'),
            {'a': {'b': 'c'}},
            {'a': ['b', 'c']},
            {'a': ('b', 'c')},
            ['a', ['b', 'c']],
            ['a', ('b', 'c')],
            ['a', {'b': 'c'}],
        ],
    )
    def test_compare_equal_data(self, data):
        other_data = copy.deepcopy(data)
        # A tuple of scalars may be cached so ids could legitimately be the same
        if data != ('a', 'b'):
            assert id(data) != id(other_data)  # sanity
            assert id(get_hashable_form(data)) != id(get_hashable_form(data))

        assert get_hashable_form(data) == get_hashable_form(data)
        assert hash(get_hashable_form(data)) == hash(get_hashable_form(data))

        assert get_hashable_form(data) in {get_hashable_form(data): 1}  # test lookup hit

    @pytest.mark.parametrize(
        'data, other_data',
        [
            [{'a': 'b'}, {'a': 'c'}],
            [{'a': 'b'}, {'a': 'b', 'c': 'd'}],
            [['a', 'b'], ['a', 'c']],
            [('a', 'b'), ('a', 'c')],
            [{'a': {'b': 'c'}}, {'a': {'b': 'd'}}],
            [{'a': ['b', 'c']}, {'a': ['b', 'd']}],
            [{'a': ('b', 'c')}, {'a': ('b', 'd')}],
            [['a', ['b', 'c']], ['a', ['b', 'd']]],
            [['a', ('b', 'c')], ['a', ('b', 'd')]],
            [['a', {'b': 'c'}], ['a', {'b': 'd'}]],
        ],
    )
    def test_compare_different_data(self, data, other_data):
        assert data != other_data  # sanity, otherwise why test this?
        assert get_hashable_form(data) != get_hashable_form(other_data)
        assert hash(get_hashable_form(data)) != hash(get_hashable_form(other_data))

        assert get_hashable_form(other_data) not in {get_hashable_form(data): 1}  # test lookup miss
        assert get_hashable_form(data) not in {get_hashable_form(other_data): 1}
