import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import HostEventModal from './HostEventModal';

const hostEvent = {
  changed: true,
  event: 'runner_on_ok',
  event_data: {
    host: 'foo',
    play: 'all',
    playbook: 'run_command.yml',
    res: {
      ansible_loop_var: 'item',
      changed: true,
      item: '1',
      msg: 'This is a debug message: 1',
      stdout:
        '              total        used        free      shared  buff/cache   available\nMem:           7973        3005         960          30        4007        4582\nSwap:          1023           0        1023',
      cmd: ['free', '-m'],
      stderr_lines: [],
      stdout_lines: [
        '              total        used        free      shared  buff/cache   available',
        'Mem:           7973        3005         960          30        4007        4582',
        'Swap:          1023           0        1023',
      ],
    },
    task: 'command',
    task_action: 'command',
  },
  event_display: 'Host OK',
  event_level: 3,
  failed: false,
  host: 1,
  host_name: 'foo',
  id: 123,
  job: 4,
  play: 'all',
  playbook: 'run_command.yml',
  stdout: `stdout: "[0;33mchanged: [localhost] => {"changed": true, "cmd": ["free", "-m"], "delta": "0:00:01.479609", "end": "2019-09-10 14:21:45.469533", "rc": 0, "start": "2019-09-10 14:21:43.989924", "stderr": "", "stderr_lines": [], "stdout": "              total        used        free      shared  buff/cache   available\nMem:           7973        3005         960          30        4007        4582\nSwap:          1023           0        1023", "stdout_lines": ["              total        used        free      shared  buff/cache   available", "Mem:           7973        3005         960          30        4007        4582", "Swap:          1023           0        1023"]}[0m"
  `,
  task: 'command',
  type: 'job_event',
  url: '/api/v2/job_events/123/',
};

/* eslint-disable no-useless-escape */
const jsonValue = `{
  \"ansible_loop_var\": \"item\",
  \"changed\": true,
  \"item\": \"1\",
  \"msg\": \"This is a debug message: 1\",
  \"stdout\": \"              total        used        free      shared  buff/cache   available\\nMem:           7973        3005         960          30        4007        4582\\nSwap:          1023           0        1023\",
  \"cmd\": [
    \"free\",
    \"-m\"
  ],
  \"stderr_lines\": [],
  \"stdout_lines\": [
    \"              total        used        free      shared  buff/cache   available\",
    \"Mem:           7973        3005         960          30        4007        4582\",
    \"Swap:          1023           0        1023\"
  ]
}`;

let detailsSection;
let jsonSection;
let standardOutSection;
let standardErrorSection;

const findSections = wrapper => {
  detailsSection = wrapper.find('section').at(0);
  jsonSection = wrapper.find('section').at(1);
  standardOutSection = wrapper.find('section').at(2);
  standardErrorSection = wrapper.find('section').at(3);
};

