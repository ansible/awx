# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

# common
import socket
import logging

# Splunk
import urllib
import json
import gzip
import cStringIO

import requests

from .utils import parse_config_file, get_config_from_env

# loggly
import traceback

from requests_futures.sessions import FuturesSession

# Logstash
from logstash import formatter

# custom
from copy import copy
from requests.auth import HTTPBasicAuth
from django.conf import settings as django_settings


# Logstash
# https://github.com/vklochan/python-logstash
class TCPLogstashHandler(logging.handlers.SocketHandler, object):
    """Python logging handler for Logstash. Sends events over TCP.
    :param host: The host of the logstash server.
    :param port: The port of the logstash server (default 5959).
    :param message_type: The type of the message (default logstash).
    :param fqdn; Indicates whether to show fully qualified domain name or not (default False).
    :param version: version of logstash event schema (default is 0).
    :param tags: list of tags for a logger (default is None).
    """

    def __init__(self, host, port=5959, message_type='logstash', tags=None, fqdn=False, version=0):
        super(TCPLogstashHandler, self).__init__(host, port)
        if version == 1:
            self.formatter = formatter.LogstashFormatterVersion1(message_type, tags, fqdn)
        else:
            self.formatter = formatter.LogstashFormatterVersion0(message_type, tags, fqdn)

    def makePickle(self, record):
        return self.formatter.format(record) + b'\n'


# techniquest borrowed from the loggly library
# https://github.com/varshneyjayant/loggly-python-handler
# MIT License

# Translation of parameter names to names in Django settings
PARAM_NAMES = {
    'host': 'LOG_AGGREGATOR_HOST',
    'port': 'LOG_AGGREGATOR_PORT',
    'message_type': 'LOG_AGGREGATOR_TYPE',
    'username': 'LOG_AGGREGATOR_USERNAME',
    'password': 'LOG_AGGREGATOR_PASSWORD',
    'enabled_loggers': 'LOG_AGGREGATOR_LOGGERS',
    'indv_facts': 'LOG_AGGREGATOR_INDIVIDUAL_FACTS',
}
# TODO: figure out what to do with LOG_AGGREGATOR_LOGGERS (if anything)


def unused_callback(sess, resp):
    pass


class HTTPSHandler(logging.Handler):
    def __init__(self, fqdn=False, **kwargs):
        super(HTTPSHandler, self).__init__()
        self.fqdn = fqdn
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
            logstash_auth = HTTPBasicAuth(self.username, self.password)
            self.session.auth = logstash_auth
        elif self.message_type == 'splunk':
            auth_header = "Splunk %s" % self.password
            headers = {
                "Authorization": auth_header,
                "Content-Type": "application/json"
            }
            self.session.headers.update(headers)

    def emit(self, record):
        if (self.host == '' or self.enabled_loggers is None or
                record.name.split('.')[-1] not in self.enabled_loggers):
            return
        try:
            payload = self.format(record)
            host = self.host
            if not host.startswith('http'):
                host = 'http://%s' % self.host
            if self.port != 80 and self.port is not None:
                host = '%s:%s' % (host, str(self.port))

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
                            kwargs = dict(data=json.dumps(fact_payload), background_callback=unused_callback)
                            self.session.post(host, **kwargs)
                        return

            kwargs = dict(data=payload, background_callback=unused_callback)
            # # splunk doesn't take "@" in the keys
            # if self.message_type == 'splunk':
            #     payload_dict = json.loads(payload)
            #     new_dict = {}
            #     for key in payload_dict:
            #         new_key = key.replace('@', '')
            #         new_dict[new_key] = payload_dict[key]
            #     new_payload = json.dumps(new_dict)
            #     kwargs['data'] = json.dumps(new_dict)
            self.session.post(host, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


# splunk
# https://github.com/andresriancho/splunk-logger

class SplunkLogger(logging.Handler):
    """
    A class to send messages to splunk storm using their API
    """
    # Required format for splunk storm
    INPUT_URL_FMT = 'https://%s/1/inputs/http'

    def __init__(self, access_token=None, project_id=None, api_domain=None):
        logging.Handler.__init__(self)
        
        self._set_auth(access_token, project_id, api_domain)
        self.url = self.INPUT_URL_FMT % self.api_domain

        self._set_url_opener()
        
        # Handle errors in authentication
        self._auth_failed = False
        
    def _set_auth(self, access_token, project_id, api_domain):
        # The access token and project id passed as parameter override the ones
        # configured in the .splunk_logger file.
        if access_token is not None and project_id is not None and api_domain is not None:
            self.project_id = project_id
            self.access_token = access_token
            self.api_domain = api_domain

        else:
            # Try to get the credentials form the configuration file
            self.project_id, self.access_token, self.api_domain = parse_config_file()

            if self.project_id is None or self.access_token is None or self.api_domain is None:
                # Try to get the credentials form the environment variables
                self.project_id, self.access_token, self.api_domain = get_config_from_env()

        if self.access_token is None or self.project_id is None:
            raise ValueError('Access token, project id and API endpoint domain'
                             ' need to be set.')

    def _set_url_opener(self):
        # We disable the logging of the requests module to avoid some infinite
        # recursion errors that might appear.
        requests_log = logging.getLogger("requests")
        requests_log.setLevel(logging.CRITICAL)

        self.session = requests.Session()
        self.session.auth = ('x', self.access_token)
        self.session.headers.update({'Content-Encoding': 'gzip'})

    def usesTime(self):
        return False

    def _compress(self, input_str):
        """
        Compress the log message in order to send less bytes to the wire.
        """
        compressed_bits = cStringIO.StringIO()
        
        f = gzip.GzipFile(fileobj=compressed_bits, mode='wb')
        f.write(input_str)
        f.close()
        
        return compressed_bits.getvalue()

    def emit(self, record):
        
        if self._auth_failed:
            # Don't send anything else once a 401 was returned
            return
        
        try:
            response = self._send_to_splunk(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            # All errors end here.
            self.handleError(record)
        else:
            if response.status_code == 401:
                self._auth_failed = True

    def _send_to_splunk(self, record):
        # http://docs.splunk.com/Documentation/Storm/latest/User/Sourcesandsourcetypes
        sourcetype = 'json_no_timestamp'
        
        host = socket.gethostname()
        
        event_dict = {'data': self.format(record),
                      'level': record.levelname,
                      'module': record.module,
                      'line': record.lineno}
        event = json.dumps(event_dict)
        event = self._compress(event)
        
        params = {'index': self.project_id,
                  'sourcetype': sourcetype,
                  'host': host}

        url = '%s?%s' % (self.url, urllib.urlencode(params))
        return self.session.post(url, data=event)

