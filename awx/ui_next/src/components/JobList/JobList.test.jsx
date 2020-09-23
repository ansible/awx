import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import {
  AdHocCommandsAPI,
  InventoryUpdatesAPI,
  JobsAPI,
  ProjectUpdatesAPI,
  SystemJobsAPI,
  UnifiedJobsAPI,
  WorkflowJobsAPI,
} from '../../api';
import JobList from './JobList';

jest.mock('../../api');

const mockResults = [
  {
    id: 1,
    url: '/api/v2/project_updates/1',
    name: 'job 1',
    type: 'project_update',
    status: 'running',
    related: {
      cancel: '/api/v2/project_updates/1/cancel',
    },
    summary_fields: {
      user_capabilities: {
        delete: true,
        start: true,
      },
    },
  },
  {
    id: 2,
    url: '/api/v2/jobs/2',
    name: 'job 2',
    type: 'job',
    status: 'running',
    related: {
      cancel: '/api/v2/jobs/2/cancel',
    },
    summary_fields: {
      user_capabilities: {
        delete: true,
        start: true,
      },
    },
  },
  {
    id: 3,
    url: '/api/v2/inventory_updates/3',
    name: 'job 3',
    type: 'inventory_update',
    status: 'running',
    related: {
      cancel: '/api/v2/inventory_updates/3/cancel',
    },
    summary_fields: {
      user_capabilities: {
        delete: true,
        start: true,
      },
    },
  },
  {
    id: 4,
    url: '/api/v2/workflow_jobs/4',
    name: 'job 4',
    type: 'workflow_job',
    status: 'running',
    related: {
      cancel: '/api/v2/workflow_jobs/4/cancel',
    },
    summary_fields: {
      user_capabilities: {
        delete: true,
        start: true,
      },
    },
  },
  {
    id: 5,
    url: '/api/v2/system_jobs/5',
    name: 'job 5',
    type: 'system_job',
    status: 'running',
    related: {
      cancel: '/api/v2/system_jobs/5/cancel',
    },
    summary_fields: {
      user_capabilities: {
        delete: true,
        edit: true,
      },
    },
  },
  {
    id: 6,
    url: '/api/v2/ad_hoc_commands/6',
    name: 'job 6',
    type: 'ad_hoc_command',
    status: 'running',
    related: {
      cancel: '/api/v2/ad_hoc_commands/6/cancel',
    },
    summary_fields: {
      user_capabilities: {
        delete: true,
        edit: true,
      },
    },
  },
];

UnifiedJobsAPI.read.mockResolvedValue({
  data: { count: 3, results: mockResults },
});

UnifiedJobsAPI.readOptions.mockResolvedValue({
  data: {
    actions: {
      GET: {},
      POST: {},
    },
    related_search_fields: [],
  },
});

function waitForLoaded(wrapper) {
  return waitForElement(
    wrapper,
    'JobList',
    el => el.find('ContentLoading').length === 0
  );
}

