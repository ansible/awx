import pytest
from winrm import Session
xfail = pytest.mark.xfail


@xfail()
def test_run_cmd():
    raise NotImplementedError()