import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

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
const selectors = {
  lineText: 'JobEventLineText',
};

describe('<JobEvent />', () => {
  test('initially renders successfully', () => {
    mountWithContexts(<JobEvent {...mockOnPlayStartEvent} />);
  });

  test('playbook event timestamps are rendered', () => {
    let wrapper = mountWithContexts(<JobEvent {...mockOnPlayStartEvent} />);
    let lineText = wrapper.find(selectors.lineText);
    expect(
      lineText.filterWhere(e => e.text().includes('18:11:22'))
    ).toHaveLength(1);

    const singleDigitTimestampEvent = {
      ...mockOnPlayStartEvent,
      created: '2019-07-11T08:01:02.906001Z',
    };
    wrapper = mountWithContexts(<JobEvent {...singleDigitTimestampEvent} />);
    lineText = wrapper.find(selectors.lineText);
    expect(
      lineText.filterWhere(e => e.text().includes('08:01:02'))
    ).toHaveLength(1);
  });

  test('ansi stdout colors are rendered as html', () => {
    const wrapper = mountWithContexts(<JobEvent {...mockRunnerOnOkEvent} />);
    const lineText = wrapper.find(selectors.lineText);
    expect(
      lineText
        .html()
        .includes('<span style="color:#486B00">ok: [localhost]</span>')
    ).toBe(true);
  });

  test("events without stdout aren't rendered", () => {
    const missingStdoutEvent = { ...mockOnPlayStartEvent };
    delete missingStdoutEvent.stdout;
    const wrapper = mountWithContexts(<JobEvent {...missingStdoutEvent} />);
    expect(wrapper.find(selectors.lineText)).toHaveLength(0);
  });
});
