"""In-memory stand-ins for receptor work units, for testing streaming and adoption without a mesh.

FakeReceptorWork implements the ReceptorWork interface. Each unit holds the events its
playbook produced and the state receptor reports. results() returns the same line
protocol the ansible-runner worker writes, so AWX's real process-phase code parses it.

Failures are injected per unit:
  - break_after=N: the stream ends after N events with no status or eof, as when the
    connection to the execution node drops.
  - status_error: status() raises, as when the node is unreachable.
  - released units disappear, and releasing or reading an unknown unit raises like receptor.

RecordingDispatcher replaces CallbackQueueDispatcher so tests can see the events that
would have gone to the callback receiver.
"""

import io
import json
import uuid

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
    def __init__(self, events=(), status='successful', state=None, exit_code=None, detail='', break_after=None, status_error=None):
        self.events = list(events)
        self.status = status
        self.state = state or TERMINAL_STATE.get(status, 'Succeeded')
        self.exit_code = exit_code
        self.detail = detail
        self.break_after = break_after
        self.status_error = status_error

    def stream(self):
        lines = []
        events = self.events if self.break_after is None else self.events[: self.break_after]
        for event in events:
            lines.append(json.dumps(event))
        if self.break_after is None:
            lines.append(json.dumps({'status': self.status, 'runner_ident': 'fake'}))
            lines.append(json.dumps({'eof': True}))
        return ('\n'.join(lines) + '\n').encode() if lines else b''


class FakeSocket:
    def __init__(self):
        self.closed = False

    def shutdown(self, how):
        self.closed = True


class FakeReceptorWork(ReceptorWork):
    def __init__(self, units=None):
        super().__init__(receptor_ctl=None)
        self.units = dict(units or {})
        self.calls = []

    def _unit(self, unit_id):
        if unit_id not in self.units:
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
        data = self._unit(unit_id).stream()
        return FakeSocket(), io.BytesIO(data[startpos or 0 :])

    def cancel(self, unit_id):
        self.calls.append(('cancel', unit_id))
        self._unit(unit_id).state = 'Failed'

    def release(self, unit_id):
        self.calls.append(('release', unit_id))
        self._unit(unit_id)
        del self.units[unit_id]


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
