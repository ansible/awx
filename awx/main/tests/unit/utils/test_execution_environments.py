import os
from unittest import mock

import pytest

from awx_plugins.interfaces._temporary_private_container_api import get_incontainer_path
from awx.main.utils.execution_environments import sanitize_pod_spec

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


class TestSanitizePodSpec:
    """Tests for the sanitize_pod_spec security function."""

    def test_forces_automount_false(self):
        """sanitize_pod_spec must force automountServiceAccountToken to False."""
        pod_spec = {
            'spec': {
                'automountServiceAccountToken': True,
                'containers': [{'name': 'worker'}],
            }
        }
        result = sanitize_pod_spec(pod_spec)
        assert result['spec']['automountServiceAccountToken'] is False

    def test_removes_secret_volume_and_mounts(self):
        """Secret volumes and their corresponding mounts must be stripped."""
        pod_spec = {
            'spec': {
                'volumes': [
                    {'name': 'steal', 'secret': {'secretName': 'pg-creds'}},
                    {'name': 'safe', 'emptyDir': {}},
                ],
                'containers': [
                    {
                        'name': 'worker',
                        'volumeMounts': [
                            {'name': 'steal', 'mountPath': '/stolen'},
                            {'name': 'safe', 'mountPath': '/cache'},
                        ],
                    }
                ],
            }
        }
        result = sanitize_pod_spec(pod_spec)
        vol_names = [v['name'] for v in result['spec']['volumes']]
        assert 'steal' not in vol_names
        assert 'safe' in vol_names
        mount_names = [m['name'] for m in result['spec']['containers'][0]['volumeMounts']]
        assert 'steal' not in mount_names
        assert 'safe' in mount_names

    def test_removes_projected_sa_token_and_mounts(self):
        """Projected volumes with serviceAccountToken must be stripped."""
        pod_spec = {
            'spec': {
                'volumes': [
                    {
                        'name': 'sat',
                        'projected': {
                            'sources': [
                                {'serviceAccountToken': {'path': 'token'}},
                            ],
                        },
                    },
                    {'name': 'cfg', 'configMap': {'name': 'app'}},
                ],
                'containers': [
                    {
                        'name': 'worker',
                        'volumeMounts': [
                            {'name': 'sat', 'mountPath': '/sat'},
                            {'name': 'cfg', 'mountPath': '/cfg'},
                        ],
                    }
                ],
            }
        }
        result = sanitize_pod_spec(pod_spec)
        vol_names = [v['name'] for v in result['spec']['volumes']]
        assert 'sat' not in vol_names
        assert 'cfg' in vol_names
        mount_names = [m['name'] for m in result['spec']['containers'][0]['volumeMounts']]
        assert 'sat' not in mount_names
        assert 'cfg' in mount_names

    def test_preserves_safe_projected_volume(self):
        """Projected volumes without serviceAccountToken must be preserved."""
        pod_spec = {
            'spec': {
                'volumes': [
                    {
                        'name': 'safe-proj',
                        'projected': {
                            'sources': [
                                {'configMap': {'name': 'app-cfg'}},
                            ],
                        },
                    }
                ],
                'containers': [{'name': 'worker'}],
            }
        }
        result = sanitize_pod_spec(pod_spec)
        assert len(result['spec']['volumes']) == 1
        assert result['spec']['volumes'][0]['name'] == 'safe-proj'

    def test_strips_mounts_from_all_container_types(self):
        """Volume mounts for removed volumes must be stripped from
        containers, initContainers, and ephemeralContainers."""
        pod_spec = {
            'spec': {
                'volumes': [
                    {'name': 'steal', 'secret': {'secretName': 'x'}},
                ],
                'containers': [
                    {
                        'name': 'w',
                        'volumeMounts': [
                            {'name': 'steal', 'mountPath': '/a'},
                        ],
                    }
                ],
                'initContainers': [
                    {
                        'name': 'init',
                        'volumeMounts': [
                            {'name': 'steal', 'mountPath': '/b'},
                        ],
                    }
                ],
                'ephemeralContainers': [
                    {
                        'name': 'debug',
                        'volumeMounts': [
                            {'name': 'steal', 'mountPath': '/c'},
                        ],
                    }
                ],
            }
        }
        result = sanitize_pod_spec(pod_spec)
        for key in ('containers', 'initContainers', 'ephemeralContainers'):
            for c in result['spec'][key]:
                mount_names = [m['name'] for m in c.get('volumeMounts', [])]
                assert 'steal' not in mount_names

    def test_no_volumes_passes_through(self):
        """A spec with no volumes passes through with automount set."""
        pod_spec = {'spec': {'containers': [{'name': 'worker'}]}}
        result = sanitize_pod_spec(pod_spec)
        assert result['spec']['automountServiceAccountToken'] is False
        assert result['spec']['containers'][0]['name'] == 'worker'

    def test_full_malicious_spec_sanitized(self):
        """The exact malicious payload from the exploit is fully sanitized."""
        pod_spec = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {'namespace': 'ansible-automation-platform'},
            'spec': {
                'serviceAccountName': 'automation-controller',
                'automountServiceAccountToken': False,
                'volumes': [
                    {
                        'name': 'sat',
                        'projected': {
                            'sources': [
                                {
                                    'serviceAccountToken': {
                                        'path': 'token',
                                        'expirationSeconds': 31536000,
                                    }
                                },
                            ],
                        },
                    },
                    {
                        'name': 'steal',
                        'secret': {
                            'secretName': 'automation-controller-postgres-configuration',
                        },
                    },
                ],
                'containers': [
                    {
                        'name': 'worker',
                        'volumeMounts': [
                            {
                                'name': 'sat',
                                'mountPath': '/var/run/secrets/sat',
                            },
                            {
                                'name': 'steal',
                                'mountPath': '/tmp/stolen',
                            },
                        ],
                    },
                ],
            },
        }
        result = sanitize_pod_spec(pod_spec)
        assert result['spec']['automountServiceAccountToken'] is False
        assert result['spec']['volumes'] == []
        for c in result['spec']['containers']:
            assert c.get('volumeMounts', []) == []

    def test_container_without_volume_mounts_key(self):
        """Containers without a volumeMounts key are left untouched."""
        pod_spec = {
            'spec': {
                'volumes': [
                    {'name': 'steal', 'secret': {'secretName': 'x'}},
                ],
                'containers': [{'name': 'worker'}],
            }
        }
        result = sanitize_pod_spec(pod_spec)
        assert 'volumeMounts' not in result['spec']['containers'][0]
        assert result['spec']['volumes'] == []

    def test_empty_spec(self):
        """A pod spec with an empty spec section is handled gracefully."""
        pod_spec = {'spec': {}}
        result = sanitize_pod_spec(pod_spec)
        assert result['spec']['automountServiceAccountToken'] is False


