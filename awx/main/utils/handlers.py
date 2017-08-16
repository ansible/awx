# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Python
import logging
import json
import requests
import time
import urlparse
import socket
import select
import six
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import RequestException

# loggly
import traceback

from django.conf import settings
from requests_futures.sessions import FuturesSession

# AWX
from awx.main.utils.formatters import LogstashFormatter


__all__ = ['HTTPSNullHandler', 'BaseHTTPSHandler', 'TCPHandler', 'UDPHandler',
           'configure_external_logger']


logger = logging.getLogger('awx.main.utils.handlers')

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
    'tcp_timeout': 'LOG_AGGREGATOR_TCP_TIMEOUT',
    'verify_cert': 'LOG_AGGREGATOR_VERIFY_CERT',
    'lvl': 'LOG_AGGREGATOR_LEVEL',
}


def unused_callback(sess, resp):
    pass


class LoggingConnectivityException(Exception):
    pass


class HTTPSNullHandler(logging.NullHandler):
    "Placeholder null handler to allow loading without database access"

    def __init__(self, *args, **kwargs):
        return super(HTTPSNullHandler, self).__init__()


class VerboseThreadPoolExecutor(ThreadPoolExecutor):

    last_log_emit = 0

    def submit(self, func, *args, **kwargs):
        def _wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                # If an exception occurs in a concurrent thread worker (like
                # a ConnectionError or a read timeout), periodically log
                # that failure.
                #
                # This approach isn't really thread-safe, so we could
                # potentially log once per thread every 10 seconds, but it
                # beats logging *every* failed HTTP request in a scenario where
                # you've typo'd your log aggregator hostname.
                now = time.time()
                if now - self.last_log_emit > 10:
                    logger.exception('failed to emit log to external aggregator')
                    self.last_log_emit = now
                raise
        return super(VerboseThreadPoolExecutor, self).submit(_wrapped, *args,
                                                             **kwargs)


LEVEL_MAPPING = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


