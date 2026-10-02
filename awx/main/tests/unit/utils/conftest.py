import logging

import pytest

_VALIDATION_SIGNALS_LOGGER = 'ansible_base.lib.utils.validation_signals'


@pytest.fixture(autouse=True)
def capture_validation_signal_logs_for_bypass_tests(request, caplog):
    """DAB caplog pattern (pytest + xdist); only for bypass observability tests."""
    if request.module.__name__ != 'awx.main.tests.unit.utils.test_validation_bypass_observability':
        return
    caplog.set_level(logging.DEBUG)
    caplog.set_level(logging.WARNING, logger=_VALIDATION_SIGNALS_LOGGER)
