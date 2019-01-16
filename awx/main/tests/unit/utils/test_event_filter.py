import pytest
import base64
import json
from io import StringIO

from django.utils.encoding import smart_bytes, smart_str
from awx.main.utils import OutputEventFilter, OutputVerboseFilter

MAX_WIDTH = 78
EXAMPLE_UUID = '890773f5-fe6d-4091-8faf-bdc8021d65dd'


def write_encoded_event_data(fileobj, data):
    b64data = smart_str(base64.b64encode(smart_bytes(json.dumps(data))))
    # pattern corresponding to OutputEventFilter expectation
    fileobj.write('\x1b[K')
    for offset in range(0, len(b64data), MAX_WIDTH):
        chunk = b64data[offset:offset + MAX_WIDTH]
        escaped_chunk = '{}\x1b[{}D'.format(chunk, len(chunk))
        fileobj.write(escaped_chunk)
    fileobj.write('\x1b[K')


@pytest.fixture
def fake_callback():
    return []


@pytest.fixture
def fake_cache():
    return {}


@pytest.fixture
def wrapped_handle(job_event_callback):
    # Preliminary creation of resources usually done in tasks.py
    return OutputEventFilter(job_event_callback)


@pytest.fixture
def job_event_callback(fake_callback, fake_cache):
    def method(event_data):
        if 'uuid' in event_data:
            cache_event = fake_cache.get(':1:ev-{}'.format(event_data['uuid']), None)
            if cache_event is not None:
                event_data.update(cache_event)
        fake_callback.append(event_data)
    return method


def test_event_recomb(fake_callback, fake_cache, wrapped_handle):
    # Pretend that this is done by the Ansible callback module
    fake_cache[':1:ev-{}'.format(EXAMPLE_UUID)] = {'event': 'foo'}
    write_encoded_event_data(wrapped_handle, {
        'uuid': EXAMPLE_UUID
    })
    wrapped_handle.write('\r\nTASK [Gathering Facts] *********************************************************\n')
    wrapped_handle.write('\u001b[0;33mchanged: [localhost]\u001b[0m\n')
    write_encoded_event_data(wrapped_handle, {})
    # stop pretending

    assert len(fake_callback) == 1
    recomb_data = fake_callback[0]
    assert 'event' in recomb_data
    assert recomb_data['event'] == 'foo'


def test_separate_verbose_events(fake_callback, wrapped_handle):
    # Pretend that this is done by the Ansible callback module
    wrapped_handle.write('Using /etc/ansible/ansible.cfg as config file\n')
    wrapped_handle.write('SSH password: \n')
    write_encoded_event_data(wrapped_handle, {  # associated with _next_ event
        'uuid': EXAMPLE_UUID
    })
    # stop pretending

    assert len(fake_callback) == 2
    for event_data in fake_callback:
        assert 'event' in event_data
        assert event_data['event'] == 'verbose'


def test_large_data_payload(fake_callback, fake_cache, wrapped_handle):
    # Pretend that this is done by the Ansible callback module
    fake_cache[':1:ev-{}'.format(EXAMPLE_UUID)] = {'event': 'foo'}
    event_data_to_encode = {
        'uuid': EXAMPLE_UUID,
        'host': 'localhost',
        'role': 'some_path_to_role'
    }
    assert len(json.dumps(event_data_to_encode)) > MAX_WIDTH
    write_encoded_event_data(wrapped_handle, event_data_to_encode)
    wrapped_handle.write('\r\nTASK [Gathering Facts] *********************************************************\n')
    wrapped_handle.write('\u001b[0;33mchanged: [localhost]\u001b[0m\n')
    write_encoded_event_data(wrapped_handle, {})
    # stop pretending

    assert len(fake_callback) == 1
    recomb_data = fake_callback[0]
    assert 'role' in recomb_data
    assert recomb_data['role'] == 'some_path_to_role'
    assert 'event' in recomb_data
    assert recomb_data['event'] == 'foo'


def test_event_lazy_parsing(fake_callback, fake_cache, wrapped_handle):
    # Pretend that this is done by the Ansible callback module
    fake_cache[':1:ev-{}'.format(EXAMPLE_UUID)] = {'event': 'foo'}
    buff = StringIO()
    event_data_to_encode = {
        'uuid': EXAMPLE_UUID,
        'host': 'localhost',
        'role': 'some_path_to_role'
    }
    write_encoded_event_data(buff, event_data_to_encode)

    # write the data to the event filter in chunks to test lazy event matching
    buff.seek(0)
    start_token_chunk = buff.read(1)  # \x1b
    start_token_remainder = buff.read(2)  # [K
    body = buff.read(15)  # next 15 bytes of base64 data
    remainder = buff.read()  # the remainder
    for chunk in (start_token_chunk, start_token_remainder, body, remainder):
        wrapped_handle.write(chunk)

    wrapped_handle.write('\r\nTASK [Gathering Facts] *********************************************************\n')
    wrapped_handle.write('\u001b[0;33mchanged: [localhost]\u001b[0m\n')
    write_encoded_event_data(wrapped_handle, {})
    # stop pretending

    assert len(fake_callback) == 1
    recomb_data = fake_callback[0]
    assert 'role' in recomb_data
    assert recomb_data['role'] == 'some_path_to_role'
    assert 'event' in recomb_data
    assert recomb_data['event'] == 'foo'


@pytest.mark.timeout(1)
def test_large_stdout_blob():
    def _callback(*args, **kw):
        pass

    f = OutputEventFilter(_callback)
    for x in range(1024 * 10):
        f.write('x' * 1024)


def test_verbose_line_buffering():
    events = []

    def _callback(event_data):
        events.append(event_data)

    f = OutputVerboseFilter(_callback)
    f.write('one two\r\n\r\n')

    assert len(events) == 2
    assert events[0]['start_line'] == 0
    assert events[0]['end_line'] == 1
    assert events[0]['stdout'] == 'one two'

    assert events[1]['start_line'] == 1
    assert events[1]['end_line'] == 2
    assert events[1]['stdout'] == ''

    f.write('three')
    assert len(events) == 2
    f.write('\r\nfou')

    # three is not pushed to buffer until its line completes
    assert len(events) == 3
    assert events[2]['start_line'] == 2
    assert events[2]['end_line'] == 3
    assert events[2]['stdout'] == 'three'

    f.write('r\r')
    f.write('\nfi')

    assert events[3]['start_line'] == 3
    assert events[3]['end_line'] == 4
    assert events[3]['stdout'] == 'four'

    f.write('ve')
    f.write('\r\n')

    assert len(events) == 5
    assert events[4]['start_line'] == 4
    assert events[4]['end_line'] == 5
    assert events[4]['stdout'] == 'five'

    f.close()

    from pprint import pprint
    pprint(events)
    assert len(events) == 6

    assert events[5]['event'] == 'EOF'
