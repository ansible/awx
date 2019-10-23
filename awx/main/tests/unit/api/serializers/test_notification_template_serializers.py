# -*- coding: utf-8 -*-
import pytest
from rest_framework.serializers import ValidationError

# AWX
from awx.api.serializers import NotificationTemplateSerializer


class StubNotificationTemplate():
    notification_type = 'email'


class TestNotificationTemplateSerializer():

    @pytest.mark.parametrize('valid_messages',
                             [None,
                              {'started': None},
                              {'started': {'message': None}},
                              {'started': {'message': 'valid'}},
                              {'started': {'body': 'valid'}},
                              {'started': {'message': 'valid', 'body': 'valid'}},
                              {'started': None, 'success': None, 'error': None},
                              {'started': {'message': None, 'body': None},
                               'success': {'message': None, 'body': None},
                               'error': {'message': None, 'body': None}},
                              {'started': {'message': '{{ job.id }}', 'body': '{{ job.status }}'},
                               'success': {'message': None, 'body': '{{ job_friendly_name }}'},
                               'error': {'message': '{{ url }}', 'body': None}},
                              {'started': {'body': '{{ job_metadata }}'}},
                              {'started': {'body': '{{ job.summary_fields.inventory.total_hosts }}'}},
                              {'started': {'body': u'Iñtërnâtiônàlizætiøn'}}
                              ])
    def test_valid_messages(self, valid_messages):
        serializer = NotificationTemplateSerializer()
        serializer.instance = StubNotificationTemplate()
        serializer.validate_messages(valid_messages)

    @pytest.mark.parametrize('invalid_messages',
                             [1,
                              [],
                              '',
                              {'invalid_event': ''},
                              {'started': 'should_be_dict'},
                              {'started': {'bad_message_type': ''}},
                              {'started': {'message': 1}},
                              {'started': {'message': []}},
                              {'started': {'message': {}}},
                              {'started': {'message': '{{ unclosed_braces'}},
                              {'started': {'message': '{{ undefined }}'}},
                              {'started': {'message': '{{ job.undefined }}'}},
                              {'started': {'message': '{{ job.id | bad_filter }}'}},
                              {'started': {'message': '{{ job.__class__ }}'}},
                              {'started': {'message': 'Newlines \n not allowed\n'}},
                              ])
    def test_invalid__messages(self, invalid_messages):
        serializer = NotificationTemplateSerializer()
        serializer.instance = StubNotificationTemplate()
        with pytest.raises(ValidationError):
            serializer.validate_messages(invalid_messages)
