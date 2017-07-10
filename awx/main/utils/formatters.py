# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

from logstash.formatter import LogstashFormatterVersion1
from copy import copy
import json
import time
import logging


class TimeFormatter(logging.Formatter):
    '''
    Custom log formatter used for inventory imports
    '''
    def format(self, record):
        record.relativeSeconds = record.relativeCreated / 1000.0
        return logging.Formatter.format(self, record)


class LogstashFormatter(LogstashFormatterVersion1):
    def __init__(self, **kwargs):
        settings_module = kwargs.pop('settings_module', None)
        ret = super(LogstashFormatter, self).__init__(**kwargs)
        if settings_module:
            self.host_id = getattr(settings_module, 'CLUSTER_HOST_ID', None)
            if hasattr(settings_module, 'LOG_AGGREGATOR_TOWER_UUID'):
                self.tower_uuid = settings_module.LOG_AGGREGATOR_TOWER_UUID
            self.message_type = getattr(settings_module, 'LOG_AGGREGATOR_TYPE', 'other')
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
        elif kind == 'system_tracking':
            data = copy(raw_data['ansible_facts'])
        else:
            data = copy(raw_data)
        if isinstance(data, basestring):
            data = json.loads(data)
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

        if kind == 'job_events':
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
                    if fd in ['created', 'modified'] and data_for_log[key] is not None:
                        time_float = time.mktime(data_for_log[key].timetuple())
                        data_for_log[key] = self.format_timestamp(time_float)
                except Exception as e:
                    data_for_log[key] = 'Exception `{}` producing field'.format(e)

            data_for_log['event_display'] = job_event.get_event_display2()

        elif kind == 'system_tracking':
            data.pop('ansible_python_version', None)
            if 'ansible_python' in data:
                data['ansible_python'].pop('version_info', None)

            data_for_log['ansible_facts'] = data
            data_for_log['ansible_facts_modified'] = raw_data['ansible_facts_modified']
            data_for_log['inventory_id'] = raw_data['inventory_id']
            data_for_log['host_name'] = raw_data['host_name']
        elif kind == 'performance':
            request = raw_data['python_objects']['request']
            response = raw_data['python_objects']['response']

            # Note: All of the below keys may not be in the response "dict"
            # For example, X-API-Query-Time and X-API-Query-Count will only
            # exist if SQL_DEBUG is turned on in settings.
            headers = [
                (float, 'X-API-Time'),  # may end with an 's' "0.33s"
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
                'data': request.data,
            }

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

            # Extra Fields
            'level': record.levelname,
            'logger_name': record.name,
        }

        if getattr(self, 'tower_uuid', None):
            message['tower_uuid'] = self.tower_uuid
        if getattr(self, 'host_id', None):
            message['cluster_host_id'] = self.host_id

        # Add extra fields
        message.update(self.get_extra_fields(record))

        # If exception, add debug info
        if record.exc_info:
            message.update(self.get_debug_fields(record))

        return self.serialize(message)
