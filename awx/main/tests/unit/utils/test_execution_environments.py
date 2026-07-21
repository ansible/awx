import os

import pytest

from awx_plugins.interfaces._temporary_private_container_api import get_incontainer_path

private_data_dir = '/tmp/pdd_iso/awx_xxx'


@pytest.mark.parametrize(
    'container_path,host_path',
    [
        ('/runner', private_data_dir),
        ('/runner/foo', f'{private_data_dir}/foo'),
        ('/runner', f'{private_data_dir}/foobar/..'),  # private_data_dir path needs to be resolved
        ('/runner/bar', f'{private_data_dir}/bar/foo/..'),
        ('/runner/foo/bar', f'{private_data_dir}/foo/bar'),
        (f'/runner{private_data_dir}', f'{private_data_dir}{private_data_dir}'),
    ],
)
def test_switch_paths(container_path, host_path):
    assert get_incontainer_path(host_path, private_data_dir) == container_path


def test_symlink_isolation_dir(tmp_path):
    src_path = tmp_path / 'symlink_src'
    dst_path = tmp_path / 'symlink_dst'

    src_path.mkdir()
    os.symlink(src_path, dst_path)

    pdd = f'{dst_path}/awx_xxx'

    assert get_incontainer_path(f'{pdd}/env/tmp1234', pdd) == '/runner/env/tmp1234'


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
        get_incontainer_path(host_path, private_data_dir)
