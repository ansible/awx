# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

from logstash.formatter import LogstashFormatterVersion1
from django.conf import settings
from copy import copy
import json
import time


class LogstashFormatter(LogstashFormatterVersion1):
    def __init__(self, **kwargs):
        ret = super(LogstashFormatter, self).__init__(**kwargs)
        self.host_id = settings.CLUSTER_HOST_ID
        return ret

    def reformat_data_for_log(self, raw_data, kind=None):
        '''
        Process dictionaries from various contexts (job events, activity stream
        changes, etc.) to give meaningful information
        Output a dictionary which will be passed in logstash or syslog format
        to the logging receiver
        '''
        if kind == 'activity_stream':
            return raw_data
        rename_fields = set((
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'id', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName', 'extra',
            'auth_token', 'tags', 'host', 'host_id', 'level', 'port', 'uuid'))
        if kind == 'system_tracking':
            data = copy(raw_data['facts_data'])
        elif kind == 'job_events':
            data = copy(raw_data['event_model_data'])
        else:
            data = copy(raw_data)
        if isinstance(data, basestring):
            data = json.loads(data)
        skip_fields = ('res', 'password', 'event_data', 'stdout')
        data_for_log = {}

        def index_by_name(alist):
            """Takes a list of dictionaries with `name` as a key in each dict
            and returns a dictionary indexed by those names"""
            adict = {}
            for item in alist:
                subdict = copy(item)
                if 'name' in subdict:
                    name = subdict.get('name', None)
                elif 'path' in subdict:
                    name = subdict.get('path', None)
                if name:
                    # Logstash v2 can not accept '.' in a name
                    name = name.replace('.', '_')
                    adict[name] = subdict
            return adict

        if kind == 'job_events':
            data.update(data.get('event_data', {}))
            for fd in data:
                if fd in skip_fields:
                    continue
                key = fd
                if fd in rename_fields:
                    key = 'event_%s' % fd
                val = data[fd]
                if key.endswith('created'):
                    time_float = time.mktime(data[fd].timetuple())
                    val = self.format_timestamp(time_float)
                data_for_log[key] = val
        elif kind == 'system_tracking':
            module_name = raw_data['module_name']
            if module_name in ['services', 'packages', 'files']:
                data_for_log[module_name] = index_by_name(data)
            elif module_name == 'ansible':
                data_for_log['ansible'] = data
                # Remove sub-keys with data type conflicts in elastic search
                data_for_log['ansible'].pop('ansible_python_version', None)
                data_for_log['ansible']['ansible_python'].pop('version_info', None)
            else:
                data_for_log['facts'] = data
            data_for_log['module_name'] = module_name
        elif kind == 'performance':
            return raw_data
        return data_for_log

    def get_extra_fields(self, record):
        fields = super(LogstashFormatter, self).get_extra_fields(record)
        if record.name.startswith('awx.analytics'):
            log_kind = record.name[len('awx.analytics.'):]
            fields = self.reformat_data_for_log(fields, kind=log_kind)
        return fields

    def format(self, record):
        message = {
            # Fields not included, but exist in related logs
            # 'path': record.pathname
            # '@version': '1', # from python-logstash
            # 'tags': self.tags,
            '@timestamp': self.format_timestamp(record.created),
            'message': record.getMessage(),
            'host': self.host,
            'type': self.message_type,
            'tower_uuid': getattr(settings, 'LOG_TOWER_UUID', None),

            # Extra Fields
            'level': record.levelname,
            'logger_name': record.name,
            'cluster_host_id': self.host_id
        }

        # Add extra fields
        message.update(self.get_extra_fields(record))

        # If exception, add debug info
        if record.exc_info:
            message.update(self.get_debug_fields(record))

        return self.serialize(message)
