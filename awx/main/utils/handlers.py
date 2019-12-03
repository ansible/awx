# Copyright (c) 2017 Ansible by Red Hat
# All Rights Reserved.

# Python
import logging
import json
import requests
import time
import threading
import socket
import select
from urllib import parse as urlparse
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import RequestException

# Django
from django.conf import settings

# requests futures, a dependency used by these handlers
from requests_futures.sessions import FuturesSession

# AWX
from awx.main.utils.formatters import LogstashFormatter


__all__ = ['BaseHTTPSHandler', 'TCPHandler', 'UDPHandler',
           'AWXProxyHandler']


logger = logging.getLogger('awx.main.utils.handlers')


# Translation of parameter names to names in Django settings
# logging settings category, only those related to handler / log emission
PARAM_NAMES = {
    'host': 'LOG_AGGREGATOR_HOST',
    'port': 'LOG_AGGREGATOR_PORT',
    'message_type': 'LOG_AGGREGATOR_TYPE',
    'username': 'LOG_AGGREGATOR_USERNAME',
    'password': 'LOG_AGGREGATOR_PASSWORD',
    'indv_facts': 'LOG_AGGREGATOR_INDIVIDUAL_FACTS',
    'tcp_timeout': 'LOG_AGGREGATOR_TCP_TIMEOUT',
    'verify_cert': 'LOG_AGGREGATOR_VERIFY_CERT',
    'protocol': 'LOG_AGGREGATOR_PROTOCOL'
}


def unused_callback(sess, resp):
    pass


class LoggingConnectivityException(Exception):
    pass


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


class SocketResult:
    '''
    A class to be the return type of methods that send data over a socket
    allows object to be used in the same way as a request futures object
    '''
    def __init__(self, ok, reason=None):
        self.ok = ok
        self.reason = reason

    def result(self):
        return self


