import React from 'react';
import { shallow } from 'enzyme';
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

// let detailsSection;
// let jsonSection;
// let standardOutSection;
// let standardErrorSection;
//
// const findSections = wrapper => {
//   detailsSection = wrapper.find('section').at(0);
//   jsonSection = wrapper.find('section').at(1);
//   standardOutSection = wrapper.find('section').at(2);
//   standardErrorSection = wrapper.find('section').at(3);
// };

describe('HostEventModal', () => {
  test('initially renders successfully', () => {
    const wrapper = shallow(
      <HostEventModal hostEvent={hostEvent} onClose={() => {}} />
    );
    expect(wrapper).toHaveLength(1);
  });

  test('should render all tabs', () => {
    const wrapper = shallow(
      <HostEventModal hostEvent={hostEvent} onClose={() => {}} isOpen />
    );

    expect(wrapper.find('Tabs Tab').length).toEqual(4);
  });

  test('should initially show details tab', () => {
    const wrapper = shallow(
      <HostEventModal hostEvent={hostEvent} onClose={() => {}} isOpen />
    );
    expect(wrapper.find('Tabs').prop('activeKey')).toEqual(0);
    expect(wrapper.find('Detail')).toHaveLength(5);

    function assertDetail(index, label, value) {
      const detail = wrapper.find('Detail').at(index);
      expect(detail.prop('label')).toEqual(label);
      expect(detail.prop('value')).toEqual(value);
    }

    const detail = wrapper.find('Detail').first();
    expect(detail.prop('value').props.children).toEqual([null, 'foo']);
    assertDetail(1, 'Play', 'all');
    assertDetail(2, 'Task', 'command');
    assertDetail(3, 'Module', 'command');
    assertDetail(4, 'Command', hostEvent.event_data.res.cmd);
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
    const wrapper = shallow(
      <HostEventModal hostEvent={hostEvent} onClose={() => {}} isOpen />
    );

    const handleTabClick = wrapper.find('Tabs').prop('onSelect');
    handleTabClick(null, 1);
    wrapper.update();

    const codeEditor = wrapper.find('CodeEditor');
    expect(codeEditor.prop('mode')).toBe('javascript');
    expect(codeEditor.prop('readOnly')).toBe(true);
    expect(codeEditor.prop('value')).toEqual(jsonValue);
  });

  test('should display Standard Out tab content on tab click', () => {
    const wrapper = shallow(
      <HostEventModal hostEvent={hostEvent} onClose={() => {}} isOpen />
    );

    const handleTabClick = wrapper.find('Tabs').prop('onSelect');
    handleTabClick(null, 2);
    wrapper.update();

    const codeEditor = wrapper.find('CodeEditor');
    expect(codeEditor.prop('mode')).toBe('javascript');
    expect(codeEditor.prop('readOnly')).toBe(true);
    expect(codeEditor.prop('value')).toEqual(hostEvent.event_data.res.stdout);
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
    const wrapper = shallow(
      <HostEventModal hostEvent={hostEventError} onClose={() => {}} isOpen />
    );

    const handleTabClick = wrapper.find('Tabs').prop('onSelect');
    handleTabClick(null, 3);
    wrapper.update();

    const codeEditor = wrapper.find('CodeEditor');
    expect(codeEditor.prop('mode')).toBe('javascript');
    expect(codeEditor.prop('readOnly')).toBe(true);
    expect(codeEditor.prop('value')).toEqual(' ');
  });

  test('should pass onClose to Modal', () => {
    const onClose = jest.fn();
    const wrapper = shallow(
      <HostEventModal hostEvent={hostEvent} onClose={onClose} isOpen />
    );

    expect(wrapper.find('Modal').prop('onClose')).toEqual(onClose);
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
    const wrapper = shallow(
      <HostEventModal hostEvent={debugTaskAction} onClose={() => {}} isOpen />
    );

    const handleTabClick = wrapper.find('Tabs').prop('onSelect');
    handleTabClick(null, 2);
    wrapper.update();

    const codeEditor = wrapper.find('CodeEditor');
    expect(codeEditor.prop('mode')).toBe('javascript');
    expect(codeEditor.prop('readOnly')).toBe(true);
    expect(codeEditor.prop('value')).toEqual('foo bar');
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
    const wrapper = shallow(
      <HostEventModal hostEvent={yumTaskAction} onClose={() => {}} isOpen />
    );

    const handleTabClick = wrapper.find('Tabs').prop('onSelect');
    handleTabClick(null, 2);
    wrapper.update();

    const codeEditor = wrapper.find('CodeEditor');
    expect(codeEditor.prop('mode')).toBe('javascript');
    expect(codeEditor.prop('readOnly')).toBe(true);
    expect(codeEditor.prop('value')).toEqual('baz');
  });
});
