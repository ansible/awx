import pytest

from django.conf import settings

from awx.main.utils import external_logging
from awx.main.utils.external_logging import construct_rsyslog_conf_template
from awx.main.tests.functional.api.test_settings import _mock_logging_defaults

'''
# Example User Data
data_logstash = {
    "LOG_AGGREGATOR_TYPE": "logstash",
    "LOG_AGGREGATOR_HOST": "localhost",
    "LOG_AGGREGATOR_PORT": 8080,
    "LOG_AGGREGATOR_PROTOCOL": "tcp",
    "LOG_AGGREGATOR_USERNAME": "logger",
    "LOG_AGGREGATOR_PASSWORD": "mcstash"
}

data_netcat = {
    "LOG_AGGREGATOR_TYPE": "other",
    "LOG_AGGREGATOR_HOST": "localhost",
    "LOG_AGGREGATOR_PORT": 9000,
    "LOG_AGGREGATOR_PROTOCOL": "udp",
}

data_loggly = {
    "LOG_AGGREGATOR_TYPE": "loggly",
    "LOG_AGGREGATOR_HOST": "http://logs-01.loggly.com/inputs/1fd38090-2af1-4e1e-8d80-492899da0f71/tag/http/",
    "LOG_AGGREGATOR_PORT": 8080,
    "LOG_AGGREGATOR_PROTOCOL": "https"
}
'''


