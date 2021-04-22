import pytest

from awx.main.utils.execution_environments import to_container_path, to_host_path


private_data_dir = '/tmp/pdd_iso/awx_xxx'


@pytest.mark.parametrize(
    'container_path,host_path',
    [
        ('/runner', private_data_dir),
        ('/runner/foo', '{0}/foo'.format(private_data_dir)),
        ('/runner/foo/bar', '{0}/foo/bar'.format(private_data_dir)),
        ('/runner{0}'.format(private_data_dir), '{0}{0}'.format(private_data_dir)),
    ],
)
def test_switch_paths(container_path, host_path):
    assert to_container_path(host_path, private_data_dir) == container_path
    assert to_host_path(container_path, private_data_dir) == host_path


@pytest.mark.parametrize(
    'container_path',
    [
        ('/foobar'),
        ('/runner/..'),
    ],
)
def test_invalid_container_path(container_path):
    with pytest.raises(RuntimeError):
        to_host_path(container_path, private_data_dir)


@pytest.mark.parametrize(
    'host_path',
    [
        ('/foobar'),
        ('/tmp/pdd_iso'),
        ('/tmp/pdd_iso/awx_xxx/..'),
    ],
)
def test_invalid_host_path(host_path):
    with pytest.raises(RuntimeError):
        to_container_path(host_path, private_data_dir)
