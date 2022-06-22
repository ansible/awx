import React from 'react';
import { act } from 'react-dom/test-utils';
import { JobsAPI, JobEventsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import JobOutput from './JobOutput';
import mockJobData from '../shared/data.job.json';
import mockJobEventsData from './data.job_events.json';

jest.mock('../../../api');

const applyJobEventMock = (mockJobEvents) => {
  const mockReadEvents = async (jobId, params) => {
    const [...results] = mockJobEvents.results;
    if (params.order_by && params.order_by.includes('-')) {
      results.reverse();
    }
    return {
      data: {
        results,
        count: mockJobEvents.count,
      },
    };
  };
  JobsAPI.readEvents = jest.fn().mockImplementation(mockReadEvents);
  JobsAPI.readChildrenSummary = jest.fn().mockResolvedValue({
    data: {
      1: [0, 100],
    },
  });
};

describe('<JobOutput />', () => {
  let wrapper;
  const mockJob = mockJobData;

  beforeEach(() => {
    applyJobEventMock(mockJobEventsData);
    Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
      configurable: true,
      value: 200,
    });
    Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
      configurable: true,
      value: 100,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should make expected api call for delete', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    });
    await waitForElement(wrapper, 'JobEvent', (el) => el.length > 0);
    await act(async () =>
      wrapper.find('button[aria-label="Delete"]').simulate('click')
    );
    await waitForElement(
      wrapper,
      'Modal',
      (el) => el.props().isOpen === true && el.props().title === 'Delete Job'
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
    await waitForElement(wrapper, 'JobEvent', (el) => el.length > 0);
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Job Delete Error"]',
      (el) => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Job Delete Error"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Job Delete Error"]',
      (el) => el.length === 0
    );
    expect(JobsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('filter should be enabled after job finishes', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    });
    await waitForElement(wrapper, 'JobEvent', (el) => el.length > 0);
    expect(wrapper.find('Search').props().isDisabled).toBe(false);
  });

  test('filter should be disabled while job is running', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <JobOutput job={{ ...mockJob, status: 'running' }} />
      );
    });
    await waitForElement(wrapper, 'JobEvent', (el) => el.length > 0);
    expect(wrapper.find('Search').props().isDisabled).toBe(true);
  });

  test('should throw error', async () => {
    JobsAPI.readEvents = () => Promise.reject(new Error());
    await act(async () => {
      wrapper = mountWithContexts(<JobOutput job={mockJob} />);
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });
  test('should show failed empty output screen', async () => {
    JobsAPI.readEvents.mockResolvedValue({
      data: {
        count: 0,
        next: null,
        previous: null,
        results: [],
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <JobOutput job={{ ...mockJob, status: 'failed' }} />
      );
    });
    await waitForElement(wrapper, 'EmptyOutput', (el) => el.length === 1);
  });
});