describe('<JobList />', () => {
  let debug;
  beforeEach(() => {
    debug = global.console.debug; // eslint-disable-line prefer-destructuring
    global.console.debug = () => {};
  });

  afterEach(() => {
    global.console.debug = debug;
  });

  test('initially renders succesfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobList />);
    });
    await waitForLoaded(wrapper);
    expect(wrapper.find('JobListItem')).toHaveLength(6);
  });

  test('should select and un-select items', async () => {
    const [mockItem] = mockResults;
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobList />);
    });
    await waitForLoaded(wrapper);

    act(() => {
      wrapper
        .find('JobListItem')
        .first()
        .invoke('onSelect')(mockItem);
    });
    wrapper.update();
    expect(
      wrapper
        .find('JobListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
    expect(
      wrapper.find('ToolbarDeleteButton').prop('itemsToDelete')
    ).toHaveLength(1);

    act(() => {
      wrapper
        .find('JobListItem')
        .first()
        .invoke('onSelect')(mockItem);
    });
    wrapper.update();
    expect(
      wrapper
        .find('JobListItem')
        .first()
        .prop('isSelected')
    ).toEqual(false);
    expect(
      wrapper.find('ToolbarDeleteButton').prop('itemsToDelete')
    ).toHaveLength(0);
  });

  test('should select and deselect all', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobList />);
    });
    await waitForLoaded(wrapper);

    act(() => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(true);
    });
    wrapper.update();
    wrapper.find('JobListItem');
    expect(
      wrapper.find('ToolbarDeleteButton').prop('itemsToDelete')
    ).toHaveLength(6);

    act(() => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(false);
    });
    wrapper.update();
    wrapper.find('JobListItem');
    expect(
      wrapper.find('ToolbarDeleteButton').prop('itemsToDelete')
    ).toHaveLength(0);
  });

  test('should send all corresponding delete API requests', async () => {
    AdHocCommandsAPI.destroy = jest.fn();
    InventoryUpdatesAPI.destroy = jest.fn();
    JobsAPI.destroy = jest.fn();
    ProjectUpdatesAPI.destroy = jest.fn();
    SystemJobsAPI.destroy = jest.fn();
    WorkflowJobsAPI.destroy = jest.fn();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobList />);
    });
    await waitForLoaded(wrapper);

    act(() => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(true);
    });
    wrapper.update();
    wrapper.find('JobListItem');
    expect(
      wrapper.find('ToolbarDeleteButton').prop('itemsToDelete')
    ).toHaveLength(6);

    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    expect(AdHocCommandsAPI.destroy).toHaveBeenCalledTimes(1);
    expect(InventoryUpdatesAPI.destroy).toHaveBeenCalledTimes(1);
    expect(JobsAPI.destroy).toHaveBeenCalledTimes(1);
    expect(ProjectUpdatesAPI.destroy).toHaveBeenCalledTimes(1);
    expect(SystemJobsAPI.destroy).toHaveBeenCalledTimes(1);
    expect(WorkflowJobsAPI.destroy).toHaveBeenCalledTimes(1);

    jest.restoreAllMocks();
  });

  test('error is shown when job not successfully deleted from api', async () => {
    JobsAPI.destroy.mockImplementation(() => {
      throw new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/jobs/2',
          },
          data: 'An error occurred',
        },
      });
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobList />);
    });
    await waitForLoaded(wrapper);
    await act(async () => {
      wrapper
        .find('JobListItem')
        .at(1)
        .invoke('onSelect')();
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    wrapper.update();
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );
  });

  test('should send all corresponding delete API requests', async () => {
    JobsAPI.cancel = jest.fn();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobList />);
    });
    await waitForLoaded(wrapper);

    act(() => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(true);
    });
    wrapper.update();
    wrapper.find('JobListItem');
    expect(
      wrapper.find('JobListCancelButton').prop('jobsToCancel')
    ).toHaveLength(6);

    await act(async () => {
      wrapper.find('JobListCancelButton').invoke('onCancel')();
    });

    expect(JobsAPI.cancel).toHaveBeenCalledTimes(6);
    expect(JobsAPI.cancel).toHaveBeenCalledWith(1, 'project_update');
    expect(JobsAPI.cancel).toHaveBeenCalledWith(2, 'job');
    expect(JobsAPI.cancel).toHaveBeenCalledWith(3, 'inventory_update');
    expect(JobsAPI.cancel).toHaveBeenCalledWith(4, 'workflow_job');
    expect(JobsAPI.cancel).toHaveBeenCalledWith(5, 'system_job');
    expect(JobsAPI.cancel).toHaveBeenCalledWith(6, 'ad_hoc_command');

    jest.restoreAllMocks();
  });

  test('error is shown when job not successfully cancelled', async () => {
    JobsAPI.cancel.mockImplementation(() => {
      throw new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/jobs/2/cancel',
          },
          data: 'An error occurred',
        },
      });
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<JobList />);
    });
    await waitForLoaded(wrapper);
    await act(async () => {
      wrapper
        .find('JobListItem')
        .at(1)
        .invoke('onSelect')();
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('JobListCancelButton').invoke('onCancel')();
    });
    wrapper.update();
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );
  });
});
