import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import useDebounce from 'hooks/useDebounce';
import { InstancesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import InstanceEdit from './InstanceEdit';

jest.mock('../../../api');
jest.mock('../../../hooks/useDebounce');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 42,
  }),
}));

const instanceData = {
  id: 42,
  hostname: 'awx_1',
  type: 'instance',
  url: '/api/v2/instances/1/',
  related: {
    named_url: '/api/v2/instances/awx_1/',
    jobs: '/api/v2/instances/1/jobs/',
    instance_groups: '/api/v2/instances/1/instance_groups/',
    peers: '/api/v2/instances/1/peers/',
  },
  summary_fields: {
    user_capabilities: {
      edit: false,
    },
    links: [],
  },
  uuid: '00000000-0000-0000-0000-000000000000',
  created: '2023-04-26T22:06:46.766198Z',
  modified: '2023-04-26T22:06:46.766217Z',
  last_seen: '2023-04-26T23:12:02.857732Z',
  health_check_started: null,
  health_check_pending: false,
  last_health_check: '2023-04-26T23:01:13.941693Z',
  errors: 'Instance received normal shutdown signal',
  capacity_adjustment: '1.00',
  version: '0.1.dev33237+g1fdef52',
  capacity: 0,
  consumed_capacity: 0,
  percent_capacity_remaining: 0,
  jobs_running: 0,
  jobs_total: 0,
  cpu: '8.0',
  memory: 8011055104,
  cpu_capacity: 0,
  mem_capacity: 0,
  enabled: true,
  managed_by_policy: true,
  node_type: 'hybrid',
  node_state: 'installed',
  ip_address: null,
  listener_port: 27199,
  peers: [],
  peers_from_control_nodes: false,
};

const instanceDataWithPeers = {
  results: [instanceData],
};

const updatedInstance = {
  node_type: 'hop',
  peers: ['test-peer'],
};

describe('<InstanceEdit/>', () => {
  let wrapper;
  let history;

  beforeAll(async () => {
    useDebounce.mockImplementation((fn) => fn);
    history = createMemoryHistory();
    InstancesAPI.readDetail.mockResolvedValue({ data: instanceData });
    InstancesAPI.readPeers.mockResolvedValue({ data: instanceDataWithPeers });

    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceEdit
          instance={instanceData}
          peers={instanceDataWithPeers}
          isEdit
          setBreadcrumb={() => {}}
        />,
        {
          context: { router: { history } },
        }
      );
    });
    expect(InstancesAPI.readDetail).toBeCalledWith(42);
  });

  afterAll(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', async () => {
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('InstanceEdit')).toHaveLength(1);
  });

  test('handleSubmit should call the api and redirect to details page', async () => {
    await act(async () => {
      wrapper.find('InstanceForm').invoke('handleSubmit')(updatedInstance);
    });
    expect(InstancesAPI.update).toHaveBeenCalledWith(42, updatedInstance);
    expect(history.location.pathname).toEqual('/instances/42/details');
  });

  test('should navigate to instance details when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').simulate('click');
    });
    expect(history.location.pathname).toEqual('/instances/42/details');
  });

  test('should navigate to instance details after successful submission', async () => {
    await act(async () => {
      wrapper.find('InstanceForm').invoke('handleSubmit')(updatedInstance);
    });
    wrapper.update();
    expect(wrapper.find('submitError').length).toBe(0);
    expect(history.location.pathname).toEqual('/instances/42/details');
  });

  test('failed form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    InstancesAPI.update.mockImplementationOnce(() => Promise.reject(error));
    await act(async () => {
      wrapper.find('InstanceForm').invoke('handleSubmit')(updatedInstance);
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
