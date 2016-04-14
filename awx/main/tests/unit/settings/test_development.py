
def test_ANSIBLE_VERSION(mocker):
    from django.conf import settings
    assert hasattr(settings, 'ANSIBLE_VERSION')

