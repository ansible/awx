# Copyright (c) 2017 Ansible Tower by Red Hat
# All Rights Reserved.

from logstash.formatter import LogstashFormatterVersion1
from django.conf import settings


# # Loggly example
# 'json': {
#     'format': '{ 
#     "loggerName":"%(name)s", 
#     "asciTime":"%(asctime)s", 
#     "fileName":"%(filename)s", 
#     "logRecordCreationTime":"%(created)f", 
#     "functionName":"%(funcName)s", 
#     "levelNo":"%(levelno)s", 
#     "lineNo":"%(lineno)d", 
#     "time":"%(msecs)d", 
#     "levelName":"%(levelname)s", 
#     "message":"%(message)s"}',
# },

class LogstashFormatter(LogstashFormatterVersion1):
    def __init__(self, **kwargs):
        ret = super(LogstashFormatter, self).__init__(**kwargs)
        self.host_id = settings.CLUSTER_HOST_ID
        return ret

    def get_extra_fields(self, record):
        fields = super(LogstashFormatter, self).get_extra_fields(record)
        fields['cluster_host_id'] = self.host_id
        return fields

    def format(self, record):
        # Create message dict
        # message = record.getMessage()
        # print ' message ' + str(message)
        message = {
            '@timestamp': self.format_timestamp(record.created),
            '@version': '1',
            'message': record.getMessage(),
            'host': self.host,
            'path': record.pathname,
            'tags': self.tags,
            'type': self.message_type,

            # Extra Fields
            'level': record.levelname,
            'logger_name': record.name,
        }

        # Add extra fields
        message.update(self.get_extra_fields(record))

        # If exception, add debug info
        if record.exc_info:
            message.update(self.get_debug_fields(record))

        return self.serialize(message)
