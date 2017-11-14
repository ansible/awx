# Copyright (c) 2017 Red Hat, Inc
from django.core.management.base import BaseCommand
import unittest
from websocket import create_connection
import json
import yaml
import time as real_time
import requests


class _Time(object):

    def __init__(self, scale=1.0):
        self.scale = scale

    def sleep(self, n):
        real_time.sleep(n * self.scale)


time = _Time()


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--time-scale', dest="time_scale", default=1.0, type=float)
        parser.add_argument('--verbose', dest="verbose", action="store_true", default=False)
        parser.add_argument('-q', '--quiet', dest="quiet", action="store_true", default=False)
        parser.add_argument('-f', '--failfast', dest="failfast", action="store_true", default=False)
        parser.add_argument('-b', '--buffer', dest="buffer", action="store_true", default=False)
        parser.add_argument('suites', nargs="*")

    def handle(self, *args, **options):
        time.scale = options.get('time_scale', 1.0)
        loader = unittest.TestLoader()
        test_suites = [TestUI,
                       TestUIWebSocket,
                       TestUndoPersistence,
                       TestRedoPersistence,
                       TestPersistence,
                       TestViews,
                       TestWorkerWebSocket,
                       TestAnsibleWebSocket,
                       TestInvalidValues]
        if options.get('suites'):
            test_suites = [x for x in test_suites if x.__name__ in options['suites']]
        tests = [loader.loadTestsFromTestCase(x) for x in test_suites]
        unittest.TextTestRunner(failfast=options.get('failfast'),
                                verbosity=0 if options.get('quiet') else 2 if options.get('verbose') else 1,
                                buffer=options.get('buffer')).run(unittest.TestSuite(tests))

        ui = MessageHandler(create_connection("ws://localhost:8001/network_ui/topology?topology_id=143"))
        ui.recv()
        ui.recv()
        ui.send('CoverageRequest')
        ui.close()


class TestViews(unittest.TestCase):

    def test_index(self):
        requests.get("http://localhost:8001/network_ui")


class MessageHandler(object):

    def __init__(self, ws):
        self.ws = ws
        self.client_id = None
        self.topology_id = None
        self.receieved_messages = []
        self.message_id = 0

    def handle_message(self, message):
        message = json.loads(message)
        self.receieved_messages.append(message)
        if message[0] == "id":
            self.client_id = message[1]
        if message[0] == "topology_id":
            self.topology_id = message[1]

    def make_message(self, msg_type, **kwargs):
        kwargs['sender'] = self.client_id
        kwargs['msg_type'] = msg_type
        kwargs['message_id'] = self.message_id
        self.message_id += 1
        return [msg_type, kwargs]

    def send(self, msg_type, **kwargs):
        self.ws.send(json.dumps(self.make_message(msg_type, **kwargs)))

    def send_message(self, message):
        self.ws.send(json.dumps(message))

    def send_multiple(self, messages):
        self.ws.send(json.dumps(['MultipleMessage', dict(sender=self.client_id, messages=messages)]))

    def recv(self):
        msg = self.ws.recv()
        self.handle_message(msg)
        return msg

    def close(self):
        self.ws.close()


class TestWorkerWebSocket(unittest.TestCase):

    def test(self):
        self.worker = MessageHandler(create_connection("ws://localhost:8001/network_ui/worker?topology_id=143"))
        self.ui = MessageHandler(create_connection("ws://localhost:8001/network_ui/tester?topology_id=143"))
        self.ui.recv()
        self.ui.recv()
        self.ui.send("Deploy")
        self.assertTrue(self.worker.recv())
        self.ui.send("Destroy")
        self.assertTrue(self.worker.recv())
        self.worker.send("Hi")

    def tearDown(self):
        self.worker.close()
        self.ui.close()


class TestAnsibleWebSocket(unittest.TestCase):

    def test(self):
        self.ws = MessageHandler(create_connection("ws://localhost:8001/network_ui/ansible?topology_id=143"))
        self.ws.send('Facts', foo=5)

    def tearDown(self):
        self.ws.close()