# Test reconfigure logging settings function
# name this whatever you want
@pytest.mark.parametrize(
    'enabled, log_type, host, port, protocol, errorfile, expected_config',
    [
        (
            True,
            'loggly',
            'http://logs-01.loggly.com/inputs/1fd38090-2af1-4e1e-8d80-492899da0f71/tag/http/',
            None,
            'https',
            '/var/log/tower/rsyslog.err',
            '\n'.join(
                [
                    'template(name="awx" type="string" string="%rawmsg-after-pri%")\nmodule(load="omhttp")',
                    'action(type="omhttp" server="logs-01.loggly.com" serverport="80" usehttps="off" allowunsignedcerts="off" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" action.resumeInterval="5" queue.spoolDirectory="/var/lib/awx" queue.filename="awx-external-logger-action-queue" queue.maxDiskSpace="1g" queue.maxFileSize="100m" queue.type="LinkedList" queue.saveOnShutdown="on" queue.syncqueuefiles="on" queue.checkpointInterval="1000" queue.size="131072" queue.highwaterMark="98304" queue.discardMark="117964" queue.discardSeverity="5" errorfile="/var/log/tower/rsyslog.err" restpath="inputs/1fd38090-2af1-4e1e-8d80-492899da0f71/tag/http/")',  # noqa
                ]
            ),
        ),
        (
            True,  # localhost w/ custom UDP port
            'other',
            'localhost',
            9000,
            'udp',
            '',  # empty errorfile
            '\n'.join(
                [
                    'template(name="awx" type="string" string="%rawmsg-after-pri%")',
                    'action(type="omfwd" target="localhost" port="9000" protocol="udp" action.resumeRetryCount="-1" action.resumeInterval="5" template="awx" queue.spoolDirectory="/var/lib/awx" queue.filename="awx-external-logger-action-queue" queue.maxDiskSpace="1g" queue.maxFileSize="100m" queue.type="LinkedList" queue.saveOnShutdown="on" queue.syncqueuefiles="on" queue.checkpointInterval="1000" queue.size="131072" queue.highwaterMark="98304" queue.discardMark="117964" queue.discardSeverity="5")',  # noqa
                ]
            ),
        ),
        (
            True,  # localhost w/ custom TCP port
            'other',
            'localhost',
            9000,
            'tcp',
            '/var/log/tower/rsyslog.err',
            '\n'.join(
                [
                    'template(name="awx" type="string" string="%rawmsg-after-pri%")',
                    'action(type="omfwd" target="localhost" port="9000" protocol="tcp" action.resumeRetryCount="-1" action.resumeInterval="5" template="awx" queue.spoolDirectory="/var/lib/awx" queue.filename="awx-external-logger-action-queue" queue.maxDiskSpace="1g" queue.maxFileSize="100m" queue.type="LinkedList" queue.saveOnShutdown="on" queue.syncqueuefiles="on" queue.checkpointInterval="1000" queue.size="131072" queue.highwaterMark="98304" queue.discardMark="117964" queue.discardSeverity="5")',  # noqa
                ]
            ),
        ),
        (
            True,  # https, default port 443
            'splunk',
            'https://yoursplunk/services/collector/event',
            None,
            None,
            '/var/log/tower/rsyslog.err',
            '\n'.join(
                [
                    'template(name="awx" type="string" string="%rawmsg-after-pri%")\nmodule(load="omhttp")',
                    'action(type="omhttp" server="yoursplunk" serverport="443" usehttps="on" allowunsignedcerts="off" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" action.resumeInterval="5" queue.spoolDirectory="/var/lib/awx" queue.filename="awx-external-logger-action-queue" queue.maxDiskSpace="1g" queue.maxFileSize="100m" queue.type="LinkedList" queue.saveOnShutdown="on" queue.syncqueuefiles="on" queue.checkpointInterval="1000" queue.size="131072" queue.highwaterMark="98304" queue.discardMark="117964" queue.discardSeverity="5" errorfile="/var/log/tower/rsyslog.err" restpath="services/collector/event")',  # noqa
                ]
            ),
        ),
        (
            True,  # http, default port 80
            'splunk',
            'http://yoursplunk/services/collector/event',
            None,
            None,
            '/var/log/tower/rsyslog.err',
            '\n'.join(
                [
                    'template(name="awx" type="string" string="%rawmsg-after-pri%")\nmodule(load="omhttp")',
                    'action(type="omhttp" server="yoursplunk" serverport="80" usehttps="off" allowunsignedcerts="off" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" action.resumeInterval="5" queue.spoolDirectory="/var/lib/awx" queue.filename="awx-external-logger-action-queue" queue.maxDiskSpace="1g" queue.maxFileSize="100m" queue.type="LinkedList" queue.saveOnShutdown="on" queue.syncqueuefiles="on" queue.checkpointInterval="1000" queue.size="131072" queue.highwaterMark="98304" queue.discardMark="117964" queue.discardSeverity="5" errorfile="/var/log/tower/rsyslog.err" restpath="services/collector/event")',  # noqa
                ]
            ),
        ),
        (
            True,  # https, custom port in URL string
            'splunk',
            'https://yoursplunk:8088/services/collector/event',
            None,
            None,
            '/var/log/tower/rsyslog.err',
            '\n'.join(
                [
                    'template(name="awx" type="string" string="%rawmsg-after-pri%")\nmodule(load="omhttp")',
                    'action(type="omhttp" server="yoursplunk" serverport="8088" usehttps="on" allowunsignedcerts="off" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" action.resumeInterval="5" queue.spoolDirectory="/var/lib/awx" queue.filename="awx-external-logger-action-queue" queue.maxDiskSpace="1g" queue.maxFileSize="100m" queue.type="LinkedList" queue.saveOnShutdown="on" queue.syncqueuefiles="on" queue.checkpointInterval="1000" queue.size="131072" queue.highwaterMark="98304" queue.discardMark="117964" queue.discardSeverity="5" errorfile="/var/log/tower/rsyslog.err" restpath="services/collector/event")',  # noqa
                ]
            ),
        ),
        (
            True,  # https, custom port explicitly specified
            'splunk',
            'https://yoursplunk/services/collector/event',
            8088,
            None,
            '/var/log/tower/rsyslog.err',
            '\n'.join(
                [
                    'template(name="awx" type="string" string="%rawmsg-after-pri%")\nmodule(load="omhttp")',
                    'action(type="omhttp" server="yoursplunk" serverport="8088" usehttps="on" allowunsignedcerts="off" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" action.resumeInterval="5" queue.spoolDirectory="/var/lib/awx" queue.filename="awx-external-logger-action-queue" queue.maxDiskSpace="1g" queue.maxFileSize="100m" queue.type="LinkedList" queue.saveOnShutdown="on" queue.syncqueuefiles="on" queue.checkpointInterval="1000" queue.size="131072" queue.highwaterMark="98304" queue.discardMark="117964" queue.discardSeverity="5" errorfile="/var/log/tower/rsyslog.err" restpath="services/collector/event")',  # noqa
                ]
            ),
        ),
        (
            True,  # no scheme specified in URL, default to https, respect custom port
            'splunk',
            'yoursplunk.org/services/collector/event',
            8088,
            'https',
            '/var/log/tower/rsyslog.err',
            '\n'.join(
                [
                    'template(name="awx" type="string" string="%rawmsg-after-pri%")\nmodule(load="omhttp")',
                    'action(type="omhttp" server="yoursplunk.org" serverport="8088" usehttps="on" allowunsignedcerts="off" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" action.resumeInterval="5" queue.spoolDirectory="/var/lib/awx" queue.filename="awx-external-logger-action-queue" queue.maxDiskSpace="1g" queue.maxFileSize="100m" queue.type="LinkedList" queue.saveOnShutdown="on" queue.syncqueuefiles="on" queue.checkpointInterval="1000" queue.size="131072" queue.highwaterMark="98304" queue.discardMark="117964" queue.discardSeverity="5" errorfile="/var/log/tower/rsyslog.err" restpath="services/collector/event")',  # noqa
                ]
            ),
        ),
        (
            True,  # respect custom http-only port
            'splunk',
            'http://yoursplunk.org/services/collector/event',
            8088,
            None,
            '/var/log/tower/rsyslog.err',
            '\n'.join(
                [
                    'template(name="awx" type="string" string="%rawmsg-after-pri%")\nmodule(load="omhttp")',
                    'action(type="omhttp" server="yoursplunk.org" serverport="8088" usehttps="off" allowunsignedcerts="off" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" action.resumeInterval="5" queue.spoolDirectory="/var/lib/awx" queue.filename="awx-external-logger-action-queue" queue.maxDiskSpace="1g" queue.maxFileSize="100m" queue.type="LinkedList" queue.saveOnShutdown="on" queue.syncqueuefiles="on" queue.checkpointInterval="1000" queue.size="131072" queue.highwaterMark="98304" queue.discardMark="117964" queue.discardSeverity="5" errorfile="/var/log/tower/rsyslog.err" restpath="services/collector/event")',  # noqa
                ]
            ),
        ),
        (
            True,  # valid sumologic config
            'sumologic',
            'https://endpoint5.collection.us2.sumologic.com/receiver/v1/http/ZaVnC4dhaV0qoiETY0MrM3wwLoDgO1jFgjOxE6-39qokkj3LGtOroZ8wNaN2M6DtgYrJZsmSi4-36_Up5TbbN_8hosYonLKHSSOSKY845LuLZBCBwStrHQ==',  # noqa
            None,
            'https',
            '/var/log/tower/rsyslog.err',
            '\n'.join(
                [
                    'template(name="awx" type="string" string="%rawmsg-after-pri%")\nmodule(load="omhttp")',
                    'action(type="omhttp" server="endpoint5.collection.us2.sumologic.com" serverport="443" usehttps="on" allowunsignedcerts="off" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" action.resumeInterval="5" queue.spoolDirectory="/var/lib/awx" queue.filename="awx-external-logger-action-queue" queue.maxDiskSpace="1g" queue.maxFileSize="100m" queue.type="LinkedList" queue.saveOnShutdown="on" queue.syncqueuefiles="on" queue.checkpointInterval="1000" queue.size="131072" queue.highwaterMark="98304" queue.discardMark="117964" queue.discardSeverity="5" errorfile="/var/log/tower/rsyslog.err" restpath="receiver/v1/http/ZaVnC4dhaV0qoiETY0MrM3wwLoDgO1jFgjOxE6-39qokkj3LGtOroZ8wNaN2M6DtgYrJZsmSi4-36_Up5TbbN_8hosYonLKHSSOSKY845LuLZBCBwStrHQ==")',  # noqa
                ]
            ),
        ),
    ],
)
def test_rsyslog_conf_template(enabled, log_type, host, port, protocol, errorfile, expected_config):
    mock_settings, _ = _mock_logging_defaults()

    # Set test settings
    logging_defaults = getattr(settings, 'LOGGING')
    setattr(mock_settings, 'LOGGING', logging_defaults)
    setattr(mock_settings, 'LOGGING["handlers"]["external_logger"]["address"]', '/var/run/awx-rsyslog/rsyslog.sock')
    setattr(mock_settings, 'LOG_AGGREGATOR_ENABLED', enabled)
    setattr(mock_settings, 'LOG_AGGREGATOR_TYPE', log_type)
    setattr(mock_settings, 'LOG_AGGREGATOR_HOST', host)
    setattr(mock_settings, 'LOG_AGGREGATOR_RSYSLOGD_ERROR_LOG_FILE', errorfile)
    if port:
        setattr(mock_settings, 'LOG_AGGREGATOR_PORT', port)
    if protocol:
        setattr(mock_settings, 'LOG_AGGREGATOR_PROTOCOL', protocol)

    # create rsyslog conf template
    tmpl = construct_rsyslog_conf_template(mock_settings)

    # check validity of created template
    assert expected_config in tmpl


