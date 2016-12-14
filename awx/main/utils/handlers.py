# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

# Python
import logging
import json
import requests
from copy import copy

# loggly
import traceback

from requests_futures.sessions import FuturesSession

# custom
from django.conf import settings as django_settings
from django.utils.log import NullHandler

# AWX external logging handler, generally designed to be used
# with the accompanying LogstashHandler, derives from python-logstash library
# Non-blocking request accomplished by FuturesSession, similar
# to the loggly-python-handler library (not used)

# Translation of parameter names to names in Django settings
PARAM_NAMES = {
    'host': 'LOG_AGGREGATOR_HOST',
    'port': 'LOG_AGGREGATOR_PORT',
    'message_type': 'LOG_AGGREGATOR_TYPE',
    'username': 'LOG_AGGREGATOR_USERNAME',
    'password': 'LOG_AGGREGATOR_PASSWORD',
    'enabled_loggers': 'LOG_AGGREGATOR_LOGGERS',
    'indv_facts': 'LOG_AGGREGATOR_INDIVIDUAL_FACTS',
    'enabled_flag': 'LOG_AGGREGATOR_ENABLED',
}


def unused_callback(sess, resp):
    pass


class HTTPSNullHandler(NullHandler):
    "Placeholder null handler to allow loading without database access"

    def __init__(self, host, **kwargs):
        return super(HTTPSNullHandler, self).__init__()


class HTTPSHandler(logging.Handler):
    def __init__(self, fqdn=False, **kwargs):
        super(HTTPSHandler, self).__init__()
        self.fqdn = fqdn
        self.async = kwargs.get('async', True)
        for fd in PARAM_NAMES:
            # settings values take precedence over the input params
            settings_name = PARAM_NAMES[fd]
            settings_val = getattr(django_settings, settings_name, None)
            if settings_val:
                setattr(self, fd, settings_val)
            elif fd in kwargs:
                setattr(self, fd, kwargs[fd])
            else:
                setattr(self, fd, None)
        self.session = FuturesSession()
        self.add_auth_information()

    def get_full_message(self, record):
        if record.exc_info:
            return '\n'.join(traceback.format_exception(*record.exc_info))
        else:
            return record.getMessage()

    def add_auth_information(self):
        if self.message_type == 'logstash':
            if not self.username:
                # Logstash authentication not enabled
                return
            logstash_auth = requests.auth.HTTPBasicAuth(self.username, self.password)
            self.session.auth = logstash_auth
        elif self.message_type == 'splunk':
            auth_header = "Splunk %s" % self.password
            headers = {
                "Authorization": auth_header,
                "Content-Type": "application/json"
            }
            self.session.headers.update(headers)

    def get_http_host(self):
        host = self.host
        if not host.startswith('http'):
            host = 'http://%s' % self.host
        if self.port != 80 and self.port is not None:
            host = '%s:%s' % (host, str(self.port))
        return host

    def get_post_kwargs(self, payload_input):
        if self.message_type == 'splunk':
            # Splunk needs data nested under key "event"
            if not isinstance(payload_input, dict):
                payload_input = json.loads(payload_input)
            payload_input = {'event': payload_input}
        if isinstance(payload_input, dict):
            payload_str = json.dumps(payload_input)
        else:
            payload_str = payload_input
        if self.async:
            return dict(data=payload_str, background_callback=unused_callback)
        else:
            return dict(data=payload_str)

    def skip_log(self, logger_name):
        if self.host == '' or (not self.enabled_flag):
            return True
        if not logger_name.startswith('awx.analytics'):
            # Tower log emission is only turned off by enablement setting
            return False
        return self.enabled_loggers is None or logger_name.split('.')[-1] not in self.enabled_loggers

    def emit(self, record):
        if self.skip_log(record.name):
            return
        try:
            payload = self.format(record)
            host = self.get_http_host()

            # Special action for System Tracking, queue up multiple log messages
            if self.indv_facts:
                payload_data = json.loads(payload)
                if record.name.startswith('awx.analytics.system_tracking'):
                    module_name = payload_data['module_name']
                    if module_name in ['services', 'packages', 'files']:
                        facts_dict = payload_data.pop(module_name)
                        for key in facts_dict:
                            fact_payload = copy(payload_data)
                            fact_payload.update(facts_dict[key])
                            self.session.post(host, **self.get_post_kwargs(fact_payload))
                        return

            if self.async:
                self.session.post(host, **self.get_post_kwargs(payload))
            else:
                requests.post(host, auth=requests.auth.HTTPBasicAuth(self.username, self.password), **self.get_post_kwargs(payload))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

