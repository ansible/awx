# Copyright (c) 2017 Red Hat, Inc
from django.core.management.base import BaseCommand

from websocket import create_connection
from ui_test import MessageHandler, _Time
from awx.network_ui.models import Device, TopologyHistory

import json

time = _Time()


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('topology_id', type=int)
        parser.add_argument('recording')
        parser.add_argument('--time-scale', dest="time_scale", default=1.0, type=float)
        parser.add_argument('--delete-topology-at-start', dest="delete_topolgy", action="store_true", default=False)

    def handle(self, *args, **options):
        print options['topology_id']
        print options['recording']
        topology_id = options['topology_id']
        if options['delete_topolgy'] is True:
            TopologyHistory.objects.filter(topology_id=topology_id).delete()
            Device.objects.filter(topology_id=topology_id).delete()
        time.scale = options.get('time_scale', 1.0)
        ui = MessageHandler(create_connection("ws://localhost:8001/network_ui/topology?topology_id={0}".format(options['topology_id'])))
        ui.recv()
        ui.recv()
        ui.send('StopRecording')
        ui.send('StartReplay')
        if options['delete_topolgy'] is True:
            ui.send_message(['History', []])
            ui.send('Snapshot', sender=ui.client_id, devices=[], links=[])
        messages = []
        with open(options['recording']) as f:
            for line in f.readlines():
                messages.append(json.loads(line))
        messages = sorted(messages, key=lambda x: x['message_id'])

        for message in messages:
            message['sender'] = ui.client_id
            message['save'] = False
            ui.send_message([message['msg_type'], message])
            if message['msg_type'] == "ViewPort":
                time.sleep(10)
            else:
                time.sleep(1)
        ui.send('StopReplay')
        ui.send('CoverageRequest')
        ui.close()
