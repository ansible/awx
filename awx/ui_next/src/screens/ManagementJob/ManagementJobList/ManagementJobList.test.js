import React from 'react';
import { act } from 'react-dom/test-utils';

import { SystemJobTemplatesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import ManagementJobList from './ManagementJobList';

jest.mock('../../../api/models/SystemJobTemplates');

const managementJobs = {
  data: {
    results: [
      {
        id: 1,
        name: 'Cleanup Activity Stream',
        description: 'Remove activity stream history',
        job_type: 'cleanup_activitystream',
        url: '/api/v2/system_job_templates/1/',
      },
      {
        id: 2,
        name: 'Cleanup Expired OAuth 2 Tokens',
        description: 'Cleanup expired OAuth 2 access and refresh tokens',
        job_type: 'cleanup_tokens',
        url: '/api/v2/system_job_templates/2/',
      },
      {
        id: 3,
        name: 'Cleanup Expired Sessions',
        description: 'Cleans out expired browser sessions',
        job_type: 'cleanup_sessions',
        url: '/api/v2/system_job_templates/3/',
      },
      {
        id: 4,
        name: 'Cleanup Job Details',
        description: 'Remove job history older than X days',
        job_type: 'cleanup_tokens',
        url: '/api/v2/system_job_templates/4/',
      },
    ],
    count: 4,
  },
};

const options = { data: { actions: { POST: true } } };

describe('<ManagementJobList/>', () => {
  beforeEach(() => {
    SystemJobTemplatesAPI.read.mockResolvedValue(managementJobs);
    SystemJobTemplatesAPI.readOptions.mockResolvedValue(options);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });
  let wrapper;

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<ManagementJobList />);
    });
    await waitForElement(wrapper, 'ManagementJobList', (el) => el.length > 0);
  });

  test('should have data fetched and render 4 rows', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<ManagementJobList />);
    });
    await waitForElement(wrapper, 'ManagementJobList', (el) => el.length > 0);

    expect(wrapper.find('ManagementJobListItem').length).toBe(4);
    expect(SystemJobTemplatesAPI.read).toBeCalled();
    expect(SystemJobTemplatesAPI.readOptions).toBeCalled();
  });

  test('should throw content error', async () => {
    SystemJobTemplatesAPI.read.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'GET',
            url: '/api/v2/system_job_templates',
          },
          data: 'An error occurred',
        },
      })
    );
    await act(async () => {
      wrapper = mountWithContexts(<ManagementJobList />);
    });
    await waitForElement(wrapper, 'ManagementJobList', (el) => el.length > 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should not render add button', async () => {
    SystemJobTemplatesAPI.read.mockResolvedValue(managementJobs);
    SystemJobTemplatesAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: false } },
    });
    await act(async () => {
      wrapper = mountWithContexts(<ManagementJobList />);
    });
    waitForElement(wrapper, 'ManagementJobList', (el) => el.length > 0);
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});
