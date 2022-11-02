import shutil
import os
from uuid import uuid4

import pytest

from awx.main.utils.execution_environments import to_container_path


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
    assert to_container_path(host_path, private_data_dir) == container_path


def test_symlink_isolation_dir(request):
    rand_str = str(uuid4())[:8]
    dst_path = f'/tmp/ee_{rand_str}_symlink_dst'
    src_path = f'/tmp/ee_{rand_str}_symlink_src'

    def remove_folders():
        os.unlink(dst_path)
        shutil.rmtree(src_path)

    request.addfinalizer(remove_folders)
    os.mkdir(src_path)
    os.symlink(src_path, dst_path)

    pdd = f'{dst_path}/awx_xxx'

    assert to_container_path(f'{pdd}/env/tmp1234', pdd) == '/runner/env/tmp1234'


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
