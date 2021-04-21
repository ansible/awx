import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import JobOutput from './JobOutput';
import { JobsAPI } from '../../../api';
import mockJobData from '../shared/data.job.json';
import mockJobEventsData from './data.job_events.json';
import mockFilteredJobEventsData from './data.filtered_job_events.json';

jest.mock('../../../api');

const generateChattyRows = () => {
  const rows = [
    '',
    'PLAY [all] *********************************************************************16:17:13',
    '',
    'TASK [debug] *******************************************************************16:17:13',
  ];

  for (let i = 1; i < 95; i++) {
    rows.push(
      `ok: [localhost] => (item=${i}) => {`,
      `    "msg": "This is a debug message: ${i}"`,
      '}'
    );
  }

  rows.push(
    '',
    'PLAY RECAP *********************************************************************16:17:15',
    'localhost                  : ok=1    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   ',
    ''
  );

  return rows;
};

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

const originalOffsetHeight = Object.getOwnPropertyDescriptor(
  HTMLElement.prototype,
  'offsetHeight'
);
const originalOffsetWidth = Object.getOwnPropertyDescriptor(
  HTMLElement.prototype,
  'offsetWidth'
);

describe('<JobOutput />', () => {
  let wrapper;
  const mockJob = mockJobData;
  const mockJobEvents = mockJobEventsData;
  beforeAll(() => {
    jest.setTimeout(5000 * 4);
  });

  afterAll(() => {
    jest.setTimeout(5000);
  });
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
    await act(async () => {
      wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    });
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);

    await checkOutput(wrapper, generateChattyRows());

    expect(wrapper.find('JobOutput').length).toBe(1);
  });

  test('navigation buttons should display output properly', async () => {
    Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
      configurable: true,
      value: 10,
    });
    Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
      configurable: true,
      value: 100,
    });
    await act(async () => {
      wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    });
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    const {
      scrollFirstButton,
      scrollLastButton,
      scrollPreviousButton,
    } = await findScrollButtons(wrapper);
    let jobEvents = wrapper.find('JobEvent');
    expect(jobEvents.at(0).prop('stdout')).toBe('');
    expect(jobEvents.at(1).prop('stdout')).toBe(
      '\r\nPLAY [all] *********************************************************************'
    );
    await act(async () => {
      scrollLastButton.simulate('click');
    });
    wrapper.update();
    jobEvents = wrapper.find('JobEvent');
    expect(jobEvents.at(jobEvents.length - 2).prop('stdout')).toBe(
      '\r\nPLAY RECAP *********************************************************************\r\n\u001b[0;32mlocalhost\u001b[0m                  : \u001b[0;32mok=1   \u001b[0m changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   \r\n'
    );
    expect(jobEvents.at(jobEvents.length - 1).prop('stdout')).toBe('');
    await act(async () => {
      scrollPreviousButton.simulate('click');
    });
    wrapper.update();
    jobEvents = wrapper.find('JobEvent');
    expect(jobEvents.at(0).prop('stdout')).toBe(
      '\u001b[0;32mok: [localhost] => (item=76) => {\u001b[0m\r\n\u001b[0;32m    "msg": "This is a debug message: 76"\u001b[0m\r\n\u001b[0;32m}\u001b[0m'
    );
    expect(jobEvents.at(1).prop('stdout')).toBe(
      '\u001b[0;32mok: [localhost] => (item=77) => {\u001b[0m\r\n\u001b[0;32m    "msg": "This is a debug message: 77"\u001b[0m\r\n\u001b[0;32m}\u001b[0m'
    );
    await act(async () => {
      scrollFirstButton.simulate('click');
    });
    wrapper.update();
    jobEvents = wrapper.find('JobEvent');
    expect(jobEvents.at(0).prop('stdout')).toBe('');
    expect(jobEvents.at(1).prop('stdout')).toBe(
      '\r\nPLAY [all] *********************************************************************'
    );
    await act(async () => {
      scrollLastButton.simulate('click');
    });
    wrapper.update();
    jobEvents = wrapper.find('JobEvent');
    expect(jobEvents.at(jobEvents.length - 2).prop('stdout')).toBe(
      '\r\nPLAY RECAP *********************************************************************\r\n\u001b[0;32mlocalhost\u001b[0m                  : \u001b[0;32mok=1   \u001b[0m changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   \r\n'
    );
    expect(jobEvents.at(jobEvents.length - 1).prop('stdout')).toBe('');
    Object.defineProperty(
      HTMLElement.prototype,
      'offsetHeight',
      originalOffsetHeight
    );
    Object.defineProperty(
      HTMLElement.prototype,
      'offsetWidth',
      originalOffsetWidth
    );
  });

  test('should make expected api call for delete', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    });
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    await act(async () =>
      wrapper.find('button[aria-label="Delete"]').simulate('click')
    );
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Delete Job'
    );
    await act(async () =>
      wrapper
        .find('Modal button[aria-label="Confirm Delete"]')
        .simulate('click')
    );
    expect(JobsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('should show error dialog for failed deletion', async () => {
    JobsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: `/api/v2/jobs/${mockJob.id}`,
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    });
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Job Delete Error"]',
      el => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Job Delete Error"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Job Delete Error"]',
      el => el.length === 0
    );
    expect(JobsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('filter should be enabled after job finishes', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    });
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    expect(wrapper.find('Search').props().isDisabled).toBe(false);
  });

  test('filter should be disabled while job is running', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <JobOutput job={{ ...mockJob, status: 'running' }} />
      );
    });
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    expect(wrapper.find('Search').props().isDisabled).toBe(true);
  });

  test('filter should trigger api call and display correct rows', async () => {
    jest.setTimeout(5000 * 4);
    const searchBtn = 'button[aria-label="Search submit button"]';
    const searchTextInput = 'input[aria-label="Search text input"]';
    await act(async () => {
      wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    });
    await waitForElement(wrapper, 'JobEvent', el => el.length > 0);
    JobsAPI.readEvents.mockClear();
    JobsAPI.readEvents.mockResolvedValueOnce({
      data: mockFilteredJobEventsData,
    });
    await act(async () => {
      wrapper.find(searchTextInput).instance().value = '99';
      wrapper.find(searchTextInput).simulate('change');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find(searchBtn).simulate('click');
    });
    wrapper.update();
    expect(JobsAPI.readEvents).toHaveBeenCalledWith(2, {
      order_by: 'start_line',
      page: 1,
      page_size: 50,
      stdout__icontains: '99',
    });
    const jobEvents = wrapper.find('JobEvent');
    expect(jobEvents.at(0).prop('stdout')).toBe(
      '\u001b[0;32mok: [localhost] => (item=99) => {\u001b[0m\r\n\u001b[0;32m    "msg": "This is a debug message: 99"\u001b[0m\r\n\u001b[0;32m}\u001b[0m'
    );
    expect(jobEvents.at(1).prop('stdout')).toBe(
      '\u001b[0;32mok: [localhost] => (item=199) => {\u001b[0m\r\n\u001b[0;32m    "msg": "This is a debug message: 199"\u001b[0m\r\n\u001b[0;32m}\u001b[0m'
    );
  });

  test('should throw error', async () => {
    JobsAPI.readEvents = () => Promise.reject(new Error());
    await act(async () => {
      wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
