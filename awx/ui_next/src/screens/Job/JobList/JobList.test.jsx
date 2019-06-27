import React from 'react';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import { UnifiedJobsAPI } from '@api';
import JobList from './JobList';

jest.mock('@api');

const mockResults = [{
  id: 1,
  url: '/api/v2/project_updates/1',
  name: 'job 1',
  type: 'project update',
  summary_fields: {
    user_capabilities: {
      delete: true,
    }
  }
}, {
  id: 2,
  url: '/api/v2/jobs/2',
  name: 'job 2',
  type: 'job',
  summary_fields: {
    user_capabilities: {
      delete: true,
    }
  }
}, {
  id: 3,
  url: '/api/v2/jobs/3',
  name: 'job 3',
  type: 'job',
  summary_fields: {
    user_capabilities: {
      delete: true,
    }
  }
}];

UnifiedJobsAPI.read.mockResolvedValue({ data: { count: 3, results: mockResults } });

describe('<JobList />', () => {
  test('initially renders succesfully', async (done) => {
    const wrapper = mountWithContexts(<JobList />);
    await waitForElement(wrapper, 'JobList', (el) => el.state('jobs').length === 3);

    done();
  });

  test('select makes expected state updates', async (done) => {
    const [mockItem] = mockResults;
    const wrapper = mountWithContexts(<JobList />);
    await waitForElement(wrapper, 'JobListItem', (el) => el.length === 3);

    wrapper.find('JobListItem').first().prop('onSelect')(mockItem);
    expect(wrapper.find('JobList').state('selected').length).toEqual(1);

    wrapper.find('JobListItem').first().prop('onSelect')(mockItem);
    expect(wrapper.find('JobList').state('selected').length).toEqual(0);

    done();
  });

  test('select-all-delete makes expected state updates and api calls', async (done) => {
    const wrapper = mountWithContexts(<JobList />);
    await waitForElement(wrapper, 'JobListItem', (el) => el.length === 3);

    wrapper.find('DataListToolbar').prop('onSelectAll')(true);
    expect(wrapper.find('JobList').state('selected').length).toEqual(3);

    wrapper.find('DataListToolbar').prop('onSelectAll')(false);
    expect(wrapper.find('JobList').state('selected').length).toEqual(0);

    wrapper.find('DataListToolbar').prop('onSelectAll')(true);
    expect(wrapper.find('JobList').state('selected').length).toEqual(3);

    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    expect(UnifiedJobsAPI.destroy).toHaveBeenCalledTimes(3);

    done();
  });
});
