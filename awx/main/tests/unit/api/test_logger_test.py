import pytest

from awx.main.utils.external_logging import construct_rsyslog_conf_template
from awx.conf import settings_registry


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
    'enabled, type, host, port, protocol, expected_config', [
        (True, 'loggly', 'http://logs-01.loggly.com/inputs/1fd38090-2af1-4e1e-8d80-492899da0f71/tag/http/', None, 'https', 
            '$IncludeConfig /etc/rsyslog.conf\ninput(type="imuxsock" Socket="/var/run/rsyslog/rsyslog.sock" unlink="on")\ntemplate(name="awx" type="string" string="%msg%")\nmodule(load="omhttp")\naction(type="omhttp" server="logs-01.loggly.com" serverport="80" usehttps="off" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" errorfile="/var/log/tower/external.err" healthchecktimeout="20000" restpath="inputs/1fd38090-2af1-4e1e-8d80-492899da0f71/tag/http/")'),
        (True, 'other', 'localhost', 9000, 'udp', 
            '$IncludeConfig /etc/rsyslog.conf\ninput(type="imuxsock" Socket="/var/run/rsyslog/rsyslog.sock" unlink="on")\ntemplate(name="awx" type="string" string="%msg%")\naction(type="omfwd" target="localhost" port="9000" protocol="udp" action.resumeRetryCount="-1" template="awx")'),
        (True, 'other', 'localhost', 9000, 'tcp', 
            '$IncludeConfig /etc/rsyslog.conf\ninput(type="imuxsock" Socket="/var/run/rsyslog/rsyslog.sock" unlink="on")\ntemplate(name="awx" type="string" string="%msg%")\naction(type="omfwd" target="localhost" port="9000" protocol="tcp" action.resumeRetryCount="-1" template="awx")'),
        (False, 'loggly', 'http://logs-01.loggly.com/inputs/1fd38090-2af1-4e1e-8d80-492899da0f71/tag/http/', 8080, 'https', 
            '$IncludeConfig /etc/rsyslog.conf'),
        (True, 'splunk', 'https://yoursplunk:8088/services/collector/event', None, None,
            '''$IncludeConfig /etc/rsyslog.conf
input(type="imuxsock" Socket="/var/run/rsyslog/rsyslog.sock" unlink="on")
template(name="awx" type="string" string="%msg%")
module(load="omhttp")
action(type="omhttp" server="yoursplunk" serverport="8088" usehttps="on" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" errorfile="/var/log/tower/external.err" healthchecktimeout="20000" restpath="services/collector/event")'''),
        (True, 'splunk', 'https://yoursplunk/services/collector/event', 8088, None,
            '''$IncludeConfig /etc/rsyslog.conf
input(type="imuxsock" Socket="/var/run/rsyslog/rsyslog.sock" unlink="on")
template(name="awx" type="string" string="%msg%")
module(load="omhttp")
action(type="omhttp" server="yoursplunk" serverport="8088" usehttps="on" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" errorfile="/var/log/tower/external.err" healthchecktimeout="20000" restpath="services/collector/event")'''),
        (True, 'splunk', 'https://yoursplunk/services/collector/event', 8088, 'https',
            '''$IncludeConfig /etc/rsyslog.conf
input(type="imuxsock" Socket="/var/run/rsyslog/rsyslog.sock" unlink="on")
template(name="awx" type="string" string="%msg%")
module(load="omhttp")
action(type="omhttp" server="yoursplunk" serverport="8088" usehttps="on" skipverifyhost="off" action.resumeRetryCount="-1" template="awx" errorfile="/var/log/tower/external.err" healthchecktimeout="20000" restpath="services/collector/event")'''),
    ]
)
def test_rsyslog_conf_template(enabled, type, host, port, protocol, expected_config):
    
    # Mock settings object
    class MockSettings:
        pass
    mock_settings = MockSettings()
    
    # Pre-populate settings obj with defaults
    for key in settings_registry.get_registered_settings(category_slug='logging'):
        value = settings_registry.get_setting_field(key).get_default()
        setattr(mock_settings, key, value)
    
    
    # Set test settings
    setattr(mock_settings, 'LOGGING_SOCK', '/var/run/rsyslog/rsyslog.sock')
    setattr(mock_settings, 'LOG_AGGREGATOR_ENABLED', enabled)
    setattr(mock_settings, 'LOG_AGGREGATOR_TYPE', type)
    setattr(mock_settings, 'LOG_AGGREGATOR_HOST', host)
    if port:
        setattr(mock_settings, 'LOG_AGGREGATOR_PORT', port)
    if protocol:
        setattr(mock_settings, 'LOG_AGGREGATOR_PROTOCOL', protocol)

    # create rsyslog conf template 
    tmpl = construct_rsyslog_conf_template(mock_settings)
    
    # check validity of created template
    assert tmpl in expected_config

