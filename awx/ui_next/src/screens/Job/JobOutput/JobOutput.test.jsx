import React from 'react';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import JobOutput, { _JobOutput } from './JobOutput';
import { JobsAPI } from '../../../api';
import mockJobData from '../shared/data.job.json';
import mockJobEventsData from './data.job_events.json';

jest.mock('../../../api');

async function checkOutput(wrapper, expectedLines) {
  await waitForElement(wrapper, 'div[type="job_event"]', el => el.length > 1);
  const jobEventLines = wrapper.find('JobEventLineText div');
  const actualLines = [];
  jobEventLines.forEach(line => {
    actualLines.push(line.text());
  });
  expect(actualLines.length).toEqual(expectedLines.length);
  expectedLines.forEach((line, index) => {
    expect(actualLines[index]).toEqual(line);
  });
}

async function findScrollButtons(wrapper) {
  const pageControls = await waitForElement(wrapper, 'PageControls');
  const scrollFirstButton = pageControls.find(
    'button[aria-label="Scroll first"]'
  );
  const scrollLastButton = pageControls.find(
    'button[aria-label="Scroll last"]'
  );
  const scrollPreviousButton = pageControls.find(
    'button[aria-label="Scroll previous"]'
  );
  return {
    scrollFirstButton,
    scrollLastButton,
    scrollPreviousButton,
  };
}

