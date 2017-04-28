import pytest

from awx.api.parsers import _remove_trailing_commas


@pytest.mark.parametrize('input_, output', [
    ('{"foo": "bar"}', '{"foo": "bar"}'),
    ('{"foo": "bar",\n\t\r }', '{"foo": "bar"}'),
    ('{"foo": ["alice", "bob"]}', '{"foo": ["alice","bob"]}'),
    ('{"foo": ["alice", "bob",\n\t\r ]}', '{"foo": ["alice","bob"]}'),
    ('{"foo": "\\"bar,\n\t\r }"}', '{"foo": "\\"bar,\n\t\r }"}'),
    ('{"foo": ["\\"alice,\n\t\r ]", "bob"]}', '{"foo": ["\\"alice,\n\t\r ]","bob"]}'),
])
def test_remove_trailing_commas(input_, output):
    assert _remove_trailing_commas(input_) == output