class TestPersistence(unittest.TestCase):

    def setUp(self):
        self.ws = MessageHandler(create_connection("ws://localhost:8001/network_ui/tester?topology_id=143"))
        self.ws.recv()
        self.ws.recv()

    def tearDown(self):
        self.ws.close()

    def test_DeviceCreate(self):
        self.ws.send('DeviceCreate', name="TestSwitch", x=0, y=500, type="switch", id=100)
        time.sleep(1)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=100)

    def test_DeviceLabelEdit(self):
        self.ws.send('DeviceCreate', name="TestSwitch", x=0, y=500, type="switch", id=100)
        time.sleep(1)
        self.ws.send('DeviceLabelEdit', name="Foo", previous_name="TestSwitch", id=100)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=100)

    def test_DeviceMove(self):
        #self.ws.send('DeviceCreate', name="TestSwitch", x=0, y=500, type="switch", id=100)
        self.ws.send_multiple([
            dict(msg_type='DeviceCreate', name="TestSwitchA", x=100, y=100, type="switch", id=100),
            dict(msg_type='DeviceCreate', name="TestSwitchB", x=900, y=100, type="switch", id=101),
            dict(msg_type='InterfaceCreate', name="swp1", id=1, device_id=100),
            dict(msg_type='InterfaceCreate', name="swp1", id=1, device_id=101),
            dict(msg_type='LinkCreate', id=100, name="A to B", from_device_id=100, to_device_id=101, from_interface_id=1, to_interface_id=1)])
        time.sleep(1)
        for i in xrange(1, 1000):
            time.sleep(0.01)
            self.ws.send('DeviceMove', x=i, y=500, previous_x=i - 1, previous_y=500, id=100)
        time.sleep(1)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=100)

    def test_LinkEdit_InterfaceEdit_LinkDestroy(self):
        self.ws.send_multiple([
            dict(msg_type='DeviceCreate', name="TestSwitchA", x=100, y=100, type="switch", id=100),
            dict(msg_type='DeviceCreate', name="TestSwitchB", x=900, y=100, type="switch", id=101),
            dict(msg_type='InterfaceCreate', name="swp1", id=1, device_id=100),
            dict(msg_type='InterfaceCreate', name="swp1", id=1, device_id=101),
            dict(msg_type='LinkCreate', id=100, name="A to B", from_device_id=100, to_device_id=101, from_interface_id=1, to_interface_id=1)])
        time.sleep(1)
        self.ws.send('InterfaceLabelEdit', id=1, device_id=100, name="swp2", previous_name="swp1")
        time.sleep(1)
        self.ws.send('LinkLabelEdit', id=100, name="B to A", previous_name="A to B")
        time.sleep(1)
        self.ws.send('LinkDestroy', id=100, from_device_id=100, to_device_id=101, from_interface_id=1, to_interface_id=1)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=100)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=101)


class TestUndoPersistence(unittest.TestCase):

    def setUp(self):
        self.ws = MessageHandler(create_connection("ws://localhost:8001/network_ui/tester?topology_id=143"))
        self.ws.recv()
        self.ws.recv()

    def test_unsupported(self):
        self.ws.send("Undo", original_message=['NotSupported', dict(sender=0, message_id=-1)])

    def test_undo(self):
        self.ws.send("Undo", original_message=['Undo', dict(sender=0, message_id=-1)])

    def test_redo(self):
        self.ws.send("Undo", original_message=['Redo', dict(sender=0, message_id=-1)])

    def test_DeviceCreate(self):
        msg = self.ws.make_message('DeviceCreate', name="TestSwitch", x=0, y=500, type="switch", id=100)
        self.ws.send_message(msg)
        self.ws.send("Undo", original_message=msg)

    def test_DeviceDestroy(self):
        msg = self.ws.make_message('DeviceCreate', name="TestSwitch", x=0, y=500, type="switch", id=100)
        self.ws.send_message(msg)
        msg = self.ws.make_message('DeviceDestroy',
                                   previous_name="TestSwitch",
                                   previous_x=0,
                                   previous_y=500,
                                   previous_type="switch",
                                   id=100)
        self.ws.send_message(msg)
        self.ws.send("Undo", original_message=msg)

    def test_DeviceMove(self):
        msg = self.ws.make_message('DeviceCreate', name="TestSwitch", x=0, y=500, type="switch", id=100)
        self.ws.send_message(msg)
        msg = self.ws.make_message('DeviceMove', x=100, y=100, previous_x=0, previous_y=500, id=100)
        self.ws.send_message(msg)
        self.ws.send("Undo", original_message=msg)

    def test_DeviceLabelEdit(self):
        msg = self.ws.make_message('DeviceCreate', name="TestSwitch", x=0, y=500, type="switch", id=100)
        self.ws.send_message(msg)
        msg = self.ws.make_message('DeviceLabelEdit', name="Foo", previous_name="TestSwitch", id=100)
        self.ws.send_message(msg)
        self.ws.send("Undo", original_message=msg)

    def test_DeviceSelected_DeviceUnSelected(self):
        self.ws.send("Undo", original_message=['DeviceSelected', dict(sender=0, message_id=-1)])
        self.ws.send("Undo", original_message=['DeviceUnSelected', dict(sender=0, message_id=-1)])

    def test_Snapshot(self):
        self.ws.send("Undo", original_message=['Snapshot', dict(sender=0, message_id=-1)])

    def tearDown(self):
        self.ws.close()

    def test_LinkEdit_InterfaceEdit_LinkDestroy(self):
        self.ws.send_multiple([
            dict(msg_type='DeviceCreate', name="TestSwitchA", x=100, y=100, type="switch", id=100),
            dict(msg_type='DeviceCreate', name="TestSwitchB", x=900, y=100, type="switch", id=101),
            dict(msg_type='InterfaceCreate', name="swp1", id=1, device_id=100),
            dict(msg_type='InterfaceCreate', name="swp1", id=1, device_id=101)])

        time.sleep(1)

        msg = self.ws.make_message('LinkCreate', id=100, name="A to B", from_device_id=100, to_device_id=101, from_interface_id=1, to_interface_id=1)
        self.ws.send_message(msg)
        self.ws.send('Undo', original_message=msg)
        time.sleep(1)
        self.ws.send('Redo', original_message=msg)
        time.sleep(1)
        msg = self.ws.make_message('LinkDestroy', id=100, name="A to B", from_device_id=100, to_device_id=101, from_interface_id=1, to_interface_id=1)
        time.sleep(1)
        self.ws.send_message(msg)
        self.ws.send('Undo', original_message=msg)
        time.sleep(1)

        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=100)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=101)


