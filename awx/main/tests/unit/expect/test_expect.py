# -*- coding: utf-8 -*-

import os
import pytest
import re
import shutil
import stat
import tempfile
import time
from collections import OrderedDict
from io import StringIO
from unittest import mock

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from django.utils.encoding import smart_str, smart_bytes

from awx.main.expect import run, isolated_manager

from django.conf import settings

HERE, FILENAME = os.path.split(__file__)


@pytest.fixture(scope='function')
def rsa_key(request):
    passphrase = 'passme'
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=1024,
        backend=default_backend()
    )
    return (
        smart_str(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.BestAvailableEncryption(smart_bytes(passphrase))
        )),
        passphrase
    )


@pytest.fixture(scope='function')
def private_data_dir(request):
    path = tempfile.mkdtemp(prefix='ansible_awx_unit_test')
    request.addfinalizer(lambda: shutil.rmtree(path))
    return path


@pytest.fixture(autouse=True)
def mock_sleep(request):
    # the process teardown mechanism uses `time.sleep` to wait on processes to
    # respond to SIGTERM; these are tests and don't care about being nice
    m = mock.patch('time.sleep')
    m.start()
    request.addfinalizer(m.stop)


def test_simple_spawn():
    stdout = StringIO()
    status, rc = run.run_pexpect(
        ['ls', '-la'],
        HERE,
        {},
        stdout,
        cancelled_callback=lambda: False,
    )
    assert status == 'successful'
    assert rc == 0
    # assert FILENAME in stdout.getvalue()


def test_error_rc():
    stdout = StringIO()
    status, rc = run.run_pexpect(
        ['ls', '-nonsense'],
        HERE,
        {},
        stdout,
        cancelled_callback=lambda: False,
    )
    assert status == 'failed'
    # I'd expect 2, but we shouldn't risk making this test platform-dependent
    assert rc > 0


def test_cancel_callback_error():
    stdout = StringIO()

    def bad_callback():
        raise Exception('unique exception')

    extra_fields = {}
    status, rc = run.run_pexpect(
        ['sleep', '2'],
        HERE,
        {},
        stdout,
        cancelled_callback=bad_callback,
        extra_update_fields=extra_fields
    )
    assert status == 'error'
    assert rc == 0
    assert extra_fields['job_explanation'] == "System error during job execution, check system logs"


@pytest.mark.timeout(3)  # https://github.com/ansible/tower/issues/2391#issuecomment-401946895
@pytest.mark.parametrize('value', ['abc123', 'Iñtërnâtiônàlizætiøn'])
def test_env_vars(value):
    stdout = StringIO()
    status, rc = run.run_pexpect(
        ['python', '-c', 'import os; print os.getenv("X_MY_ENV")'],
        HERE,
        {'X_MY_ENV': value},
        stdout,
        cancelled_callback=lambda: False,
    )
    assert status == 'successful'
    assert rc == 0
    assert value in stdout.getvalue()


def test_password_prompt():
    stdout = StringIO()
    expect_passwords = OrderedDict()
    expect_passwords[re.compile(r'Password:\s*?$', re.M)] = 'secret123'
    status, rc = run.run_pexpect(
        ['python', '-c', 'import time; print raw_input("Password: "); time.sleep(.05)'],
        HERE,
        {},
        stdout,
        cancelled_callback=lambda: False,
        expect_passwords=expect_passwords
    )
    assert status == 'successful'
    assert rc == 0
    assert 'secret123' in stdout.getvalue()


def test_job_timeout():
    stdout = StringIO()
    extra_update_fields={}
    status, rc = run.run_pexpect(
        ['python', '-c', 'import time; time.sleep(5)'],
        HERE,
        {},
        stdout,
        cancelled_callback=lambda: False,
        extra_update_fields=extra_update_fields,
        job_timeout=.01,
        pexpect_timeout=0,
    )
    assert status == 'failed'
    assert extra_update_fields == {'job_explanation': 'Job terminated due to timeout'}


