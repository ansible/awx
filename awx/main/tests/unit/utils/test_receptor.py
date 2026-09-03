from awx.main.tasks.receptor import _convert_args_to_cli, compute_execution_timing


def test_file_cleanup_scenario():
    args = _convert_args_to_cli({'exclude_strings': ['awx_423_', 'awx_582_'], 'file_pattern': '/tmp/awx_*_*'})
    assert ' '.join(args) == 'cleanup --exclude-strings "awx_423_" "awx_582_" --file-pattern=/tmp/awx_*_*'


def test_image_cleanup_scenario():
    # See input dict in awx.main.tests.unit.models.test_ha
    args = _convert_args_to_cli(
        {
            'file_pattern': '',
            'process_isolation_executable': 'podman',
            'remove_images': ['quay.invalid/foo/bar:latest', 'quay.invalid/foo/bar:devel'],
            'image_prune': True,
        }
    )
    assert (
        ' '.join(args)
        == 'cleanup --remove-images "quay.invalid/foo/bar:latest" "quay.invalid/foo/bar:devel" --image-prune --process-isolation-executable=podman'
    )


def test_compute_execution_timing_deltas():
    marks = {'transmit_start': 10.0, 'transmit_end': 12.5, 'processor_end': 40.0}
    timing = compute_execution_timing(
        'ansible-runner',
        marks,
        runner_starting_at=13.0,
        first_event_at=18.0,
        wrapup_event_at=38.0,
    )
    assert timing == {
        'work_type': 'ansible-runner',
        'receptor_transmit_s': 2.5,
        'runner_setup_s': 0.5,
        'ee_start_s': 5.0,
        'playbook_s': 20.0,
        'result_stream_s': 2.0,
    }


def test_compute_execution_timing_missing_clocks():
    timing = compute_execution_timing('local', {'transmit_start': 1.0})
    assert timing['work_type'] == 'local'
    assert timing['receptor_transmit_s'] is None
    assert timing['ee_start_s'] is None
    assert timing['playbook_s'] is None
