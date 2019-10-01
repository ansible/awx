import React from 'react';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import {
  AdHocCommandsAPI,
  InventoryUpdatesAPI,
  JobsAPI,
  ProjectUpdatesAPI,
  SystemJobsAPI,
  UnifiedJobsAPI,
  WorkflowJobsAPI,
} from '@api';
import JobList from './JobList';

jest.mock('@api');

const mockResults = [
  {
    id: 1,
    url: '/api/v2/project_updates/1',
    name: 'job 1',
    type: 'project_update',
    summary_fields: {
      user_capabilities: {
        delete: true,
      },
    },
  },
  {
    id: 2,
    url: '/api/v2/jobs/2',
    name: 'job 2',
    type: 'job',
    summary_fields: {
      user_capabilities: {
        delete: true,
      },
    },
  },
  {
    id: 3,
    url: '/api/v2/inventory_updates/3',
    name: 'job 3',
    type: 'inventory_update',
    summary_fields: {
      user_capabilities: {
        delete: true,
      },
    },
  },
  {
    id: 4,
    url: '/api/v2/workflow_jobs/4',
    name: 'job 4',
    type: 'workflow_job',
    summary_fields: {
      user_capabilities: {
        delete: true,
      },
    },
  },
  {
    id: 5,
    url: '/api/v2/system_jobs/5',
    name: 'job 5',
    type: 'system_job',
    summary_fields: {
      user_capabilities: {
        delete: true,
      },
    },
  },
  {
    id: 6,
    url: '/api/v2/ad_hoc_commands/6',
    name: 'job 6',
    type: 'ad_hoc_command',
    summary_fields: {
      user_capabilities: {
        delete: true,
      },
    },
  },
];

UnifiedJobsAPI.read.mockResolvedValue({
  data: { count: 3, results: mockResults },
});

describe('<JobList />', () => {
  test('initially renders succesfully', async done => {
    const wrapper = mountWithContexts(<JobList />);
    await waitForElement(
      wrapper,
      'JobList',
      el => el.state('jobs').length === 6
    );

    done();
  });

  test('select makes expected state updates', async done => {
    const [mockItem] = mockResults;
    const wrapper = mountWithContexts(<JobList />);
    await waitForElement(wrapper, 'JobListItem', el => el.length === 6);

    wrapper
      .find('JobListItem')
      .first()
      .prop('onSelect')(mockItem);
    expect(wrapper.find('JobList').state('selected').length).toEqual(1);

    wrapper
      .find('JobListItem')
      .first()
      .prop('onSelect')(mockItem);
    expect(wrapper.find('JobList').state('selected').length).toEqual(0);

    done();
  });

  test('select-all-delete makes expected state updates and api calls', async done => {
    AdHocCommandsAPI.destroy = jest.fn();
    InventoryUpdatesAPI.destroy = jest.fn();
    JobsAPI.destroy = jest.fn();
    ProjectUpdatesAPI.destroy = jest.fn();
    SystemJobsAPI.destroy = jest.fn();
    WorkflowJobsAPI.destroy = jest.fn();
    const wrapper = mountWithContexts(<JobList />);
    await waitForElement(wrapper, 'JobListItem', el => el.length === 6);

    wrapper.find('DataListToolbar').prop('onSelectAll')(true);
    expect(wrapper.find('JobList').state('selected').length).toEqual(6);

    wrapper.find('DataListToolbar').prop('onSelectAll')(false);
    expect(wrapper.find('JobList').state('selected').length).toEqual(0);

    wrapper.find('DataListToolbar').prop('onSelectAll')(true);
    expect(wrapper.find('JobList').state('selected').length).toEqual(6);

    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    expect(AdHocCommandsAPI.destroy).toHaveBeenCalledTimes(1);
    expect(InventoryUpdatesAPI.destroy).toHaveBeenCalledTimes(1);
    expect(JobsAPI.destroy).toHaveBeenCalledTimes(1);
    expect(ProjectUpdatesAPI.destroy).toHaveBeenCalledTimes(1);
    expect(SystemJobsAPI.destroy).toHaveBeenCalledTimes(1);
    expect(WorkflowJobsAPI.destroy).toHaveBeenCalledTimes(1);

    done();
  });

  test('error is shown when job not successfully deleted from api', async done => {
    JobsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/jobs/2',
          },
          data: 'An error occurred',
        },
      })
    );
    const wrapper = mountWithContexts(<JobList />);
    wrapper.find('JobList').setState({
      jobs: mockResults,
      itemCount: 6,
      selected: mockResults.slice(1, 2),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );

    done();
  });
});