describe('HostEventModal', () => {
  test('initially renders successfully', () => {
    const wrapper = mountWithContexts(
      <HostEventModal hostEvent={hostEvent} onClose={() => {}} />
    );
    expect(wrapper).toHaveLength(1);
  });

  test('should render all tabs', () => {
    const wrapper = mountWithContexts(
      <HostEventModal hostEvent={hostEvent} onClose={() => {}} isOpen />
    );

    /* eslint-disable react/button-has-type */
    expect(wrapper.find('Tabs TabButton').length).toEqual(4);
  });

  test('should show details tab content on mount', () => {
    const wrapper = mountWithContexts(
      <HostEventModal hostEvent={hostEvent} onClose={() => {}} isOpen />
    );
    findSections(wrapper);
    expect(detailsSection.find('TextList').length).toBe(1);

    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }

    // StatusIcon adds visibly hidden accessibility text " changed "
    assertDetail('Host Name', ' changed foo');
    assertDetail('Play', 'all');
    assertDetail('Task', 'command');
    assertDetail('Module', 'command');
    assertDetail('Command', 'free-m');
  });

  test('should display successful host status icon', () => {
    const successfulHostEvent = { ...hostEvent, changed: false };
    const wrapper = mountWithContexts(
      <HostEventModal
        hostEvent={successfulHostEvent}
        onClose={() => {}}
        isOpen
      />
    );
    const icon = wrapper.find('StatusIcon');
    expect(icon.prop('status')).toBe('ok');
    expect(icon.find('StatusIcon SuccessfulTop').length).toBe(1);
    expect(icon.find('StatusIcon SuccessfulBottom').length).toBe(1);
  });

  test('should display skipped host status icon', () => {
    const skippedHostEvent = { ...hostEvent, event: 'runner_on_skipped' };
    const wrapper = mountWithContexts(
      <HostEventModal hostEvent={skippedHostEvent} onClose={() => {}} isOpen />
    );

    const icon = wrapper.find('StatusIcon');
    expect(icon.prop('status')).toBe('skipped');
    expect(icon.find('StatusIcon SkippedTop').length).toBe(1);
    expect(icon.find('StatusIcon SkippedBottom').length).toBe(1);
  });

  test('should display unreachable host status icon', () => {
    const unreachableHostEvent = {
      ...hostEvent,
      event: 'runner_on_unreachable',
      changed: false,
    };
    const wrapper = mountWithContexts(
      <HostEventModal
        hostEvent={unreachableHostEvent}
        onClose={() => {}}
        isOpen
      />
    );

    const icon = wrapper.find('StatusIcon');
    expect(icon.prop('status')).toBe('unreachable');
    expect(icon.find('StatusIcon UnreachableTop').length).toBe(1);
    expect(icon.find('StatusIcon UnreachableBottom').length).toBe(1);
  });

  test('should display failed host status icon', () => {
    const unreachableHostEvent = {
      ...hostEvent,
      changed: false,
      failed: true,
      event: 'runner_on_failed',
    };
    const wrapper = mountWithContexts(
      <HostEventModal
        hostEvent={unreachableHostEvent}
        onClose={() => {}}
        isOpen
      />
    );

    const icon = wrapper.find('StatusIcon');
    expect(icon.prop('status')).toBe('failed');
    expect(icon.find('StatusIcon FailedTop').length).toBe(1);
    expect(icon.find('StatusIcon FailedBottom').length).toBe(1);
  });

  test('should display JSON tab content on tab click', () => {
    const wrapper = mountWithContexts(
      <HostEventModal hostEvent={hostEvent} onClose={() => {}} isOpen />
    );

    findSections(wrapper);
    expect(jsonSection.find('EmptyState').length).toBe(1);
    wrapper.find('button[aria-label="JSON tab"]').simulate('click');
    findSections(wrapper);
    expect(jsonSection.find('CodeMirrorInput').length).toBe(1);

    const codemirror = jsonSection.find('CodeMirrorInput Controlled');
    expect(codemirror.prop('mode')).toBe('javascript');
    expect(codemirror.prop('options').readOnly).toBe(true);
    expect(codemirror.prop('value')).toEqual(jsonValue);
  });

  test('should display Standard Out tab content on tab click', () => {
    const wrapper = mountWithContexts(
      <HostEventModal hostEvent={hostEvent} onClose={() => {}} isOpen />
    );

    findSections(wrapper);
    expect(standardOutSection.find('EmptyState').length).toBe(1);
    wrapper.find('button[aria-label="Standard out tab"]').simulate('click');
    findSections(wrapper);
    expect(standardOutSection.find('CodeMirrorInput').length).toBe(1);

    const codemirror = standardOutSection.find('CodeMirrorInput Controlled');
    expect(codemirror.prop('mode')).toBe('javascript');
    expect(codemirror.prop('options').readOnly).toBe(true);
    expect(codemirror.prop('value')).toEqual(hostEvent.event_data.res.stdout);
  });

  test('should display Standard Error tab content on tab click', () => {
    const hostEventError = {
      ...hostEvent,
      event_data: {
        res: {
          stderr: '',
        },
      },
    };
    const wrapper = mountWithContexts(
      <HostEventModal hostEvent={hostEventError} onClose={() => {}} isOpen />
    );
    findSections(wrapper);
    expect(standardErrorSection.find('EmptyState').length).toBe(1);
    wrapper.find('button[aria-label="Standard error tab"]').simulate('click');
    findSections(wrapper);
    expect(standardErrorSection.find('CodeMirrorInput').length).toBe(1);

    const codemirror = standardErrorSection.find('CodeMirrorInput Controlled');
    expect(codemirror.prop('mode')).toBe('javascript');
    expect(codemirror.prop('options').readOnly).toBe(true);
    expect(codemirror.prop('value')).toEqual(' ');
  });

  test('should call onClose when close button is clicked', () => {
    const onClose = jest.fn();
    const wrapper = mountWithContexts(
      <HostEventModal hostEvent={hostEvent} onClose={onClose} isOpen />
    );
    wrapper.find('button[aria-label="Close"]').simulate('click');
    expect(onClose).toBeCalled();
  });

  test('should render standard out of debug task', () => {
    const debugTaskAction = {
      ...hostEvent,
      event_data: {
        taskAction: 'debug',
        res: {
          result: {
            stdout: 'foo bar',
          },
        },
      },
    };
    const wrapper = mountWithContexts(
      <HostEventModal hostEvent={debugTaskAction} onClose={() => {}} isOpen />
    );
    wrapper.find('button[aria-label="Standard out tab"]').simulate('click');
    findSections(wrapper);
    const codemirror = standardOutSection.find('CodeMirrorInput Controlled');
    expect(codemirror.prop('value')).toEqual('foo bar');
  });

  test('should render standard out of yum task', () => {
    const yumTaskAction = {
      ...hostEvent,
      event_data: {
        taskAction: 'yum',
        res: {
          results: ['baz', 'bar'],
        },
      },
    };
    const wrapper = mountWithContexts(
      <HostEventModal hostEvent={yumTaskAction} onClose={() => {}} isOpen />
    );
    wrapper.find('button[aria-label="Standard out tab"]').simulate('click');
    findSections(wrapper);
    const codemirror = standardOutSection.find('CodeMirrorInput Controlled');
    expect(codemirror.prop('value')).toEqual('baz');
  });
});