class TestPodManagerSanitization:
    """Verify PodManager.pod_definition calls sanitize_pod_spec."""

    @mock.patch('awx.main.scheduler.kubernetes.get_default_pod_spec')
    def test_pod_manager_strips_malicious_volumes(self, mock_get_default):
        """PodManager.pod_definition must strip secret volumes via
        sanitize_pod_spec, not just set automountServiceAccountToken."""
        from awx.main.scheduler.kubernetes import PodManager

        mock_get_default.return_value = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {'namespace': 'default'},
            'spec': {
                'automountServiceAccountToken': True,
                'containers': [
                    {'name': 'worker', 'image': 'test:latest'},
                ],
                'volumes': [
                    {
                        'name': 'steal',
                        'secret': {'secretName': 'pg-creds'},
                    },
                ],
            },
        }
        pm = PodManager(task=None)
        pod_def = pm.pod_definition
        assert pod_def['spec']['automountServiceAccountToken'] is False
        vol_names = [v['name'] for v in pod_def['spec'].get('volumes', [])]
        assert 'steal' not in vol_names

    @mock.patch('awx.main.scheduler.kubernetes.get_default_pod_spec')
    def test_pod_manager_allows_safe_spec(self, mock_get_default):
        """PodManager.pod_definition must preserve safe volumes."""
        from awx.main.scheduler.kubernetes import PodManager

        mock_get_default.return_value = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {'namespace': 'default'},
            'spec': {
                'containers': [
                    {'name': 'worker', 'image': 'test:latest'},
                ],
                'volumes': [
                    {'name': 'cfg', 'configMap': {'name': 'app'}},
                ],
            },
        }
        pm = PodManager(task=None)
        pod_def = pm.pod_definition
        assert pod_def['spec']['automountServiceAccountToken'] is False
        vol_names = [v['name'] for v in pod_def['spec'].get('volumes', [])]
        assert 'cfg' in vol_names


class TestReceptorJobSanitization:
    """Verify AWXReceptorJob.pod_definition calls sanitize_pod_spec."""

    @mock.patch('awx.main.tasks.receptor.settings')
    @mock.patch('awx.main.tasks.receptor.get_default_pod_spec')
    def test_receptor_job_strips_malicious_volumes(
        self,
        mock_get_default,
        mock_settings,
    ):
        """AWXReceptorJob.pod_definition must strip secret volumes via
        sanitize_pod_spec."""
        from awx.main.tasks.receptor import AWXReceptorJob

        mock_settings.IS_K8S = True
        mock_settings.AWX_RUNNER_KEEPALIVE_SECONDS = 0
        mock_settings.AWX_MOUNT_ISOLATED_PATHS_ON_K8S = False
        mock_settings.INSTALL_UUID = 'test-uuid'
        mock_get_default.return_value = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {'namespace': 'default'},
            'spec': {
                'automountServiceAccountToken': True,
                'containers': [
                    {'name': 'worker', 'image': 'default:latest'},
                ],
                'volumes': [
                    {
                        'name': 'steal',
                        'secret': {'secretName': 'pg-creds'},
                    },
                ],
            },
        }
        task = mock.MagicMock()
        task.instance.is_container_group_task = True
        task.instance.execution_environment.image = 'test:latest'
        task.instance.execution_environment.pull = ''
        task.instance.execution_environment.credential = None
        task.instance.instance_group.pod_spec_override = ''
        task.instance.instance_group.credential = None
        task.instance.id = 42
        job = AWXReceptorJob(task, runner_params={'settings': {}})
        pod_def = job.pod_definition
        assert pod_def['spec']['automountServiceAccountToken'] is False
        vol_names = [v['name'] for v in pod_def['spec'].get('volumes', [])]
        assert 'steal' not in vol_names
