import pytest

def test_ANSILE_VERSION(mocker):
    from django.conf import settings
    assert hasattr(settings, 'ANSIBLE_VERSION')

