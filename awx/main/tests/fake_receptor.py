"""In-memory stand-ins for receptor work units, for testing streaming and adoption without a mesh.

FakeReceptorWork implements the ReceptorWork interface. Each unit holds the events its
playbook produced and the state receptor reports. results() returns the same line
protocol the ansible-runner worker writes, so AWX's real process-phase code parses it.

Failures are injected per unit:
  - break_after=N: the stream ends after N events with no status or eof, as when the
    connection to the execution node drops.
  - status_error: status() raises, as when the node is unreachable. adopt() and cancel() raise too.
  - results_error: results() raises, as when the results stream cannot be opened or breaks.
  - artifacts: files the playbook left in its artifact directory, {relative path: content}
    or {relative path: (content, seconds_old)}. They are streamed the way an ansible-runner
    worker streams them: a zip of the artifact directory, paths relative to it, file
    modification times preserved.
  - remote_only: this controller's receptor does not hold the unit, so status() and results()
    raise until adopt() takes it over from the execution node.
  - released units disappear, and releasing or reading an unknown unit raises like receptor.

RecordingDispatcher replaces CallbackQueueDispatcher so tests can see the events that
would have gone to the callback receiver.
"""

import base64
import io
import json
import time
import uuid
import zipfile

from awx.main.tasks.receptor import ReceptorWork

TERMINAL_STATE = {'successful': 'Succeeded', 'failed': 'Failed', 'canceled': 'Failed', 'error': 'Failed'}


def make_events(count, failed_tasks=()):
    """Return `count` runner events shaped like a playbook run: start, tasks, then stats."""
    events = []
    for counter in range(1, count + 1):
        if counter == 1:
            event = 'playbook_on_start'
        elif counter == count:
            event = 'playbook_on_stats'
        elif counter in failed_tasks:
            event = 'runner_on_failed'
        else:
            event = 'runner_on_ok'
        events.append(
            {
                'uuid': str(uuid.uuid4()),
                'counter': counter,
                'event': event,
                'stdout': f'line {counter}',
                'start_line': counter - 1,
                'end_line': counter,
                'event_data': {},
            }
        )
    return events


class FakeWorkUnit:
    def __init__(
        self,
        events=(),
        status='successful',
        state=None,
        exit_code=None,
        detail='',
        break_after=None,
        status_error=None,
        remote_only=False,
        results_error=None,
        artifacts=None,
    ):
        self.events = list(events)
        self.status = status
        self.state = state or TERMINAL_STATE.get(status, 'Succeeded')
        self.exit_code = exit_code
        self.detail = detail
        self.break_after = break_after
        self.status_error = status_error
        self.remote_only = remote_only
        self.results_error = results_error
        self.artifacts = artifacts or {}

    def _artifacts_zip(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for path, content in self.artifacts.items():
                content, seconds_old = content if isinstance(content, tuple) else (content, 0)
                info = zipfile.ZipInfo(path, date_time=time.localtime(time.time() - seconds_old)[:6])
                info.external_attr = 0o644 << 16
                archive.writestr(info, content)
        return buffer.getvalue()

    def stream(self):
        lines = []
        events = self.events if self.break_after is None else self.events[: self.break_after]
        for event in events:
            lines.append(json.dumps(event))
        data = ('\n'.join(lines) + '\n').encode() if lines else b''
        if self.break_after is None:
            if self.artifacts:
                # The base64 runs straight into the next line, as the worker writes it.
                archive = self._artifacts_zip()
                data += json.dumps({'zipfile': len(archive)}).encode() + b'\n' + base64.b64encode(archive)
            data += (json.dumps({'status': self.status, 'runner_ident': 'fake'}) + '\n' + json.dumps({'eof': True}) + '\n').encode()
        return data


class FakeSocket:
    def __init__(self):
        self.closed = False

    def shutdown(self, how):
        self.closed = True

    def close(self):
        self.closed = True


class FakeReceptorWork(ReceptorWork):
    def __init__(self, units=None):
        super().__init__(receptor_ctl=None)
        self.units = dict(units or {})
        self.calls = []

    def _unit(self, unit_id):
        if unit_id not in self.units or self.units[unit_id].remote_only:
            raise RuntimeError(f'ERROR: unknown work unit {unit_id}')
        return self.units[unit_id]

    def list(self):
        self.calls.append(('list',))
        return {unit_id: {'StateName': unit.state, 'ExtraData': {}} for unit_id, unit in self.units.items()}

    def status(self, unit_id):
        self.calls.append(('status', unit_id))
        unit = self._unit(unit_id)
        if unit.status_error:
            raise unit.status_error
        status = {'StateName': unit.state, 'Detail': unit.detail, 'StdoutSize': len(unit.stream())}
        if unit.exit_code is not None:
            status['ExitCode'] = unit.exit_code
        return status

    def results(self, unit_id, startpos=None):
        self.calls.append(('results', unit_id, startpos))
        unit = self._unit(unit_id)
        if unit.results_error:
            raise unit.results_error
        data = unit.stream()
        return FakeSocket(), io.BytesIO(data[startpos or 0 :])

    def cancel(self, unit_id):
        self.calls.append(('cancel', unit_id))
        unit = self._unit(unit_id)
        if unit.status_error:
            raise unit.status_error
        unit.state = 'Failed'

    def release(self, unit_id):
        self.calls.append(('release', unit_id))
        self._unit(unit_id)
        del self.units[unit_id]

    def adopt(self, node, unit_id):
        self.calls.append(('adopt', node, unit_id))
        unit = self.units.get(unit_id)
        if unit is None:
            raise RuntimeError(f'ERROR: unknown work unit {unit_id} on {node}')
        if unit.status_error:
            raise unit.status_error
        unit.remote_only = False
        return {'unitid': unit_id, 'result': 'Adopted'}

    def close(self):
        self.calls.append(('close',))


class RecordingDispatcher:
    """Collects callback-receiver messages instead of sending them to Redis."""

    dispatched = []

    def __init__(self):
        pass

    def dispatch(self, obj):
        RecordingDispatcher.dispatched.append(obj)

    @classmethod
    def reset(cls):
        cls.dispatched = []

    @classmethod
    def counters(cls):
        return [e['counter'] for e in cls.dispatched if 'counter' in e]