class TestRedoPersistence(unittest.TestCase):

    def setUp(self):
        self.ws = MessageHandler(create_connection("ws://localhost:8001/network_ui/tester?topology_id=143"))
        self.ws.recv()
        self.ws.recv()

    def test_unsupported(self):
        self.ws.send("Redo", original_message=['NotSupported', dict(sender=0, message_id=-1)])

    def test_undo(self):
        self.ws.send("Redo", original_message=['Undo', dict(sender=0, message_id=-1)])

    def test_redo(self):
        self.ws.send("Redo", original_message=['Redo', dict(sender=0, message_id=-1)])

    def test_DeviceSelected_DeviceUnSelected(self):
        self.ws.send("Redo", original_message=['DeviceSelected', dict(sender=0, message_id=-1)])
        self.ws.send("Redo", original_message=['DeviceUnSelected', dict(sender=0, message_id=-1)])

    def test_Snapshot(self):
        self.ws.send("Redo", original_message=['Snapshot', dict(sender=0, message_id=-1)])

    def tearDown(self):
        self.ws.close()


class TestUIWebSocket(unittest.TestCase):

    def test(self):
        self.ui = MessageHandler(create_connection("ws://localhost:8001/network_ui/topology?topology_id=143"))
        self.ui.recv()
        self.ui.recv()
        self.ui.send("Hello")

    def tearDown(self):
        self.ui.close()


