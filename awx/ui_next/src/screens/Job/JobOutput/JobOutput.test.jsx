import React from 'react';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import JobOutput from './JobOutput';
import { JobsAPI } from '@api';
import mockJobData from '../shared/data.job.json';
import mockJobEventsData from './data.job_events.json';

jest.mock('@api');

async function checkOutput(wrapper, expectedLines) {
  await waitForElement(wrapper, 'div[type="job_event"]', el => el.length > 1);
  const jobEventLines = wrapper.find('div[type="job_event_line_text"]');
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
  const menuControls = await waitForElement(wrapper, 'MenuControls');
  const scrollFirstButton = menuControls.find(
    'button[aria-label="scroll first"]'
  );
  const scrollLastButton = menuControls.find(
    'button[aria-label="scroll last"]'
  );
  const scrollPreviousButton = menuControls.find(
    'button[aria-label="scroll previous"]'
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

  test('initially renders succesfully', async done => {
    wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    await checkOutput(wrapper, [
      '',
      'PLAY [all] *********************************************************************15:37:25',
      '',
      'TASK [debug] *******************************************************************15:37:25',
      'ok: [localhost] => (item=1) => {',
      '    "msg": "This is a debug message: 1"',
      '}',
      'ok: [localhost] => (item=2) => {',
      '    "msg": "This is a debug message: 2"',
      '}',
      'ok: [localhost] => (item=3) => {',
      '    "msg": "This is a debug message: 3"',
      '}',
      'ok: [localhost] => (item=4) => {',
      '    "msg": "This is a debug message: 4"',
      '}',
      'ok: [localhost] => (item=5) => {',
      '    "msg": "This is a debug message: 5"',
      '}',
      'ok: [localhost] => (item=6) => {',
      '    "msg": "This is a debug message: 6"',
      '}',
      'ok: [localhost] => (item=7) => {',
      '    "msg": "This is a debug message: 7"',
      '}',
      'ok: [localhost] => (item=8) => {',
      '    "msg": "This is a debug message: 8"',
      '}',
      'ok: [localhost] => (item=9) => {',
      '    "msg": "This is a debug message: 9"',
      '}',
      'ok: [localhost] => (item=10) => {',
      '    "msg": "This is a debug message: 10"',
      '}',
      'ok: [localhost] => (item=11) => {',
      '    "msg": "This is a debug message: 11"',
      '}',
      'ok: [localhost] => (item=12) => {',
      '    "msg": "This is a debug message: 12"',
      '}',
      'ok: [localhost] => (item=13) => {',
      '    "msg": "This is a debug message: 13"',
      '}',
      'ok: [localhost] => (item=14) => {',
      '    "msg": "This is a debug message: 14"',
      '}',
      'ok: [localhost] => (item=15) => {',
      '    "msg": "This is a debug message: 15"',
      '}',
      'ok: [localhost] => (item=16) => {',
      '    "msg": "This is a debug message: 16"',
      '}',
    ]);

    expect(wrapper.find('JobOutput').length).toBe(1);
    done();
  });

  test('should call scrollToRow with expected index when scroll "previous" button is clicked', async done => {
    const handleScrollPrevious = jest.spyOn(
      JobOutput.prototype,
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
    done();
  });

  test('should call scrollToRow with expected indices on when scroll "first" and "last" buttons are clicked', async done => {
    const handleScrollFirst = jest.spyOn(
      JobOutput.prototype,
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
    done();
  });

  test('should call scrollToRow with expected index on when scroll "last" button is clicked', async done => {
    const handleScrollLast = jest.spyOn(
      JobOutput.prototype,
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
    done();
  });

  test('should throw error', async done => {
    JobsAPI.readEvents = () => Promise.reject(new Error());
    wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
    done();
  });
});