def test_manual_cancellation():
    stdout = StringIO()
    status, rc = run.run_pexpect(
        ['python', '-c', 'print raw_input("Password: ")'],
        HERE,
        {},
        stdout,
        cancelled_callback=lambda: True,  # this callable will cause cancellation
        # the lack of password inputs will cause stdin to hang
        pexpect_timeout=0,
    )
    assert status == 'canceled'


def test_build_isolated_job_data(private_data_dir, rsa_key):
    pem, passphrase = rsa_key
    mgr = isolated_manager.IsolatedManager(
        ['ls', '-la'], HERE, {}, StringIO(), ''
    )
    mgr.private_data_dir = private_data_dir
    mgr.build_isolated_job_data()

    path = os.path.join(private_data_dir, 'project')
    assert os.path.isdir(path)

    # <private_data_dir>/project is a soft link to HERE, which is the directory
    # _this_ test file lives in
    assert os.path.exists(os.path.join(path, FILENAME))

    path = os.path.join(private_data_dir, 'artifacts')
    assert os.path.isdir(path)
    assert stat.S_IMODE(os.stat(path).st_mode) == stat.S_IXUSR + stat.S_IWUSR + stat.S_IRUSR  # user rwx

    path = os.path.join(private_data_dir, 'args')
    with open(path, 'r') as f:
        assert stat.S_IMODE(os.stat(path).st_mode) == stat.S_IRUSR # user r/o
        assert f.read() == '["ls", "-la"]'

    path = os.path.join(private_data_dir, '.rsync-filter')
    with open(path, 'r') as f:
        data = f.read()
        assert data == '\n'.join([
            '- /project/.git',
            '- /project/.svn',
            '- /project/.hg',
            '- /artifacts/job_events/*-partial.json.tmp',
            '- /env'
        ])


def test_run_isolated_job(private_data_dir, rsa_key):
    env = {'JOB_ID': '1'}
    pem, passphrase = rsa_key
    mgr = isolated_manager.IsolatedManager(
        ['ls', '-la'], HERE, env, StringIO(), ''
    )
    mgr.private_data_dir = private_data_dir
    secrets = {
        'env': env,
        'passwords': {
            r'Enter passphrase for .*:\s*?$': passphrase
        },
        'ssh_key_data': pem
    }
    mgr.build_isolated_job_data()
    stdout = StringIO()
    # Mock environment variables for callback module
    with mock.patch('os.getenv') as env_mock:
        env_mock.return_value = '/path/to/awx/lib'
        status, rc = run.run_isolated_job(private_data_dir, secrets, stdout)
    assert status == 'successful'
    assert rc == 0
    assert FILENAME in stdout.getvalue()

    assert '/path/to/awx/lib' in env['PYTHONPATH']
    assert env['ANSIBLE_STDOUT_CALLBACK'] == 'awx_display'
    assert env['ANSIBLE_CALLBACK_PLUGINS'] == '/path/to/awx/lib/isolated_callbacks'
    assert env['AWX_ISOLATED_DATA_DIR'] == private_data_dir


def test_run_isolated_adhoc_command(private_data_dir, rsa_key):
    env = {'AD_HOC_COMMAND_ID': '1'}
    pem, passphrase = rsa_key
    mgr = isolated_manager.IsolatedManager(
        ['pwd'], HERE, env, StringIO(), ''
    )
    mgr.private_data_dir = private_data_dir
    secrets = {
        'env': env,
        'passwords': {
            r'Enter passphrase for .*:\s*?$': passphrase
        },
        'ssh_key_data': pem
    }
    mgr.build_isolated_job_data()
    stdout = StringIO()
    # Mock environment variables for callback module
    with mock.patch('os.getenv') as env_mock:
        env_mock.return_value = '/path/to/awx/lib'
        status, rc = run.run_isolated_job(private_data_dir, secrets, stdout)
    assert status == 'successful'
    assert rc == 0

    # for ad-hoc jobs, `ansible` is invoked from the `private_data_dir`, so
    # an ad-hoc command that runs `pwd` should print `private_data_dir` to stdout
    assert private_data_dir in stdout.getvalue()

    assert '/path/to/awx/lib' in env['PYTHONPATH']
    assert env['ANSIBLE_STDOUT_CALLBACK'] == 'minimal'
    assert env['ANSIBLE_CALLBACK_PLUGINS'] == '/path/to/awx/lib/isolated_callbacks'
    assert env['AWX_ISOLATED_DATA_DIR'] == private_data_dir


