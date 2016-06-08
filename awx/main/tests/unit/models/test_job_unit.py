import json

from awx.main.tasks import RunJob


def test_job_safe_args_redacted_passwords(job_with_secret_key_unit):
    """Verify that safe_args hides passwords in the job extra_vars"""
    kwargs = {'ansible_version': '2.1'}
    run_job = RunJob()
    safe_args = run_job.build_safe_args(job_with_secret_key_unit, **kwargs)
    ev_index = safe_args.index('-e') + 1
    extra_vars = json.loads(safe_args[ev_index])
    assert extra_vars['secret_key'] == '$encrypted$'
    assert extra_vars['submitter_email'] == 'foobar@redhat.com'

def test_job_args_unredacted_passwords(job_with_secret_key_unit):
    kwargs = {'ansible_version': '2.1'}
    run_job = RunJob()
    args = run_job.build_args(job_with_secret_key_unit, **kwargs)
    ev_index = args.index('-e') + 1
    extra_vars = json.loads(args[ev_index])
    assert extra_vars['secret_key'] == '6kQngg3h8lgiSTvIEb21'
    assert extra_vars['submitter_email'] == 'foobar@redhat.com'