describe('<JobOutput />', () => {
  let wrapper;
  const mockJob = mockJobData;
  const mockJobEvents = mockJobEventsData;
  const scrollMock = jest.fn();

  beforeEach(() => {
    JobsAPI.readEvents.mockResolvedValue({
      data: {
        count: 100,
        next: null,
        previous: null,
        results: mockJobEvents.results,
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('initially renders succesfully', async () => {
    wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    await checkOutput(wrapper, [
      'ok: [localhost] => (item=37) => {',
      '    "msg": "This is a debug message: 37"',
      '}',
      'ok: [localhost] => (item=38) => {',
      '    "msg": "This is a debug message: 38"',
      '}',
      'ok: [localhost] => (item=39) => {',
      '    "msg": "This is a debug message: 39"',
      '}',
      'ok: [localhost] => (item=40) => {',
      '    "msg": "This is a debug message: 40"',
      '}',
      'ok: [localhost] => (item=41) => {',
      '    "msg": "This is a debug message: 41"',
      '}',
      'ok: [localhost] => (item=42) => {',
      '    "msg": "This is a debug message: 42"',
      '}',
      'ok: [localhost] => (item=43) => {',
      '    "msg": "This is a debug message: 43"',
      '}',
      'ok: [localhost] => (item=44) => {',
      '    "msg": "This is a debug message: 44"',
      '}',
      'ok: [localhost] => (item=45) => {',
      '    "msg": "This is a debug message: 45"',
      '}',
      'ok: [localhost] => (item=46) => {',
      '    "msg": "This is a debug message: 46"',
      '}',
      'ok: [localhost] => (item=47) => {',
      '    "msg": "This is a debug message: 47"',
      '}',
      'ok: [localhost] => (item=48) => {',
      '    "msg": "This is a debug message: 48"',
      '}',
      'ok: [localhost] => (item=49) => {',
      '    "msg": "This is a debug message: 49"',
      '}',
      'ok: [localhost] => (item=50) => {',
      '    "msg": "This is a debug message: 50"',
      '}',
      'ok: [localhost] => (item=51) => {',
      '    "msg": "This is a debug message: 51"',
      '}',
      'ok: [localhost] => (item=52) => {',
      '    "msg": "This is a debug message: 52"',
      '}',
      'ok: [localhost] => (item=53) => {',
      '    "msg": "This is a debug message: 53"',
      '}',
      'ok: [localhost] => (item=54) => {',
      '    "msg": "This is a debug message: 54"',
      '}',
      'ok: [localhost] => (item=55) => {',
      '    "msg": "This is a debug message: 55"',
      '}',
      'ok: [localhost] => (item=56) => {',
      '    "msg": "This is a debug message: 56"',
      '}',
      'ok: [localhost] => (item=57) => {',
      '    "msg": "This is a debug message: 57"',
      '}',
      'ok: [localhost] => (item=58) => {',
      '    "msg": "This is a debug message: 58"',
      '}',
      'ok: [localhost] => (item=59) => {',
      '    "msg": "This is a debug message: 59"',
      '}',
      'ok: [localhost] => (item=60) => {',
      '    "msg": "This is a debug message: 60"',
      '}',
      'ok: [localhost] => (item=61) => {',
      '    "msg": "This is a debug message: 61"',
      '}',
      'ok: [localhost] => (item=62) => {',
      '    "msg": "This is a debug message: 62"',
      '}',
      'ok: [localhost] => (item=63) => {',
      '    "msg": "This is a debug message: 63"',
      '}',
      'ok: [localhost] => (item=64) => {',
      '    "msg": "This is a debug message: 64"',
      '}',
      'ok: [localhost] => (item=65) => {',
      '    "msg": "This is a debug message: 65"',
      '}',
      'ok: [localhost] => (item=66) => {',
      '    "msg": "This is a debug message: 66"',
      '}',
      'ok: [localhost] => (item=67) => {',
      '    "msg": "This is a debug message: 67"',
      '}',
      'ok: [localhost] => (item=68) => {',
      '    "msg": "This is a debug message: 68"',
      '}',
      'ok: [localhost] => (item=69) => {',
      '    "msg": "This is a debug message: 69"',
      '}',
      'ok: [localhost] => (item=70) => {',
      '    "msg": "This is a debug message: 70"',
      '}',
      'ok: [localhost] => (item=71) => {',
      '    "msg": "This is a debug message: 71"',
      '}',
      'ok: [localhost] => (item=72) => {',
      '    "msg": "This is a debug message: 72"',
      '}',
      'ok: [localhost] => (item=73) => {',
      '    "msg": "This is a debug message: 73"',
      '}',
      'ok: [localhost] => (item=74) => {',
      '    "msg": "This is a debug message: 74"',
      '}',
      'ok: [localhost] => (item=75) => {',
      '    "msg": "This is a debug message: 75"',
      '}',
      'ok: [localhost] => (item=76) => {',
      '    "msg": "This is a debug message: 76"',
      '}',
      'ok: [localhost] => (item=77) => {',
      '    "msg": "This is a debug message: 77"',
      '}',
      'ok: [localhost] => (item=78) => {',
      '    "msg": "This is a debug message: 78"',
      '}',
      'ok: [localhost] => (item=79) => {',
      '    "msg": "This is a debug message: 79"',
      '}',
      'ok: [localhost] => (item=80) => {',
      '    "msg": "This is a debug message: 80"',
      '}',
      'ok: [localhost] => (item=81) => {',
      '    "msg": "This is a debug message: 81"',
      '}',
      'ok: [localhost] => (item=82) => {',
      '    "msg": "This is a debug message: 82"',
      '}',
      'ok: [localhost] => (item=83) => {',
      '    "msg": "This is a debug message: 83"',
      '}',
      'ok: [localhost] => (item=84) => {',
      '    "msg": "This is a debug message: 84"',
      '}',
      'ok: [localhost] => (item=85) => {',
      '    "msg": "This is a debug message: 85"',
      '}',
      'ok: [localhost] => (item=86) => {',
      '    "msg": "This is a debug message: 86"',
      '}',
      'ok: [localhost] => (item=87) => {',
      '    "msg": "This is a debug message: 87"',
      '}',
      'ok: [localhost] => (item=88) => {',
      '    "msg": "This is a debug message: 88"',
      '}',
      'ok: [localhost] => (item=89) => {',
      '    "msg": "This is a debug message: 89"',
      '}',
      'ok: [localhost] => (item=90) => {',
      '    "msg": "This is a debug message: 90"',
      '}',
      'ok: [localhost] => (item=91) => {',
      '    "msg": "This is a debug message: 91"',
      '}',
      'ok: [localhost] => (item=92) => {',
      '    "msg": "This is a debug message: 92"',
      '}',
      'ok: [localhost] => (item=93) => {',
      '    "msg": "This is a debug message: 93"',
      '}',
      'ok: [localhost] => (item=94) => {',
      '    "msg": "This is a debug message: 94"',
      '}',
      '',
      'PLAY RECAP *********************************************************************15:37:26',
      'localhost                  : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   ',
      '',
    ]);

    expect(wrapper.find('JobOutput').length).toBe(1);
  });

  test('should call scrollToRow with expected index when scroll "previous" button is clicked', async () => {
    const handleScrollPrevious = jest.spyOn(
      _JobOutput.prototype,
      'handleScrollPrevious'
    );
    wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    const { scrollLastButton, scrollPreviousButton } = await findScrollButtons(
      wrapper
    );
    wrapper.find('JobOutput').instance().scrollToRow = scrollMock;

    scrollLastButton.simulate('click');
    scrollPreviousButton.simulate('click');

    expect(handleScrollPrevious).toHaveBeenCalled();
    expect(scrollMock).toHaveBeenCalledTimes(2);
    expect(scrollMock.mock.calls).toEqual([[100], [0]]);
  });

  test('should call scrollToRow with expected indices on when scroll "first" and "last" buttons are clicked', async () => {
    const handleScrollFirst = jest.spyOn(
      _JobOutput.prototype,
      'handleScrollFirst'
    );
    wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    const { scrollFirstButton, scrollLastButton } = await findScrollButtons(
      wrapper
    );
    wrapper.find('JobOutput').instance().scrollToRow = scrollMock;

    scrollFirstButton.simulate('click');
    scrollLastButton.simulate('click');
    scrollFirstButton.simulate('click');

    expect(handleScrollFirst).toHaveBeenCalled();
    expect(scrollMock).toHaveBeenCalledTimes(3);
    expect(scrollMock.mock.calls).toEqual([[0], [100], [0]]);
  });

  test('should call scrollToRow with expected index on when scroll "last" button is clicked', async () => {
    const handleScrollLast = jest.spyOn(
      _JobOutput.prototype,
      'handleScrollLast'
    );
    wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    await waitForElement(wrapper, 'EmptyStateBody', el => el.length === 0);
    wrapper
      .find('JobOutput')
      .instance()
      .handleResize({ width: 100 });
    const { scrollLastButton } = await findScrollButtons(wrapper);
    wrapper.find('JobOutput').instance().scrollToRow = scrollMock;

    scrollLastButton.simulate('click');

    expect(handleScrollLast).toHaveBeenCalled();
    expect(scrollMock).toHaveBeenCalledTimes(1);
    expect(scrollMock.mock.calls).toEqual([[100]]);
  });

  test('should make expected api call for delete', async () => {
    wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    wrapper.find('button[aria-label="Delete"]').simulate('click');
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Delete Job'
    );
    wrapper.find('Modal button[aria-label="Delete"]').simulate('click');
    expect(JobsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('should show error dialog for failed deletion', async () => {
    JobsAPI.destroy.mockRejectedValue(new Error({}));
    wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    wrapper.find('button[aria-label="Delete"]').simulate('click');
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Delete Job'
    );
    wrapper.find('Modal button[aria-label="Delete"]').simulate('click');
    await waitForElement(wrapper, 'Modal ErrorDetail');
    const errorModalCloseBtn = wrapper.find(
      'ModalBox[aria-label="Job Delete Error"] ModalBoxCloseButton'
    );
    errorModalCloseBtn.simulate('click');
    await waitForElement(wrapper, 'Modal ErrorDetail', el => el.length === 0);
  });

  test('should throw error', async () => {
    JobsAPI.readEvents = () => Promise.reject(new Error());
    wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
