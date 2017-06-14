import cStringIO
import pytest
import base64
import json

from awx.main.utils import OutputEventFilter

MAX_WIDTH = 78
EXAMPLE_UUID = '890773f5-fe6d-4091-8faf-bdc8021d65dd'


def write_encoded_event_data(fileobj, data):
    b64data = base64.b64encode(json.dumps(data))
    # pattern corresponding to OutputEventFilter expectation
    fileobj.write(u'\x1b[K')
    for offset in xrange(0, len(b64data), MAX_WIDTH):
        chunk = b64data[offset:offset + MAX_WIDTH]
        escaped_chunk = u'{}\x1b[{}D'.format(chunk, len(chunk))
        fileobj.write(escaped_chunk)
    fileobj.write(u'\x1b[K')


@pytest.fixture
def fake_callback():
    return []


@pytest.fixture
def fake_cache():
    return {}


@pytest.fixture
def wrapped_handle(job_event_callback):
    # Preliminary creation of resources usually done in tasks.py
    stdout_handle = cStringIO.StringIO()
    return OutputEventFilter(stdout_handle, job_event_callback)


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


def test_verbose_event_no_markings(fake_callback, wrapped_handle):
    '''
    This occurs with jobs that do not have events but still generate
    and output stream, like system jobs
    '''
    wrapped_handle.write('Running tower-manage command \n')
    assert wrapped_handle._fileobj.getvalue() == 'Running tower-manage command \n'


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