class BaseHandler(logging.Handler):
    def __init__(self, **kwargs):
        super(BaseHandler, self).__init__()
        for fd in PARAM_NAMES:
            setattr(self, fd, kwargs.get(fd, None))

    @classmethod
    def from_django_settings(cls, settings, *args, **kwargs):
        for param, django_setting_name in PARAM_NAMES.items():
            kwargs[param] = getattr(settings, django_setting_name, None)
        return cls(*args, **kwargs)

    def get_full_message(self, record):
        if record.exc_info:
            return '\n'.join(traceback.format_exception(*record.exc_info))
        else:
            return record.getMessage()

    def _send(self, payload):
        """Actually send message to log aggregator.
        """
        return payload

    def _format_and_send_record(self, record):
        if self.indv_facts:
            return [self._send(json.loads(self.format(record)))]
        return [self._send(self.format(record))]

    def _skip_log(self, logger_name):
        if self.host == '' or (not self.enabled_flag):
            return True
        # Don't send handler-related records.
        if logger_name == logger.name:
            return True
        # AWX log emission is only turned off by enablement setting
        if not logger_name.startswith('awx.analytics'):
            return False
        return self.enabled_loggers is None or logger_name[len('awx.analytics.'):] not in self.enabled_loggers

    def emit(self, record):
        """
            Emit a log record.  Returns a list of zero or more
            implementation-specific objects for tests.
        """
        if not record.name.startswith('awx.analytics') and record.levelno < LEVEL_MAPPING[self.lvl]:
            return []
        if self._skip_log(record.name):
            return []
        try:
            return self._format_and_send_record(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def _get_host(self, scheme='', hostname_only=False):
        """Return the host name of log aggregator.
        """
        host = self.host or ''
        # urlparse requires '//' to be provided if scheme is not specified
        original_parsed = urlparse.urlsplit(host)
        if (not original_parsed.scheme and not host.startswith('//')) or original_parsed.hostname is None:
            host = '%s://%s' % (scheme, host) if scheme else '//%s' % host
        parsed = urlparse.urlsplit(host)

        if hostname_only:
            return parsed.hostname

        try:
            port = parsed.port or self.port
        except ValueError:
            port = self.port
        netloc = parsed.netloc if port is None else '%s:%s' % (parsed.hostname, port)

        url_components = list(parsed)
        url_components[1] = netloc
        ret = urlparse.urlunsplit(url_components)
        return ret.lstrip('/')


class BaseHTTPSHandler(BaseHandler):
    def _add_auth_information(self):
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

    def __init__(self, fqdn=False, **kwargs):
        self.fqdn = fqdn
        super(BaseHTTPSHandler, self).__init__(**kwargs)
        self.session = FuturesSession(executor=VerboseThreadPoolExecutor(
            max_workers=2  # this is the default used by requests_futures
        ))
        self._add_auth_information()

    @classmethod
    def perform_test(cls, settings):
        """
        Tests logging connectivity for the current logging settings.
        @raises LoggingConnectivityException
        """
        handler = cls.from_django_settings(settings)
        handler.enabled_flag = True
        handler.setFormatter(LogstashFormatter(settings_module=settings))
        logger = logging.getLogger(__file__)
        fn, lno, func = logger.findCaller()
        record = logger.makeRecord('awx', 10, fn, lno,
                                   'AWX Connection Test', tuple(),
                                   None, func)
        futures = handler.emit(record)
        for future in futures:
            try:
                resp = future.result()
                if not resp.ok:
                    raise LoggingConnectivityException(
                        ': '.join([str(resp.status_code), resp.reason or ''])
                    )
            except RequestException as e:
                raise LoggingConnectivityException(str(e))

    def _get_post_kwargs(self, payload_input):
        if self.message_type == 'splunk':
            # Splunk needs data nested under key "event"
            if not isinstance(payload_input, dict):
                payload_input = json.loads(payload_input)
            payload_input = {'event': payload_input}
        if isinstance(payload_input, dict):
            payload_str = json.dumps(payload_input)
        else:
            payload_str = payload_input
        kwargs = dict(data=payload_str, background_callback=unused_callback,
                      timeout=self.tcp_timeout)
        if self.verify_cert is False:
            kwargs['verify'] = False
        return kwargs


    def _send(self, payload):
        """See:
            https://docs.python.org/3/library/concurrent.futures.html#future-objects
            http://pythonhosted.org/futures/
        """
        return self.session.post(self._get_host(scheme='http'),
                                 **self._get_post_kwargs(payload))


def _encode_payload_for_socket(payload):
    encoded_payload = payload
    if isinstance(encoded_payload, dict):
        encoded_payload = json.dumps(encoded_payload, ensure_ascii=False)
    if isinstance(encoded_payload, six.text_type):
        encoded_payload = encoded_payload.encode('utf-8')
    return encoded_payload


class TCPHandler(BaseHandler):
    def _send(self, payload):
        payload = _encode_payload_for_socket(payload)
        sok = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sok.connect((self._get_host(hostname_only=True), self.port or 0))
            sok.setblocking(0)
            _, ready_to_send, _ = select.select([], [sok], [], float(self.tcp_timeout))
            if len(ready_to_send) == 0:
                logger.warning("Socket currently busy, failed to send message")
                sok.close()
                return
            sok.send(payload)
        except Exception as e:
            logger.exception("Error sending message from %s: %s" %
                             (TCPHandler.__name__, e.message))
        sok.close()


class UDPHandler(BaseHandler):
    def __init__(self, **kwargs):
        super(UDPHandler, self).__init__(**kwargs)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _send(self, payload):
        payload = _encode_payload_for_socket(payload)
        return self.socket.sendto(payload, (self._get_host(hostname_only=True), self.port or 0))


HANDLER_MAPPING = {
    'https': BaseHTTPSHandler,
    'tcp': TCPHandler,
    'udp': UDPHandler,
}


ColorHandler = logging.StreamHandler

if settings.COLOR_LOGS is True:
    try:
        from logutils.colorize import ColorizingStreamHandler

        class ColorHandler(ColorizingStreamHandler):

            def format(self, record):
                message = logging.StreamHandler.format(self, record)
                return '\n'.join([
                    self.colorize(line, record)
                    for line in message.splitlines()
                ])

            level_map = {
                logging.DEBUG: (None, 'green', True),
                logging.INFO: (None, None, True),
                logging.WARNING: (None, 'yellow', True),
                logging.ERROR: (None, 'red', True),
                logging.CRITICAL: (None, 'red', True),
            }
    except ImportError:
        # logutils is only used for colored logs in the dev environment
        pass


def _add_or_remove_logger(address, instance):
    specific_logger = logging.getLogger(address)
    for i, handler in enumerate(specific_logger.handlers):
        if isinstance(handler, (HTTPSNullHandler, BaseHTTPSHandler)):
            specific_logger.handlers[i] = instance or HTTPSNullHandler()
            break
    else:
        if instance is not None:
            specific_logger.handlers.append(instance)


def configure_external_logger(settings_module, is_startup=True):
    is_enabled = settings_module.LOG_AGGREGATOR_ENABLED
    if is_startup and (not is_enabled):
        # Pass-through if external logging not being used
        return

    instance = None
    if is_enabled:
        handler_class = HANDLER_MAPPING[settings_module.LOG_AGGREGATOR_PROTOCOL]
        instance = handler_class.from_django_settings(settings_module)

        # Obtain the Formatter class from settings to maintain customizations
        configurator = logging.config.DictConfigurator(settings_module.LOGGING)
        formatter_config = settings_module.LOGGING['formatters']['json'].copy()
        formatter_config['settings_module'] = settings_module
        formatter = configurator.configure_custom(formatter_config)

        instance.setFormatter(formatter)

    awx_logger_instance = instance
    if is_enabled and 'awx' not in settings_module.LOG_AGGREGATOR_LOGGERS:
        awx_logger_instance = None

    _add_or_remove_logger('awx.analytics', instance)
    _add_or_remove_logger('awx', awx_logger_instance)
