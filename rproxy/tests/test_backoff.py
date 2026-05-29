import pytest

from unittest import mock

from rproxy.backoff import exponential_backoff


@pytest.mark.parametrize(
    ('attempt', 'base_delay', 'jitter', 'start_delay', 'expected'),
    (
        pytest.param(1, 2, 0, 0, 2, id='delay_1'),
        pytest.param(3, 2, 0, 0, 8, id='delay_2'),
        pytest.param(2, 2, 0, 1, 5, id='start_delay_1'),
        pytest.param(2, 2, 0.5, 0, (2, 6), id='jitter_range_1'),
        pytest.param(2, 2, 0, 1, 5, id='start_delay_2'),
        pytest.param(1, 2, 2, -10, (0, None), id='start_delay_negative'),
        pytest.param(
            3,
            2,
            0.5,
            1,
            (
                5,
                12,
            ),
            id='jitter_range_2',
        ),
    ),
)
def test_exponential_backoff(attempt, base_delay, jitter, start_delay, expected):
    """Unit tests for exponential_backoff."""

    mock_sleep = mock.Mock()

    # Test 1: Base delay only
    exponential_backoff(attempt, base_delay=base_delay, jitter=jitter, start_delay=start_delay, sleep_fn=mock_sleep)
    first_call = mock_sleep.mock_calls[0]
    _, args, _ = first_call
    sleep_time = args[0]
    if isinstance(expected, (int, float)):
        assert sleep_time == expected
    elif isinstance(expected, tuple):
        lower_bound, upper_bound = expected
        if lower_bound is not None:
            assert lower_bound <= sleep_time
        if upper_bound is not None:
            assert sleep_time <= upper_bound

    return
