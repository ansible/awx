# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from mock import MagicMock, Mock

# Django
from django.test import SimpleTestCase

# AWX
from awx.fact.models.fact import * # noqa
from awx.main.management.commands.run_socketio_service import SocketSessionManager, SocketSession, SocketController

__all__ = ['SocketSessionManagerUnitTest', 'SocketControllerUnitTest',]

class WeakRefable():
    pass

class SocketSessionManagerUnitTest(SimpleTestCase):

    def setUp(self):
        self.session_manager = SocketSessionManager()
        super(SocketSessionManagerUnitTest, self).setUp()

    def create_sessions(self, count, token_key=None):
        self.sessions = []
        self.count = count
        for i in range(0, count):
            self.sessions.append(SocketSession(i, token_key or i, WeakRefable()))
            self.session_manager.add_session(self.sessions[i])

    def test_multiple_session_diff_token(self):
        self.create_sessions(10)

        for s in self.sessions:
            self.assertIn(s.token_key, self.session_manager.socket_session_token_key_map)
            self.assertEqual(s, self.session_manager.socket_session_token_key_map[s.token_key][s.session_id])


    def test_multiple_session_same_token(self):
        self.create_sessions(10, token_key='foo')

        sessions_dict = self.session_manager.lookup("foo")
        self.assertEqual(len(sessions_dict), 10)
        for s in self.sessions:
            self.assertIn(s.session_id, sessions_dict)
            self.assertEqual(s, sessions_dict[s.session_id])

    def test_prune_sessions_max(self):
        self.create_sessions(self.session_manager.SESSIONS_MAX + 10)

        self.assertEqual(len(self.session_manager.socket_sessions), self.session_manager.SESSIONS_MAX)


class SocketControllerUnitTest(SimpleTestCase):

    def setUp(self):
        self.socket_controller = SocketController(SocketSessionManager())
        server = Mock()
        self.socket_controller.set_server(server)
        super(SocketControllerUnitTest, self).setUp()

    def create_clients(self, count, token_key=None):
        self.sessions = []
        self.sockets =[]
        self.count = count
        self.sockets_dict = {}
        for i in range(0, count):
            if isinstance(token_key, list):
                token_key_actual = token_key[i]
            else:
                token_key_actual = token_key or i
            socket = MagicMock(session=dict())
            socket_session = SocketSession(i, token_key_actual, socket)
            self.sockets.append(socket)
            self.sessions.append(socket_session)
            self.sockets_dict[i] = socket
            self.socket_controller.add_session(socket_session)

            socket.session['socket_session'] = socket_session
            socket.send_packet = Mock()
        self.socket_controller.server.sockets = self.sockets_dict

    def test_broadcast_packet(self):
        self.create_clients(10)
        packet = {
            "hello": "world"
        }
        self.socket_controller.broadcast_packet(packet)
        for s in self.sockets:
            s.send_packet.assert_called_with(packet)

    def test_send_packet(self):
        self.create_clients(5, token_key=[0, 1, 2, 3, 4])
        packet = {
            "hello": "world"
        }
        self.socket_controller.send_packet(packet, 2)
        self.assertEqual(0, len(self.sockets[0].send_packet.mock_calls))
        self.assertEqual(0, len(self.sockets[1].send_packet.mock_calls))
        self.sockets[2].send_packet.assert_called_once_with(packet)
        self.assertEqual(0, len(self.sockets[3].send_packet.mock_calls))
        self.assertEqual(0, len(self.sockets[4].send_packet.mock_calls))

    def test_send_packet_multiple_sessions_one_token(self):
        self.create_clients(5, token_key=[0, 1, 1, 1, 2])
        packet = {
            "hello": "world"
        }
        self.socket_controller.send_packet(packet, 1)
        self.assertEqual(0, len(self.sockets[0].send_packet.mock_calls))
        self.sockets[1].send_packet.assert_called_once_with(packet)
        self.sockets[2].send_packet.assert_called_once_with(packet)
        self.sockets[3].send_packet.assert_called_once_with(packet)
        self.assertEqual(0, len(self.sockets[4].send_packet.mock_calls))

