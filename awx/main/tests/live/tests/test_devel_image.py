import os

RSYSLOG_CONFIG = '/var/lib/awx/rsyslog/rsyslog.conf'


def test_rsyslog_config_readable():
    with open(RSYSLOG_CONFIG, 'r') as f:
        content = f.read()
        assert '/var/lib/awx/rsyslog' in content
    assert oct(os.stat(RSYSLOG_CONFIG).st_mode) == '0o100640'
