"""
Test utility functions and classes for inventory variable handling.
"""

import pytest

from awx.main.utils.inventory_vars import InventoryVariable
from awx.main.utils.inventory_vars import InventoryGroupVariables


def test_inventory_variable_update_basic():
    """Test basic functionality of an inventory variable."""
    x = InventoryVariable("x")
    assert x.has_no_source
    x.update(1, 101)
    assert str(x) == "1"
    x.update(2, 102)
    assert str(x) == "2"
    x.update(3, 103)
    assert str(x) == "3"
    x.delete(102)
    assert str(x) == "3"
    x.delete(103)
    assert str(x) == "1"
    x.delete(101)
    assert x.value is None
    assert x.has_no_source


@pytest.mark.parametrize(
    "updates",  # (<source_id>, <value>, <expected_value>)
    [
        ((101, 1, 1),),
        ((101, 1, 1), (101, None, None)),
        ((101, 1, 1), (102, 2, 2), (102, None, 1)),
        ((101, 1, 1), (102, 2, 2), (101, None, 2), (102, None, None)),
        (
            (101, 0, 0),
            (101, 1, 1),
            (102, 2, 2),
            (103, 3, 3),
            (102, None, 3),
            (103, None, 1),
            (101, None, None),
        ),
    ],
)
def test_inventory_variable_update(updates: tuple[int, int | None, int | None]):
    """
    Test if the variable value is set correctly on a sequence of updates.

    For this test, the value `None` implies the deletion of the source.
    """
    x = InventoryVariable("x")
    for src_id, value, expected_value in updates:
        if value is None:
            x.delete(src_id)
        else:
            x.update(value, src_id)
        assert x.value == expected_value


def test_inventory_group_variables_update_basic():
    """Test basic functionality of an inventory variables update."""
    vars = InventoryGroupVariables(1)
    vars.update_from_src({"x": 1, "y": 2}, 101)
    assert vars == {"x": 1, "y": 2}


@pytest.mark.parametrize(
    "updates",  # (<source_id>, <vars>: dict, <expected_vars>: dict)
    [
        ((101, {"x": 1, "y": 1}, {"x": 1, "y": 1}),),
        (
            (101, {"x": 1, "y": 1}, {"x": 1, "y": 1}),
            (102, {}, {"x": 1, "y": 1}),
        ),
        (
            (101, {"x": 1, "y": 1}, {"x": 1, "y": 1}),
            (102, {"x": 2}, {"x": 2, "y": 1}),
        ),
        (
            (101, {"x": 1, "y": 1}, {"x": 1, "y": 1}),
            (102, {"x": 2, "y": 2}, {"x": 2, "y": 2}),
        ),
        (
            (101, {"x": 1, "y": 1}, {"x": 1, "y": 1}),
            (102, {"x": 2, "z": 2}, {"x": 2, "y": 1, "z": 2}),
        ),
        (
            (101, {"x": 1, "y": 1}, {"x": 1, "y": 1}),
            (102, {"x": 2, "z": 2}, {"x": 2, "y": 1, "z": 2}),
            (102, {}, {"x": 1, "y": 1}),
        ),
        (
            (101, {"x": 1, "y": 1}, {"x": 1, "y": 1}),
            (102, {"x": 2, "z": 2}, {"x": 2, "y": 1, "z": 2}),
            (103, {"x": 3}, {"x": 3, "y": 1, "z": 2}),
            (101, {}, {"x": 3, "z": 2}),
        ),
    ],
)
def test_inventory_group_variables_update(updates: tuple[int, int | None, int | None]):
    """
    Test if the group vars are set correctly on various update sequences.
    """
    groupvars = InventoryGroupVariables(2)
    for src_id, vars, expected_vars in updates:
        groupvars.update_from_src(vars, src_id)
        assert groupvars == expected_vars