STATS_MODULE = 'module(load="impstats" interval="{}" format="json" resetCounters="off" ruleset="awx_queue_stats")'
STATS_RULESET = 'ruleset(name="awx_queue_stats" queue.type="Direct") { action(type="omfile" file="/dev/stdout") }'


@pytest.fixture
def conf_d(tmp_path, monkeypatch):
    """An empty drop-in directory in place of /var/lib/awx/rsyslog/conf.d."""
    monkeypatch.setattr(external_logging, 'CONF_D_DIRECTORY', str(tmp_path))
    return tmp_path


def _queue_stats_lines(enabled, stats_interval):
    mock_settings, _ = _mock_logging_defaults()

    logging_defaults = getattr(settings, 'LOGGING')
    setattr(mock_settings, 'LOGGING', logging_defaults)
    setattr(mock_settings, 'LOG_AGGREGATOR_ENABLED', enabled)
    setattr(mock_settings, 'LOG_AGGREGATOR_TYPE', 'other')
    setattr(mock_settings, 'LOG_AGGREGATOR_HOST', 'localhost')
    setattr(mock_settings, 'LOG_AGGREGATOR_PORT', 9000)
    setattr(mock_settings, 'LOG_AGGREGATOR_PROTOCOL', 'tcp')
    if stats_interval is not None:
        setattr(mock_settings, 'LOG_AGGREGATOR_ACTION_QUEUE_STATS_INTERVAL', stats_interval)

    lines = construct_rsyslog_conf_template(mock_settings).split('\n')
    return [line for line in lines if 'impstats' in line or 'awx_queue_stats' in line]