class TestUI(unittest.TestCase):

    def setUp(self):
        self.ws = MessageHandler(create_connection("ws://localhost:8001/network_ui/tester?topology_id=143"))
        self.ui = MessageHandler(create_connection("ws://localhost:8001/network_ui/topology?topology_id=143"))
        self.ws.recv()
        self.ws.recv()
        self.ui.recv()
        self.ui.recv()

    def tearDown(self):
        self.ui.close()
        self.ws.close()

    def test_DeviceStatus(self):
        self.ws.send('DeviceCreate', name="TestSwitch", x=0, y=500, type="switch", id=100)
        self.ws.send('DeviceMove', x=100, y=100, previous_x=0, previous_y=500, id=100)
        self.ws.send('DeviceStatus', name="TestSwitch", working=True, status=None)
        time.sleep(1)
        self.ws.send('DeviceStatus', name="TestSwitch", working=False, status="pass")
        time.sleep(1)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=100)

    def test_TaskStatus(self):
        self.ws.send('DeviceCreate', name="TestSwitch", x=0, y=500, type="switch", id=100)
        self.ws.send('DeviceMove', x=100, y=100, previous_x=0, previous_y=500, id=100)
        self.ws.send('TaskStatus', device_name="TestSwitch", task_id="1", working=True, status=None)
        time.sleep(1)
        self.ws.send('TaskStatus', device_name="TestSwitch", task_id="1", working=False, status="pass")
        time.sleep(1)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=100)

    def test_DeviceSelect(self):
        self.ws.send('DeviceCreate', name="TestSwitch", x=0, y=500, type="switch", id=100)
        self.ws.send('DeviceMove', x=100, y=100, previous_x=0, previous_y=500, id=100)
        self.ws.send('DeviceSelected', id=100)
        time.sleep(1)
        self.ws.send('DeviceUnSelected', id=100)
        time.sleep(1)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=100)

    def test_LinkSelect(self):
        self.ws.send('DeviceCreate', name="TestSwitchA", x=100, y=100, type="switch", id=100)
        self.ws.send('DeviceCreate', name="TestSwitchB", x=900, y=100, type="switch", id=101)
        self.ws.send('InterfaceCreate', name="swp1", id=1, device_id=100)
        self.ws.send('InterfaceCreate', name="swp1", id=1, device_id=101)
        time.sleep(1)
        self.ws.send('LinkCreate', id=100, name="A to B", from_device_id=100, to_device_id=101, from_interface_id=1, to_interface_id=1)
        self.ws.send('LinkSelected', id=100)
        time.sleep(1)
        self.ws.send('LinkUnSelected', id=100)
        time.sleep(1)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=100)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=101)

    def test_LinkSelect2(self):
        self.ws.send_multiple([
            dict(msg_type='DeviceCreate', name="TestSwitchA", x=100, y=100, type="switch", id=100),
            dict(msg_type='DeviceCreate', name="TestSwitchB", x=900, y=100, type="switch", id=101),
            dict(msg_type='InterfaceCreate', name="swp1", id=1, device_id=100),
            dict(msg_type='InterfaceCreate', name="swp1", id=1, device_id=101),
            dict(msg_type='LinkCreate', id=100, name="A to B", from_device_id=100, to_device_id=101, from_interface_id=1, to_interface_id=1)])
        self.ws.send('LinkSelected', id=100)
        time.sleep(1)
        self.ws.send('LinkUnSelected', id=100)
        time.sleep(1)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=100)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=101)

    def test_Facts(self):
        self.ws.send('DeviceCreate', name="TestSwitchA", x=100, y=100, type="switch", id=100)
        self.ws.send('DeviceCreate', name="TestSwitchB", x=900, y=100, type="switch", id=101)
        self.ws.send('InterfaceCreate', name="swp1", id=1, device_id=100)
        self.ws.send('InterfaceCreate', name="swp1", id=1, device_id=101)
        time.sleep(1)
        self.ws.send('LinkCreate', id=100, name="A to B", from_device_id=100, to_device_id=101, from_interface_id=1, to_interface_id=1)
        time.sleep(1)
        self.ws.send('Facts', key="TestSwitchA", value=dict(ansible_local=dict(ptm={'port': "swp1", 'cbl status': 'fail'})))
        time.sleep(1)
        self.ws.send('Facts', key="TestSwitchA", value=dict(ansible_local=dict(ptm={'port': "swp1", 'cbl status': 'pass'})))
        time.sleep(1)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=100)
        self.ws.send('DeviceDestroy',
                     previous_name="TestSwitch",
                     previous_x=0,
                     previous_y=500,
                     previous_type="switch",
                     id=101)

    def test_Snapshot(self):
        self.ws.send('Snapshot', **yaml.load('''
devices:
- id: 116
  interfaces:
  - id: 1
    name: swp1
    network: 186105
    remote_device_name: Switch2
    remote_interface_name: swp1
  name: Switch1
  type: switch
  x: -1969
  y: -320
- id: 117
  interfaces:
  - id: 1
    name: swp1
    network: 186105
    remote_device_name: Switch1
    remote_interface_name: swp1
  name: Switch2
  type: switch
  x: -1711
  y: -323
links:
- from_device: Switch2
  from_device_id: 117
  from_interface: swp1
  from_interface_id: 1
  network: 186105
  to_device: Switch1
  to_device_id: 116
  to_interface: swp1
  to_interface_id: 1
name: topology
topology_id: 143
'''))

        time.sleep(1)


class TestInvalidValues(unittest.TestCase):

    def test_bad_topology_id1(self):
        self.ws = MessageHandler(create_connection("ws://localhost:8001/network_ui/tester?topology_id=0"))
        self.ws.close()

    def test_bad_topology_id2(self):
        self.ws = MessageHandler(create_connection("ws://localhost:8001/network_ui/tester?topology_id=foo"))
        self.ws.close()

    def test_bad_sender(self):
        self.ws = MessageHandler(create_connection("ws://localhost:8001/network_ui/tester?topology_id=143"))
        self.ws.ws.send(json.dumps(['DeviceCreate', dict(sender=-1, name="TestSwitchA", x=100, y=100, type="switch", id=100)]))
        self.ws.ws.send(json.dumps(['DeviceDestroy', dict(sender=-1, previous_name="TestSwitchA",
                                                          previous_x=100, previous_y=100, previous_type="switch", id=100)]))
        self.ws.close()

    def test_unsupported_command(self):
        self.ws = MessageHandler(create_connection("ws://localhost:8001/network_ui/tester?topology_id=143"))
        self.ws.recv()
        self.ws.recv()
        self.ws.send("NotSupported")
        self.ws.send_multiple([dict(msg_type="NotSupported")])
        self.ws.close()
