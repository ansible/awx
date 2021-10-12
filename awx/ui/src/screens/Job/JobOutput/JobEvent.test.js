import React from 'react';
import { shallow } from 'enzyme';
import JobEvent from './JobEvent';

const mockOnPlayStartEvent = {
  created: '2019-07-11T18:11:22.005319Z',
  event: 'playbook_on_play_start',
  counter: 2,
  start_line: 0,
  end_line: 2,
  stdout:
    '\r\nPLAY [add hosts to inventory] **************************************************',
};
const mockRunnerOnOkEvent = {
  created: '2019-07-11T18:09:22.906001Z',
  event: 'runner_on_ok',
  counter: 5,
  start_line: 4,
  end_line: 5,
  stdout: '\u001b[0;32mok: [localhost]\u001b[0m',
};

const singleDigitTimestampEvent = {
  ...mockOnPlayStartEvent,
  created: '2019-07-11T08:01:02.906001Z',
};

const mockSingleDigitTimestampEventLineTextHtml = [
  { lineNumber: 0, html: '' },
  {
    lineNumber: 1,
    html: 'PLAY [add hosts to inventory] **************************************************<span class="time">08:01:02</span>',
  },
];

const mockAnsiLineTextHtml = [
  {
    lineNumber: 4,
    html: '<span class="output--1977390340">ok: [localhost]</span>',
  },
];

const mockOnPlayStartLineTextHtml = [
  { lineNumber: 0, html: '' },
  {
    lineNumber: 1,
    html: 'PLAY [add hosts to inventory] **************************************************<span class="time">18:11:22</span>',
  },
];

describe('<JobEvent />', () => {
  test('playbook event timestamps are rendered', () => {
    const wrapper1 = shallow(
      <JobEvent
        lineTextHtml={mockOnPlayStartLineTextHtml}
        event={mockOnPlayStartEvent}
      />
    );
    const lineText1 = wrapper1.find('JobEventLineText');
    const html1 = lineText1.at(1).prop('dangerouslySetInnerHTML').__html;
    expect(html1.includes('18:11:22')).toBe(true);

    const wrapper2 = shallow(
      <JobEvent
        lineTextHtml={mockSingleDigitTimestampEventLineTextHtml}
        event={singleDigitTimestampEvent}
      />
    );
    const lineText2 = wrapper2.find('JobEventLineText');
    const html2 = lineText2.at(1).prop('dangerouslySetInnerHTML').__html;
    expect(html2.includes('08:01:02')).toBe(true);
  });

  test('ansi stdout colors are rendered as html', () => {
    const wrapper = shallow(
      <JobEvent
        lineTextHtml={mockAnsiLineTextHtml}
        event={mockRunnerOnOkEvent}
      />
    );
    const lineText = wrapper.find('JobEventLineText');
    expect(
      lineText
        .prop('dangerouslySetInnerHTML')
        .__html.includes(
          '<span class="output--1977390340">ok: [localhost]</span>'
        )
    ).toBe(true);
  });

  test("events without stdout aren't rendered", () => {
    const missingStdoutEvent = { ...mockOnPlayStartEvent };
    delete missingStdoutEvent.stdout;
    const wrapper = shallow(
      <JobEvent lineTextHtml={[]} event={missingStdoutEvent} />
    );
    expect(wrapper.find('JobEventLineText')).toHaveLength(0);
  });
});