class BaseHandler(logging.Handler):
    def __init__(self, host=None, port=None, indv_facts=None, **kwargs):
        super(BaseHandler, self).__init__()
        self.host = host
        self.port = port
        self.indv_facts = indv_facts

    def _send(self, payload):
        """Actually send message to log aggregator.
        """
        return payload

    def _format_and_send_record(self, record):
        if self.indv_facts:
            return [self._send(json.loads(self.format(record)))]
        return [self._send(self.format(record))]

    def emit(self, record):
        """
            Emit a log record.  Returns a list of zero or more
            implementation-specific objects for tests.
        """
        try:
            return self._format_and_send_record(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
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
    '''
    Originally derived from python-logstash library
    Non-blocking request accomplished by FuturesSession, similar
    to the loggly-python-handler library
    '''
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

    def __init__(self, fqdn=False, message_type=None, username=None, password=None,
                 tcp_timeout=5, verify_cert=True, **kwargs):
        self.fqdn = fqdn
        self.message_type = message_type
        self.username = username
        self.password = password
        self.tcp_timeout = tcp_timeout
        self.verify_cert = verify_cert
        super(BaseHTTPSHandler, self).__init__(**kwargs)
        self.session = FuturesSession(executor=VerboseThreadPoolExecutor(
            max_workers=2  # this is the default used by requests_futures
        ))
        self._add_auth_information()

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
        return self.session.post(self._get_host(scheme='https'),
                                 **self._get_post_kwargs(payload))


def _encode_payload_for_socket(payload):
    encoded_payload = payload
    if isinstance(encoded_payload, dict):
        encoded_payload = json.dumps(encoded_payload, ensure_ascii=False)
    if isinstance(encoded_payload, str):
        encoded_payload = encoded_payload.encode('utf-8')
    return encoded_payload


class TCPHandler(BaseHandler):
    def __init__(self, tcp_timeout=5, **kwargs):
        self.tcp_timeout = tcp_timeout
        super(TCPHandler, self).__init__(**kwargs)

    def _send(self, payload):
        payload = _encode_payload_for_socket(payload)
        sok = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sok.connect((self._get_host(hostname_only=True), self.port or 0))
            sok.setblocking(0)
            _, ready_to_send, _ = select.select([], [sok], [], float(self.tcp_timeout))
            if len(ready_to_send) == 0:
                ret = SocketResult(False, "Socket currently busy, failed to send message")
                logger.warning(ret.reason)
            else:
                sok.send(payload)
                ret = SocketResult(True)  # success!
        except Exception as e:
            ret = SocketResult(False, "Error sending message from %s: %s" %
                               (TCPHandler.__name__,
                                ' '.join(str(arg) for arg in e.args)))
            logger.exception(ret.reason)
        finally:
            sok.close()
        return ret


class UDPHandler(BaseHandler):
    message = "Cannot determine if UDP messages are received."

    def __init__(self, **kwargs):
        super(UDPHandler, self).__init__(**kwargs)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _send(self, payload):
        payload = _encode_payload_for_socket(payload)
        self.socket.sendto(payload, (self._get_host(hostname_only=True), self.port or 0))
        return SocketResult(True, reason=self.message)


class AWXNullHandler(logging.NullHandler):
    '''
    Only additional this does is accept arbitrary __init__ params because
    the proxy handler does not (yet) work with arbitrary handler classes
    '''
    def __init__(self, *args, **kwargs):
        super(AWXNullHandler, self).__init__()


HANDLER_MAPPING = {
    'https': BaseHTTPSHandler,
    'tcp': TCPHandler,
    'udp': UDPHandler,
}


class AWXProxyHandler(logging.Handler):
    '''
    Handler specific to the AWX external logging feature

    Will dynamically create a handler specific to the configured
    protocol, and will create a new one automatically on setting change

    Managing parameters:
    All parameters will get their value from settings as a default
    if the parameter was either provided on init, or set manually,
    this value will take precedence.
    Parameters match same parameters in the actualized handler classes.
    '''

    thread_local = threading.local()
    _auditor = None

    def __init__(self, **kwargs):
        # TODO: process 'level' kwarg
        super(AWXProxyHandler, self).__init__(**kwargs)
        self._handler = None
        self._old_kwargs = {}

    @property
    def auditor(self):
        if not self._auditor:
            self._auditor = logging.handlers.RotatingFileHandler(
                filename='/var/log/tower/external.log',
                maxBytes=1024 * 1024 * 50, # 50 MB
                backupCount=5,
            )

            class WritableLogstashFormatter(LogstashFormatter):
                @classmethod
                def serialize(cls, message):
                    return json.dumps(message)

            self._auditor.setFormatter(WritableLogstashFormatter())
        return self._auditor

    def get_handler_class(self, protocol):
        return HANDLER_MAPPING.get(protocol, AWXNullHandler)

    def get_handler(self, custom_settings=None, force_create=False):
        new_kwargs = {}
        use_settings = custom_settings or settings
        for field_name, setting_name in PARAM_NAMES.items():
            val = getattr(use_settings, setting_name, None)
            if val is None:
                continue
            new_kwargs[field_name] = val
        if new_kwargs == self._old_kwargs and self._handler and (not force_create):
            # avoids re-creating session objects, and other such things
            return self._handler
        self._old_kwargs = new_kwargs.copy()
        # TODO: remove any kwargs no applicable to that particular handler
        protocol = new_kwargs.pop('protocol', None)
        HandlerClass = self.get_handler_class(protocol)
        # cleanup old handler and make new one
        if self._handler:
            self._handler.close()
        logger.debug('Creating external log handler due to startup or settings change.')
        self._handler = HandlerClass(**new_kwargs)
        if self.formatter:
            # self.format(record) is called inside of emit method
            # so not safe to assume this can be handled within self
            self._handler.setFormatter(self.formatter)
        return self._handler

    def emit(self, record):
        if AWXProxyHandler.thread_local.enabled:
            actual_handler = self.get_handler()
            if settings.LOG_AGGREGATOR_AUDIT:
                self.auditor.setLevel(settings.LOG_AGGREGATOR_LEVEL)
                self.auditor.emit(record)
            return actual_handler.emit(record)

    def perform_test(self, custom_settings):
        """
        Tests logging connectivity for given settings module.
        @raises LoggingConnectivityException
        """
        handler = self.get_handler(custom_settings=custom_settings, force_create=True)
        handler.setFormatter(LogstashFormatter())
        logger = logging.getLogger(__file__)
        fn, lno, func, _ = logger.findCaller()
        record = logger.makeRecord('awx', 10, fn, lno,
                                   'AWX Connection Test', tuple(),
                                   None, func)
        futures = handler.emit(record)
        for future in futures:
            try:
                resp = future.result()
                if not resp.ok:
                    if isinstance(resp, SocketResult):
                        raise LoggingConnectivityException(
                            'Socket error: {}'.format(resp.reason or '')
                        )
                    else:
                        raise LoggingConnectivityException(
                            ': '.join([str(resp.status_code), resp.reason or ''])
                        )
            except RequestException as e:
                raise LoggingConnectivityException(str(e))

    @classmethod
    def disable(cls):
        cls.thread_local.enabled = False


AWXProxyHandler.thread_local.enabled = True


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
