import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { InstanceGroupsAPI } from '../../../api';

import InstanceGroupEdit from './InstanceGroupEdit';

jest.mock('../../../api');

const instanceGroupData = {
  id: 42,
  type: 'instance_group',
  url: '/api/v2/instance_groups/42/',
  related: {
    jobs: '/api/v2/instance_groups/42/jobs/',
    instances: '/api/v2/instance_groups/7/instances/',
  },
  name: 'Foo',
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

const updatedInstanceGroup = {
  name: 'Bar',
  policy_instance_percentage: 42,
};

describe('<InstanceGroupEdit>', () => {
  let wrapper;
  let history;

  beforeAll(async () => {
    history = createMemoryHistory();
    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceGroupEdit instanceGroup={instanceGroupData} />,
        {
          context: { router: { history } },
        }
      );
    });
  });

  afterAll(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('tower instance group name can not be updated', async () => {
    let towerWrapper;
    await act(async () => {
      towerWrapper = mountWithContexts(
        <InstanceGroupEdit
          instanceGroup={{ ...instanceGroupData, name: 'tower' }}
        />,
        {
          context: { router: { history } },
        }
      );
    });
    expect(
      towerWrapper.find('input#instance-group-name').prop('disabled')
    ).toBeTruthy();
    expect(
      towerWrapper.find('input#instance-group-name').prop('value')
    ).toEqual('tower');
  });

  test('handleSubmit should call the api and redirect to details page', async () => {
    await act(async () => {
      wrapper.find('InstanceGroupForm').invoke('onSubmit')(
        updatedInstanceGroup
      );
    });
    expect(InstanceGroupsAPI.update).toHaveBeenCalledWith(
      42,
      updatedInstanceGroup
    );
  });

  test('should navigate to instance group details when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    });
    expect(history.location.pathname).toEqual('/instance_groups/42/details');
  });

  test('should navigate to instance group details after successful submission', async () => {
    await act(async () => {
      wrapper.find('InstanceGroupForm').invoke('onSubmit')(
        updatedInstanceGroup
      );
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(history.location.pathname).toEqual('/instance_groups/42/details');
  });

  test('failed form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    InstanceGroupsAPI.update.mockImplementationOnce(() =>
      Promise.reject(error)
    );
    await act(async () => {
      wrapper.find('InstanceGroupForm').invoke('onSubmit')(
        updatedInstanceGroup
      );
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
