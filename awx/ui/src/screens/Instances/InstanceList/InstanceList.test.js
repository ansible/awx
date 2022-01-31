import React from 'react';
import { act } from 'react-dom/test-utils';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';

import { InstancesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import InstanceList from './InstanceList';

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
  }),
}));

const instances = [
  {
    id: 1,
    type: 'instance',
    url: '/api/v2/instances/1/',
    capacity_adjustment: '0.40',
    version: '13.0.0',
    capacity: 10,
    consumed_capacity: 0,
    percent_capacity_remaining: 60.0,
    jobs_running: 0,
    jobs_total: 68,
    cpu: 6,
    node_type: 'control',
    memory: 2087469056,
    cpu_capacity: 24,
    mem_capacity: 1,
    enabled: true,
    managed_by_policy: true,
  },
  {
    id: 2,
    type: 'instance',
    url: '/api/v2/instances/2/',
    capacity_adjustment: '0.40',
    version: '13.0.0',
    capacity: 10,
    consumed_capacity: 0,
    percent_capacity_remaining: 60.0,
    jobs_running: 0,
    jobs_total: 68,
    cpu: 6,
    node_type: 'hybrid',
    memory: 2087469056,
    cpu_capacity: 24,
    mem_capacity: 1,
    enabled: true,
    managed_by_policy: false,
  },
  {
    id: 3,
    type: 'instance',
    url: '/api/v2/instances/3/',
    capacity_adjustment: '0.40',
    version: '13.0.0',
    capacity: 10,
    consumed_capacity: 0,
    percent_capacity_remaining: 60.0,
    jobs_running: 0,
    jobs_total: 68,
    cpu: 6,
    node_type: 'execution',
    memory: 2087469056,
    cpu_capacity: 24,
    mem_capacity: 1,
    enabled: false,
    managed_by_policy: true,
  },
  {
    id: 4,
    type: 'instance',
    url: '/api/v2/instances/4/',
    capacity_adjustment: '0.40',
    version: '13.0.0',
    capacity: 10,
    consumed_capacity: 0,
    percent_capacity_remaining: 60.0,
    jobs_running: 0,
    jobs_total: 68,
    cpu: 6,
    node_type: 'hop',
    memory: 2087469056,
    cpu_capacity: 24,
    mem_capacity: 1,
    enabled: false,
    managed_by_policy: true,
  },
];

describe('<InstanceList/>', () => {
  let wrapper;

  const options = { data: { actions: { POST: true } } };

  beforeEach(async () => {
    InstancesAPI.read.mockResolvedValue({
      data: {
        count: instances.length,
        results: instances,
      },
    });
    InstancesAPI.readOptions.mockResolvedValue(options);
    const history = createMemoryHistory({
      initialEntries: ['/instances/1'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/instances/:id">
          <InstanceList />
        </Route>,
        {
          context: {
            router: { history, route: { location: history.location } },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should have data fetched', () => {
    expect(wrapper.find('InstanceList').length).toBe(1);
  });

  test('should fetch instances from the api and render them in the list', () => {
    expect(InstancesAPI.read).toHaveBeenCalled();
    expect(InstancesAPI.readOptions).toHaveBeenCalled();
    expect(wrapper.find('InstanceListItem').length).toBe(4);
  });

  test('should run health check', async () => {
    // Ensures health check button is disabled on mount
    expect(
      wrapper.find('Button[ouiaId="health-check"]').prop('isDisabled')
    ).toBe(true);
    await act(async () =>
      wrapper.find('DataListToolbar').prop('onSelectAll')(instances)
    );
    wrapper.update();

    // Ensures health check button is disabled because a hop node is among
    // the selected.
    expect(
      wrapper.find('Button[ouiaId="health-check"]').prop('isDisabled')
    ).toBe(true);

    await act(async () =>
      wrapper.find('input[aria-label="Select row 3"]').prop('onChange')(false)
    );
    wrapper.update();
    await act(async () =>
      wrapper.find('Button[ouiaId="health-check"]').prop('onClick')()
    );
    expect(InstancesAPI.healthCheck).toBeCalledTimes(3);
  });
  test('should render health check error', async () => {
    InstancesAPI.healthCheck.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'create',
            url: '/api/v2/instances',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    expect(
      wrapper.find('Button[ouiaId="health-check"]').prop('isDisabled')
    ).toBe(true);
    await act(async () =>
      wrapper.find('input[aria-label="Select row 1"]').prop('onChange')(true)
    );
    wrapper.update();
    expect(
      wrapper.find('Button[ouiaId="health-check"]').prop('isDisabled')
    ).toBe(false);
    await act(async () =>
      wrapper.find('Button[ouiaId="health-check"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('AlertModal')).toHaveLength(1);
  });

  test('Health check button should remain disabled', async () => {
    await act(async () =>
      wrapper.find('input[aria-label="Select row 3"]').prop('onChange')(true)
    );
    wrapper.update();
    expect(
      wrapper.find('Button[ouiaId="health-check"]').prop('isDisabled')
    ).toBe(true);
    expect(wrapper.find('Tooltip[ouiaId="healthCheckTooltip"]').length).toBe(1);
  });
});
