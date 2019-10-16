# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

import time
import ssl
import logging

import irc.client

from django.utils.encoding import smart_text
from django.utils.translation import ugettext_lazy as _

from awx.main.notifications.base import AWXBaseEmailBackend
from awx.main.notifications.custom_notification_base import CustomNotificationBase

logger = logging.getLogger('awx.main.notifications.irc_backend')


class IrcBackend(AWXBaseEmailBackend, CustomNotificationBase):

    init_parameters = {"server": {"label": "IRC Server Address", "type": "string"},
                       "port": {"label": "IRC Server Port", "type": "int"},
                       "nickname": {"label": "IRC Nick", "type": "string"},
                       "password": {"label": "IRC Server Password", "type": "password"},
                       "use_ssl": {"label": "SSL Connection", "type": "bool"},
                       "targets": {"label": "Destination Channels or Users", "type": "list"}}
    recipient_parameter = "targets"
    sender_parameter = None

    def __init__(self, server, port, nickname, password, use_ssl, fail_silently=False, **kwargs):
        super(IrcBackend, self).__init__(fail_silently=fail_silently)
        self.server = server
        self.port = port
        self.nickname = nickname
        self.password = password if password != "" else None
        self.use_ssl = use_ssl
        self.connection = None

    def open(self):
        if self.connection is not None:
            return False
        if self.use_ssl:
            connection_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
        else:
            connection_factory = irc.connection.Factory()
        try:
            self.reactor = irc.client.Reactor()
            self.connection = self.reactor.server().connect(
                self.server,
                self.port,
                self.nickname,
                password=self.password,
                connect_factory=connection_factory,
            )
        except irc.client.ServerConnectionError as e:
            logger.error(smart_text(_("Exception connecting to irc server: {}").format(e)))
            if not self.fail_silently:
                raise
        return True

    def close(self):
        if self.connection is None:
            return
        self.connection = None

    def on_connect(self, connection, event):
        for c in self.channels:
            if irc.client.is_channel(c):
                connection.join(c)
            else:
                for m in self.channels[c]:
                    connection.privmsg(c, m.subject)
                self.channels_sent += 1

    def on_join(self, connection, event):
        for m in self.channels[event.target]:
            connection.privmsg(event.target, m.subject)
        self.channels_sent += 1

    def send_messages(self, messages):
        if self.connection is None:
            self.open()
        self.channels = {}
        self.channels_sent = 0
        for m in messages:
            for r in m.recipients():
                if r not in self.channels:
                    self.channels[r] = []
                self.channels[r].append(m)
        self.connection.add_global_handler("welcome", self.on_connect)
        self.connection.add_global_handler("join", self.on_join)
        start_time = time.time()
        process_time = time.time()
        while self.channels_sent < len(self.channels) and (process_time - start_time) < 60:
            self.reactor.process_once(0.1)
            process_time = time.time()
        self.reactor.disconnect_all()
        return self.channels_sent
