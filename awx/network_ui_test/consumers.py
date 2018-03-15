# Copyright (c) 2018 Red Hat, Inc
# In consumers.py
from channels import Group, Channel
from channels.sessions import channel_session
from awx.network_ui.models import Topology, Client
from awx.network_ui.models import TopologyInventory
from awx.network_ui_test.models import FSMTrace, EventTrace, Coverage, TopologySnapshot
from awx.network_ui_test.models import TestCase, TestResult, CodeUnderTest, Result
import urlparse
import logging
from django.utils.dateparse import parse_datetime


from pprint import pformat

import json
# Connected to websocket.connect

HISTORY_MESSAGE_IGNORE_TYPES = ['DeviceSelected',
                                'DeviceUnSelected',
                                'LinkSelected',
                                'LinkUnSelected',
                                'MouseEvent',
                                'MouseWheelEvent',
                                'KeyEvent']


logger = logging.getLogger("awx.network_ui_test.consumers")


class NetworkUIException(Exception):

    pass


def parse_inventory_id(data):
    inventory_id = data.get('inventory_id', ['null'])
    try:
        inventory_id = int(inventory_id[0])
    except ValueError:
        inventory_id = None
    if not inventory_id:
        inventory_id = None
    return inventory_id

# TestPersistence


class _TestPersistence(object):

    def handle(self, message):
        topology_id = message.get('topology')
        assert topology_id is not None, "No topology_id"
        client_id = message.get('client')
        assert client_id is not None, "No client_id"
        data = json.loads(message['text'])
        if isinstance(data[1], list):
            logger.error("Message has no sender")
            return
        if isinstance(data[1], dict) and client_id != data[1].get('sender'):
            logger.error("client_id mismatch expected: %s actual %s", client_id, data[1].get('sender'))
            logger.error(pformat(data))
            return
        message_type = data[0]
        message_value = data[1]
        handler = self.get_handler(message_type)
        if handler is not None:
            try:
                handler(message_value, topology_id, client_id)
            except NetworkUIException, e:
                Group("client-%s" % client_id).send({"text": json.dumps(["Error", str(e)])})
                raise
            except Exception, e:
                Group("client-%s" % client_id).send({"text": json.dumps(["Error", "Server Error"])})
                raise
            except BaseException, e:
                Group("client-%s" % client_id).send({"text": json.dumps(["Error", "Server Error"])})
                raise
        else:
            logger.warning("Unsupported message %s: no handler", message_type)

    def get_handler(self, message_type):
        return getattr(self, "on{0}".format(message_type), None)

    def onMultipleMessage(self, message_value, topology_id, client_id):
        for message in message_value['messages']:
            handler = self.get_handler(message['msg_type'])
            if handler is not None:
                handler(message, topology_id, client_id)
            else:
                logger.warning("Unsupported message %s", message['msg_type'])

    def onCoverageRequest(self, coverage, topology_id, client_id):
        pass

    def onTestResult(self, test_result, topology_id, client_id):
        xyz, _, rest = test_result['code_under_test'].partition('-')
        commits_since, _, commit_hash = rest.partition('-')
        commit_hash = commit_hash.strip('g')

        x, y, z = [int(i) for i in xyz.split('.')]

        code_under_test, _ = CodeUnderTest.objects.get_or_create(version_x=x,
                                                                 version_y=y,
                                                                 version_z=z,
                                                                 commits_since=int(commits_since),
                                                                 commit_hash=commit_hash)

        logger.error("TR: %s", test_result)
        tr = TestResult(id=test_result['id'],
                        result_id=Result.objects.get(name=test_result['result']).pk,
                        test_case_id=TestCase.objects.get(name=test_result['name']).pk,
                        code_under_test_id=code_under_test.pk,
                        client_id=client_id,
                        time=parse_datetime(test_result['date']))
        tr.save()


    def onCoverage(self, coverage, topology_id, client_id):
        Coverage(test_result_id=TestResult.objects.get(id=coverage['result_id'], client_id=client_id).pk,
                 coverage_data=json.dumps(coverage['coverage'])).save()

    def onStartRecording(self, recording, topology_id, client_id):
        pass

    def onStopRecording(self, recording, topology_id, client_id):
        pass

    def write_event(self, event, topology_id, client_id):
        if event.get('save', True):
            EventTrace(trace_session_id=event['trace_id'],
                       event_data=json.dumps(event),
                       message_id=event['message_id'],
                       client_id=client_id).save()

    onViewPort = write_event
    onMouseEvent = write_event
    onTouchEvent = write_event
    onMouseWheelEvent = write_event
    onKeyEvent = write_event

    def onFSMTrace(self, message_value, diagram_id, client_id):
        FSMTrace(trace_session_id=message_value['trace_id'],
                 fsm_name=message_value['fsm_name'],
                 from_state=message_value['from_state'],
                 to_state=message_value['to_state'],
                 order=message_value['order'],
                 client_id=client_id,
                 message_type=message_value['recv_message_type'] or "none").save()

    def onSnapshot(self, snapshot, topology_id, client_id):
        TopologySnapshot(trace_session_id=snapshot['trace_id'],
                         snapshot_data=json.dumps(snapshot),
                         order=snapshot['order'],
                         client_id=client_id,
                         topology_id=topology_id).save()


test_persistence = _TestPersistence()


# UI Channel Events

@channel_session
def ws_connect(message):
    # Accept connection
    data = urlparse.parse_qs(message.content['query_string'])
    inventory_id = parse_inventory_id(data)
    topology_ids = list(TopologyInventory.objects.filter(inventory_id=inventory_id).values_list('topology_id', flat=True))
    topology_id = 0
    if len(topology_ids) > 0:
        topology_id = topology_ids[0]
    if topology_id:
        topology = Topology.objects.get(topology_id=topology_id)
    else:
        topology = Topology(name="topology", scale=1.0, panX=0, panY=0)
        topology.save()
        TopologyInventory(inventory_id=inventory_id, topology_id=topology.topology_id).save()
    topology_id = topology.topology_id
    message.channel_session['topology_id'] = topology_id
    client = Client()
    client.save()
    message.channel_session['client_id'] = client.pk
    Group("client-%s" % client.pk).add(message.reply_channel)
    message.reply_channel.send({"text": json.dumps(["id", client.pk])})
    send_tests(message.reply_channel)


def send_tests(channel):
    for name, test_case_data in TestCase.objects.all().values_list('name', 'test_case_data'):
        channel.send({"text": json.dumps(["TestCase", [name, json.loads(test_case_data)]])})


@channel_session
def ws_message(message):
    Channel('test_persistence').send({"text": message['text'],
                                      "topology": message.channel_session['topology_id'],
                                      "client": message.channel_session['client_id']})


@channel_session
def ws_disconnect(message):
    pass