@pytest.mark.parametrize(
    'enabled, stats_interval, expected_interval',
    [
        (True, None, None),  # registered default (0): no impstats, configuration unchanged
        (True, 0, None),
        (True, 60, 60),
        (True, 1, 1),
        (True, 2147483647, 2147483647),  # the largest impstats can hold
        (False, 60, None),  # no external action, so no queue to report on
    ],
)
def test_rsyslog_conf_queue_stats(conf_d, enabled, stats_interval, expected_interval):
    stats = _queue_stats_lines(enabled, stats_interval)
    assert stats == ([] if expected_interval is None else [STATS_MODULE.format(expected_interval), STATS_RULESET])


@pytest.mark.parametrize(
    'drop_in',
    [
        'module(load="impstats" interval="5" log.syslog="off" log.file="/tmp/impstats.log")',
        "module ( load = 'impstats' interval='5' )",
        'module(\n  load="impstats"\n  interval="5"\n)',
        'module(interval="5" load="impstats")',
        'module(load="/usr/lib64/rsyslog/impstats.so")',
        '$ModLoad impstats',
        '$modload impstats.so  # legacy directives are case-insensitive',
    ],
)
def test_rsyslog_conf_queue_stats_defers_to_a_drop_in(conf_d, caplog, drop_in):
    # rsyslog refuses a second load of a module, which fails rsyslogd -N1 and the logging test,
    # so the drop-in's impstats stands and neither our module nor its ruleset is emitted.
    (conf_d / 'other.conf').write_text('module(load="imfile")\n')
    (conf_d / 'impstats.conf').write_text(drop_in + '\n')

    with caplog.at_level('WARNING'):
        stats = _queue_stats_lines(True, 60)

    assert stats == []
    assert str(conf_d / 'impstats.conf') in caplog.text
    assert str(conf_d / 'other.conf') not in caplog.text
    assert 'LOG_AGGREGATOR_ACTION_QUEUE_STATS_INTERVAL is ignored' in caplog.text


