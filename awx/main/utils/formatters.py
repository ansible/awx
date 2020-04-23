# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

from copy import copy
import json
import logging
import traceback
import socket
from datetime import datetime

from dateutil.tz import tzutc
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings


class TimeFormatter(logging.Formatter):
    '''
    Custom log formatter used for inventory imports
    '''
    def format(self, record):
        record.relativeSeconds = record.relativeCreated / 1000.0
        return logging.Formatter.format(self, record)


class LogstashFormatterBase(logging.Formatter):
    """Base class taken from python-logstash=0.4.6
    modified here since that version

    For compliance purposes, this was the license at the point of divergence:

    The MIT License (MIT)

    Copyright (c) 2013, Volodymyr Klochan

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
    """

    def __init__(self, message_type='Logstash', fqdn=False):
        self.message_type = message_type

        if fqdn:
            self.host = socket.getfqdn()
        else:
            self.host = socket.gethostname()

    def get_extra_fields(self, record):
        # The list contains all the attributes listed in
        # http://docs.python.org/library/logging.html#logrecord-attributes
        skip_list = (
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName', 'extra')

        easy_types = (str, bool, dict, float, int, list, type(None))

        fields = {}

        for key, value in record.__dict__.items():
            if key not in skip_list:
                if isinstance(value, easy_types):
                    fields[key] = value
                else:
                    fields[key] = repr(value)

        return fields

    def get_debug_fields(self, record):
        return {
            'stack_trace': self.format_exception(record.exc_info),
            'lineno': record.lineno,
            'process': record.process,
            'thread_name': record.threadName,
            'funcName': record.funcName,
            'processName': record.processName,
        }

    @classmethod
    def format_exception(cls, exc_info):
        return ''.join(traceback.format_exception(*exc_info)) if exc_info else ''

    @classmethod
    def serialize(cls, message):
        return json.dumps(message, cls=DjangoJSONEncoder) + '\n'


class LogstashFormatter(LogstashFormatterBase):

    def __init__(self, *args, **kwargs):
        self.cluster_host_id = settings.CLUSTER_HOST_ID
        self.tower_uuid = None
        uuid = (
            getattr(settings, 'LOG_AGGREGATOR_TOWER_UUID', None) or
            getattr(settings, 'INSTALL_UUID', None)
        )
        if uuid:
            self.tower_uuid = uuid
        super(LogstashFormatter, self).__init__(*args, **kwargs)

    def reformat_data_for_log(self, raw_data, kind=None):
        '''
        Process dictionaries from various contexts (job events, activity stream
        changes, etc.) to give meaningful information
        Output a dictionary which will be passed in logstash or syslog format
        to the logging receiver
        '''
        if kind == 'activity_stream':
            try:
                raw_data['changes'] = json.loads(raw_data.get('changes', '{}'))
            except Exception:
                pass  # best effort here, if it's not valid JSON, then meh
            return raw_data
        elif kind == 'system_tracking':
            data = copy(raw_data.get('ansible_facts', {}))
        else:
            data = copy(raw_data)
        if isinstance(data, str):
            data = json.loads(data)
        data_for_log = {}

        if kind == 'job_events' and raw_data.get('python_objects', {}).get('job_event'):
            job_event = raw_data['python_objects']['job_event']
            for field_object in job_event._meta.fields:

                if not field_object.__class__ or not field_object.__class__.__name__:
                    field_class_name = ''
                else:
                    field_class_name = field_object.__class__.__name__
                if field_class_name in ['ManyToOneRel', 'ManyToManyField']:
                    continue

                fd = field_object.name
                key = fd
                if field_class_name == 'ForeignKey':
                    fd = '{}_id'.format(field_object.name)

                try:
                    data_for_log[key] = getattr(job_event, fd)
                except Exception as e:
                    data_for_log[key] = 'Exception `{}` producing field'.format(e)

            data_for_log['event_display'] = job_event.get_event_display2()
            if hasattr(job_event, 'workflow_job_id'):
                data_for_log['workflow_job_id'] = job_event.workflow_job_id

        elif kind == 'system_tracking':
            data.pop('ansible_python_version', None)
            if 'ansible_python' in data:
                data['ansible_python'].pop('version_info', None)

            data_for_log['ansible_facts'] = data
            data_for_log['ansible_facts_modified'] = raw_data.get('ansible_facts_modified')
            data_for_log['inventory_id'] = raw_data.get('inventory_id')
            data_for_log['host_name'] = raw_data.get('host_name')
            data_for_log['job_id'] = raw_data.get('job_id')
        elif kind == 'performance':
            def convert_to_type(t, val):
                if t is float:
                    val = val[:-1] if val.endswith('s') else val
                    try:
                        return float(val)
                    except ValueError:
                        return val
                elif t is int:
                    try:
                        return int(val)
                    except ValueError:
                        return val
                elif t is str:
                    return val

            request = raw_data['python_objects']['request']
            response = raw_data['python_objects']['response']

            # Note: All of the below keys may not be in the response "dict"
            # For example, X-API-Query-Time and X-API-Query-Count will only
            # exist if SQL_DEBUG is turned on in settings.
            headers = [
                (float, 'X-API-Time'),  # may end with an 's' "0.33s"
                (float, 'X-API-Total-Time'),
                (int, 'X-API-Query-Count'),
                (float, 'X-API-Query-Time'), # may also end with an 's'
                (str, 'X-API-Node'),
            ]
            data_for_log['x_api'] = {k: convert_to_type(t, response[k]) for (t, k) in headers if k in response}

            data_for_log['request'] = {
                'method': request.method,
                'path': request.path,
                'path_info': request.path_info,
                'query_string': request.META['QUERY_STRING'],
            }

            if hasattr(request, 'data'):
                data_for_log['request']['data'] = request.data

        return data_for_log

    def get_extra_fields(self, record):
        fields = super(LogstashFormatter, self).get_extra_fields(record)
        if record.name.startswith('awx.analytics'):
            log_kind = record.name[len('awx.analytics.'):]
            fields = self.reformat_data_for_log(fields, kind=log_kind)
        # General AWX metadata
        fields['cluster_host_id'] = self.cluster_host_id
        fields['tower_uuid'] = self.tower_uuid
        return fields

    def format(self, record):
        stamp = datetime.utcfromtimestamp(record.created)
        stamp = stamp.replace(tzinfo=tzutc())
        message = {
            # Field not included, but exist in related logs
            # 'path': record.pathname
            '@timestamp': stamp,
            'message': record.getMessage(),
            'host': self.host,

            # Extra Fields
            'level': record.levelname,
            'logger_name': record.name,
        }

        # Add extra fields
        message.update(self.get_extra_fields(record))

        # If exception, add debug info
        if record.exc_info:
            message.update(self.get_debug_fields(record))

        if settings.LOG_AGGREGATOR_TYPE == 'splunk':
            # splunk messages must have a top level "event" key
            message = {'event': message}
        return self.serialize(message)