def test_check_isolated_job(private_data_dir, rsa_key):
    pem, passphrase = rsa_key
    stdout = StringIO()
    mgr = isolated_manager.IsolatedManager(['ls', '-la'], HERE, {}, stdout, '')
    mgr.private_data_dir = private_data_dir
    mgr.instance = mock.Mock(id=123, pk=123, verbosity=5, spec_set=['id', 'pk', 'verbosity'])
    mgr.started_at = time.time()
    mgr.host = 'isolated-host'

    os.mkdir(os.path.join(private_data_dir, 'artifacts'))
    with mock.patch('awx.main.expect.run.run_pexpect') as run_pexpect:

        def _synchronize_job_artifacts(args, cwd, env, buff, **kw):
            buff.write('checking job status...')
            for filename, data in (
                ['status', 'failed'],
                ['rc', '1'],
                ['stdout', 'KABOOM!'],
            ):
                with open(os.path.join(private_data_dir, 'artifacts', filename), 'w') as f:
                    f.write(data)
            return ('successful', 0)

        run_pexpect.side_effect = _synchronize_job_artifacts
        with mock.patch.object(mgr, '_missing_artifacts') as missing_artifacts:
            missing_artifacts.return_value = False
            status, rc = mgr.check(interval=0)

        assert status == 'failed'
        assert rc == 1
        assert stdout.getvalue() == 'KABOOM!'

        run_pexpect.assert_called_with(
            [
                'ansible-playbook', 'check_isolated.yml',
                '-u', settings.AWX_ISOLATED_USERNAME,
                '-T', str(settings.AWX_ISOLATED_CONNECTION_TIMEOUT),
                '-i', 'isolated-host,',
                '-e', '{"src": "%s"}' % private_data_dir,
                '-vvvvv'
            ],
            '/awx_devel/awx/playbooks', mgr.management_env, mock.ANY,
            cancelled_callback=None,
            idle_timeout=0,
            job_timeout=0,
            pexpect_timeout=5,
            proot_cmd='bwrap'
        )


def test_check_isolated_job_timeout(private_data_dir, rsa_key):
    pem, passphrase = rsa_key
    stdout = StringIO()
    extra_update_fields = {}
    mgr = isolated_manager.IsolatedManager(['ls', '-la'], HERE, {}, stdout, '',
                                           job_timeout=1,
                                           extra_update_fields=extra_update_fields)
    mgr.private_data_dir = private_data_dir
    mgr.instance = mock.Mock(id=123, pk=123, verbosity=5, spec_set=['id', 'pk', 'verbosity'])
    mgr.started_at = time.time()
    mgr.host = 'isolated-host'

    with mock.patch('awx.main.expect.run.run_pexpect') as run_pexpect:

        def _synchronize_job_artifacts(args, cwd, env, buff, **kw):
            buff.write('checking job status...')
            return ('failed', 1)

        run_pexpect.side_effect = _synchronize_job_artifacts
        status, rc = mgr.check(interval=0)

        assert status == 'failed'
        assert rc == 1
        assert stdout.getvalue() == 'checking job status...'

    assert extra_update_fields['job_explanation'] == 'Job terminated due to timeout'