@pytest.mark.parametrize(
    'name, drop_in',
    [
        ('impstats.conf', '# module(load="impstats" interval="5")'),
        ('impstats.conf', '#$ModLoad impstats'),
        ('impstats.conf', '/*\nmodule(load="impstats" interval="5")\n*/'),
        ('impstats.conf', 'action(type="omfile" file="/tmp/impstats.log")'),  # names impstats, does not load it
        ('impstats.conf', 'module(load="impstatsx")'),
        ('impstats.conf.disabled', 'module(load="impstats" interval="5")'),  # outside the include's *.conf
    ],
)
def test_rsyslog_conf_queue_stats_ignores_drop_ins_that_do_not_load_impstats(conf_d, caplog, name, drop_in):
    (conf_d / name).write_text(drop_in + '\n')

    with caplog.at_level('WARNING'):
        stats = _queue_stats_lines(True, 60)

    assert stats == [STATS_MODULE.format(60), STATS_RULESET]
    assert 'impstats is already loaded' not in caplog.text


def test_rsyslog_conf_queue_stats_without_a_conf_d_directory(tmp_path, monkeypatch, caplog):
    monkeypatch.setattr(external_logging, 'CONF_D_DIRECTORY', str(tmp_path / 'not-created'))

    with caplog.at_level('WARNING'):
        stats = _queue_stats_lines(True, 60)

    assert stats == [STATS_MODULE.format(60), STATS_RULESET]
    assert 'impstats is already loaded' not in caplog.text


@pytest.mark.parametrize('enabled, stats_interval', [(True, 0), (False, 60)])
def test_rsyslog_conf_queue_stats_off_says_nothing_about_a_drop_in(conf_d, caplog, enabled, stats_interval):
    # With the setting off there is no conflict to report.
    (conf_d / 'impstats.conf').write_text('module(load="impstats" interval="5")\n')

    with caplog.at_level('WARNING'):
        stats = _queue_stats_lines(enabled, stats_interval)

    assert stats == []
    assert 'impstats is already loaded' not in caplog.text


def test_splunk_auth():
    mock_settings, _ = _mock_logging_defaults()
    # Set test settings
    logging_defaults = getattr(settings, 'LOGGING')
    setattr(mock_settings, 'LOGGING', logging_defaults)
    setattr(mock_settings, 'LOG_AGGREGATOR_ENABLED', True)
    setattr(mock_settings, 'LOG_AGGREGATOR_TYPE', 'splunk')
    setattr(mock_settings, 'LOG_AGGREGATOR_HOST', 'example.org')
    setattr(mock_settings, 'LOG_AGGREGATOR_PASSWORD', 'SECRET-TOKEN')

    tmpl = construct_rsyslog_conf_template(mock_settings)
    assert 'httpheaderkey="Authorization" httpheadervalue="Splunk SECRET-TOKEN"' in tmpl
