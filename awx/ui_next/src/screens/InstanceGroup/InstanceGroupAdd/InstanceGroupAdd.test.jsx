import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { InstanceGroupsAPI } from '../../../api';
import InstanceGroupAdd from './InstanceGroupAdd';

jest.mock('../../../api');

const instanceGroupData = {
  id: 42,
  type: 'instance_group',
  url: '/api/v2/instance_groups/42/',
  related: {
    jobs: '/api/v2/instance_groups/42/jobs/',
    instances: '/api/v2/instance_groups/7/instances/',
  },
  name: 'Bar',
  created: '2020-07-21T18:41:02.818081Z',
  modified: '2020-07-24T20:32:03.121079Z',
  capacity: 24,
  committed_capacity: 0,
  consumed_capacity: 0,
  percent_capacity_remaining: 100.0,
  jobs_running: 0,
  jobs_total: 0,
  instances: 1,
  controller: null,
  is_controller: false,
  is_isolated: false,
  is_containerized: false,
  credential: null,
  policy_instance_percentage: 46,
  policy_instance_minimum: 12,
  policy_instance_list: [],
  pod_spec_override: '',
  summary_fields: {
    user_capabilities: {
      edit: true,
      delete: true,
    },
  },
};

InstanceGroupsAPI.create.mockResolvedValue({
  data: {
    id: 42,
  },
});

describe('<InstanceGroupAdd/>', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/instance_groups'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<InstanceGroupAdd />, {
        context: { router: { history } },
      });
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('handleSubmit should call the api and redirect to details page', async () => {
    await act(async () => {
      wrapper.find('InstanceGroupForm').prop('onSubmit')(instanceGroupData);
    });
    wrapper.update();
    expect(InstanceGroupsAPI.create).toHaveBeenCalledWith(instanceGroupData);
    expect(history.location.pathname).toBe('/instance_groups/42/details');
  });

  test('handleCancel should return the user back to the instance group list', async () => {
    wrapper.find('Button[aria-label="Cancel"]').simulate('click');
    expect(history.location.pathname).toEqual('/instance_groups');
  });

  test('failed form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    InstanceGroupsAPI.create.mockImplementationOnce(() =>
      Promise.reject(error)
    );
    await act(async () => {
      wrapper.find('InstanceGroupForm').invoke('onSubmit')(instanceGroupData);
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
