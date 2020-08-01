from unittest import mock
import datetime as dt
from django.core.mail.message import EmailMessage

import awx.main.notifications.grafana_backend as grafana_backend


def test_send_messages():
    with mock.patch('awx.main.notifications.grafana_backend.requests') as requests_mock:
        requests_mock.post.return_value.status_code = 200
        m={}
        m['started'] = dt.datetime.utcfromtimestamp(60).isoformat()
        m['finished'] = dt.datetime.utcfromtimestamp(120).isoformat()
        m['subject'] = "test subject"
        backend = grafana_backend.GrafanaBackend("testapikey")
        message = EmailMessage(m['subject'],{"started":m['started'],"finished":m['finished']}, [], ['https://example.com', ])
        sent_messages = backend.send_messages([message, ])
        requests_mock.post.assert_called_once_with(
            'https://example.com/api/annotations',
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer testapikey'},
            json={'text': 'test subject', 'isRegion': True, 'timeEnd': 120000, 'panelId': None, 'time': 60000, 'dashboardId': None},
            verify=True)
        assert sent_messages == 1


def test_send_messages_with_no_verify_ssl():
    with mock.patch('awx.main.notifications.grafana_backend.requests') as requests_mock:
        requests_mock.post.return_value.status_code = 200
        m={}
        m['started'] = dt.datetime.utcfromtimestamp(60).isoformat()
        m['finished'] = dt.datetime.utcfromtimestamp(120).isoformat()
        m['subject'] = "test subject"
        backend = grafana_backend.GrafanaBackend("testapikey",grafana_no_verify_ssl=True)
        message = EmailMessage(m['subject'],{"started":m['started'],"finished":m['finished']}, [], ['https://example.com', ])
        sent_messages = backend.send_messages([message, ])
        requests_mock.post.assert_called_once_with(
            'https://example.com/api/annotations',
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer testapikey'},
            json={'text': 'test subject', 'isRegion': True, 'timeEnd': 120000, 'panelId': None,'time': 60000, 'dashboardId': None},
            verify=False)
        assert sent_messages == 1


def test_send_messages_with_dashboardid():
    with mock.patch('awx.main.notifications.grafana_backend.requests') as requests_mock:
        requests_mock.post.return_value.status_code = 200
        m={}
        m['started'] = dt.datetime.utcfromtimestamp(60).isoformat()
        m['finished'] = dt.datetime.utcfromtimestamp(120).isoformat()
        m['subject'] = "test subject"
        backend = grafana_backend.GrafanaBackend("testapikey",dashboardId=42)
        message = EmailMessage(m['subject'],{"started":m['started'],"finished":m['finished']}, [], ['https://example.com', ])
        sent_messages = backend.send_messages([message, ])
        requests_mock.post.assert_called_once_with(
            'https://example.com/api/annotations',
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer testapikey'},
            json={'text': 'test subject', 'isRegion': True, 'timeEnd': 120000, 'panelId': None, 'time': 60000, 'dashboardId': 42},
            verify=True)
        assert sent_messages == 1


def test_send_messages_with_panelid():
    with mock.patch('awx.main.notifications.grafana_backend.requests') as requests_mock:
        requests_mock.post.return_value.status_code = 200
        m={}
        m['started'] = dt.datetime.utcfromtimestamp(60).isoformat()
        m['finished'] = dt.datetime.utcfromtimestamp(120).isoformat()
        m['subject'] = "test subject"
        backend = grafana_backend.GrafanaBackend("testapikey",dashboardId=None,panelId=42)
        message = EmailMessage(m['subject'],{"started":m['started'],"finished":m['finished']}, [], ['https://example.com', ])
        sent_messages = backend.send_messages([message, ])
        requests_mock.post.assert_called_once_with(
            'https://example.com/api/annotations',
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer testapikey'},
            json={'text': 'test subject', 'isRegion': True, 'timeEnd': 120000, 'panelId': 42, 'time': 60000, 'dashboardId': None},
            verify=True)
        assert sent_messages == 1


def test_send_messages_with_bothids():
    with mock.patch('awx.main.notifications.grafana_backend.requests') as requests_mock:
        requests_mock.post.return_value.status_code = 200
        m={}
        m['started'] = dt.datetime.utcfromtimestamp(60).isoformat()
        m['finished'] = dt.datetime.utcfromtimestamp(120).isoformat()
        m['subject'] = "test subject"
        backend = grafana_backend.GrafanaBackend("testapikey",dashboardId=42,panelId=42)
        message = EmailMessage(m['subject'],{"started":m['started'],"finished":m['finished']}, [], ['https://example.com', ])
        sent_messages = backend.send_messages([message, ])
        requests_mock.post.assert_called_once_with(
            'https://example.com/api/annotations',
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer testapikey'},
            json={'text': 'test subject', 'isRegion': True, 'timeEnd': 120000, 'panelId': 42, 'time': 60000, 'dashboardId': 42},
            verify=True)
        assert sent_messages == 1


def test_send_messages_with_tags():
    with mock.patch('awx.main.notifications.grafana_backend.requests') as requests_mock:
        requests_mock.post.return_value.status_code = 200
        m={}
        m['started'] = dt.datetime.utcfromtimestamp(60).isoformat()
        m['finished'] = dt.datetime.utcfromtimestamp(120).isoformat()
        m['subject'] = "test subject"
        backend = grafana_backend.GrafanaBackend("testapikey",dashboardId=None,panelId=None,annotation_tags=["ansible"])
        message = EmailMessage(m['subject'],{"started":m['started'],"finished":m['finished']}, [], ['https://example.com', ])
        sent_messages = backend.send_messages([message, ])
        requests_mock.post.assert_called_once_with(
            'https://example.com/api/annotations',
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer testapikey'},
            json={'tags': ['ansible'], 'text': 'test subject', 'isRegion': True, 'timeEnd': 120000, 'panelId': None, 'time': 60000, 'dashboardId': None},
            verify=True)
        assert sent_messages == 1
